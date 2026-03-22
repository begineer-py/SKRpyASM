import logging
from ninja import Router
from ninja.errors import HttpError
from typing import List, Optional
from asgiref.sync import sync_to_async
from c2_core.config.logging import log_function_call

from apps.core.models import IP, Subdomain, URLResult
from apps.core.schemas import (
    SuccessSendToAISchema,
    NucleiScanIPByIdsSchema,
    NucleiScanSubdomainByIdsSchema,
    NucleiScanURLByIdsSchema,
    ErrorSchema,
)
from .tasks import (
    perform_nuclei_scans_for_ip_batch,
    perform_nuclei_scans_for_subdomain_batch,
    perform_nuclei_scans_for_url_batch,
    scan_url_tech_stack,
    scan_subdomain_tech,
)

router = Router()
logger = logging.getLogger(__name__)


# =============================================================================
# 通用 ID 驗證器
# =============================================================================

async def validate_ids_exist(model, requested_ids: List[int], asset_name: str):
    """驗證一組 ID 是否存在於資料庫中"""
    found_ids_qs = model.objects.filter(id__in=requested_ids)
    found_ids = await sync_to_async(list)(found_ids_qs.values_list("id", flat=True))

    missing_ids = set(requested_ids) - set(found_ids)
    if missing_ids:
        logger.warning(f"{asset_name} ID 不存在: {missing_ids}")
        raise HttpError(
            404, f"操，這些 {asset_name} ID 不在資料庫裡: {list(missing_ids)}"
        )

    return list(found_ids)


# =============================================================================
# API 端點設定 Registry (Factory)
# =============================================================================

async def _check_url_readiness(valid_ids):
    """URL 的前置掃描任務必須完成"""
    unready_qs = URLResult.objects.filter(id__in=valid_ids).exclude(
        discovered_by_scans__status="COMPLETED"
    )
    unready_ids = await sync_to_async(list)(unready_qs.values_list("id", flat=True))
    if unready_ids:
        raise HttpError(400, f"操，這些 URL ID 的掃描任務還沒完成: {unready_ids}")
    return valid_ids


_NUCLEI_API_CONFIG = {
    "ip": {
        "model": IP,
        "asset_name": "IP",
        "readiness_check": None,
        "trigger_task": perform_nuclei_scans_for_ip_batch,
    },
    "subdomain": {
        "model": Subdomain,
        "asset_name": "Subdomain",
        "readiness_check": None,
        "trigger_task": perform_nuclei_scans_for_subdomain_batch,
    },
    "url": {
        "model": URLResult,
        "asset_name": "URL",
        "readiness_check": _check_url_readiness,
        "trigger_task": perform_nuclei_scans_for_url_batch,
    },
}


# =============================================================================
# 通用觸發器 Helper
# =============================================================================

async def _trigger_nuclei_scan(
    asset_type: str, requested_ids: List[int], tags: Optional[List[str]] = None, callback_step_id: Optional[int] = None
) -> int:
    """通用 Nuclei 掃描觸發器"""
    cfg = _NUCLEI_API_CONFIG[asset_type]
    logger.info(f"接收到 {cfg['asset_name']} Nuclei 掃描請求: {requested_ids} (Step: {callback_step_id})")

    valid_ids = await validate_ids_exist(cfg["model"], requested_ids, cfg["asset_name"])

    if cfg["readiness_check"]:
        valid_ids = await cfg["readiness_check"](valid_ids)

    cfg["trigger_task"].delay(valid_ids, tags, callback_step_id=callback_step_id)
    return len(valid_ids)


# =============================================================================
# 漏洞掃描端點 (重構後)
# =============================================================================

@router.post("/ips", response={202: SuccessSendToAISchema, 404: ErrorSchema})
async def scan_ips(request, payload: NucleiScanIPByIdsSchema):
    """IP 掃描"""
    count = await _trigger_nuclei_scan("ip", payload.ids, payload.tags, callback_step_id=payload.callback_step_id)
    return 202, SuccessSendToAISchema(detail=f"成功派發 {count} 個 IP 的掃描任務")


@router.post("/subdomains", response={202: SuccessSendToAISchema, 404: ErrorSchema})
async def scan_subdomains(request, payload: NucleiScanSubdomainByIdsSchema):
    """子域名掃描"""
    count = await _trigger_nuclei_scan("subdomain", payload.ids, payload.tags, callback_step_id=payload.callback_step_id)
    return 202, SuccessSendToAISchema(detail=f"成功派發 {count} 個子域名的掃描任務")


@router.post(
    "/urls", response={202: SuccessSendToAISchema, 400: ErrorSchema, 404: ErrorSchema}
)
async def scan_urls(request, payload: NucleiScanURLByIdsSchema):
    """URL 掃描"""
    count = await _trigger_nuclei_scan("url", payload.ids, payload.tags, callback_step_id=payload.callback_step_id)
    return 202, SuccessSendToAISchema(detail=f"成功派發 {count} 個 URL 的掃描任務")


# =============================================================================
# 技術辨識端點 (暫不納入 Factory，保持原樣)
# =============================================================================

@router.post("/subs_tech", response={202: SuccessSendToAISchema, 404: ErrorSchema})
async def post_sub_tech(request, payload: NucleiScanSubdomainByIdsSchema):
    """子域名技術辨識"""
    logger.info(f"接收到子域名技術辨識請求: {payload.ids}")
    valid_ids = await validate_ids_exist(Subdomain, payload.ids, "Subdomain")
    scan_subdomain_tech.delay(valid_ids)
    return 202, SuccessSendToAISchema(detail=f"成功派發 {len(valid_ids)} 個子域名的技術辨識任務")


@router.post(
    "/urls_tech",
    response={202: SuccessSendToAISchema, 400: ErrorSchema, 404: ErrorSchema},
)
async def post_url_tech(request, payload: NucleiScanURLByIdsSchema):
    """URL 技術辨識"""
    logger.info(f"接收到 URL 技術辨識請求: {payload.ids}")
    valid_ids = await validate_ids_exist(URLResult, payload.ids, "URL")

    # 校驗任務狀態
    valid_ids = await _check_url_readiness(valid_ids)

    scan_url_tech_stack.delay(valid_ids)
    return 202, SuccessSendToAISchema(detail=f"成功派發 {len(valid_ids)} 個 URL 的技術辨識任務")
