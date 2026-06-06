import logging

import httpx
from asgiref.sync import sync_to_async
from celery import shared_task

from c2_core.config.logging import log_function_call
from c2_core.settings import API_BASE_URL
from apps.core.models import IP, Subdomain, URLResult
from .utils import is_content_already_analyzed

logger = logging.getLogger(__name__)

# API Endpoints (對應新版 unified scanners API)
NUCLEI_SCAN_URL = f"{API_BASE_URL}/api/scanners/vuln"


@shared_task(name="scheduler.tasks.trigger_scan_urls_without_nuclei_results")
@log_function_call()
async def trigger_scan_urls_without_nuclei_results(batch_size: int = 5):
    """
    定時任務：選出尚未掃描漏洞的 URL ID 並派發
    """
    logger.info(f"定時任務：Nuclei 掃描 URL (Limit {batch_size}, ID 模式)")

    def _fetch():
        candidate_qs = (
            URLResult.objects.filter(content_fetch_status="SUCCESS_FETCHED")
            .exclude(nuclei_scans__status__in=["COMPLETED", "RUNNING"])
            .order_by("-id")[: batch_size * 5]
        )
        valid_ids = []
        for url_obj in candidate_qs:
            if len(valid_ids) >= batch_size:
                break
            if is_content_already_analyzed(url_obj, analysis_type="NUCLEI"):
                logger.debug(f"跳過全局重複內容 (ID: {url_obj.id}): {url_obj.url}")
                continue
            valid_ids.append(url_obj.id)
        return valid_ids

    valid_ids = await sync_to_async(_fetch)()

    if not valid_ids:
        return "No unique URL IDs for Nuclei scan."

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(f"{NUCLEI_SCAN_URL}/urls", json={"ids": valid_ids})
        return f"Dispatched {len(valid_ids)} URL IDs to Nuclei."
    except Exception as e:
        logger.error(f"Nuclei URL API Failed: {e}")


@shared_task(name="scheduler.tasks.trigger_scan_subdomains_without_nuclei_results")
@log_function_call()
async def trigger_scan_subdomains_without_nuclei_results(batch_size: int = 5):
    """
    定時任務：選出尚未掃描漏洞的子域名 ID 並派發
    """
    logger.info(f"定時任務：Nuclei 掃描子域名 (Limit {batch_size}, ID 模式)")

    def _fetch():
        return list(
            Subdomain.objects.filter(is_active=True)
            .exclude(nuclei_scans__status__in=["COMPLETED", "RUNNING"])
            .order_by("-id")
            .values_list("id", flat=True)[:batch_size]
        )

    target_ids = await sync_to_async(_fetch)()

    if not target_ids:
        return "No Subdomain IDs pending."

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"{NUCLEI_SCAN_URL}/subdomains", json={"ids": target_ids}
            )
        return f"Dispatched {len(target_ids)} Subdomain IDs to Nuclei."
    except Exception as e:
        logger.error(f"Nuclei Subdomain API Failed: {e}")


@shared_task(name="scheduler.tasks.trigger_scan_ips_without_nuclei_results")
@log_function_call()
async def trigger_scan_ips_without_nuclei_results(batch_size: int = 10):
    """
    定時任務：選出尚未掃描漏洞的 IP ID 並派發
    """
    logger.info(f"定時任務：Nuclei 掃描 IP (Limit {batch_size}, ID 模式)")

    def _fetch():
        return list(
            IP.objects.all()
            .exclude(nuclei_scans__status__in=["COMPLETED", "RUNNING"])
            .order_by("-id")
            .values_list("id", flat=True)[:batch_size]
        )

    target_ids = await sync_to_async(_fetch)()

    if not target_ids:
        return "No IP IDs pending for Nuclei scan."

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(f"{NUCLEI_SCAN_URL}/ips", json={"ids": target_ids})
        return f"Dispatched {len(target_ids)} IP IDs to Nuclei."
    except Exception as e:
        logger.error(f"Nuclei IP API Failed: {e}")
