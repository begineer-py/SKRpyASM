import logging
from urllib.parse import urlparse

from asgiref.sync import sync_to_async
from ninja import Router
from ninja.errors import HttpError

from apps.core.models import Subdomain
from apps.core.schemas import ErrorSchema
from c2_core.config.logging import log_function_call

from .schemas import KatanaScanSchema, KatanaScanSuccessSchema
from .tasks import scan_katana

router = Router()
logger = logging.getLogger(__name__)


@log_function_call
@router.post(
    "/katana",
    response={
        200: KatanaScanSuccessSchema,
        400: ErrorSchema,
        404: ErrorSchema,
        500: ErrorSchema,
    },
    tags=["Katana"],
    summary="使用 Katana 主動爬取子域名的所有存活 URL",
)
async def run_katana_scan(request, payload: KatanaScanSchema):
    """觸發 Katana 主動爬蟲，發現子域名下當前存活的 URL（補充 GAU 被動歷史資料）。"""
    clean_name = payload.name
    if clean_name.startswith("http"):
        clean_name = urlparse(clean_name).hostname or clean_name

    subdomain = None

    if payload.subdomain_id:
        subdomain = await Subdomain.objects.filter(id=payload.subdomain_id).afirst()

    if not subdomain:
        subdomains = Subdomain.objects.filter(name=clean_name)
        subdomain = await subdomains.afirst()

    if not subdomain:
        raise HttpError(404, f"Subdomain '{clean_name}' does not exist.")

    if subdomain.is_active is False:
        raise HttpError(400, f"Subdomain '{subdomain.name}' is not active.")
    if subdomain.is_resolvable is False:
        raise HttpError(400, f"Subdomain '{subdomain.name}' is not resolvable.")

    try:
        task = scan_katana.delay(
            subdomain.id,
            depth=payload.depth,
            js_crawl=payload.js_crawl,
            execution_graph_id=payload.execution_graph_id,
            execution_node_id=payload.execution_node_id,
        )
        if payload.execution_node_id:
            from apps.core.services import ExecutionService

            await sync_to_async(ExecutionService.set_node_external_task_id)(payload.execution_node_id, task.id)
        logger.info(
            f"Katana 任務已派發: Task ID {task.id} -> Subdomain {subdomain.id} "
            f"(depth={payload.depth}, ExecutionNode: {payload.execution_node_id})"
        )
    except Exception as e:
        logger.error(f"Celery 任務派發失敗: {e}")
        raise HttpError(500, "Failed to schedule Katana scanning task.")

    return KatanaScanSuccessSchema(name=subdomain.name, if_run=True)
