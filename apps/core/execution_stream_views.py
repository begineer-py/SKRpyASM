"""SSE endpoint for durable execution graph events."""

import asyncio
import json
import logging
import time
from typing import AsyncGenerator

from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt

from apps.core.models import ExecutionEvent, ExecutionGraph


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


def _event_payload(event: ExecutionEvent) -> dict:
    return {
        "id": event.id,
        "graph_id": event.graph_id,
        "node_id": event.node_id,
        "sequence": event.sequence,
        "event_type": event.event_type,
        "status": event.status,
        "content": event.content,
        "payload": event.payload,
        "created_at": event.created_at.isoformat(),
    }


async def _stream_execution_events_generator(graph_id: int, last_sequence: int = 0) -> AsyncGenerator[str, None]:
    start_time = time.monotonic()
    current_sequence = last_sequence
    checkpoint_interval = 2
    last_checkpoint = time.monotonic()
    idle_timeout = 300
    last_event_time = time.monotonic()

    try:
        try:
            await ExecutionGraph.objects.aget(id=graph_id)
        except ExecutionGraph.DoesNotExist:
            yield _sse_event({"error": f"ExecutionGraph {graph_id} not found", "type": "NotFound"}, event="error")
            yield _sse_event("[DONE]", event="done")
            return

        yield _sse_event({"status": "started", "graph_id": graph_id}, event="start")

        while True:
            if time.monotonic() - last_event_time > idle_timeout:
                logger.debug("[ExecutionEvent SSE] idle timeout for graph_id=%s", graph_id)
                break

            new_events = ExecutionEvent.objects.filter(
                graph_id=graph_id,
                sequence__gt=current_sequence,
            ).order_by("sequence")

            async for event in new_events:
                payload = _event_payload(event)
                yield _sse_event(payload, event=event.event_type, event_id=event.sequence)
                current_sequence = event.sequence
                last_event_time = time.monotonic()

            now = time.monotonic()
            if now - last_checkpoint > checkpoint_interval:
                yield _sse_event(
                    {
                        "type": "checkpoint",
                        "sequence": current_sequence,
                        "elapsed_ms": int((now - start_time) * 1000),
                    },
                    event="checkpoint",
                )
                last_checkpoint = now

            await asyncio.sleep(0.5)

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        yield _sse_event({"elapsed_ms": elapsed_ms, "final_sequence": current_sequence}, event="stats")
        yield _sse_event("[DONE]", event="done")
    except Exception as exc:
        logger.error(
            "[ExecutionEvent SSE] exception for graph_id=%s: %s: %s",
            graph_id,
            type(exc).__name__,
            exc,
            exc_info=True,
        )
        yield _sse_event(
            {"error": str(exc), "type": type(exc).__name__, "elapsed_ms": int((time.monotonic() - start_time) * 1000)},
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
async def stream_execution_events(request, graph_id: int):
    last_sequence = request.GET.get("last_sequence") or request.headers.get("Last-Event-ID") or "0"
    try:
        last_sequence = int(last_sequence)
        if last_sequence < 0:
            last_sequence = 0
    except (ValueError, TypeError):
        async def error_gen():
            yield _sse_event({"error": "last_sequence must be a non-negative integer"}, event="error")
            yield _sse_event("[DONE]", event="done")

        return _make_sse_response(error_gen())

    return _make_sse_response(_stream_execution_events_generator(graph_id, last_sequence))
