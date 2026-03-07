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
    SuccessSendToAISchema,  # 返回格式一樣,不改
    NucleiScanIPByIdsSchema,
    NucleiScanSubdomainByIdsSchema,
    NucleiScanURLByIdsSchema,
)
from apps.core.schemas import ErrorSchema
from .tasks import (
    perform_nuclei_scans_for_ip_batch,
    perform_nuclei_scans_for_subdomain_batch,
    perform_nuclei_scans_for_url_batch,
    scan_url_tech_stack,
    scan_subdomain_tech,
)

router = Router()
logger = logging.getLogger(__name__)


# --- 核心邏輯：驗證 ID 是否存在 ---
async def validate_ids_exist(model, requested_ids: List[int], asset_name: str):
    """
    驗證一組 ID 是否存在於資料庫中。
    """
    found_ids_qs = model.objects.filter(id__in=requested_ids)
    found_ids = await sync_to_async(list)(found_ids_qs.values_list("id", flat=True))

    missing_ids = set(requested_ids) - set(found_ids)
    if missing_ids:
        logger.warning(f"{asset_name} ID 不存在: {missing_ids}")
        raise HttpError(
            404, f"操，這些 {asset_name} ID 不在資料庫裡: {list(missing_ids)}"
        )

    return list(found_ids)


# --- IP 掃描 ---
@router.post("/ips", response={202: SuccessSendToAISchema, 404: ErrorSchema})
async def scan_ips(request, payload: NucleiScanIPByIdsSchema):
    logger.info(f"接收到 IP 掃描請求: {payload.ids}")
    valid_ids = await validate_ids_exist(IP, payload.ids, "IP")

    perform_nuclei_scans_for_ip_batch.delay(valid_ids)
    return 202, SuccessSendToAISchema(
        detail=f"成功派發 {len(valid_ids)} 個 IP 的掃描任務"
    )


# --- 子域名漏洞掃描 ---
@router.post("/subdomains", response={202: SuccessSendToAISchema, 404: ErrorSchema})
async def scan_subdomains(request, payload: NucleiScanSubdomainByIdsSchema):
    logger.info(f"接收到子域名掃描請求: {payload.ids}")
    valid_ids = await validate_ids_exist(Subdomain, payload.ids, "Subdomain")

    perform_nuclei_scans_for_subdomain_batch.delay(valid_ids)
    return 202, SuccessSendToAISchema(
        detail=f"成功派發 {len(valid_ids)} 個子域名的掃描任務"
    )


# --- 子域名技術辨識 (sub_tech) ---
@router.post("/subs_tech", response={202: SuccessSendToAISchema, 404: ErrorSchema})
async def post_sub_tech(request, payload: NucleiScanSubdomainByIdsSchema):
    logger.info(f"接收到子域名技術辨識請求: {payload.ids}")
    valid_ids = await validate_ids_exist(Subdomain, payload.ids, "Subdomain")

    scan_subdomain_tech.delay(valid_ids)
    return 202, SuccessSendToAISchema(
        detail=f"成功派發 {len(valid_ids)} 個子域名的技術辨識任務"
    )


# --- URL 漏洞分析 ---
@router.post(
    "/urls", response={202: SuccessSendToAISchema, 400: ErrorSchema, 404: ErrorSchema}
)
async def scan_urls(request, payload: NucleiScanURLByIdsSchema):
    logger.info(f"接收到 URL 分析請求: {payload.ids}")

    # 1. 第一道防線：ID 存在
    valid_ids = await validate_ids_exist(URLResult, payload.ids, "URL")

    # 2. 第二道防線：前置掃描必須完成
    unready_qs = URLResult.objects.filter(id__in=valid_ids).exclude(
        discovered_by_scans__status="COMPLETED"
    )
    unready_ids = await sync_to_async(list)(unready_qs.values_list("id", flat=True))

    if unready_ids:
        raise HttpError(400, f"操，這些 URL ID 的掃描任務還沒完成: {unready_ids}")

    perform_nuclei_scans_for_url_batch.delay(valid_ids)
    return 202, SuccessSendToAISchema(
        detail=f"成功派發 {len(valid_ids)} 個 URL 的掃描任務"
    )


# --- URL 技術辨識 (url_tech) ---
@router.post(
    "/urls_tech",
    response={202: SuccessSendToAISchema, 400: ErrorSchema, 404: ErrorSchema},
)
async def post_url_tech(request, payload: NucleiScanURLByIdsSchema):
    logger.info(f"接收到 URL 技術辨識請求: {payload.ids}")

    valid_ids = await validate_ids_exist(URLResult, payload.ids, "URL")

    # 校驗任務狀態
    unready_qs = URLResult.objects.filter(id__in=valid_ids).exclude(
        discovered_by_scans__status="COMPLETED"
    )
    unready_ids = await sync_to_async(list)(unready_qs.values_list("id", flat=True))
    if unready_ids:
        raise HttpError(400, f"操，掃描沒完不能辨識技術: {unready_ids}")

    scan_url_tech_stack.delay(valid_ids)
    return 202, SuccessSendToAISchema(
        detail=f"成功派發 {len(valid_ids)} 個 URL 的技術辨識任務"
    )
