import logging
import httpx  # 改用 httpx，這才是 async 該用的
import os
from urllib.parse import urlparse


from ninja import Router
from pydantic import Extra


from apps.core.models import Seed, Subdomain, ExtractedJS, JavaScriptFile
from .schemas import (
    ErrorSchema,
    JSAnalyzeRequest,
)
from apps.core.schemas import FlaresolverrTriggerSchema, FlaresolverrResponse
from .tasks import perform_scan_for_url, perform_js_scan, download_external_js
from c2_core.config.logging import log_function_call

router = Router()
logger = logging.getLogger(__name__)

# --- API 實作 ---


@log_function_call()
@router.post(
    "/start_scanner",
    response={200: FlaresolverrResponse, 404: FlaresolverrResponse, 500: ErrorSchema},
)
async def start_crawl(request, trigger_data: FlaresolverrTriggerSchema):
    url = trigger_data.url
    seed_id = trigger_data.seed_id
    hostname = urlparse(url).hostname
    auto_create = trigger_data.auto_create

    target_id = None

    # 1. 驗證 Seed
    if seed_id:
        target_id = (
            await Seed.objects.filter(id=seed_id)
            .values_list("target_id", flat=True)
            .afirst()
        )
        logger.info(f"目標 ID: {target_id}")

    # 2. 驗證 Subdomain
    if not target_id and hostname:
        target_id = (
            await Subdomain.objects.filter(name=hostname)
            .values_list("target_id", flat=True)
            .afirst()
        )

    # 3. Get Out 邏輯
    if not target_id:
        msg = f"目標 {hostname} 無法關聯到任何有效的 Target。若為新資產請提供包含 Target 的 Seed ID。"
        logger.warning(f"[API] 拒絕掃描: {msg}")
        return 404, FlaresolverrResponse(
            detail=msg,
            status_code=404,
            if_run=False,
        )
    # 4. 觸發 Celery
    perform_scan_for_url.delay(
        url=url,
        method=trigger_data.method,
        seed_id=seed_id,
        auto_create=auto_create,
        target_id=target_id,
    )

    return 200, FlaresolverrResponse(
        detail="FlareSolverr 掃描任務已成功觸發。",
        status_code=200,
        if_run=True,
    )


@log_function_call()
@router.post(
    "/check_flaresolverr",
    response={200: bool, 500: ErrorSchema},
)
async def check_flaresolverr(request):
    logger.info("檢查 FlareSolverr 狀態...")
    url = os.getenv("FLARESOLVERR_URL") or "http://localhost:8191/v1"

    try:
        # 使用 httpx 進行非阻塞請求
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)

        if response.status_code == 200:
            logger.info("FlareSolverr 正常啟動")
            return True
        return False
    except Exception as e:
        logger.error(f"檢查 FlareSolverr 失敗: {e}")
        # 如果是檢查 API，建議直接回傳 False 而不是噴 500，除非是系統真的炸了
        return False


@router.post("/json_analyze", response={200: FlaresolverrResponse})
async def json_analyze(request, data: JSAnalyzeRequest):
    map = {
        "inline": ExtractedJS,
        "external": JavaScriptFile,
    }
    model = map.get(data.type)
    if not model:
        return FlaresolverrResponse(
            detail="不支援的類型", status_code=400, if_run=False
        )
    available = await model.objects.filter(id=data.id).aexists()
    if not available:
        return FlaresolverrResponse(
            detail="找不到指定的 JavaScript", status_code=404, if_run=False
        )
    perform_js_scan.delay(data.id, data.type)
    return FlaresolverrResponse(
        detail="AI 掃描任務已提交", status_code=200, if_run=True
    )
