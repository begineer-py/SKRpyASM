# subdomain_finder/api.py

import logging
from ninja import Router
from ninja.errors import HttpError

from apps.core.models.assets import Seed, Subdomain
from apps.core.models.scans_record_modles import SubfinderScan
from c2_core.config.logging import log_function_call
from .schemas import (
    SubfinderScanSchema,
    DomainReconTriggerSchema,
)  # <-- 使用新的 Trigger Schema
from apps.core.schemas import ErrorSchema
from .tasks import start_subfinder

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
    接收一個 seed_id，驗證其類型為 DOMAIN，並啟動一個完整的偵察鏈。

    - 如果找不到對應的 Seed 或類型不對，返回 404/400。
    - 如果已有正在進行的掃描，返回 409。
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
