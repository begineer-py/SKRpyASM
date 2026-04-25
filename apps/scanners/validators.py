"""
apps/scanners/validators.py

共用驗證器 (Shared Validators)

原本分散在 nuclei_scanner/api.py 和 analyze_ai/api.py 兩個完全相同的
validate_ids_in_db() 函式，現在統一管理於此。

使用範例::

    from apps.scanners.validators import validate_ids_in_db, check_no_active_scan

    # API Layer (async)
    valid_ids = await validate_ids_in_db(IP, [1, 2, 3], "IP")

    # Task Layer (sync)
    check_no_active_scan(NmapScan, {"ips_discovered": ip_obj}, "Nmap")
"""

from __future__ import annotations

import logging
from typing import List, Type

from asgiref.sync import sync_to_async
from django.db import models
from ninja.errors import HttpError

logger = logging.getLogger(__name__)


# =============================================================================
# Async validators (用於 API Layer)
# =============================================================================


async def validate_ids_in_db(
    model: Type[models.Model],
    requested_ids: List[int],
    asset_name: str,
) -> List[int]:
    """
    【通用 ID 存在性驗證器 — 非同步版】

    確認傳入的所有 ID 都存在於對應資料表中。
    若有任何 ID 不存在，拋出 HTTP 404 錯誤。

    Args:
        model:         Django Model 類別（如 IP, Subdomain, URLResult）
        requested_ids: 前端傳入需要驗證的 ID 列表
        asset_name:    用於錯誤訊息的資產名稱（如 "IP", "子域名", "URL"）

    Returns:
        已驗證存在的 ID 列表

    Raises:
        HttpError(404): 若有 ID 在資料庫中不存在
    """
    found_ids_qs = model.objects.filter(id__in=requested_ids)
    found_ids = await sync_to_async(list)(found_ids_qs.values_list("id", flat=True))

    missing_ids = set(requested_ids) - set(found_ids)
    if missing_ids:
        logger.warning(f"請求的 {asset_name} ID {missing_ids} 不存在於資料庫")
        raise HttpError(
            404, f"操，這些 {asset_name} ID 不在資料庫裡: {sorted(missing_ids)}"
        )

    return list(found_ids)


async def check_no_active_scan_async(
    scan_model: Type[models.Model],
    filter_kwargs: dict,
    tool_name: str,
    identifier: str = "",
) -> None:
    """
    【重複掃描防護 — 非同步版】

    確認指定條件下沒有 PENDING 或 RUNNING 的掃描任務。

    Args:
        scan_model:    掃描記錄模型（如 NmapScan, SubfinderScan）
        filter_kwargs: 用於過濾的欄位（如 {"ips_discovered": ip_obj}）
        tool_name:     工具名稱（用於錯誤訊息）
        identifier:    識別符（如 IP 字串、Domain 名稱），顯示在錯誤訊息中

    Raises:
        HttpError(409): 若已有正在進行的掃描
    """
    active_scan = await scan_model.objects.filter(
        **filter_kwargs, status__in=["PENDING", "RUNNING"]
    ).afirst()

    if active_scan:
        raise HttpError(
            409,
            f"{identifier or ''} 已有正在進行中的 {tool_name} 掃描任務 "
            f"(ID: {active_scan.id})，請等待完成後再試。",
        )


# =============================================================================
# Sync validators (用於 Celery Task Layer 或同步程式碼)
# =============================================================================


def validate_ids_in_db_sync(
    model: Type[models.Model],
    requested_ids: List[int],
    asset_name: str,
) -> List[int]:
    """
    【通用 ID 存在性驗證器 — 同步版】

    與 validate_ids_in_db 邏輯相同，但適用於同步（非 async）呼叫情境。

    Raises:
        ValueError: 若有 ID 在資料庫中不存在
    """
    found_ids = list(
        model.objects.filter(id__in=requested_ids).values_list("id", flat=True)
    )
    missing_ids = set(requested_ids) - set(found_ids)
    if missing_ids:
        logger.warning(f"請求的 {asset_name} ID {missing_ids} 不存在於資料庫")
        raise ValueError(
            f"這些 {asset_name} ID 不在資料庫裡: {sorted(missing_ids)}"
        )
    return found_ids
