import ninja
from ninja import Router
from ninja.errors import HttpError
from typing import List, Optional
from datetime import datetime
import requests
import os
from django.core.exceptions import ObjectDoesNotExist
from c2_core.config.logging import log_function_call
import logging

router = Router()
logger = logging.getLogger(__name__)


from .models.pentest_config import PentestHeaderConfig
from .models.target_request_config import TargetRequestConfig
from .models.base import Target
from .models import ExecutionArtifact, ExecutionEvent, ExecutionGraph, ExecutionNode
from .schemas import (
    ExecutionArtifactSchema,
    ExecutionEventSchema,
    ExecutionGraphDetailSchema,
    ExecutionGraphSchema,
    ExecutionNodeSchema,
    PentestHeaderConfigOut,
    PentestHeaderConfigUpdate,
    TargetRequestConfigOut,
    TargetRequestConfigUpdate,
    ResolvedRequestConfigOut,
)
from .header_injection import resolve_request_config


@router.get("/pentest-config", response=PentestHeaderConfigOut, tags=["Core - Pentest Config"])
def get_pentest_config(request):
    return PentestHeaderConfig.get_config()


@router.put("/pentest-config", response=PentestHeaderConfigOut, tags=["Core - Pentest Config"])
def update_pentest_config(request, data: PentestHeaderConfigUpdate):
    config = PentestHeaderConfig.get_config()
    updated = data.model_dump(exclude_unset=True)
    for attr, value in updated.items():
        setattr(config, attr, value)
    config.save()
    from django.core.cache import cache
    cache.delete("pentest_header_config")
    return PentestHeaderConfig.get_config()


@router.get("/target-request-config/{target_id}", response=TargetRequestConfigOut, tags=["Core - Target Request Config"])
def get_target_request_config(request, target_id: int):
    try:
        config = TargetRequestConfig.objects.get(target_id=target_id)
    except TargetRequestConfig.DoesNotExist:
        return TargetRequestConfigOut(
            target_id=target_id,
            header_enabled=None,
            header_username=None,
            header_prefix=None,
            custom_headers={},
            rps=None,
            max_concurrency=None,
            timeout=None,
            updated_at=datetime.now(),
        )
    return config


@router.put("/target-request-config/{target_id}", response=TargetRequestConfigOut, tags=["Core - Target Request Config"])
def update_target_request_config(request, target_id: int, data: TargetRequestConfigUpdate):
    try:
        Target.objects.get(pk=target_id)
    except Target.DoesNotExist:
        raise HttpError(404, f"Target {target_id} 不存在")

    config, _ = TargetRequestConfig.objects.get_or_create(target_id=target_id)
    updated = data.model_dump(exclude_unset=True)
    for attr, value in updated.items():
        setattr(config, attr, value)
    config.save()
    return config


@router.delete("/target-request-config/{target_id}", tags=["Core - Target Request Config"])
def delete_target_request_config(request, target_id: int):
    deleted, _ = TargetRequestConfig.objects.filter(target_id=target_id).delete()
    if deleted == 0:
        raise HttpError(404, f"Target {target_id} 沒有自訂請求設定")
    return {"detail": f"已刪除 Target {target_id} 的自訂請求設定，將回退到全域設定"}


@router.get("/executions", response=List[ExecutionGraphSchema], tags=["Core - Executions"])
def list_execution_graphs(
    request,
    thread_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
):
    limit = max(1, min(limit, 200))
    queryset = ExecutionGraph.objects.all().order_by("-started_at")
    if thread_id is not None:
        queryset = queryset.filter(thread_id=thread_id)
    if status:
        queryset = queryset.filter(status=status)
    return list(queryset[:limit])


@router.get("/executions/{graph_id}", response=ExecutionGraphDetailSchema, tags=["Core - Executions"])
def get_execution_graph(request, graph_id: int):
    try:
        graph = ExecutionGraph.objects.prefetch_related("nodes", "events", "artifacts").get(id=graph_id)
    except ExecutionGraph.DoesNotExist:
        raise HttpError(404, f"ExecutionGraph {graph_id} 不存在")
    return {
        "id": graph.id,
        "thread_id": graph.thread_id,
        "assistant_id": graph.assistant_id,
        "run_id": graph.run_id,
        "title": graph.title,
        "status": graph.status,
        "metadata": graph.metadata,
        "started_at": graph.started_at,
        "updated_at": graph.updated_at,
        "completed_at": graph.completed_at,
        "nodes": list(graph.nodes.all()),
        "events": list(graph.events.all()),
        "artifacts": list(graph.artifacts.all()),
    }


@router.get("/executions/{graph_id}/nodes", response=List[ExecutionNodeSchema], tags=["Core - Executions"])
def list_execution_nodes(request, graph_id: int):
    if not ExecutionGraph.objects.filter(id=graph_id).exists():
        raise HttpError(404, f"ExecutionGraph {graph_id} 不存在")
    return list(ExecutionNode.objects.filter(graph_id=graph_id).order_by("sequence", "id"))


@router.get("/executions/{graph_id}/events", response=List[ExecutionEventSchema], tags=["Core - Executions"])
def list_execution_events(request, graph_id: int, after: int = 0, limit: int = 200):
    if not ExecutionGraph.objects.filter(id=graph_id).exists():
        raise HttpError(404, f"ExecutionGraph {graph_id} 不存在")
    limit = max(1, min(limit, 500))
    return list(
        ExecutionEvent.objects.filter(graph_id=graph_id, sequence__gt=max(after, 0))
        .order_by("sequence", "id")[:limit]
    )


@router.get("/executions/{graph_id}/artifacts", response=List[ExecutionArtifactSchema], tags=["Core - Executions"])
def list_execution_artifacts(request, graph_id: int, node_id: Optional[int] = None):
    if not ExecutionGraph.objects.filter(id=graph_id).exists():
        raise HttpError(404, f"ExecutionGraph {graph_id} 不存在")
    queryset = ExecutionArtifact.objects.filter(graph_id=graph_id).order_by("created_at", "id")
    if node_id is not None:
        queryset = queryset.filter(node_id=node_id)
    return list(queryset)


@router.get("/target-request-config/{target_id}/resolved", response=ResolvedRequestConfigOut, tags=["Core - Target Request Config"])
def get_resolved_request_config(request, target_id: int):
    try:
        Target.objects.get(pk=target_id)
    except Target.DoesNotExist:
        raise HttpError(404, f"Target {target_id} 不存在")
    return resolve_request_config(target_id)
