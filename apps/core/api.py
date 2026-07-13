from ninja import Router
from ninja.errors import HttpError
from typing import List, Optional
from datetime import datetime
import logging

router = Router()
logger = logging.getLogger(__name__)


from .models.pentest_config import PentestHeaderConfig
from .models.target_request_config import TargetRequestConfig
from .models.base import Target
from .models import (
    ContentBlob,
    ExecutionArtifact,
    ExecutionEvent,
    ExecutionGraph,
    ExecutionNode,
    Overview,
    SubAgentDispatch,
)
from .schemas import (
    AgentInteractionTreeSchema,
    AssetPentestRecordsSchema,
    ContentBlobPageSchema,
    ContentBlobSummarySchema,
    DispatchGraphSchema,
    ErrorSchema,
    ExecutionArtifactSchema,
    ExecutionEventSchema,
    ExecutionGraphDetailSchema,
    ExecutionGraphSchema,
    ExecutionGraphUpdateSchema,
    ExecutionNodeSchema,
    PentestHeaderConfigOut,
    PentestHeaderConfigUpdate,
    ResolvedRequestConfigOut,
    SubAgentDispatchSchema,
    TargetRequestConfigOut,
    TargetRequestConfigUpdate,
    TargetTopologySchema,
)
from .header_injection import resolve_request_config
from .services.topology import (
    build_dispatch_tree,
    build_target_topology,
    get_asset_pentest_records,
)


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
    target_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    include_archived: bool = False,
    search: Optional[str] = None,
):
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    queryset = ExecutionGraph.objects.all().order_by("-started_at")
    if thread_id is not None:
        queryset = queryset.filter(thread_id=thread_id)
    if target_id is not None:
        # 1:1 關係：target 只有唯一 overview，直接取得其 thread_ids
        ov = Overview.objects.filter(target_id=target_id).first()
        if ov:
            thread_ids = {ov.thread_id, ov.parent_thread_id}
            thread_ids.discard(None)
        else:
            thread_ids = set()
        queryset = queryset.filter(thread_id__in=thread_ids) if thread_ids else queryset.none()
    if status:
        queryset = queryset.filter(status=status)
    if search:
        queryset = queryset.filter(title__icontains=search)
    # archived 標記存在 metadata JSONField（不新增 DB 欄位）
    # 注意：exclude(metadata__archived=True) 在 PostgreSQL 會因 NULL 三值邏輯
    # 把「沒有 archived key」的列一併排除，故改用 contains。
    if not include_archived:
        queryset = queryset.exclude(metadata__contains={"archived": True})
    return list(queryset[offset : offset + limit])


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


@router.patch("/executions/{graph_id}", response=ExecutionGraphSchema, tags=["Core - Executions"])
def update_execution_graph(request, graph_id: int, data: ExecutionGraphUpdateSchema):
    """更新 ExecutionGraph 的 title，或以 metadata.archived 標記封存。"""
    try:
        graph = ExecutionGraph.objects.get(id=graph_id)
    except ExecutionGraph.DoesNotExist:
        raise HttpError(404, f"ExecutionGraph {graph_id} 不存在")

    updated = data.model_dump(exclude_unset=True)
    if "title" in updated and updated["title"] is not None:
        graph.title = updated["title"]
    if "archived" in updated and updated["archived"] is not None:
        meta = dict(graph.metadata or {})
        meta["archived"] = bool(updated["archived"])
        graph.metadata = meta
    graph.save()
    return graph


@router.delete("/executions/{graph_id}", response={200: dict, 404: ErrorSchema}, tags=["Core - Executions"])
def delete_execution_graph(request, graph_id: int):
    """刪除 ExecutionGraph（CASCADE 清理 nodes/events/artifacts）。"""
    deleted, _ = ExecutionGraph.objects.filter(id=graph_id).delete()
    if deleted == 0:
        raise HttpError(404, f"ExecutionGraph {graph_id} 不存在")
    return {"detail": f"ExecutionGraph {graph_id} 已刪除"}


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


def _blob_summary(blob: ContentBlob) -> dict:
    page_breakdown = blob.page_breakdown or []
    page_count = len(page_breakdown) if page_breakdown else None
    return {
        "blob_id": blob.id,
        "ai_summary": blob.ai_summary or "",
        "content_size": blob.content_size or 0,
        "page_count": page_count,
        "source_type": blob.source_type,
        "created_at": blob.created_at,
    }


@router.get(
    "/threads/{caller_thread_id}/dispatches/",
    response=List[SubAgentDispatchSchema],
    tags=["Core - SubAgent Dispatches"],
)
def list_thread_dispatches(request, caller_thread_id: int):
    """列出 caller thread 透過 SubAgentDispatch 派發的所有子代理記錄。

    每筆附帶對應 ExecutionGraph 與 ContentBlob 摘要（從 ExecutionArtifact 聚合）。
    此 API 是 query_dispatched_agents AI 工具的 REST 等價物（以 dispatcher_thread 查詢）。
    """
    dispatches = (
        SubAgentDispatch.objects.filter(dispatcher_thread_id=caller_thread_id)
        .select_related("sub_thread", "overview")
        .order_by("-dispatched_at")
    )
    result = []
    for d in dispatches:
        graph_data = None
        content_blobs: list = []
        if d.sub_thread_id:
            graph = (
                ExecutionGraph.objects.filter(thread_id=d.sub_thread_id)
                .order_by("-started_at")
                .first()
            )
            if graph:
                graph_data = {
                    "graph_id": graph.id,
                    "status": graph.status,
                    "title": graph.title or "",
                    "assistant_id": graph.assistant_id or "",
                }
                # 聚合 ContentBlob（透過 ExecutionArtifact FK 或 data.blob_id）
                artifacts = (
                    ExecutionArtifact.objects.filter(graph_id=graph.id)
                    .select_related("content_blob")
                    .order_by("created_at", "id")
                )
                seen_blob_ids = set()
                for art in artifacts:
                    blob = art.content_blob
                    if blob is None:
                        blob_id = (art.data or {}).get("blob_id")
                        if blob_id and blob_id not in seen_blob_ids:
                            blob = ContentBlob.objects.filter(id=blob_id).first()
                    if blob is None or blob.id in seen_blob_ids:
                        continue
                    seen_blob_ids.add(blob.id)
                    content_blobs.append(_blob_summary(blob))

        result.append(
            {
                "dispatch_id": d.id,
                "sub_agent_type": d.sub_agent_type,
                "objective": d.objective or "",
                "result_summary": d.result_summary or "",
                "synthesized": d.synthesized,
                "dispatched_at": d.dispatched_at,
                "completed_at": d.completed_at,
                "status": d.status,
                "dispatcher_thread_id": d.dispatcher_thread_id,
                "callee_thread_id": d.sub_thread_id,
                "overview_id": d.overview_id,
                "graph": graph_data,
                "content_blobs": content_blobs,
            }
        )
    return result


@router.get(
    "/blobs/{blob_id}/page/{page_num}/",
    response={200: ContentBlobPageSchema, 404: ErrorSchema},
    tags=["Core - Content Blobs"],
)
def get_content_blob_page(request, blob_id: int, page_num: int):
    """讀取 ContentBlob.page_breakdown 的指定頁（1-indexed）。

    直接從 DB 讀取，不觸發 LLM。底層邏輯與 apps.core.services.pagination.read_page 一致。
    """
    try:
        blob = ContentBlob.objects.get(id=blob_id)
    except ContentBlob.DoesNotExist:
        raise HttpError(404, f"ContentBlob {blob_id} 不存在")

    page_breakdown = blob.page_breakdown or []
    if not page_breakdown:
        raise HttpError(404, f"ContentBlob {blob_id} 沒有 page_breakdown")

    total = len(page_breakdown)
    if page_num < 1 or page_num > total:
        raise HttpError(404, f"Page {page_num} out of range (1-{total})")

    page = page_breakdown[page_num - 1] or {}
    return {
        "blob_id": blob_id,
        "page": page_num,
        "total_pages": total,
        "title": page.get("title") or "Untitled",
        "content": page.get("content") or "",
    }


@router.get(
    "/targets/{target_id}/topology/",
    response={200: TargetTopologySchema, 404: ErrorSchema},
    tags=["Core - Topology"],
)
def get_target_topology(request, target_id: int):
    """資產拓撲圖資料：節點 + 邊 + 當前 AI 攻擊位置（AssetLock / WalkCursor）。"""
    data = build_target_topology(target_id)
    if data is None:
        raise HttpError(404, f"Target {target_id} 不存在")
    return data


@router.get(
    "/assets/{asset_type}/{asset_id}/pentest-records/",
    response={200: AssetPentestRecordsSchema, 404: ErrorSchema},
    tags=["Core - Topology"],
)
def get_asset_pentest_records_api(request, asset_type: str, asset_id: int):
    """資產滲透記錄：Action 列表 + 相關 Vulnerability / CVE。"""
    data = get_asset_pentest_records(asset_type, asset_id)
    if data is None:
        raise HttpError(404, f"不支援的資產類型: {asset_type}")
    return data


@router.get(
    "/threads/{root_thread_id}/dispatch-tree/",
    response={200: AgentInteractionTreeSchema, 404: ErrorSchema},
    tags=["Core - SubAgent Dispatches"],
)
def get_dispatch_tree(request, root_thread_id: int):
    """Agent 互動樹：從 root thread 展開所有 SubAgentDispatch 層級。"""
    data = build_dispatch_tree(root_thread_id)
    if data is None:
        raise HttpError(404, f"Thread {root_thread_id} 不存在")
    return data


@router.get("/target-request-config/{target_id}/resolved", response=ResolvedRequestConfigOut, tags=["Core - Target Request Config"])
def get_resolved_request_config(request, target_id: int):
    try:
        Target.objects.get(pk=target_id)
    except Target.DoesNotExist:
        raise HttpError(404, f"Target {target_id} 不存在")
    return resolve_request_config(target_id)
