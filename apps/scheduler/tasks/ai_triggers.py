"""
⚠️  DEPRECATED ⚠️

此模組已廢棄。
原先的深度 AI 分析 (IPAIAnalysis, SubdomainAIAnalysis, URLAIAnalysis) 已移除，
所有分析統一由 InitialAIAnalysis + Overview 流程處理。
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="scheduler.tasks.trigger_pending_ai_analyses")
def trigger_pending_ai_analyses(batch_size: int = 10):
    logger.info("[DEPRECATED] trigger_pending_ai_analyses: 深度 AI 分析模型已移除，此任務無需執行。")
    return "DEPRECATED: 深度 AI 分析已廢棄，請使用 InitialAIAnalysis + Overview 流程。"
