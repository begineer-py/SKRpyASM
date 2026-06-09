from typing import Any, Optional


def log_http_exchange(
    *,
    step_id: Optional[int],
    execution_graph_id: Optional[int] = None,
    execution_node_id: Optional[int] = None,
    tool: str,
    request: dict[str, Any],
    response: dict[str, Any],
    level: str = "INFO",
) -> None:
    """Persist HTTP request/response as execution graph telemetry.

    step_id is accepted for transitional callers but no longer writes StepLog.
    """

    if not execution_graph_id:
        return

    from apps.core.models import ExecutionGraph, ExecutionNode
    from apps.core.services import ExecutionService

    graph = ExecutionGraph.objects.filter(id=execution_graph_id).first()
    if not graph:
        return
    node = ExecutionNode.objects.filter(id=execution_node_id, graph=graph).first() if execution_node_id else None

    payload = {
        "tool": tool,
        "request": request,
        "response": {
            "status_code": response.get("status_code"),
            "response_url": response.get("response_url"),
            "headers": response.get("response_headers"),
            # Do not dump megabytes into DB logs.
            "body_preview": (response.get("response_text") or "")[:2000],
        },
    }

    status_code = response.get("status_code") or 0
    status = "SUCCEEDED" if status_code < 400 else "FAILED"
    content = f"{tool} {request.get('method')} {request.get('url')} -> {status_code}"

    ExecutionService.emit_event(
        graph=graph,
        node=node,
        event_type="http_exchange",
        status=status,
        content=content,
        payload={
            "tool": tool,
            "level": level,
            "status_code": status_code,
            "response_url": response.get("response_url"),
            "step_id": step_id,
        },
    )

    ExecutionService.attach_artifact(
        graph=graph,
        node=node,
        artifact_type="http_exchange",
        name=f"{tool}:{request.get('method')}:{request.get('url')}",
        content=content,
        data=payload,
        metadata={"status": status, "status_code": status_code},
    )
