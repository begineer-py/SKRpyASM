import logging
from typing import List

from ninja import Router
from ninja.errors import HttpError

from apps.core.models import InitialAIAnalysis
from apps.core.schemas import (
    SuccessSendToAISchema,
    ScanIdsSchema,
    ErrorSchema,
)
from .tasks import trigger_initial_ai_analysis

router = Router()
logger = logging.getLogger(__name__)


@router.post(
    "/initial", response={202: SuccessSendToAISchema, 400: ErrorSchema, 404: ErrorSchema}
)
async def analyze_ai_initial(request, payload: ScanIdsSchema):
    """Initial AI 分析"""
    valid_ids = payload.ids
    if not valid_ids:
        raise HttpError(400, "請提供要分析的 InitialAIAnalysis ID。")
    trigger_initial_ai_analysis.delay(analysis_ids=valid_ids)
    return 202, SuccessSendToAISchema(
        detail=f"Initial AI 分析任務已成功派發給 {len(valid_ids)} 個記錄。"
    )
