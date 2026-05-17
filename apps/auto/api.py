"""
⚠️  DEPRECATED ⚠️

此模組已被移除。
原先的深度 AI 分析 (IPAIAnalysis, SubdomainAIAnalysis, URLAIAnalysis) 已廢棄，
所有分析統一由 InitialAIAnalysis + Overview 流程處理。
無需再將分析記錄手動轉換為執行步驟 — AutomationAgent 會透過 Overview 自動接管。
"""

import logging
from ninja import Router
from ninja.errors import HttpError

router = Router()
logger = logging.getLogger(__name__)


@router.post("/convert/{asset_type}", deprecated=True)
async def convert_analysis_deprecated(request, asset_type: str, payload: dict):
    raise HttpError(410, f"此端點已移除。深度 AI 分析模型 (IPAIAnalysis/SubdomainAIAnalysis/URLAIAnalysis) 已廢棄，請使用統一的 InitialAIAnalysis + Overview 流程。")
