import logging
from ninja import Router, Schema
from ninja.errors import HttpError
from typing import List
import os
from django.db.models import Q
from asgiref.sync import sync_to_async
from c2_core.config.logging import log_function_call

from apps.core.models import NmapScan
from django.db.models import Q

# 媽的，把我們的模型和 Schema 全都叫進來
from apps.core.models import IP, Subdomain, URLResult, URLScan
from apps.core.schemas import (
    SuccessSendToAISchema,
    ScanIdsSchema,
    URLScanIdsSchema,
)
from apps.core.schemas import ErrorSchema
from .tasks import (
    trigger_ai_analysis_for_ips,
    trigger_ai_analysis_for_subdomains,
    trigger_ai_analysis_for_urls,
)

router = Router()
logger = logging.getLogger(__name__)


# --- 核心邏輯：驗證 ID 是否存在 ---
async def validate_ids_in_db(model, requested_ids: List[int], asset_name: str):
    """
    通用驗證器：確認傳入的 ID 是否全部存在於資料庫中。
    """
    found_ids_qs = model.objects.filter(id__in=requested_ids)
    found_ids = await sync_to_async(list)(found_ids_qs.values_list("id", flat=True))

    missing_ids = set(requested_ids) - set(found_ids)
    if missing_ids:
        logger.warning(f"請求分析的 {asset_name} 中，ID {missing_ids} 不存在")
        raise HttpError(
            404, f"操，這些 {asset_name} ID 不在資料庫裡: {list(missing_ids)}"
        )

    return list(found_ids)


# IP AI 分析
@log_function_call()
@router.post(
    "/ips", response={202: SuccessSendToAISchema, 400: ErrorSchema, 404: ErrorSchema}
)
async def analyze_ai_ips(request, payload: ScanIdsSchema):
    requested_ids = payload.ids
    logger.info(f"接收到 IP AI 分析請求 for IDs: {requested_ids}")

    # 防線一：確認所有 ID 記錄都存在
    valid_ids = await validate_ids_in_db(IP, requested_ids, "IP")

    # 防線二：確認所有 IP 至少有一次成功的 Nmap 掃描
    ready_ids_qs = IP.objects.filter(
        id__in=valid_ids, discovered_by_scans__status="COMPLETED"
    ).distinct()

    ready_ids = await sync_to_async(list)(ready_ids_qs.values_list("id", flat=True))

    if len(ready_ids) != len(valid_ids):
        unready_ids = set(valid_ids) - set(ready_ids)
        logger.warning(f"IP IDs {unready_ids} 掃描未完成")
        raise HttpError(
            400, f"操，這些 IP ID 還沒跑完 Nmap 掃描，分析個毛: {list(unready_ids)}"
        )

    try:
        trigger_ai_analysis_for_ips.delay(ready_ids)
        logger.info(f"成功為 {len(ready_ids)} 個 IP ID 派發 AI 分析任務")
    except Exception as e:
        logger.exception(f"派發 AI 分析失敗: {e}")
        raise HttpError(500, "內部錯誤：無法派發任務")

    return 202, SuccessSendToAISchema(
        detail=f"AI 分析任務已成功派發給 {len(ready_ids)} 個 IP。"
    )


# 子域名 AI 分析
@log_function_call()
@router.post("/subdomains", response={202: SuccessSendToAISchema, 404: ErrorSchema})
async def analyze_ai_subdomains(request, payload: ScanIdsSchema):
    requested_ids = payload.ids
    logger.info(f"接收到子域名 AI 分析請求 for IDs: {requested_ids}")

    # 戰術驗證：確認 ID 真的躺在資料庫裡
    valid_ids = await validate_ids_in_db(Subdomain, requested_ids, "Subdomain")

    try:
        trigger_ai_analysis_for_subdomains.delay(valid_ids)
        logger.info(f"已為 {len(valid_ids)} 個子域名 ID 派發 AI 分析任務")
    except Exception as e:
        logger.exception(f"派發任務失敗: {e}")
        raise HttpError(500, "內部錯誤：無法派發任務")

    return 202, SuccessSendToAISchema(
        detail=f"AI 分析任務已成功派發給 {len(valid_ids)} 個子域名。"
    )


# URL AI 分析
@log_function_call()
@router.post(
    "/urls", response={202: SuccessSendToAISchema, 400: ErrorSchema, 404: ErrorSchema}
)
async def analyze_ai_urls(request, payload: URLScanIdsSchema):
    requested_ids = payload.ids
    logger.info(f"接收到 URL AI 分析請求 for IDs: {requested_ids}")

    # 防線一：ID 必須存在
    valid_ids = await validate_ids_in_db(URLResult, requested_ids, "URL")

    # 防線二：URL 的掃描任務 (URLScan) 狀態必須為 'COMPLETED'
    unready_qs = URLResult.objects.filter(id__in=valid_ids).exclude(
        discovered_by_scans__status="COMPLETED"
    )
    unready_ids = await sync_to_async(list)(unready_qs.values_list("id", flat=True))

    if unready_ids:
        logger.warning(f"URL IDs {unready_ids} 掃描任務未完成")
        raise HttpError(400, f"操，這些 URL ID 的掃描任務沒完，無法分析: {unready_ids}")

    try:
        trigger_ai_analysis_for_urls.delay(valid_ids)
        logger.info(f"已為 {len(valid_ids)} 個 URL ID 派發 AI 分析任務")
    except Exception as e:
        logger.exception(f"派發失敗: {e}")
        raise HttpError(500, "內部錯誤：無法派發任務")

    return 202, SuccessSendToAISchema(
        detail=f"AI 分析任務已成功派發給 {len(valid_ids)} 個 URL。"
    )
