import logging
import httpx  # 改用 httpx，這才是 async 該用的
import os
from urllib.parse import urlparse


from asgiref.sync import sync_to_async
from ninja import Router
from pydantic import Extra


from apps.core.models import Seed, Subdomain, ExtractedJS, JavaScriptFile
from .schemas import (
    ErrorSchema,
    JSAnalyzeRequest,
)
from apps.core.schemas import FlaresolverrTriggerSchema, FlaresolverrResponse
from .tasks import perform_scan_for_url, perform_js_scan, download_external_js
from .request_schemas import (
    FlareSolverrSendRequestSchema,
    FlareSolverrSendRequestResponse,
)
from .tasks import perform_flaresolverr_request
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
    target_id = trigger_data.target_id
    auto_create = trigger_data.auto_create

    # 1. 驗證 Seed (如果沒傳 target_id)
    if not target_id and seed_id:
        target_id = (
            await Seed.objects.filter(id=seed_id)
            .values_list("target_id", flat=True)
            .afirst()
        )
        logger.info(f"從 Seed ID 獲取目標 ID: {target_id}")

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
    task = perform_scan_for_url.delay(
        url=url,
        method=trigger_data.method,
        seed_id=seed_id,
        auto_create=auto_create,
        target_id=target_id,
        execution_graph_id=trigger_data.execution_graph_id,
        execution_node_id=trigger_data.execution_node_id,
        body=trigger_data.body,
        content_type=trigger_data.content_type,
        host_header=trigger_data.host_header,
    )
    if trigger_data.execution_node_id:
        from apps.core.services import ExecutionService

        await sync_to_async(ExecutionService.set_node_external_task_id)(trigger_data.execution_node_id, task.id)

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
    url = os.getenv("FLARESOLVERR_URL") or "http://localhost:8191"

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


@log_function_call()
@router.post(
    "/send_request",
    response={202: FlareSolverrSendRequestResponse, 404: FlareSolverrSendRequestResponse},
)
async def send_request(request, payload: FlareSolverrSendRequestSchema):
    """Send an arbitrary HTTP request via FlareSolverr with session reuse.

    This endpoint is designed for the AI workflow; it persists request/response
    traces under the ExecutionNode.
    """

    # Keep the same asset ownership gate as the crawler: require target mapping.
    url = payload.url
    hostname = urlparse(url).hostname
    target_id = payload.target_id
    seed_id = payload.seed_id

    if not target_id and seed_id:
        target_id = (
            await Seed.objects.filter(id=seed_id)
            .values_list("target_id", flat=True)
            .afirst()
        )

    if not target_id and hostname:
        target_id = (
            await Subdomain.objects.filter(name=hostname)
            .values_list("target_id", flat=True)
            .afirst()
        )

    if not target_id:
        return 404, FlareSolverrSendRequestResponse(
            detail=f"目標 {hostname} 無法關聯到任何有效的 Target。",
            status_code=404,
            if_run=False,
        )

    task = perform_flaresolverr_request.delay(
        url=payload.url,
        method=payload.method,
        headers=payload.headers or {},
        cookies=payload.cookies or "",
        body=payload.body,
        content_type=payload.content_type,
        host_header=payload.host_header,
        session_key=payload.session_key,
        refresh_session=payload.refresh_session,
        execution_graph_id=payload.execution_graph_id,
        execution_node_id=payload.execution_node_id,
    )
    if payload.execution_node_id:
        from apps.core.services import ExecutionService

        await sync_to_async(ExecutionService.set_node_external_task_id)(payload.execution_node_id, task.id)

    return 202, FlareSolverrSendRequestResponse(
        detail="FlareSolverr request 任務已提交。",
        status_code=202,
        if_run=True,
    )
