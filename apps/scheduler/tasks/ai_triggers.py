import logging
import requests
from django.db.models import Count, Q
from celery import shared_task
from django.utils import timezone

from c2_core.config.logging import log_function_call
from c2_core.settings import API_BASE_URL
from apps.core.models import (
    IPAIAnalysis,
    SubdomainAIAnalysis,
    URLAIAnalysis,
)

logger = logging.getLogger(__name__)

# API Endpoints
AI_ANALYZES_IP = f"{API_BASE_URL}/api/analyze_ai/ips"
AI_ANALYZES_SUBDOMAINS = f"{API_BASE_URL}/api/analyze_ai/subdomains"
AI_ANALYZES_URL = f"{API_BASE_URL}/api/analyze_ai/urls"


@shared_task(name="scheduler.tasks.trigger_pending_ai_analyses")
@log_function_call()
def trigger_pending_ai_analyses(batch_size: int = 10):
    """
    定時任務：掃描所有處於 PENDING 狀態且關聯於 PLANNING 狀態 Overview 的 AI 分析記錄。
    自動將它們發送給 analyze_ai 引擎進行處理。
    這種設計完全符合「連續循環 (Continuous Loop)」架構，而不是盲目掃描資產。
    """
    summary = {"ip": 0, "subdomain": 0, "url": 0}

    # 1. IP
    ip_pending = IPAIAnalysis.objects.filter(
        status="PENDING",
        overview__status="PLANNING"
    ).values_list("ip_id", flat=True)[:batch_size]

    if ip_pending:
        ip_ids = list(ip_pending)
        try:
            requests.post(AI_ANALYZES_IP, json={"ids": ip_ids}, timeout=5)
            summary["ip"] = len(ip_ids)
            logger.info(f"Dispatched {len(ip_ids)} PENDING IPAIAnalysis records.")
        except Exception as e:
            logger.error(f"AI IP API Failed: {e}")

    # 2. Subdomain
    sub_pending = SubdomainAIAnalysis.objects.filter(
        status="PENDING",
        overview__status="PLANNING"
    ).values_list("subdomain_id", flat=True)[:batch_size]

    if sub_pending:
        sub_ids = list(sub_pending)
        try:
            requests.post(AI_ANALYZES_SUBDOMAINS, json={"ids": sub_ids}, timeout=5)
            summary["subdomain"] = len(sub_ids)
            logger.info(f"Dispatched {len(sub_ids)} PENDING SubdomainAIAnalysis records.")
        except Exception as e:
            logger.error(f"AI Subdomain API Failed: {e}")

    # 3. URL
    url_pending = URLAIAnalysis.objects.filter(
        status="PENDING",
        overview__status="PLANNING"
    ).values_list("url_result_id", flat=True)[:batch_size]

    if url_pending:
        url_ids = list(url_pending)
        try:
            requests.post(AI_ANALYZES_URL, json={"ids": url_ids}, timeout=5)
            summary["url"] = len(url_ids)
            logger.info(f"Dispatched {len(url_ids)} PENDING URLAIAnalysis records.")
        except Exception as e:
            logger.error(f"AI URL API Failed: {e}")

    if sum(summary.values()) == 0:
        return "No PENDING AI analyses found for PLANNING Overviews."
        
    return summary
