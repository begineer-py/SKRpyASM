import logging
from os import name
from shutil import which
from django.contrib.messages import success
from ninja import Router
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import (
    get_object_or_404,
)
from c2_core.config.logging import log_function_call
from apps.core.schemas import ErrorSchema
from apps.core.models import Target
from .tasks import scan_all_url
from .schemas import (
    ScanAllUrlSchema,
    SuccessScanAllUrlSchema,
)
from apps.core.schemas import ErrorSchema
from apps.core.models import Subdomain, Seed
import logging
from c2_core.config.logging import (
    log_function_call,
)

from ninja.errors import HttpError

router = Router()  # 路由实例
logger = logging.getLogger(__name__)  # 日志记录器


@log_function_call
@router.post(
    "/get_all_url",
    response={
        200: SuccessScanAllUrlSchema,
        400: ErrorSchema,
        404: ErrorSchema,
        500: ErrorSchema,
    },
    tags=["get_all_url"],
    summary="根據 subdomain 獲取所有 url",
)
async def get_all_url(
    request,
    payloads: ScanAllUrlSchema,
):
    "獲取一個子域名下所有的url"
    subdomain = await Subdomain.objects.aget(name=payloads.name)

    if subdomain.is_active == False:
        logger.warning(f"子域名: {payloads.name} is not active")
        raise HttpError(
            400,
            f"Subdomain '{payloads.name}' is not active.",
        )
    elif subdomain.is_resolvable == False:
        logger.warning(f"子域名: {payloads.name} is not resolvable")
        raise HttpError(
            400,
            f"Subdomain '{payloads.name}' is not resolvable.",
        )

    try:
        # 使用 .delay() 或 .apply_async() 觸發
        task = scan_all_url.delay(subdomain.id)
        logger.info(f"GAU 任務已派發: Task ID {task.id} -> Subdomain {subdomain.id}")
    except Exception as e:
        logger.error(f"Celery 任務派發失敗: {e}")
        raise HttpError(500, "Failed to schedule scanning task.")

    # 4. 返回結果
    # 這裡的結構必須符合 async_success_get_all_url Schema
    return SuccessScanAllUrlSchema(
        name=subdomain.name,
        if_run=True,
    )
