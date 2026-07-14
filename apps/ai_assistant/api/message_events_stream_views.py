"""持久化 SSE endpoint：廣播指定 thread 的 Message 表變更。

用途：解決「前端刷新時 AI 回應尚未寫入 DB → 永遠看不到」的問題。
前端在 mount 時訂閱此 endpoint，後端輪詢 Message 表，偵測到新訊息或
既有訊息更新時 push SSE event，觸發前端重新載入。

與 thread_events_stream_views.py 的差異：
  - thread_events 只廣播 ThreadEvent（工具執行時間軸）
  - 本 endpoint 廣播 Message（聊天訊息）的新增
"""

import asyncio
import json
import logging
import time
from typing import AsyncGenerator

from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt

from apps.core.models import Thread, Message


logger = logging.getLogger(__name__)


def _sse_event(data: str | dict, event: str | None = None, event_id: int | None = None) -> str:
    if isinstance(data, dict):
        data = json.dumps(data)
    elif not isinstance(data, str):
        try:
            data = json.dumps(data)
        except (TypeError, ValueError):
            data = str(data)

    lines = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    if event:
        lines.append(f"event: {event}")
    for line in data.split("\n"):
        lines.append(f"data: {line}")
    lines.append("")
    lines.append("")
    return "\n".join(lines)


def _message_summary(msg: Message) -> dict:
    """產生輕量摘要給前端，避免傳整個 message JSONField。"""
    return {
        "id": msg.id,
        "thread_id": msg.thread_id,
        "role": msg.role,
        "created_at": msg.created_at.isoformat(),
    }


async def _stream_message_events_generator(thread_id: int, last_message_id: int = 0) -> AsyncGenerator[str, None]:
    t_start = time.monotonic()
    current_max_id = last_message_id
    checkpoint_interval = 5
    last_checkpoint = time.monotonic()
    idle_timeout = 600  # 10 分鐘無新訊息即關閉，前端會自動重連
    last_event_time = time.monotonic()

    try:
        try:
            await Thread.objects.aget(id=thread_id)
        except Thread.DoesNotExist:
            yield _sse_event({"error": f"Thread {thread_id} not found", "type": "NotFound"}, event="error")
            yield _sse_event("[DONE]", event="done")
            return

        yield _sse_event(
            {"status": "started", "thread_id": thread_id, "last_message_id": current_max_id},
            event="start",
        )

        while True:
            if time.monotonic() - last_event_time > idle_timeout:
                logger.debug("[MessageEvent SSE] idle timeout for thread_id=%s", thread_id)
                break

            # 輪詢：找出 id > current_max_id 的新訊息
            new_messages = (
                Message.objects.filter(thread_id=thread_id, id__gt=current_max_id)
                .order_by("id")
            )

            async for msg in new_messages:
                payload = _message_summary(msg)
                yield _sse_event(payload, event="message_created", event_id=msg.id)
                current_max_id = msg.id
                last_event_time = time.monotonic()

            now = time.monotonic()
            if now - last_checkpoint > checkpoint_interval:
                yield _sse_event(
                    {
                        "type": "checkpoint",
                        "last_message_id": current_max_id,
                        "elapsed_ms": int((now - t_start) * 1000),
                    },
                    event="checkpoint",
                )
                last_checkpoint = now

            await asyncio.sleep(0.8)

        elapsed_ms = int((time.monotonic() - t_start) * 1000)
        yield _sse_event(
            {"elapsed_ms": elapsed_ms, "final_message_id": current_max_id},
            event="stats",
        )
        yield _sse_event("[DONE]", event="done")
    except Exception as exc:
        logger.error(
            "[MessageEvent SSE] exception for thread_id=%s: %s: %s",
            thread_id,
            type(exc).__name__,
            exc,
            exc_info=True,
        )
        yield _sse_event(
            {"error": str(exc), "type": type(exc).__name__, "elapsed_ms": int((time.monotonic() - t_start) * 1000)},
            event="error",
        )
        yield _sse_event("[DONE]", event="done")


def _make_sse_response(generator: AsyncGenerator) -> StreamingHttpResponse:
    response = StreamingHttpResponse(generator, content_type="text/event-stream", charset="utf-8")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    response["Access-Control-Allow-Origin"] = "*"
    response["Connection"] = "keep-alive"
    return response


@csrf_exempt
async def stream_thread_message_events(request, thread_id: int):
    """ASGI SSE endpoint: GET /api/assistant/threads/<thread_id>/messages/events/stream/

    Query params:
      - last_message_id: int (斷線續傳游標，預設 0)
    """
    last_message_id = request.GET.get("last_message_id") or request.headers.get("Last-Event-ID") or "0"
    try:
        last_message_id = int(last_message_id)
        if last_message_id < 0:
            last_message_id = 0
    except (ValueError, TypeError):
        async def error_gen():
            yield _sse_event({"error": "last_message_id must be a non-negative integer"}, event="error")
            yield _sse_event("[DONE]", event="done")

        return _make_sse_response(error_gen())

    return _make_sse_response(_stream_message_events_generator(thread_id, last_message_id))
