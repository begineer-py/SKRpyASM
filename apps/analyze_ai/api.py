import logging
from typing import List

from ninja import Router
from ninja.errors import HttpError
from asgiref.sync import sync_to_async
from c2_core.config.logging import log_function_call

from apps.scanners.validators import validate_ids_in_db


from apps.core.models import IP, Subdomain, URLResult,InitialAIAnalysis
from apps.core.schemas import (
    SuccessSendToAISchema,
    ScanIdsSchema,
    URLScanIdsSchema,
    ErrorSchema,
)
from .tasks import (
    trigger_ai_analysis_for_ips,
    trigger_ai_analysis_for_subdomains,
    trigger_ai_analysis_for_urls,
    trigger_initial_ai_analysis,
)

router = Router()
logger = logging.getLogger(__name__)



# =============================================================================
# API 端點設定 Registry（工廠設定）
# =============================================================================

# 每種資產型別的「就緒條件」驗證函式
# 格式：{ asset_type: async_readiness_checker(valid_ids) -> ready_ids }
# 若無就緒條件則為 None（直接全部觸發）
async def _check_ip_readiness(valid_ids):
    """IP 必須有至少一次 COMPLETED 的 Nmap 掃描。"""
    from apps.core.models import IP
    ready_ids_qs = IP.objects.filter(
        id__in=valid_ids, discovered_by_scans__status="COMPLETED"
    ).distinct()
    ready_ids = await sync_to_async(list)(ready_ids_qs.values_list("id", flat=True))
    if len(ready_ids) != len(valid_ids):
        unready = set(valid_ids) - set(ready_ids)
        logger.warning(f"IP IDs {unready} 掃描未完成")
        raise HttpError(
            400,
            f"操，這些 IP ID 還沒跑完 Nmap 掃描，分析個毛: {list(unready)}",
        )
    return ready_ids


async def _check_url_readiness(valid_ids):
    """URL 的掃描任務必須已 COMPLETED。"""
    from apps.core.models import URLResult
    unready_qs = URLResult.objects.filter(id__in=valid_ids).exclude(
        discovered_by_scans__status="COMPLETED"
    )
    unready_ids = await sync_to_async(list)(unready_qs.values_list("id", flat=True))
    if unready_ids:
        logger.warning(f"URL IDs {unready_ids} 掃描任務未完成")
        raise HttpError(
            400,
            f"操，這些 URL ID 的掃描任務沒完，無法分析: {unready_ids}",
        )
    return valid_ids


# API 端點工廠設定表
_ANALYZE_API_CONFIG = {
    "ip": {
        "model": IP,
        "asset_name": "IP",
        "readiness_check": _check_ip_readiness,
        "trigger_task": trigger_ai_analysis_for_ips,
        "success_unit": "IP",
    },
    "subdomain": {
        "model": Subdomain,
        "asset_name": "Subdomain",
        "readiness_check": None,  # 子域名無需額外就緒驗證
        "trigger_task": trigger_ai_analysis_for_subdomains,
        "success_unit": "子域名",
    },
    "url": {
        "model": URLResult,
        "asset_name": "URL",
        "readiness_check": _check_url_readiness,
        "trigger_task": trigger_ai_analysis_for_urls,
        "success_unit": "URL",
    },
    "initial": {
        "model": InitialAIAnalysis,
        "asset_name": "InitialAIAnalysis",
        "readiness_check": None,
        "trigger_task": trigger_initial_ai_analysis,
        "success_unit": "InitialAIAnalysis",
    },
}


# =============================================================================
# 通用分析觸發器（Generic Trigger Helper）
# =============================================================================

async def _trigger_analysis(asset_type: str, requested_ids: List[int]) -> dict:
    """
    【通用分析觸發器】

    根據 asset_type 從 _ANALYZE_API_CONFIG 取得設定，
    執行 ID 驗證 → 就緒性檢查 → 派發 Celery 任務。

    Returns:
        {"count": int} — 成功派發的資產數量
    """
    cfg = _ANALYZE_API_CONFIG[asset_type]
    logger.info(
        f"接收到 {cfg['asset_name']} AI 分析請求 for IDs: {requested_ids}"
    )

    # 防線一：ID 必須存在
    valid_ids = await validate_ids_in_db(
        cfg["model"], requested_ids, cfg["asset_name"]
    )

    # 防線二：選擇性就緒驗證
    if cfg["readiness_check"] is not None:
        valid_ids = await cfg["readiness_check"](valid_ids)

    # 派發任務
    try:
        cfg["trigger_task"].delay(valid_ids)
        logger.info(
            f"成功為 {len(valid_ids)} 個 {cfg['asset_name']} ID 派發 AI 分析任務"
        )
    except Exception as e:
        logger.exception(f"派發 AI 分析失敗: {e}")
        raise HttpError(500, "內部錯誤：無法派發任務")

    return {"count": len(valid_ids), "unit": cfg["success_unit"]}


# =============================================================================
# API 端點（精簡版）
# =============================================================================

@log_function_call()
@router.post(
    "/ips", response={202: SuccessSendToAISchema, 400: ErrorSchema, 404: ErrorSchema}
)
async def analyze_ai_ips(request, payload: ScanIdsSchema):
    """IP AI 分析"""
    result = await _trigger_analysis("ip", payload.ids)
    return 202, SuccessSendToAISchema(
        detail=f"AI 分析任務已成功派發給 {result['count']} 個 {result['unit']}。"
    )


@log_function_call()
@router.post("/subdomains", response={202: SuccessSendToAISchema, 404: ErrorSchema})
async def analyze_ai_subdomains(request, payload: ScanIdsSchema):
    """子域名 AI 分析"""
    result = await _trigger_analysis("subdomain", payload.ids)
    return 202, SuccessSendToAISchema(
        detail=f"AI 分析任務已成功派發給 {result['count']} 個 {result['unit']}。"
    )


@log_function_call()
@router.post(
    "/urls", response={202: SuccessSendToAISchema, 400: ErrorSchema, 404: ErrorSchema}
)
async def analyze_ai_urls(request, payload: URLScanIdsSchema):
    """URL AI 分析"""
    result = await _trigger_analysis("url", payload.ids)
    return 202, SuccessSendToAISchema(
        detail=f"AI 分析任務已成功派發給 {result['count']} 個 {result['unit']}。"
    )
@log_function_call()
@router.post(
    "/initial", response={202: SuccessSendToAISchema, 400: ErrorSchema, 404: ErrorSchema}
)
async def analyze_ai_initial(request, payload: ScanIdsSchema):
    """Initial AI 分析"""
    result = await _trigger_analysis("initial", payload.ids)
    return 202, SuccessSendToAISchema(
        detail=f"Initial AI 分析任務已成功派發給 {result['count']} 個 {result['unit']}。"
    )
    