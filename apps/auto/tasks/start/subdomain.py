"""
auto/tasks/start/subdomain.py

Subdomain 自動化任務：讀取 SubdomainAIAnalysis.command_actions →
透過 GraphQL 查詢子域名資產 → 建立 Step/Method/Payload/Verification。
"""

import json
import logging

from celery import shared_task

from apps.core.models import SubdomainAIAnalysis
from apps.analyze_ai.tasks.common import fetch_subdomain_data_for_batch
from c2_core.config.logging import log_function_call

from .common import create_steps_from_analysis

logger = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=True)
@log_function_call()
def start_subdomain_ai_analysis(self, sub_ai_analysis_id: int = None):
    """
    【Subdomain 自動化】讀取 SubdomainAIAnalysis.command_actions →
    GraphQL 查詢子域名資產 → 建立 Step/Method/Payload/Verification。
    """
    # ── 1. 驗證分析記錄 ──
    try:
        analysis = SubdomainAIAnalysis.objects.select_related("subdomain").get(
            id=sub_ai_analysis_id
        )
    except SubdomainAIAnalysis.DoesNotExist:
        logger.error(f"SubdomainAIAnalysis#{sub_ai_analysis_id} 不存在，任務終止。")
        return

    if analysis.status != "COMPLETED":
        logger.warning(
            f"SubdomainAIAnalysis#{sub_ai_analysis_id} 狀態={analysis.status}，跳過。"
        )
        return

    # ── 2. 取得 command_actions ──
    command_actions = analysis.command_actions or []
    if not command_actions:
        logger.info(
            f"SubdomainAIAnalysis#{sub_ai_analysis_id} 沒有 command_actions，跳過。"
        )
        return

    # ── 3. GraphQL 取得子域名最新資料 ──
    try:
        sub_data = fetch_subdomain_data_for_batch([analysis.subdomain_id])
        asset_context = json.dumps(sub_data, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"GraphQL 查詢 Subdomain#{analysis.subdomain_id} 失敗: {e}")
        asset_context = "{}"

    # ── 4. 建立 Step 鏈 ──
    count = create_steps_from_analysis(
        command_actions=command_actions,
        asset_fk_field="subdomain",
        asset_fk_value=analysis.subdomain,
        analysis_id=sub_ai_analysis_id,
        analysis_summary=analysis.summary,
        analysis_risk_score=analysis.risk_score,
        potential_vulnerabilities=analysis.potential_vulnerabilities,
        asset_context_json=asset_context,
    )
    logger.info(
        f"✅ SubdomainAIAnalysis#{sub_ai_analysis_id} → 建立 {count} 個 Step"
    )
