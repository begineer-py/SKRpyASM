import logging
from django.db.models import query
import requests
from celery import shared_task

from c2_core.config.logging import log_function_call
from c2_core.settings import API_BASE_URL
from apps.core.models import IP, Subdomain, URLResult, TechStack

logger = logging.getLogger(__name__)

# API Endpoints (對應你剛改好的 ID 版 API)
NUCLEI_SCAN_URL = f"{API_BASE_URL}/api/nuclei"


@log_function_call()
def url_to_trigger(batch_size) -> list[int]:
    # 1. 建立基礎 QuerySet
    query = URLResult.objects.exclude(is_tech_analyzed=True).exclude(
        content_fetch_status__in=["PENDING", "SUCCESS_REDIRECTED_EXTERNAL"]
    )

    # 2. 處理「無法解析」的 URL：直接標記為已分析，但不回傳
    # 這樣這些 DNS/網路錯誤的資料下次就不會再被選進 query
    query.filter(
        content_fetch_status__in=[
            "FAILED_NETWORK_ERROR",
            "FAILED_BLOCKED",
            "FAILED_DNS_ERROR",
            "FAILED_TIMEOUT",
            "FAILED_CLIENT_ERROR",
            "FAILED_SERVER_ERROR",
        ]
    ).update(is_tech_analyzed=True)

    # 3. 處理「可以解析」的 URL：排除掉剛剛標記過的失敗項
    to_trigger = query.exclude(is_tech_analyzed=True)

    # 4. 只取出這批「要送去分析」的 ID，並限制 batch_size
    # 這樣我們就不會一次標記太多「成功但還沒送出去」的資料
    triggered_ids = list(to_trigger.values_list("id", flat=True)[:batch_size])

    # 5. 將真正要回傳的這批 ID 標記為已分析
    if triggered_ids:
        URLResult.objects.filter(id__in=triggered_ids).update(is_tech_analyzed=True)

    return triggered_ids


@shared_task(name="scheduler.tasks.trigger_nuclei_tech_scan_url")
@log_function_call()
def trigger_nuclei_tech_scan(batch_size: int = 1):
    """
    定時任務：選出尚未掃描技術棧的 URL ID 並派發
    """
    logger.info("定時任務：Nuclei 技術棧掃描 (ID 模式)")
    ids = url_to_trigger(batch_size)
    if not ids:
        return "No URL IDs to scan."
    logger.info(f"需要掃描的 URL ID: {ids}")
    try:
        # payload 改成 {"ids": [...]}
        requests.post(f"{NUCLEI_SCAN_URL}/urls_tech", json={"ids": ids}, timeout=5)
        return f"Dispatched {len(ids)} URL IDs to Nuclei."
    except Exception as e:
        logger.error(f"Nuclei URL API Failed: {e}")


@log_function_call()
def subdomain_to_trigger(batch_size) -> list[int]:
    """
    篩選出需要進行技術分析的 Subdomain ID
    """
    # 1. 建立基礎 QuerySet
    # 篩選條件：尚未分析過，且必須是啟用的 (is_active=True)
    query = Subdomain.objects.filter(is_tech_analyzed=False, is_active=True)

    # 2. 處理「無法解析」的 Subdomain：直接標記為已分析，但不回傳
    # 如果 DNS 無法解析 (is_resolvable=False)，則不需要送去掃描技術棧
    query.filter(is_resolvable=False).update(is_tech_analyzed=True)

    # 3. 處理「可以解析」的 Subdomain：排除掉剛剛標記過的不可解析項
    to_trigger = query.filter(is_resolvable=True)

    # 4. 只取出這批「要送去分析」的 ID，並限制 batch_size
    triggered_ids = list(to_trigger.values_list("id", flat=True)[:batch_size])

    # 5. 將真正要回傳的這批 ID 標記為已分析 (避免重複派發)
    if triggered_ids:
        Subdomain.objects.filter(id__in=triggered_ids).update(is_tech_analyzed=True)

    return triggered_ids


@shared_task(name="scheduler.tasks.trigger_nuclei_tech_scan_subdomain")
@log_function_call()
def trigger_nuclei_tech_scan_subdomain(batch_size: int = 100):
    """
    定時任務：選出尚未掃描技術棧的 Subdomain ID 並派發
    端點對應：/api/nuclei/subs_tech
    """
    logger.info("定時任務：Nuclei Subdomain 技術棧掃描 (ID 模式)")

    ids = subdomain_to_trigger(batch_size)

    if not ids:
        logger.info("沒有需要掃描的 Subdomain ID")
        return "No Subdomains to dispatch."

    logger.info(f"需要掃描的 Subdomain ID: {ids}")

    try:
        # 呼叫你指定的 subs_tech 端點
        response = requests.post(
            f"{NUCLEI_SCAN_URL}/subs_tech", json={"ids": ids}, timeout=10
        )
        response.raise_for_status()
        return f"Dispatched {len(ids)} Subdomain IDs to Nuclei subs_tech."
    except Exception as e:
        logger.error(f"Nuclei Subdomain API Failed: {e}")
        # 如果發送失敗，考慮是否要把 is_tech_analyzed 改回 False 以便下次重試
        # Subdomain.objects.filter(id__in=ids).update(is_tech_analyzed=False)
        return f"Error: {str(e)}"
