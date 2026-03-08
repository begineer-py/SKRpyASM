# apps/subfinder/api.py
# 子域名發現與偵察鏈啟動 API
import logging
from ninja import Router
from ninja.errors import HttpError

from apps.core.models import Seed, Subdomain
from apps.core.models import SubfinderScan, AmassScan
from c2_core.config.logging import log_function_call
from .schemas import (
    SubfinderScanSchema,
    DomainReconTriggerSchema,
)  # <-- 使用新的 Trigger Schema
from apps.core.schemas import ErrorSchema
from .tasks import start_subfinder, start_amass_scan

router = Router()
logger = logging.getLogger(__name__)


@log_function_call()
@router.post(
    "/start_subfinder",
    response={
        200: SubfinderScanSchema,
        400: ErrorSchema,
        404: ErrorSchema,
        409: ErrorSchema,
    },
    summary="對指定的 DOMAIN 種子啟動一個完整的偵察鏈",
    tags=["Recon Chain"],
)
async def start_full_domain_recon(
    request, payload: DomainReconTriggerSchema
) -> SubfinderScanSchema:
    """
    啟動完整領域偵察鏈。

    接收一個 seed_id，驗證其類型為 DOMAIN，並啟動一個由 Subfinder 開始的自動化掃描流程。

    流程：
    1. 驗證 Seed 存在且類型為 DOMAIN。
    2. 檢查是否已有活躍掃描任務。
    3. 創建掃描記錄並設置為 PENDING 狀態。
    4. 透過 Celery 觸發異步偵察任務。
    """
    seed_id = payload.seed_id
    logger.info(f"收到對 Seed ID: {seed_id} 的 DOMAIN 偵察鏈啟動請求。")

    # 1. 直接獲取 Seed，並驗證類型
    try:
        seed = await Seed.objects.select_related("target").aget(id=seed_id)
        if seed.type != "DOMAIN":
            raise HttpError(
                400, f"Seed ID {seed_id} 的類型為 '{seed.type}'，不是 'DOMAIN'。"
            )
        if not seed.is_active:
            raise HttpError(400, f"Seed ID {seed_id} 當前為非活躍狀態。")
    except Seed.DoesNotExist:
        raise HttpError(404, f"找不到 Seed ID: {seed_id}。")

    # 2. 檢查是否有正在進行的掃描
    existing_scan = await SubfinderScan.objects.filter(
        which_seed=seed, status__in=["PENDING", "RUNNING"]
    ).afirst()
    if existing_scan:
        raise HttpError(
            409,
            f"Seed '{seed.value}' (ID: {seed.id}) 已有正在進行中的掃描任務 (ID: {existing_scan.id})。",
        )

    # 3. 創建一個新的掃描記錄
    scan_record = await SubfinderScan.objects.acreate(which_seed=seed, status="PENDING")

    # 附加上關聯數據，以便 Schema 正確序列化
    scan_record.which_seed = seed

    # 4. 觸發 Celery 任務
    start_subfinder.delay(scan_id=scan_record.id)

    logger.info(f"偵察鏈已為 Seed '{seed.value}' 啟動，掃描記錄 ID: {scan_record.id}")

    return scan_record


@log_function_call()
@router.post(
    "/start_amass",
    response={
        200: SubfinderScanSchema,
        400: ErrorSchema,
        404: ErrorSchema,
        409: ErrorSchema,
    },
    summary="對指定的 DOMAIN 種子啟動一個完整的偵察鏈",
    tags=["Recon Chain"],
)
async def start_amass_recon(
    request, payload: DomainReconTriggerSchema
) -> SubfinderScanSchema:
    """
    啟動完整領域偵察鏈。

    接收一個 seed_id，驗證其類型為 DOMAIN，並啟動一個由 Amass 開始的自動化掃描流程。

    流程：
    1. 驗證 Seed 存在且類型為 DOMAIN。
    2. 檢查是否已有活躍掃描任務。
    3. 創建掃描記錄並設置為 PENDING 狀態。
    4. 透過 Celery 觸發異步偵察任務。
    """
    seed_id = payload.seed_id
    logger.info(f"收到對 Seed ID: {seed_id} 的 Amass 偵察鏈啟動請求。")

    # 1. 直接獲取 Seed，並驗證類型
    try:
        seed = await Seed.objects.select_related("target").aget(id=seed_id)
        if seed.type != "DOMAIN":
            raise HttpError(
                400, f"Seed ID {seed_id} 的類型為 '{seed.type}'，不是 'DOMAIN'。"
            )
        if not seed.is_active:
            raise HttpError(400, f"Seed ID {seed_id} 當前為非活躍狀態。")
    except Seed.DoesNotExist:
        raise HttpError(404, f"找不到 Seed ID: {seed_id}。")

    # 2. 檢查是否有正在進行的掃描
    existing_scan = await AmassScan.objects.filter(
        which_seed=seed, status__in=["PENDING", "RUNNING"]
    ).afirst()
    if existing_scan:
        raise HttpError(
            409,
            f"Seed '{seed.value}' (ID: {seed.id}) 已有正在進行中的掃描任務 (ID: {existing_scan.id})。",
        )
    existing_subfinder_scan = await SubfinderScan.objects.filter(
        which_seed_id=seed_id
    ).aexists()
    if not existing_subfinder_scan:
        raise HttpError(400, f"請先執行 Subfinder 掃描以獲取初步資產。")
    # 3. 創建一個新的掃描記錄
    # 附加上關聯數據，以便 Schema 正確序列化
    scan_record = await AmassScan.objects.acreate(
        which_seed=seed,
        which_target=seed.target,
        status="PENDING",
    )
    # 4. 觸發 Celery 任務
    
    start_amass_scan.delay(scan_id=scan_record.id,seed_id=seed_id) # 👈 傳給它這筆 Scan 真正的 ID

    logger.info(f"amass 偵察鏈已為 Seed '{seed.value}' 啟動，掃描記錄 ID: {scan_record.id}")

    return scan_record
