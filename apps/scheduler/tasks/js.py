import asyncio
import logging

import httpx
from asgiref.sync import sync_to_async
from celery import shared_task

from apps.core.models import JavaScriptFile, ExtractedJS
from c2_core.settings import API_BASE_URL

logger = logging.getLogger(__name__)

JS_AI_SCAN_URL = f"{API_BASE_URL}/api/flaresolverr/json_analyze"


async def _post_all(url: str, payloads: list, timeout: int = 5) -> None:
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = [client.post(url, json=p) for p in payloads]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error(f"連線 API 失敗 (index {i}): {r}")
        elif isinstance(r, httpx.Response) and r.status_code != 200:
            logger.warning(f"API 拒絕請求 (index {i}): {r.text}")


@shared_task(name="scheduler.tasks.trigger_scan_js")
async def trigger_scan_js(batch_size: int = 10):
    """
    定時任務：找出還沒分析過的 JS，透過 API 丟給 AI 掃描
    """
    logger.info("定時任務啟動：自動搜刮未分析 JS")

    def _fetch():
        external_ids = list(
            JavaScriptFile.objects.filter(is_analyzed=False).values_list("id", flat=True)[:batch_size]
        )
        inline_ids = list(
            ExtractedJS.objects.filter(is_analyzed=False).values_list("id", flat=True)[:batch_size]
        )
        return (
            [{"id": tid, "type": "external"} for tid in external_ids]
            + [{"id": tid, "type": "inline"} for tid in inline_ids]
        )

    payloads = await sync_to_async(_fetch)()

    if payloads:
        await _post_all(JS_AI_SCAN_URL, payloads)

    logger.info("定時任務完成：所有待掃描任務已提交")
