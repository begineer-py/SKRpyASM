"""
auto/tasks/start/ip.py

IP 自動化任務：讀取 IPAIAnalysis.command_actions →
透過 GraphQL 查詢 IP 資產 → 建立 Step/Method/Payload/Verification。
"""

import json
import logging

from celery import shared_task

from apps.core.models import IPAIAnalysis
from apps.analyze_ai.tasks.common import fetch_ip_data_for_batch
from c2_core.config.logging import log_function_call

from .common import create_steps_from_analysis

logger = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=True)
@log_function_call()
def start_ip_ai_analysis(self, ip_ai_analysis_id: int = None):
    """
    【IP 自動化】讀取 IPAIAnalysis.command_actions →
    GraphQL 查詢 IP 資產 → 建立 Step/Method/Payload/Verification。
    """
    # ── 1. 驗證分析記錄 ──
    try:
        analysis = IPAIAnalysis.objects.select_related("ip").get(id=ip_ai_analysis_id)
    except IPAIAnalysis.DoesNotExist:
        logger.error(f"IPAIAnalysis#{ip_ai_analysis_id} 不存在，任務終止。")
        return

    if analysis.status != "COMPLETED":
        logger.warning(f"IPAIAnalysis#{ip_ai_analysis_id} 狀態={analysis.status}，跳過。")
        return

    # ── 2. 取得 command_actions ──
    command_actions = analysis.command_actions or []
    if not command_actions:
        logger.info(f"IPAIAnalysis#{ip_ai_analysis_id} 沒有 command_actions，跳過。")
        return

    # ── 3. GraphQL 取得 IP 最新資料 ──
    try:
        ip_data = fetch_ip_data_for_batch([analysis.ip_id])
        asset_context = json.dumps(ip_data, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"GraphQL 查詢 IP#{analysis.ip_id} 失敗: {e}")
        asset_context = "{}"

    # ── 4. 建立 Step 鏈 ──
    count = create_steps_from_analysis(
        command_actions=command_actions,
        asset_fk_field="ip",
        asset_fk_value=analysis.ip,
        analysis_id=ip_ai_analysis_id,
        analysis_summary=analysis.summary,
        analysis_risk_score=analysis.risk_score,
        potential_vulnerabilities=analysis.potential_vulnerabilities,
        asset_context_json=asset_context,
    )
    logger.info(f"✅ IPAIAnalysis#{ip_ai_analysis_id} → 建立 {count} 個 Step")
