# flaresolverr/api.py
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
from .schemas import (
    FlaresolverrTriggerSchema,
    check_flaresolverr,
    ErrorSchema,
    PayloadSchema,
)
from typing import List, Union, Optional, Annotated

from .tasks import (
    perform_scan_for_url,
)  # 把你的 task import 進來 # 從當前包導入 Celery 異步任務

router = Router()  # 創建一個 Ninja Router 實例
logger = logging.getLogger(__name__)  # 獲取當前模塊的日誌記錄器

# 將同步的 get_object_or_404 包裝成可 await 的版本，方便在 async 視圖中使用
get_object_or_404 = sync_to_async(django_get_object_or_404, thread_sensitive=True)


@log_function_call()  # 記錄函數調用的裝飾器
@router.post(  # 定義一個 HTTP POST 請求的路由
    "/start_scanner",  # API 路徑
    response={
        200: check_flaresolverr,
        404: ErrorSchema,
        500: ErrorSchema,
    },  # 定義不同 HTTP 狀態碼對應的響應 schema
)
async def start_crawl(
    request, trigger_data: FlaresolverrTriggerSchema
):  # 定義一個異步函數來啟動 FlareSolverr 掃描
    perform_scan_for_url.delay(  # 調用 Celery 任務的 delay 方法，將任務異步放入隊列
        url=trigger_data.url,  # 傳遞 URL 參數給任務
        method=trigger_data.method,  # 傳遞 HTTP 方法參數給任務
        seed_id=trigger_data.seed_id,
    )

    # 返回一個有意義的回應，告訴前端「老子已經把任務交辦下去了」
    return {  # 返回一個字典作為 API 響應
        "detail": "FlareSolverr 掃描任務已成功觸發，正在後台執行。",  # 響應詳情消息
        "status_code": 200,  # 響應狀態碼
        "if_run": True,  # 你 schema 裡有這個，那就給他 # 響應中包含任務是否運行的標誌
    }


@log_function_call()  # 記錄函數調用的裝飾器
@router.post(  # 定義一個 HTTP POST 請求的路由
    "/check_flaresolverr",  # API 路徑
    response={
        200: check_flaresolverr,
        404: ErrorSchema,
        500: ErrorSchema,
    },  # 定義不同 HTTP 狀態碼對應的響應 schema
)
async def check_flaresolverr(  # 定義一個異步函數來檢查 FlareSolverr 服務狀態
    request,  # 請求對象
):
    logger.info(f"準備檢查 FlareSolverr是否啓動")  # 記錄信息日誌
    try:  # 嘗試執行以下代碼塊
        response = await requests.get(  # 異步發送 HTTP GET 請求到 FlareSolverr 服務
            os.getenv("FLARESOLVERR_URL")
            or "http://localhost:8191/v1"  # 從環境變量獲取 FlareSolverr URL，如果不存在則使用默認值
        )
        if response.status_code == 200:  # 如果響應狀態碼為 200
            logger.info(
                "FlareSolverr 啟動成功"
            )  # 記錄信息日誌表示 FlareSolverr 啟動成功
            return True  # 返回 True
        else:  # 如果響應狀態碼不是 200
            logger.warning(
                "FlareSolverr 啟動失敗"
            )  # 記錄警告日誌表示 FlareSolverr 啟動失敗
            return False  # 返回 False
    except Exception as e:  # 捕獲其他所有異常
        logger.exception(
            f"檢查 FlareSolverr 時發生錯誤: {e}"
        )  # 記錄異常日誌，包含詳細錯誤信息
        raise HttpError(
            status_code=500, message="內部錯誤：無法檢查 FlareSolverr"
        )  # 拋出 HTTP 500 錯誤


@log_function_call
@router.post(
    "/payload_sender",
    response={
        200: check_flaresolverr,
        404: ErrorSchema,
        500: ErrorSchema,
    },
)
async def payload_sender(request, payload_data: PayloadSchema):
    logger.info(f"準備針對 {payload_data.url} 發送 {payload_data.method} 請求")
    try:
        response = await requests.request(
            method=payload_data.method,
            url=payload_data.url,
            headers=payload_data.headers,
            cookies=payload_data.cookies,
            data=payload_data.payload,
        )
        return response.json()
    except Exception as e:
        logger.exception(f"發送請求時發生錯誤: {e}")
        raise HttpError(status_code=500, message="內部錯誤：無法發送請求")
