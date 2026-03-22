import logging
import requests
from celery import shared_task

from c2_core.config.logging import log_function_call
from c2_core.settings import API_BASE_URL
from apps.core.models import Subdomain, URLResult, URLScan

logger = logging.getLogger(__name__)

# API Endpoints
GET_ALL_URL_ENDPOINT_TEMPLATE = f"{API_BASE_URL}/api/get_all_url/get_all_url"
FLARESOLVERR_START_SCANNER_URL = f"{API_BASE_URL}/api/flaresolverr/start_scanner"


@shared_task(name="scheduler.tasks.scan_subdomains_without_url_results")
@log_function_call()
def scan_subdomains_without_url_results(batch_size: int = 5):
    logger.info(f"定時任務啟動：查找無被GAU掃描的子域名 (Limit {batch_size})")
    gau_subdomain_ids = URLScan.objects.filter(tool="gau").values_list(
        "target_subdomain_id", flat=True
    )

    # 2. 排除掉這些 ID
    subdomains_to_scan = (
        Subdomain.objects.filter(is_active=True, is_resolvable=True, target__isnull=False)
        .exclude(id__in=gau_subdomain_ids)
        .order_by("-id")[:batch_size]
    )

    actual_count = len(subdomains_to_scan)
    if actual_count == 0:
        return "No new Subdomains to scan."

    success_count = 0
    for sub_obj in subdomains_to_scan:
        try:
            resp = requests.post(
                GET_ALL_URL_ENDPOINT_TEMPLATE, json={"name": sub_obj.name}, timeout=5
            )
            if 200 <= resp.status_code < 300:
                success_count += 1
        except Exception as e:
            logger.error(f"URL Scan Req Failed ({sub_obj.name}): {e}")

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

    success_count = 0
    for url_obj in urls_to_scan:
        try:
            resp = requests.post(
                FLARESOLVERR_START_SCANNER_URL,
                json={
                    "url": url_obj.url,
                    "method": "GET",
                    "target_id": url_obj.target_id,
                },
                timeout=5,
            )
            if 200 <= resp.status_code < 300:
                success_count += 1
        except Exception as e:
            logger.error(f"FlareSolverr Req Failed ({url_obj.url}): {e}")

    return f"Triggered Fetch for {success_count}/{actual_count} URLs."
