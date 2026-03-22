# apps/subfinder/api.py
# 子域名發現與偵察鏈啟動 API

import logging
from ninja import Router
from ninja.errors import HttpError
from typing import Type, Optional
from django.db.models import Model

from apps.core.models import Seed, SubfinderScan, AmassScan
from c2_core.config.logging import log_function_call
from .schemas import (
    SubfinderScanSchema,
    DomainReconTriggerSchema,
)
from apps.core.schemas import ErrorSchema
from .tasks import start_subfinder, start_amass_scan

router = Router()
logger = logging.getLogger(__name__)


# =============================================================================
# API 觸發器配置 (Registry)
# =============================================================================

_RECON_CONFIG = {
    "subfinder": {
        "scan_model": SubfinderScan,
        "trigger_task": start_subfinder,
        "description": "Subfinder",
    },
    "amass": {
        "scan_model": AmassScan,
        "trigger_task": start_amass_scan,
        "description": "Amass",
    },
}


# =============================================================================
# 通用觸發器 Helper
# =============================================================================

async def _trigger_recon_chain(
    tool_key: str, seed_id: int
) -> Model:
    """
    【通用偵察鏈啟動助手】
    處理 Seed 驗證、重複檢查與 Record 建立。
    """
    cfg = _RECON_CONFIG[tool_key]
    logger.info(f"收到對 Seed ID: {seed_id} 的 {cfg['description']} 偵察鏈啟動請求。")

    # 1. 驗證 Seed
    try:
        seed = await Seed.objects.select_related("target").aget(id=seed_id)
        if seed.type != "DOMAIN":
            raise HttpError(400, f"Seed ID {seed_id} 的類型為 '{seed.type}'，不是 'DOMAIN'。")
        if not seed.is_active:
            raise HttpError(400, f"Seed ID {seed_id} 當前為非活躍狀態。")
    except Seed.DoesNotExist:
        raise HttpError(404, f"找不到 Seed ID: {seed_id}。")

    # 2. 檢查是否有正在進行的掃描
    existing_scan = await cfg["scan_model"].objects.filter(
        which_seed=seed, status__in=["PENDING", "RUNNING"]
    ).afirst()
    if existing_scan:
        raise HttpError(
            409,
            f"Seed '{seed.value}' (ID: {seed.id}) 已有正在進行中的 {cfg['description']} 掃描任務 (ID: {existing_scan.id})。",
        )

    # Amass 特有檢查：必須先跑過 Subfinder (邏輯來自原代碼)
    if tool_key == "amass":
        existing_subfinder_scan = await SubfinderScan.objects.filter(
            which_seed_id=seed_id
        ).aexists()
        if not existing_subfinder_scan:
            raise HttpError(400, f"請先執行 Subfinder 掃描以獲取初步資產。")

    # 3. 建立掃描記錄
    create_params = {"which_seed": seed, "status": "PENDING"}
    if tool_key == "amass":
        create_params["which_target"] = seed.target

    scan_record = await cfg["scan_model"].objects.acreate(**create_params)
    scan_record.which_seed = seed # 序列化需要

    # 4. 觸發任務
    if tool_key == "amass":
        cfg["trigger_task"].delay(scan_id=scan_record.id, seed_id=seed_id)
    else:
        cfg["trigger_task"].delay(scan_id=scan_record.id)

    logger.info(f"{cfg['description']} 偵察鏈啟動成功: Seed='{seed.value}', ScanID={scan_record.id}")
    return scan_record


# =============================================================================
# API 端點
# =============================================================================

@log_function_call()
@router.post(
    "/start_subfinder",
    response={200: SubfinderScanSchema, 400: ErrorSchema, 404: ErrorSchema, 409: ErrorSchema},
    summary="啟動 Subfinder 偵察任務",
    tags=["Recon Chain"],
)
async def start_full_domain_recon(request, payload: DomainReconTriggerSchema):
    """啟動基於 Subfinder 的子域名發現流程"""
    return await _trigger_recon_chain("subfinder", payload.seed_id)


@log_function_call()
@router.post(
    "/start_amass",
    response={200: SubfinderScanSchema, 400: ErrorSchema, 404: ErrorSchema, 409: ErrorSchema},
    summary="啟動 Amass 被動掃描任務",
    tags=["Recon Chain"],
)
async def start_amass_recon(request, payload: DomainReconTriggerSchema):
    """啟動基於 Amass 的增強發現流程"""
    return await _trigger_recon_chain("amass", payload.seed_id)
