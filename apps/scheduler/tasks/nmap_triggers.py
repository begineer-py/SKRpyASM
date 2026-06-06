import logging

import httpx
from asgiref.sync import sync_to_async
from celery import shared_task
from django.db.models import Count

from c2_core.config.logging import log_function_call
from c2_core.settings import API_BASE_URL
from apps.core.models import IP

logger = logging.getLogger(__name__)

# API Endpoints
NMAP_API_ENDPOINT = f"{API_BASE_URL}/api/scanners/nmap/start_scan"


async def _post_all(url: str, payloads: list, timeout: int = 10) -> int:
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = [client.post(url, json=p) for p in payloads]
        import asyncio
        results = await asyncio.gather(*tasks, return_exceptions=True)
    return sum(
        1 for r in results
        if isinstance(r, httpx.Response) and 200 <= r.status_code < 300
    )


@shared_task(name="scheduler.tasks.scan_ips_without_nmap_results")
@log_function_call()
async def scan_ips_without_nmap_results(batch_size: int = 10):
    logger.info(f"定時任務啟動：查找無 Nmap 記錄的 IP (Limit {batch_size})")

    def _fetch():
        return list(
            IP.objects.annotate(scan_count=Count("discovered_by_scans"))
            .filter(
                scan_count=0,
                target__isnull=False,
                which_seed__isnull=False
            )
            .prefetch_related("which_seed")[:batch_size]
        )

    def _build_payloads(ips):
        return [
            {"seed_ids": [s.id for s in ip_obj.which_seed.all()], "ip": ip_obj.address}
            for ip_obj in ips
        ]

    ips_to_scan = await sync_to_async(_fetch)()
    actual_count = len(ips_to_scan)
    if actual_count == 0:
        return "No new IPs to scan."

    payloads = await sync_to_async(_build_payloads)(ips_to_scan)
    success_count = await _post_all(NMAP_API_ENDPOINT, payloads)
    return f"Triggered Nmap for {success_count}/{actual_count} IPs."
