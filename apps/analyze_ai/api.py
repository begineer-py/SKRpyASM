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
    SuccessSendIPSchema,
    SuccessSendSubdomainSchema,
    SuccessSendURLSchema,
)
from apps.core.schemas import ErrorSchema
from .tasks import (
    trigger_ai_analysis_for_ips,
    trigger_ai_analysis_for_subdomains,
    trigger_ai_analysis_for_urls,
)

router = Router()
logger = logging.getLogger(__name__)


# --- 核心邏輯：驗證資產是否存在 ---
# 我們把重複的邏輯抽成一個可複用的兵器
async def validate_assets_exist(
    model, query, requested_assets: List[str], asset_name: str
):
    """
    異步驗證一組資產是否存在於資料庫中。
    如果任何一個資產不存在，直接拋出 404 HttpError。
    """
    # 執行一次數據庫查詢，把所有東西撈出來
    # sync_to_async(list) 是關鍵，它在異步上下文中執行同步的 ORM 查詢並立即評估結果
    found_assets_qs = model.objects.filter(query)
    found_assets = await sync_to_async(list)(found_assets_qs)

    # 用 set 來比較，效率最高，還能自動去重
    requested_set = set(requested_assets)

    # 根據 model 類型，從對象中提取出字符串值來構建 found_set
    if model == IP:
        found_set = {asset.ipv4 for asset in found_assets if asset.ipv4} | {
            asset.ipv6 for asset in found_assets if asset.ipv6
        }
    elif model == Subdomain:
        found_set = {asset.name for asset in found_assets}
    elif model == URLResult:
        found_set = {asset.url for asset in found_assets}
    else:
        # 預防性防禦
        raise TypeError("Unsupported model type for validation")

    # 如果請求的數量和找到的數量不匹配，說明有鬼
    if len(found_set) != len(requested_set):
        missing_assets = requested_set - found_set
        logger.warning(
            f"請求分析的 {asset_name} 中，有 {len(missing_assets)} 個不存在: {missing_assets}"
        )
        raise HttpError(
            404, f"操，這些 {asset_name} 不在資料庫裡: {list(missing_assets)}"
        )

    logger.info(f"驗證通過: {len(found_assets)} 個 {asset_name} 均存在於資料庫中。")
    return found_assets


# IP分析 (升級版)
@log_function_call()
@router.post(
    "/ips",
    response={
        202: SuccessSendToAISchema,
        400: ErrorSchema,  # <--- 新增：用於邏輯錯誤，如掃描未完成
        404: ErrorSchema,
        422: ErrorSchema,
    },
    summary="對一批 IP 地址觸發 AI 分析 (僅限已完成掃描的 IP)",
)
async def analyze_ai_ips(request, payload: SuccessSendIPSchema):
    ips_to_check = payload.ips
    requested_ips_set = set(ips_to_check)
    logger.info(
        f"接收到 AI 分析請求 for {len(requested_ips_set)} 個 IP: {ips_to_check}"
    )

    # --- 戰術驗證：雙重防線 ---
    base_query = Q(ipv4__in=requested_ips_set) | Q(ipv6__in=requested_ips_set)

    # 防線一：確認所有 IP 記錄都存在。
    found_ips_qs = IP.objects.filter(base_query)

    # 為了高效比較，我們需要把查到的 IP 對象轉回字符串列表
    found_ips_from_db = await sync_to_async(list)(found_ips_qs)
    found_ips_set = set()
    for ip_obj in found_ips_from_db:
        if ip_obj.ipv4:
            found_ips_set.add(ip_obj.ipv4)
        if ip_obj.ipv6:
            found_ips_set.add(ip_obj.ipv6)

    # 過濾掉請求中但數據庫裡不存在的IP
    found_ips_set = found_ips_set.intersection(requested_ips_set)

    if found_ips_set != requested_ips_set:
        missing_ips = requested_ips_set - found_ips_set
        logger.warning(
            f"請求分析的 IP 中，有 {len(missing_ips)} 個不存在: {missing_ips}"
        )
        raise HttpError(404, f"操，這些 IP 不在資料庫裡: {list(missing_ips)}")

    logger.info("第一道防線通過：所有請求的 IP 記錄均存在。")

    # 防線二：確認所有 IP 至少有一次成功的 Nmap 掃描。
    # 我們直接查找那些「合格」的 IP。
    ready_ips_qs = IP.objects.filter(
        base_query, discovered_by_scans__status="COMPLETED"
    ).distinct()  # distinct() 確保如果一個IP有多個成功掃描，它只出現一次

    ready_ips_from_db = await sync_to_async(list)(ready_ips_qs)
    ready_ips_set = set()
    for ip_obj in ready_ips_from_db:
        if ip_obj.ipv4:
            ready_ips_set.add(ip_obj.ipv4)
        if ip_obj.ipv6:
            ready_ips_set.add(ip_obj.ipv6)

    ready_ips_set = ready_ips_set.intersection(requested_ips_set)

    if ready_ips_set != requested_ips_set:
        unready_ips = requested_ips_set - ready_ips_set
        logger.warning(
            f"請求分析的 IP 中，有 {len(unready_ips)} 個沒有已完成的 Nmap 掃描: {unready_ips}"
        )
        raise HttpError(
            400, f"操，這些 IP 還沒有完成 Nmap 掃描，無法分析: {list(unready_ips)}"
        )

    logger.info("第二道防線通過：所有 IP 均有關聯的已完成 Nmap 掃描。")

    # --- 驗證通過，準備派發任務 ---

    # final_ip_objects 就是我們第一步查出來的 found_ips_from_db
    final_ip_objects = found_ips_from_db

    try:
        ip_ids_to_send = [ip.id for ip in final_ip_objects]

        trigger_ai_analysis_for_ips.delay(ip_ids_to_send)
        logger.info(f"準備為 {len(final_ip_objects)} 個 IP 派發 AI 分析任務。")
    except Exception as e:
        logger.exception(f"派發 AI 分析任務失敗：{e}")
        raise HttpError(status_code=500, message="內部錯誤：無法派發 AI 分析任務")

    return 202, SuccessSendToAISchema(
        detail=f"AI 分析任務已成功派發給 {len(final_ip_objects)} 個 IP。"
    )


# 子域名分析
@log_function_call()
@router.post(
    "/subdomains",
    response={
        202: SuccessSendToAISchema,
        404: ErrorSchema,
        422: ErrorSchema,
    },
    summary="對一批子域名觸發 AI 分析",
    description="核心流程：驗證子域名存在 -> 提取 ID -> 丟給 Celery 異步處理 (調用 Hasura 獲取詳細 DNS/URL 數據 -> AI 分析)",
)
async def analyze_ai_subdomains(request, payload: SuccessSendSubdomainSchema):
    subdomains_to_check = payload.subdomains
    logger.info(
        f"接收到 AI 分析請求 for {len(subdomains_to_check)} 個子域名: {subdomains_to_check}"
    )

    # 1. 構造查詢: 在 name 字段中查找
    query = Q(name__in=subdomains_to_check)

    # 2. 戰術驗證：確認這些子域名真的躺在我們的資料庫裡
    # 使用之前定義的通用驗證函數 validate_assets_exist
    found_subdomains = await validate_assets_exist(
        Subdomain, query, subdomains_to_check, "Subdomains"
    )

    # 3. 提取 ID 並派發任務
    try:
        # 提取 ID 列表，這是 Celery 任務需要的彈藥
        subdomain_ids = [sub.id for sub in found_subdomains]

        # 調用 Celery 任務 (Fire and Forget)
        # 注意：具體的 Hasura 查詢和 Prompt 填充邏輯都在這個 task 裡
        trigger_ai_analysis_for_subdomains.delay(subdomain_ids)

        logger.info(
            f"已為 {len(found_subdomains)} 個子域名成功派發 AI 分析任務 (Task ID dispatched)."
        )

    except Exception as e:
        logger.exception(f"派發 AI 分析任務失敗：{e}")
        raise HttpError(status_code=500, message="內部錯誤：無法派發 AI 分析任務")

    # 4. 返回 202 Accepted，不阻塞客戶端
    return 202, SuccessSendToAISchema(
        detail=f"AI 分析任務已成功派發給 {len(found_subdomains)} 個子域名。"
    )


@log_function_call()
@router.post(
    "/urls",
    response={
        202: SuccessSendToAISchema,
        400: ErrorSchema,  # <--- 新增：用於邏輯錯誤，如任務未完成
        404: ErrorSchema,
        422: ErrorSchema,
    },
    summary="對一批 URL 觸發 AI 分析 (僅限已完成掃描的 URL)",
)
async def analyze_ai_urls(request, payload: SuccessSendURLSchema):
    urls_to_check = payload.urls
    requested_urls_set = set(urls_to_check)
    logger.info(f"接收到 AI 分析請求 for {len(requested_urls_set)} 個 URL。")

    # --- 戰術驗證：雙重防線 ---

    # 防線一：確認所有 URLResult 記錄都存在。
    # 這是最基礎的檢查，一次性從數據庫撈出所有匹配的 URL 字符串。
    # 使用 .values_list('url', flat=True) 是最高效的方式，我們暫時不需要完整的對象。
    found_urls_qs = URLResult.objects.filter(url__in=requested_urls_set)
    found_urls_list = await sync_to_async(list)(
        found_urls_qs.values_list("url", flat=True)
    )
    found_urls_set = set(found_urls_list)

    if found_urls_set != requested_urls_set:
        missing_urls = requested_urls_set - found_urls_set
        logger.warning(
            f"請求分析的 URL 中，有 {len(missing_urls)} 個不存在: {missing_urls}"
        )
        raise HttpError(404, f"操，這些 URL 不在資料庫裡: {list(missing_urls)}")

    logger.info("第一道防線通過：所有請求的 URL 記錄均存在。")

    # 防線二：確認所有 URL 的父掃描任務 (URLScan) 狀態均為 'COMPLETED'。
    # 我們反向查找那些「不合格」的 URL。
    unready_urls_qs = URLResult.objects.filter(url__in=requested_urls_set).exclude(
        discovered_by_scans__status="COMPLETED"
    )

    unready_urls_list = await sync_to_async(list)(
        unready_urls_qs.values_list("url", flat=True)
    )

    if unready_urls_list:
        logger.warning(
            f"請求分析的 URL 中，有 {len(unready_urls_list)} 個的掃描任務未完成: {unready_urls_list}"
        )
        # 400 Bad Request: 請求本身在語法上沒錯，但在語義上是無效的。
        raise HttpError(
            400,
            f"操，這些 URL 的掃描任務還未完成或已失敗，無法分析: {unready_urls_list}",
        )

    logger.info("第二道防線通過：所有 URL 的掃描任務均已完成。")

    # --- 驗證通過，準備派發任務 ---

    # 此時 found_urls_qs 包含了所有我們要的 URLResult 對象
    final_url_objects = await sync_to_async(list)(found_urls_qs)

    try:
        trigger_ai_analysis_for_urls.delay([url.id for url in final_url_objects])
        logger.info(f"準備為 {len(final_url_objects)} 個 URL 派發 AI 分析任務。")
    except Exception as e:
        logger.exception(f"派發 AI 分析任務失敗：{e}")
        raise HttpError(status_code=500, message="內部錯誤：無法派發 AI 分析任務")

    return 202, SuccessSendToAISchema(
        detail=f"AI 分析任務已成功派發給 {len(final_url_objects)} 個 URL。"
    )
