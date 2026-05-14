"""
django_ai_assistant/api/logs_stream_views.py

Server-Sent Events (SSE) streaming endpoint for Step execution logs.

Provides real-time streaming of StepLog entries as they are created during
AI agent execution. This enables frontend components to display live updates
of tool execution, action results, and agent decisions without polling.

Endpoint: GET /api/v1/steps/{step_id}/logs/stream/
Query params:
  - last_sequence: int (optional) — Only stream logs after this sequence number
  
Response format:
  - event: "log" — A new StepLog entry (JSON)
  - event: "checkpoint" — Periodic heartbeat with latest sequence number
  - event: "done" — Streaming has completed
  - event: "error" — An error occurred during streaming
"""

import asyncio
import json
import logging
from typing import AsyncGenerator

from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt


logger = logging.getLogger(__name__)


def _sse_event(data: str, event: str | None = None) -> str:
    """
    Format a single SSE event string.
    
    Args:
        data: The event data (will be JSON stringified if dict)
        event: Optional event type name
        
    Returns:
        Properly formatted SSE event string
    """
    if isinstance(data, dict):
        data = json.dumps(data)
    
    lines = []
    if event:
        lines.append(f"event: {event}")
    
    # Escape newlines within data so each logical event is on its own line
    for line in data.split("\n"):
        lines.append(f"data: {line}")
    
    lines.append("")  # blank line = end of event
    lines.append("")
    return "\n".join(lines)


async def _stream_logs_generator(step_id: int, last_sequence: int = 0) -> AsyncGenerator[str, None]:
    """
    Async generator that yields SSE-formatted log entries.
    
    Streams logs from the database as they are created, starting from
    the provided sequence number. Includes periodic checkpoint events
    to maintain connection and allow client-side state synchronization.
    
    Args:
        step_id: The Step ID to stream logs for
        last_sequence: Only stream logs after this sequence number
        
    Yields:
        SSE-formatted event strings
    """
    import time
    from django.apps import apps
    from django.db.models import Max
    
    t_start = time.monotonic()
    current_sequence = last_sequence
    checkpoint_interval = 2  # Send checkpoint every 2 seconds
    last_checkpoint = time.monotonic()
    
    try:
        # Import StepLog model dynamically to avoid circular imports
        StepLog = apps.get_model('core', 'StepLog')
        Step = apps.get_model('core', 'Step')
        
        # Verify step exists
        try:
            step = await Step.objects.aget(id=step_id)
        except Step.DoesNotExist:
            error_data = {"error": f"Step {step_id} not found", "type": "NotFound"}
            yield _sse_event(error_data, event="error")
            yield _sse_event("[DONE]", event="done")
            return
        
        # Signal that streaming has started
        yield _sse_event({"status": "started", "step_id": step_id}, event="start")
        
        # Keep streaming until no new logs for a while (step completed or timeout)
        idle_timeout = 60  # Stop after 60 seconds of no new logs
        last_log_time = time.monotonic()
        
        while True:
            # Check if we've been idle for too long
            if time.monotonic() - last_log_time > idle_timeout:
                logger.debug(f"[SSE logs stream] Timeout after {idle_timeout}s idle for step_id={step_id}")
                break
            
            # Query new logs since last_sequence
            new_logs = StepLog.objects.filter(
                step_id=step_id,
                sequence__gt=current_sequence
            ).order_by('sequence')
            
            async for log in new_logs:
                # Serialize the log entry
                log_data = {
                    "id": log.id,
                    "step_id": log.step_id,
                    "sequence": log.sequence,
                    "level": log.level,
                    "tag": log.tag,
                    "message": log.message,
                    "action_status": log.action_status,
                    "execution_time_ms": log.execution_time_ms,
                    "created_at": log.created_at.isoformat(),
                }
                
                # Stream the log entry
                yield _sse_event(log_data, event="log")
                current_sequence = log.sequence
                last_log_time = time.monotonic()
            
            # Send periodic checkpoint to maintain connection
            now = time.monotonic()
            if now - last_checkpoint > checkpoint_interval:
                checkpoint_data = {
                    "type": "checkpoint",
                    "sequence": current_sequence,
                    "elapsed_ms": int((now - t_start) * 1000),
                }
                yield _sse_event(checkpoint_data, event="checkpoint")
                last_checkpoint = now
            
            # Brief sleep to avoid tight loop and database hammering
            await asyncio.sleep(0.5)
        
        # Stream final stats
        elapsed_ms = int((time.monotonic() - t_start) * 1000)
        yield _sse_event(
            {"elapsed_ms": elapsed_ms, "final_sequence": current_sequence},
            event="stats"
        )
        
        # Signal completion
        yield _sse_event("[DONE]", event="done")
        logger.info(f"[SSE logs stream] Completed for step_id={step_id} (elapsed={elapsed_ms}ms)")
        
    except Exception as exc:
        logger.error(
            f"[SSE logs stream] Exception for step_id={step_id}: "
            f"{type(exc).__name__}: {exc}",
            exc_info=True,
        )
        elapsed_ms = int((time.monotonic() - t_start) * 1000)
        error_data = {
            "error": str(exc),
            "type": type(exc).__name__,
            "elapsed_ms": elapsed_ms,
        }
        yield _sse_event(error_data, event="error")
        yield _sse_event("[DONE]", event="done")


def _make_sse_response(generator: AsyncGenerator) -> StreamingHttpResponse:
    """
    Create a StreamingHttpResponse with proper SSE headers.
    
    Args:
        generator: Async generator yielding SSE event strings
        
    Returns:
        Configured StreamingHttpResponse
    """
    response = StreamingHttpResponse(
        generator,
        content_type="text/event-stream",
        charset="utf-8"
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    response["Access-Control-Allow-Origin"] = "*"
    response["Connection"] = "keep-alive"
    return response


@csrf_exempt
async def stream_step_logs(request, step_id: int):
    """
    ASGI SSE endpoint: GET /api/v1/steps/{step_id}/logs/stream/
    
    Streams StepLog entries for a given step in real-time using Server-Sent Events.
    Supports resuming from a specific sequence number for reconnection scenarios.
    
    Query params:
      - last_sequence: int (optional) — Only stream logs after this sequence
      
    Returns:
        StreamingHttpResponse with SSE-formatted log entries
        
    Example:
        >>> # Frontend JavaScript
        >>> const eventSource = new EventSource('/api/v1/steps/123/logs/stream/?last_sequence=5');
        >>> eventSource.addEventListener('log', (e) => {
        ...     const log = JSON.parse(e.data);
        ...     console.log(`[${log.level}] ${log.message}`);
        ... });
    """
    # Get optional last_sequence param for resuming streams
    last_sequence = request.GET.get("last_sequence", "0")
    try:
        last_sequence = int(last_sequence)
        if last_sequence < 0:
            last_sequence = 0
    except (ValueError, TypeError):
        # Invalid sequence number
        async def error_gen():
            yield _sse_event(
                {"error": "last_sequence must be a non-negative integer"},
                event="error"
            )
            yield _sse_event("[DONE]", event="done")
        return _make_sse_response(error_gen())
    
    logger.info(f"[SSE logs stream] Started for step_id={step_id}, last_sequence={last_sequence}")
    return _make_sse_response(_stream_logs_generator(step_id, last_sequence))
