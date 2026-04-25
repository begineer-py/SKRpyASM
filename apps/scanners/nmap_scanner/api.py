# apps/nmap_scanner/api.py
# Nmap 掃描啟動與管理 API

import logging
from ninja import Router, Schema
from ninja.errors import HttpError
from typing import List, Optional
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count

# 導入資產與掃描核心模型
from apps.core.models import IP, Seed
from apps.core.models import NmapScan
from .schemas import (
    NmapScanTriggerSchema,
    NmapScanSchema,
    ErrorSchema,
)
from .tasks import perform_nmap_scan
from c2_core.config.logging import log_function_call
from django.db.models import Q
from asgiref.sync import sync_to_async

router = Router()
logger = logging.getLogger(__name__)

@router.post("/start_scan", response={202: NmapScanSchema})
@log_function_call()
async def start_nmap_scan(request, trigger_data: NmapScanTriggerSchema):
    """
    對指定 IP 啟動 Nmap 異步掃描。
    
    流程：
    1. 驗證傳入的所有 Seed ID 是否存在。
    2. 驗證目標 IP 是否已存在於資產庫（IP 模型）。
    3. 將 IP 與傳入的 Seeds 建立關聯（歸屬權確認）。
    4. 檢查該 IP 是否已有正在執行的掃描任務，避免重疊。
    5. 根據請求參數組裝 Nmap 命令字串。
    6. 創建 NmapScan 數據庫記錄並關聯 Seeds/IP。
    7. 投遞 Celery 任務執行實際掃描。
    """
    ip_str = trigger_data.ip
    seed_ids = trigger_data.seed_ids  # 這是 List[int]

    if not seed_ids:
        raise HttpError(400, "必須提供至少一個 seed_id")

    # 1. 批量獲取 Seeds
    seeds = await sync_to_async(list)(Seed.objects.filter(id__in=seed_ids))

    if len(seeds) != len(seed_ids):
        found_ids = [s.id for s in seeds]
        missing = set(seed_ids) - set(found_ids)
        raise HttpError(404, f"部分 seed 找不到: {missing}")

    # 2. 獲取或確認 IP
    try:
        ip_obj = await IP.objects.filter(address=ip_str).afirst()
        if not ip_obj:
            raise HttpError(404, f"找不到 IP 資產: {ip_str}")

        # [同步歸屬權]：把這個 IP 關聯到「所有」傳入的 Seed
        await sync_to_async(ip_obj.which_seed.add)(*seeds)

    except Exception as e:
        if isinstance(e, HttpError):
            raise e
        raise HttpError(500, f"資產查詢或關聯失敗: {str(e)}")

    # 3. 檢查是否有正在進行的掃描
    existing_active_scan = await NmapScan.objects.filter(
        ips_discovered=ip_obj, status__in=["PENDING", "RUNNING"]
    ).afirst()

    if existing_active_scan:
        raise HttpError(
            409,
            f"IP {ip_str} 已有正在進行中的任務 (ID: {existing_active_scan.id})",
        )

    # 4. 參數組裝 (保持不變)
    args = []
    # ... (參數組裝代碼省略) ...
    args.append(f"-T{trigger_data.scan_rate}")
    args.append("-oX -")
    final_nmap_args = " ".join(args)

    # 5. 創建 NmapScan 紀錄
    # [修正點]：acreate 的時候不要傳 which_seed，因為它是 M2M
    scan_record = await NmapScan.objects.acreate(
        nmap_args=final_nmap_args,
        status="PENDING",
    )

    # 6. 建立所有 M2M 關聯
    # 關聯 Seeds (把所有 seed_ids 都加進去)
    await sync_to_async(scan_record.which_seed.add)(*seeds)
    # 關聯 IP
    await sync_to_async(scan_record.ips_discovered.add)(ip_obj)

    logger.info(
        f"為 IP {ip_str} 創建新的 NmapScan 記錄: ID={scan_record.id} (Seeds: {seed_ids})"
    )

    # 7. 觸發任務
    perform_nmap_scan.delay(
        scan_id=scan_record.id,
        ip_address=ip_str,
        nmap_args=final_nmap_args,
        callback_step_id=trigger_data.callback_step_id,
    )

    # 8. 回傳
    return NmapScanSchema(
        id=scan_record.id,
        ip_id=ip_obj.id,
        ip_address=[ip_obj.address],
        scan_type="custom_scan",
        nmap_args=scan_record.nmap_args,
        status=scan_record.status,
        started_at=scan_record.started_at,
        completed_at=scan_record.completed_at,
        error_message=scan_record.error_message,
    )
