import asyncio
import logging

import httpx
from celery import shared_task

from c2_core.config.logging import log_function_call
from c2_core.settings import API_BASE_URL
from apps.core.models import Subdomain, URLResult, URLScan

logger = logging.getLogger(__name__)

# API Endpoints
GET_ALL_URL_ENDPOINT_TEMPLATE = f"{API_BASE_URL}/api/scanners/crawler/get_all_url"
FLARESOLVERR_START_SCANNER_URL = f"{API_BASE_URL}/api/flaresolverr/start_scanner"


async def _post_all(url: str, payloads: list, timeout: int = 5) -> int:
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = [client.post(url, json=p) for p in payloads]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    return sum(
        1 for r in results
        if isinstance(r, httpx.Response) and 200 <= r.status_code < 300
    )


@shared_task(name="scheduler.tasks.scan_subdomains_without_url_results")
@log_function_call()
def scan_subdomains_without_url_results(batch_size: int = 5):
    logger.info(f"定時任務啟動：查找無被GAU掃描的子域名 (Limit {batch_size})")
    gau_subdomain_ids = URLScan.objects.filter(tool="gau").values_list(
        "target_subdomain_id", flat=True
    )

    subdomains_to_scan = (
        Subdomain.objects.filter(is_active=True, is_resolvable=True, target__isnull=False)
        .exclude(id__in=gau_subdomain_ids)
        .order_by("-id")[:batch_size]
    )

    actual_count = len(subdomains_to_scan)
    if actual_count == 0:
        return "No new Subdomains to scan."

    payloads = [{"name": sub.name, "subdomain_id": sub.id} for sub in subdomains_to_scan]
    success_count = asyncio.run(_post_all(GET_ALL_URL_ENDPOINT_TEMPLATE, payloads))
    return f"Triggered URL Scan for {success_count}/{actual_count} Subdomains."


@shared_task(name="scheduler.tasks.scan_urls_missing_response")
@log_function_call()
def scan_urls_missing_response(batch_size: int = 5):
    logger.info(f"定時任務啟動：查找未抓取內容的 URL (Limit {batch_size})")

    urls_to_scan = URLResult.objects.filter(
        content_fetch_status="PENDING",
        target__isnull=False
    ).order_by("-id")[:batch_size]

    actual_count = len(urls_to_scan)
    if actual_count == 0:
        return "No new URLs to fetch."

    payloads = [
        {"url": url_obj.url, "method": "GET", "target_id": url_obj.target_id}
        for url_obj in urls_to_scan
    ]
    success_count = asyncio.run(_post_all(FLARESOLVERR_START_SCANNER_URL, payloads))
    return f"Triggered Fetch for {success_count}/{actual_count} URLs."
