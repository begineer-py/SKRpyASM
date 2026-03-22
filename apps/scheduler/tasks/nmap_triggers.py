import logging
import requests
from celery import shared_task
from django.db.models import Count

from c2_core.config.logging import log_function_call
from c2_core.settings import API_BASE_URL
from apps.core.models import IP

logger = logging.getLogger(__name__)

# API Endpoints
NMAP_API_ENDPOINT = f"{API_BASE_URL}/api/nmap/start_scan"


@shared_task(name="scheduler.tasks.scan_ips_without_nmap_results")
@log_function_call()
def scan_ips_without_nmap_results(batch_size: int = 10):
    logger.info(f"定時任務啟動：查找無 Nmap 記錄的 IP (Limit {batch_size})")

    ips_to_scan = (
        IP.objects.annotate(scan_count=Count("discovered_by_scans"))
        .filter(
            scan_count=0,
            target__isnull=False,
            which_seed__isnull=False
        )
        .prefetch_related("which_seed")[:batch_size]  # M2M 必須用這個
    )
    actual_count = len(ips_to_scan)
    if actual_count == 0:
        return "No new IPs to scan."

    success_count = 0
    for ip_obj in ips_to_scan:
        payload = {
            "seed_ids": [seed.id for seed in ip_obj.which_seed.all()],
            "ip": ip_obj.address,
        }
        try:
            resp = requests.post(NMAP_API_ENDPOINT, json=payload, timeout=10)
            if 200 <= resp.status_code < 300:
                success_count += 1
            else:
                logger.error(f"Nmap API Error {ip_obj.address}: {resp.status_code}")
        except Exception as e:
            logger.exception(f"Nmap Req Failed: {e}")

    return f"Triggered Nmap for {success_count}/{actual_count} IPs."
