# apps/core/http_sender/api.py
import logging
from random import seed  # 導入 logging 模組，用於記錄日誌
from ninja import Router  # 從 ninja 框架導入 Router，用於定義 API 路由
from ninja.errors import HttpError  # 從 ninja 框架導入 HttpError，用於拋出 HTTP 錯誤
from typing import List, Union  # 導入 typing 模組中的 List 和 Optional，用於類型提示
import requests  # 導入 requests 模組，用於發送 HTTP 請求
import os  # 導入 os 模組，用於與操作系統交互（例如獲取環境變量）
from django.http import HttpRequest  # <--- 操，就是這一行！把它加上！
from ninja.responses import Response  # <-- 媽的，把它 import 進來！

from django.core.exceptions import (
    ObjectDoesNotExist,
)  # 從 django 導入 ObjectDoesNotExist 異常，用於處理對象未找到的情況
from apps.core.models import Seed  # 從 targets 應用導入 Target 模型
from django.shortcuts import (
    get_object_or_404 as django_get_object_or_404,
)  # 同步版 get_object_or_404
from asgiref.sync import sync_to_async  # 將同步函數轉為可 await 的異步函數
from urllib.parse import unquote  # 用於解碼 URL 參數

from c2_core.config.logging import (
    log_function_call,
)  # 從 c2_core 配置導入 log_function_call 裝飾器，用於記錄函數調用
from typing import List, Union, Optional, Annotated
from .schemas import RemainEndpoint

router = Router()  # 創建一個 Ninja Router 實例
logger = logging.getLogger(__name__)  # 獲取當前模塊的日誌記錄器
from apps.core.models import Endpoint
from apps.core.schemas import FlaresolverrTriggerSchema, FlaresolverrResponse
from .tasks import fuzz_endpoint


@log_function_call()
@router.post("/fuzz", response={202: FlaresolverrResponse, 404: FlaresolverrResponse})
async def fuzz(request, payload: RemainEndpoint):
    available = await Endpoint.objects.filter(id=payload.id).aexists()
    if not available:
        return 404, FlaresolverrResponse(
            status_code=404, detail="Endpoint not found", if_run=False
        )
    fuzz_endpoint.delay(endpoint_id=payload.id, cookies=payload.cookies)
    return 202, FlaresolverrResponse(
        status_code=202, detail="Endpoint fuzzing started", if_run=True
    )
