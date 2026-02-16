import logging
import requests
from celery import shared_task
from django.db.models import Q, Count

from c2_core.config.logging import log_function_call
from c2_core.settings import API_BASE_URL
from apps.core.models import IP, Subdomain, URLResult, URLScan

logger = logging.getLogger(__name__)

# API Endpoints
NMAP_API_ENDPOINT = f"{API_BASE_URL}/api/nmap/start_scan"
GET_ALL_URL_ENDPOINT_TEMPLATE = f"{API_BASE_URL}/api/get_all_url/get_all_url"
FLARESOLVERR_START_SCANNER_URL = f"{API_BASE_URL}/api/flaresolverr/start_scanner"
AI_ANALYZES_IP = f"{API_BASE_URL}/api/analyze_ai/ips"
AI_ANALYZES_SUBDOMAINS = f"{API_BASE_URL}/api/analyze_ai/subdomains"
AI_ANALYZES_URL = f"{API_BASE_URL}/api/analyze_ai/urls"
NUCLEI_SCAN_URL = f"{API_BASE_URL}/api/nuclei"

logger.info(f"{API_BASE_URL}/api/flaresolverr/start_scanner")


# 1. Nmap 掃描觸發器
@shared_task(name="scheduler.tasks.scan_ips_without_nmap_results")
@log_function_call()
def scan_ips_without_nmap_results(batch_size: int = 10):
    logger.info(f"定時任務啟動：查找無 Nmap 記錄的 IP (Limit {batch_size})")

    ips_to_scan = (
        IP.objects.annotate(scan_count=Count("discovered_by_scans"))
        .filter(scan_count=0)
        .prefetch_related("which_seed")[:batch_size]  # M2M 必須用這個
    )
    actual_count = len(ips_to_scan)
    if actual_count == 0:
        return "No new IPs to scan."

    success_count = 0
    for ip_obj in ips_to_scan:
        payload = {
            "seed_ids": [seed.id for seed in ip_obj.which_seed.all()],
            "ip": ip_obj.ipv4 or ip_obj.ipv6,
        }
        try:
            resp = requests.post(NMAP_API_ENDPOINT, json=payload, timeout=10)
            if 200 <= resp.status_code < 300:
                success_count += 1
            else:
                logger.error(f"Nmap API Error {ip_obj.ipv4}: {resp.status_code}")
        except Exception as e:
            logger.exception(f"Nmap Req Failed: {e}")

    return f"Triggered Nmap for {success_count}/{actual_count} IPs."


# 2. Subdomain URL 發現觸發器
@shared_task(name="scheduler.tasks.scan_subdomains_without_url_results")
@log_function_call()
def scan_subdomains_without_url_results(batch_size: int = 5):
    logger.info(f"定時任務啟動：查找無被GAU掃描的子域名 (Limit {batch_size})")
    gau_subdomain_ids = URLScan.objects.filter(tool="gau").values_list(
        "target_subdomain_id", flat=True
    )

    # 2. 排除掉這些 ID
    subdomains_to_scan = (
        Subdomain.objects.filter(is_active=True, is_resolvable=True)
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


# 3. URL 內容抓取觸發器 (FlareSolverr)
@shared_task(name="scheduler.tasks.scan_urls_missing_response")
@log_function_call()
def scan_urls_missing_response(batch_size: int = 5):
    logger.info(f"定時任務啟動：查找未抓取內容的 URL (Limit {batch_size})")

    urls_to_scan = URLResult.objects.filter(content_fetch_status="PENDING").order_by(
        "-id"
    )[:batch_size]

    actual_count = len(urls_to_scan)
    if actual_count == 0:
        return "No new URLs to fetch."

    success_count = 0
    for url_obj in urls_to_scan:
        try:
            resp = requests.post(
                FLARESOLVERR_START_SCANNER_URL,
                json={"url": url_obj.url, "method": "GET"},
                timeout=5,
            )
            if 200 <= resp.status_code < 300:
                success_count += 1
        except Exception as e:
            logger.error(f"FlareSolverr Req Failed ({url_obj.url}): {e}")

    return f"Triggered Fetch for {success_count}/{actual_count} URLs."


# 4. AI 分析 IP 觸發器
@shared_task(name="scheduler.tasks.trigger_scan_ips_without_ai_results")
@log_function_call()
def trigger_scan_ips_without_ai_results(batch_size: int = 10):
    logger.info(f"定時任務：AI 分析 IP (Limit {batch_size})")

    ips_qs = (
        # 修正：使用正確的 M2M 字段名 'discovered_by_scans'
        IP.objects.filter(discovered_by_scans__status="COMPLETED")
        .exclude(ai_analysis__status__in=["COMPLETED", "RUNNING"])
        .distinct()  # 關鍵：防止因多個 Nmap 掃描記錄導致同一 IP 重複出現
        .order_by("-id")[:batch_size]
    )

    targets = list(set([ip.ipv4 or ip.ipv6 for ip in ips_qs if ip.ipv4 or ip.ipv6]))
    if not targets:
        return

    try:
        requests.post(AI_ANALYZES_IP, json={"ips": targets}, timeout=5)
    except Exception as e:
        logger.error(f"AI IP API Failed: {e}")


# 5. AI 分析 Subdomain 觸發器
@shared_task(name="scheduler.tasks.trigger_scan_subdomains_without_ai_results")
@log_function_call()
def trigger_scan_subdomains_without_ai_results(batch_size: int = 10):
    logger.info(f"定時任務：AI 分析子域名 (Limit {batch_size})")

    subdomains_qs = (
        Subdomain.objects.filter(is_active=True)
        .exclude(ai_analysis__status__in=["COMPLETED", "RUNNING"])
        .order_by("-id")[:batch_size]
    )
    targets = list(subdomains_qs.values_list("name", flat=True))
    if not targets:
        return

    try:
        requests.post(AI_ANALYZES_SUBDOMAINS, json={"subdomains": targets}, timeout=5)
    except Exception as e:
        logger.error(f"AI Subdomain API Failed: {e}")


# ==========================================
# 核心優化：URL 去重邏輯 (Hash & Final URL)
# ==========================================


def is_content_already_analyzed(url_obj, analysis_type="AI"):
    """
    檢查該 URL 的【內容】或【最終跳轉】在【全局歷史】中是否已經被分析過。
    analysis_type: "AI" 或 "NUCLEI"
    """
    # 1. 檢查 Hash (內容指紋)
    if url_obj.raw_response_hash:
        query = Q(raw_response_hash=url_obj.raw_response_hash)

        # 根據類型構造查詢：查找【是否有任何】具有相同 Hash 的 URL 已經完成了分析
        if analysis_type == "AI":
            # 查找是否存在 ai_analysis__status='COMPLETED' 的記錄
            if (
                URLResult.objects.filter(query, ai_analysis__status="COMPLETED")
                .exclude(id=url_obj.id)
                .exists()
            ):
                return True
        elif analysis_type == "NUCLEI":
            # 查找是否存在 nuclei_scans__status='COMPLETED' 的記錄
            if (
                URLResult.objects.filter(query, nuclei_scans__status="COMPLETED")
                .exclude(id=url_obj.id)
                .exists()
            ):
                return True

    # 2. 檢查 Final URL (跳轉終點)
    if url_obj.final_url:
        # 如果 Final URL 和當前 URL 不同，才需要去查
        if url_obj.final_url != url_obj.url:
            query = Q(final_url=url_obj.final_url) | Q(url=url_obj.final_url)

            if analysis_type == "AI":
                if (
                    URLResult.objects.filter(query, ai_analysis__status="COMPLETED")
                    .exclude(id=url_obj.id)
                    .exists()
                ):
                    return True
            elif analysis_type == "NUCLEI":
                if (
                    URLResult.objects.filter(query, nuclei_scans__status="COMPLETED")
                    .exclude(id=url_obj.id)
                    .exists()
                ):
                    return True

    return False


# 6. AI 分析 URL 觸發器 (已升級去重)
@shared_task(name="scheduler.tasks.trigger_scan_urls_without_ai_results")
@log_function_call()
def trigger_scan_urls_without_ai_results(batch_size: int = 5):
    logger.info(f"定時任務：AI 分析 URL (Limit {batch_size}, 全局去重模式)")

    # 1. 初步獲取候選集 (多取一點，因為很多會被過濾掉)
    candidate_qs = (
        URLResult.objects.filter(content_fetch_status="SUCCESS_FETCHED")
        .exclude(ai_analysis__status__in=["COMPLETED", "RUNNING"])
        .exclude(status_code=404)
        .order_by("-id")[: batch_size * 5]  # 取 5 倍的量來篩選
    )

    valid_targets = []

    # 2. 逐個進行【全局歷史檢查】
    for url_obj in candidate_qs:
        if len(valid_targets) >= batch_size:
            break

        # 如果內容已經被分析過了（哪怕是別的 URL），就跳過！
        if is_content_already_analyzed(url_obj, analysis_type="AI"):
            # 選項：這裡可以順便把當前 URL 標記為 "SKIPPED_DUPLICATE" 以免下次再查
            # 但為了性能，我們先只做跳過
            logger.debug(f"跳過全局重複內容: {url_obj.url}")
            continue

        valid_targets.append(url_obj.url)

    if not valid_targets:
        return "No unique URLs for AI analysis (Global Deduplication)."

    try:
        requests.post(AI_ANALYZES_URL, json={"urls": valid_targets}, timeout=5)
        return f"Dispatched {len(valid_targets)} Unique URLs to AI."
    except Exception as e:
        logger.error(f"AI URL API Failed: {e}")


# 7. Nuclei 分析 URL 觸發器 (全局去重版)
@shared_task(name="scheduler.tasks.trigger_scan_urls_without_nuclei_results")
@log_function_call()
def trigger_scan_urls_without_nuclei_results(batch_size: int = 5):
    logger.info(f"定時任務：Nuclei 掃描 URL (Limit {batch_size}, 全局去重模式)")

    candidate_qs = (
        URLResult.objects.filter(content_fetch_status="SUCCESS_FETCHED")
        .exclude(nuclei_scans__status__in=["COMPLETED", "RUNNING"])
        .order_by("-id")[: batch_size * 5]
    )

    valid_targets = []

    for url_obj in candidate_qs:
        if len(valid_targets) >= batch_size:
            break

        # Nuclei 全局去重檢查
        if is_content_already_analyzed(url_obj, analysis_type="NUCLEI"):
            logger.debug(f"跳過全局重複內容: {url_obj.url}")
            continue

        valid_targets.append(url_obj.url)

    if not valid_targets:
        return "No unique URLs for Nuclei scan."

    try:
        requests.post(
            f"{NUCLEI_SCAN_URL}/urls", json={"urls": valid_targets}, timeout=5
        )
        return f"Dispatched {len(valid_targets)} Unique URLs to Nuclei."
    except Exception as e:
        logger.error(f"Nuclei URL API Failed: {e}")


# 8. Nuclei 分析 Subdomain 觸發器
@shared_task(name="scheduler.tasks.trigger_scan_subdomains_without_nuclei_results")
@log_function_call()
def trigger_scan_subdomains_without_nuclei_results(batch_size: int = 5):
    logger.info(f"定時任務：Nuclei 掃描子域名 (Limit {batch_size})")

    subdomains_qs = (
        Subdomain.objects.filter(is_active=True)
        .exclude(nuclei_scans__status__in=["COMPLETED", "RUNNING"])
        .order_by("-id")[:batch_size]
    )
    targets = list(subdomains_qs.values_list("name", flat=True))

    if not targets:
        return

    try:
        requests.post(
            f"{NUCLEI_SCAN_URL}/subdomains", json={"hosts": targets}, timeout=5
        )
    except Exception as e:
        logger.error(f"Nuclei Subdomain API Failed: {e}")


# 9. Nuclei 分析 IP 觸發器 (邏輯修復版)
@shared_task(name="scheduler.tasks.trigger_scan_ips_without_nuclei_results")
@log_function_call()
def trigger_scan_ips_without_nuclei_results(batch_size: int = 10):
    """
    IP 發現即掃描：只要 IP 存在且沒有成功的 Nuclei 記錄，就開火。
    """
    logger.info(f"定時任務：Nuclei 掃描 IP (Limit {batch_size})")

    # 修正邏輯：使用 exclude status 而不是 isnull，允許重試
    ips_qs = (
        IP.objects.all()
        .exclude(nuclei_scans__status__in=["COMPLETED", "RUNNING"])
        .order_by("-id")[:batch_size]
    )

    target_ips = []
    for ip_obj in ips_qs:
        val = ip_obj.ipv4 or ip_obj.ipv6
        if val:
            target_ips.append(val)

    target_ips = list(set(target_ips))

    if not target_ips:
        return "No IPs pending for Nuclei scan."

    try:
        requests.post(f"{NUCLEI_SCAN_URL}/ips", json={"ips": target_ips}, timeout=5)
        return f"Dispatched {len(target_ips)} IPs to Nuclei."
    except Exception as e:
        logger.error(f"Nuclei IP API Failed: {e}")
