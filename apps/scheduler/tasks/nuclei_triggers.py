import logging
import requests
from celery import shared_task

from c2_core.config.logging import log_function_call
from c2_core.settings import API_BASE_URL
from apps.core.models import IP, Subdomain, URLResult
from .utils import is_content_already_analyzed

logger = logging.getLogger(__name__)

# API Endpoints (對應你剛改好的 ID 版 API)
NUCLEI_SCAN_URL = f"{API_BASE_URL}/api/nuclei"


@shared_task(name="scheduler.tasks.trigger_scan_urls_without_nuclei_results")
@log_function_call()
def trigger_scan_urls_without_nuclei_results(batch_size: int = 5):
    """
    定時任務：選出尚未掃描漏洞的 URL ID 並派發
    """
    logger.info(f"定時任務：Nuclei 掃描 URL (Limit {batch_size}, ID 模式)")

    candidate_qs = (
        URLResult.objects.filter(content_fetch_status="SUCCESS_FETCHED")
        .exclude(nuclei_scans__status__in=["COMPLETED", "RUNNING"])
        .order_by("-id")[: batch_size * 5]
    )

    valid_ids = []

    for url_obj in candidate_qs:
        if len(valid_ids) >= batch_size:
            break

        # Nuclei 全局去重檢查 (即便用 ID 傳輸，內容重複仍可跳過)
        if is_content_already_analyzed(url_obj, analysis_type="NUCLEI"):
            logger.debug(f"跳過全局重複內容 (ID: {url_obj.id}): {url_obj.url}")
            continue

        valid_ids.append(url_obj.id)

    if not valid_ids:
        return "No unique URL IDs for Nuclei scan."

    try:
        # payload 改成 {"ids": [...]}
        requests.post(f"{NUCLEI_SCAN_URL}/urls", json={"ids": valid_ids}, timeout=5)
        return f"Dispatched {len(valid_ids)} URL IDs to Nuclei."
    except Exception as e:
        logger.error(f"Nuclei URL API Failed: {e}")


@shared_task(name="scheduler.tasks.trigger_scan_subdomains_without_nuclei_results")
@log_function_call()
def trigger_scan_subdomains_without_nuclei_results(batch_size: int = 5):
    """
    定時任務：選出尚未掃描漏洞的子域名 ID 並派發
    """
    logger.info(f"定時任務：Nuclei 掃描子域名 (Limit {batch_size}, ID 模式)")

    subdomains_qs = (
        Subdomain.objects.filter(is_active=True)
        .exclude(nuclei_scans__status__in=["COMPLETED", "RUNNING"])
        .order_by("-id")[:batch_size]
    )

    # 直接提取 ID
    target_ids = list(subdomains_qs.values_list("id", flat=True))

    if not target_ids:
        return "No Subdomain IDs pending."

    try:
        # payload 改成 {"ids": [...]}
        requests.post(
            f"{NUCLEI_SCAN_URL}/subdomains", json={"ids": target_ids}, timeout=5
        )
        return f"Dispatched {len(target_ids)} Subdomain IDs to Nuclei."
    except Exception as e:
        logger.error(f"Nuclei Subdomain API Failed: {e}")


@shared_task(name="scheduler.tasks.trigger_scan_ips_without_nuclei_results")
@log_function_call()
def trigger_scan_ips_without_nuclei_results(batch_size: int = 10):
    """
    定時任務：選出尚未掃描漏洞的 IP ID 並派發
    """
    logger.info(f"定時任務：Nuclei 掃描 IP (Limit {batch_size}, ID 模式)")

    ips_qs = (
        IP.objects.all()
        .exclude(nuclei_scans__status__in=["COMPLETED", "RUNNING"])
        .order_by("-id")[:batch_size]
    )

    # 以前還要分 ipv4/ipv6 字串，現在直接拿 ID 爽快多了
    target_ids = list(ips_qs.values_list("id", flat=True))

    if not target_ids:
        return "No IP IDs pending for Nuclei scan."

    try:
        # payload 改成 {"ids": [...]}
        requests.post(f"{NUCLEI_SCAN_URL}/ips", json={"ids": target_ids}, timeout=5)
        return f"Dispatched {len(target_ids)} IP IDs to Nuclei."
    except Exception as e:
        logger.error(f"Nuclei IP API Failed: {e}")
