import logging
import requests
from django.db.models import Count, Q
from celery import shared_task
from django.utils import timezone

from c2_core.config.logging import log_function_call
from c2_core.settings import API_BASE_URL
from apps.core.models import (
    IP,
    Subdomain,
    URLResult,
    IPAIAnalysis,
    SubdomainAIAnalysis,
    URLAIAnalysis,
)
from .utils import is_content_already_analyzed

logger = logging.getLogger(__name__)

# API Endpoints
AI_ANALYZES_IP = f"{API_BASE_URL}/api/analyze_ai/ips"
AI_ANALYZES_SUBDOMAINS = f"{API_BASE_URL}/api/analyze_ai/subdomains"
AI_ANALYZES_URL = f"{API_BASE_URL}/api/analyze_ai/urls"

# =============================================================================
# 1. IP AI 分析調度
# =============================================================================


@shared_task(name="scheduler.tasks.trigger_scan_ips_without_ai_results")
@log_function_call()
def trigger_scan_ips_without_ai_results(batch_size: int = 10):
    """
    定時任務：選出完成 Nmap 掃描但尚未 AI 分析的 IP。
    自動排除沒有開放端口的 IP。
    """
    # 1. 找出潛在候選人 (Nmap 已完成且沒有 AI 分析記錄或分析失敗的)
    base_query = (
        IP.objects.filter(discovered_by_scans__status="COMPLETED")
        .exclude(ai_analysis__status__in=["COMPLETED", "RUNNING"])
        .distinct()
    )

    # 2. 自動排除：沒有開放端口的 IP 直接標記為 FAILED (跳過)
    # 使用 Count 聚合檢查是否有開放端口
    ips_with_no_ports = base_query.annotate(
        open_port_count=Count("ports", filter=Q(ports__state="open"))
    ).filter(open_port_count=0)

    for ip in ips_with_no_ports:
        IPAIAnalysis.objects.update_or_create(
            ip=ip,
            defaults={
                "status": "FAILED",
                "error_message": "No open ports found, skipping AI analysis.",
            },
        )

    # 3. 篩選真正要分析的 (有開放端口的)
    to_trigger = base_query.annotate(
        open_port_count=Count("ports", filter=Q(ports__state="open"))
    ).filter(open_port_count__gt=0)[:batch_size]

    target_ids = list(to_trigger.values_list("id", flat=True))

    if not target_ids:
        return "No suitable IP IDs for AI analysis."

    # 4. 標記為 RUNNING
    for tid in target_ids:
        IPAIAnalysis.objects.update_or_create(ip_id=tid, defaults={"status": "RUNNING"})

    try:
        requests.post(AI_ANALYZES_IP, json={"ids": target_ids}, timeout=5)
        return f"Dispatched {len(target_ids)} IPs."
    except Exception as e:
        logger.error(f"AI IP API Failed: {e}")
        IPAIAnalysis.objects.filter(ip_id__in=target_ids).update(status="PENDING")


# =============================================================================
# 2. Subdomain AI 分析調度
# =============================================================================


@shared_task(name="scheduler.tasks.trigger_scan_subdomains_without_ai_results")
@log_function_call()
def trigger_scan_subdomains_without_ai_results(batch_size: int = 10):
    """
    定時任務：選出尚未 AI 分析的子域名。
    自動排除無法解析 (is_resolvable=False) 的子域名。
    """
    base_query = Subdomain.objects.filter(is_active=True).exclude(
        ai_analysis__status__in=["COMPLETED", "RUNNING"]
    )

    # 1. 自動排除：不可解析的子域名
    unresolvable_subs = base_query.filter(is_resolvable=False)
    for sub in unresolvable_subs:
        SubdomainAIAnalysis.objects.update_or_create(
            subdomain=sub,
            defaults={
                "status": "FAILED",
                "error_message": "DNS unresolvable, skipping AI.",
            },
        )

    # 2. 篩選可解析的
    to_trigger_ids = list(
        base_query.filter(is_resolvable=True).values_list("id", flat=True)[:batch_size]
    )

    if not to_trigger_ids:
        return "No Subdomains pending."

    # 3. 標記為 RUNNING
    for tid in to_trigger_ids:
        SubdomainAIAnalysis.objects.update_or_create(
            subdomain_id=tid, defaults={"status": "RUNNING"}
        )

    try:
        requests.post(AI_ANALYZES_SUBDOMAINS, json={"ids": to_trigger_ids}, timeout=5)
        return f"Dispatched {len(to_trigger_ids)} Subdomains."
    except Exception as e:
        logger.error(f"AI Subdomain API Failed: {e}")
        SubdomainAIAnalysis.objects.filter(subdomain_id__in=to_trigger_ids).update(
            status="PENDING"
        )


# =============================================================================
# 3. URL AI 分析調度
# =============================================================================


@shared_task(name="scheduler.tasks.trigger_scan_urls_without_ai_results")
@log_function_call()
def trigger_scan_urls_without_ai_results(batch_size: int = 5):
    """
    定時任務：AI 分析 URL。
    自動排除 404、抓取失敗、內容重複的資產。
    """
    # 1. 建立基礎 QuerySet (只取成功抓取且沒分析過的)
    query = URLResult.objects.filter(content_fetch_status="SUCCESS_FETCHED").exclude(
        ai_analysis__status__in=["COMPLETED", "RUNNING"]
    )

    # 2. 自動排除：狀態碼 404 的 URL
    urls_404 = query.filter(status_code=404)
    for u in urls_404:
        URLAIAnalysis.objects.update_or_create(
            url_result=u,
            defaults={
                "status": "FAILED",
                "error_message": "404 Not Found, skipping AI.",
            },
        )

    # 3. 篩選出非 404 的資產進行內容去重
    candidate_qs = query.exclude(status_code=404).order_by("-id")[: batch_size * 3]

    valid_ids = []
    for url_obj in candidate_qs:
        if len(valid_ids) >= batch_size:
            break

        # 全局內容去重檢查 (基於 Hash 或相似度)
        if is_content_already_analyzed(url_obj, analysis_type="AI"):
            URLAIAnalysis.objects.update_or_create(
                url_result=url_obj,
                defaults={
                    "status": "COMPLETED",
                    "summary": "Skipped due to duplicate content.",
                },
            )
            continue

        valid_ids.append(url_obj.id)

    if not valid_ids:
        return "No unique URL IDs."

    # 4. 標記為 RUNNING
    for tid in valid_ids:
        URLAIAnalysis.objects.update_or_create(
            url_result_id=tid, defaults={"status": "RUNNING"}
        )

    try:
        requests.post(AI_ANALYZES_URL, json={"ids": valid_ids}, timeout=10)
        return f"Dispatched {len(valid_ids)} URL IDs."
    except Exception as e:
        logger.error(f"AI URL API Failed: {e}")
        # 失敗回退狀態
        URLAIAnalysis.objects.filter(url_result_id__in=valid_ids).update(
            status="PENDING"
        )
