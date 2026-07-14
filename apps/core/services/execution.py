from __future__ import annotations

from typing import Any

from django.db import connection, transaction
from django.utils import timezone

from apps.core.models import ExecutionArtifact, ExecutionEvent, ExecutionGraph, ExecutionNode, Thread


class ExecutionService:
    @staticmethod
    @transaction.atomic
    def start_graph(
        *,
        thread: Thread | None = None,
        assistant_id: str = "",
        run_id: str | None = None,
        title: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionGraph:
        graph = ExecutionGraph.objects.create(
            thread=thread,
            assistant_id=assistant_id,
            run_id=run_id,
            title=title,
            metadata=metadata or {},
        )
        ExecutionService.emit_event(
            graph=graph,
            event_type="graph_started",
            status=ExecutionGraph.Status.RUNNING,
            content=title,
            payload={"assistant_id": assistant_id, "run_id": run_id},
        )
        return graph

    @staticmethod
    def get_or_create_graph_for_thread(
        *,
        thread: Thread | None,
        assistant_id: str = "",
        run_id: str | None = None,
        title: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionGraph | None:
        if thread is None:
            return None
        existing = (
            ExecutionGraph.objects.filter(
                thread=thread,
                status__in=[ExecutionGraph.Status.RUNNING, ExecutionGraph.Status.WAITING],
            )
            .order_by("-started_at")
            .first()
        )
        if existing:
            return existing
        return ExecutionService.start_graph(
            thread=thread,
            assistant_id=assistant_id,
            run_id=run_id,
            title=title,
            metadata=metadata,
        )

    @staticmethod
    @transaction.atomic
    def complete_graph(graph: ExecutionGraph, *, content: Any = "", payload: dict[str, Any] | None = None) -> ExecutionGraph:
        graph.status = ExecutionGraph.Status.SUCCEEDED
        graph.completed_at = timezone.now()
        graph.save(update_fields=["status", "completed_at", "updated_at"])
        ExecutionService.emit_event(
            graph=graph,
            event_type="graph_completed",
            status=ExecutionGraph.Status.SUCCEEDED,
            content=content,
            payload=payload,
        )
        return graph

    @staticmethod
    @transaction.atomic
    def fail_graph(graph: ExecutionGraph, *, error: Any = "", payload: dict[str, Any] | None = None) -> ExecutionGraph:
        graph.status = ExecutionGraph.Status.FAILED
        graph.completed_at = timezone.now()
        graph.save(update_fields=["status", "completed_at", "updated_at"])
        ExecutionService.emit_event(
            graph=graph,
            event_type="graph_failed",
            status=ExecutionGraph.Status.FAILED,
            content=error,
            payload=payload,
        )
        return graph

    @staticmethod
    @transaction.atomic
    def start_node(
        *,
        graph: ExecutionGraph,
        name: str,
        kind: str = ExecutionNode.Kind.TASK,
        parent: ExecutionNode | None = None,
        tool_call_id: str | None = None,
        input: dict[str, Any] | None = None,  # noqa: A002
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionNode:
        sequence = ExecutionService._next_node_sequence(graph)
        node = ExecutionNode.objects.create(
            graph=graph,
            parent=parent,
            name=name,
            kind=kind,
            status=ExecutionNode.Status.RUNNING,
            tool_call_id=tool_call_id,
            input=input or {},
            metadata=metadata or {},
            sequence=sequence,
            started_at=timezone.now(),
        )
        ExecutionService.emit_event(
            graph=graph,
            node=node,
            event_type="node_started",
            status=ExecutionNode.Status.RUNNING,
            content=name,
            payload={"kind": kind, "tool_call_id": tool_call_id},
        )
        return node

    @staticmethod
    @transaction.atomic
    def wait_node(
        node: ExecutionNode,
        *,
        wait_reason: str = "ASYNC_CALLBACK",
        content: Any = "",
        payload: dict[str, Any] | None = None,
    ) -> ExecutionNode:
        node.status = ExecutionNode.Status.WAITING
        node.wait_reason = wait_reason
        node.save(update_fields=["status", "wait_reason", "updated_at"])
        if node.graph.status == ExecutionGraph.Status.RUNNING:
            node.graph.status = ExecutionGraph.Status.WAITING
            node.graph.save(update_fields=["status", "updated_at"])
        ExecutionService.emit_event(
            graph=node.graph,
            node=node,
            event_type="node_waiting",
            status=ExecutionNode.Status.WAITING,
            content=content,
            payload={"wait_reason": wait_reason, **(payload or {})},
        )
        return node

    @staticmethod
    @transaction.atomic
    def complete_node(
        node: ExecutionNode,
        *,
        output: dict[str, Any] | None = None,
        content: Any = "",
        payload: dict[str, Any] | None = None,
        reconcile_graph: bool = True,
    ) -> ExecutionNode:
        node.status = ExecutionNode.Status.SUCCEEDED
        node.output = output or {}
        node.completed_at = timezone.now()
        node.save(update_fields=["status", "output", "completed_at", "updated_at"])
        ExecutionService.emit_event(
            graph=node.graph,
            node=node,
            event_type="node_completed",
            status=ExecutionNode.Status.SUCCEEDED,
            content=content,
            payload=payload,
        )
        # 先觸發 agent wake（註冊 on_commit callback）再 reconcile graph status，
        # 確保 wake_agent_on_scan_completion 看到的狀態（RUNNING）是真實的 agent 活動
        # 而非 reconcile 將 WAITING→RUNNING 的副作用。
        ExecutionService._maybe_trigger_agent_wake(node)
        if reconcile_graph:
            ExecutionService.reconcile_graph_status(node.graph)
        return node

    @staticmethod
    @transaction.atomic
    def fail_node(
        node: ExecutionNode,
        *,
        error: dict[str, Any] | None = None,
        content: Any = "",
        payload: dict[str, Any] | None = None,
        reconcile_graph: bool = True,
    ) -> ExecutionNode:
        node.status = ExecutionNode.Status.FAILED
        node.error = error or {}
        node.completed_at = timezone.now()
        node.save(update_fields=["status", "error", "completed_at", "updated_at"])
        ExecutionService.emit_event(
            graph=node.graph,
            node=node,
            event_type="node_failed",
            status=ExecutionNode.Status.FAILED,
            content=content,
            payload=payload,
        )
        # 先觸發 agent wake（註冊 on_commit callback）再 reconcile graph status，
        # 確保 wake_agent_on_scan_completion 看到的狀態（RUNNING）是真實的 agent 活動
        # 而非 reconcile 將 WAITING→RUNNING 的副作用。
        ExecutionService._maybe_trigger_agent_wake(node)
        if reconcile_graph:
            ExecutionService.reconcile_graph_status(node.graph)
        return node

    @staticmethod
    @transaction.atomic
    def reconcile_graph_status(graph: ExecutionGraph) -> ExecutionGraph:
        graph = ExecutionGraph.objects.select_for_update().get(id=graph.id)
        if graph.status in [
            ExecutionGraph.Status.SUCCEEDED,
            ExecutionGraph.Status.FAILED,
            ExecutionGraph.Status.CANCELLED,
            ExecutionGraph.Status.BLOCKED,
        ]:
            return graph

        statuses = list(graph.nodes.values_list("status", flat=True))
        if not statuses:
            return graph

        active_statuses = {
            ExecutionNode.Status.PENDING,
            ExecutionNode.Status.RUNNING,
            ExecutionNode.Status.WAITING,
        }
        if any(status in active_statuses for status in statuses):
            next_status = ExecutionGraph.Status.WAITING if ExecutionNode.Status.WAITING in statuses else ExecutionGraph.Status.RUNNING
            if graph.status != next_status:
                graph.status = next_status
                graph.save(update_fields=["status", "updated_at"])
            return graph

        # 部分容錯：只有「全部 node 都 FAILED」才判 graph 死刑。
        # 混合狀態（有 SUCCEEDED 也有 FAILED）= 部分成功 → graph 保持 RUNNING，
        # 讓 agent 有機會消化已拿到的結果、決定是否重試失敗的局部。
        #
        # 嚴重程度分層：
        #   - 全部 FAILED          → fail_graph（mission 真的失敗）
        #   - 部分 FAILED + 有成功  → graph 保持 RUNNING（結果仍可用，agent 自行判斷）
        #   - 全部 SUCCEEDED/SKIPPED → graph 保持 RUNNING（等 agent 完成 mission）
        failed_count = sum(1 for s in statuses if s == ExecutionNode.Status.FAILED)
        if failed_count > 0:
            if failed_count == len(statuses):
                # 全部失敗 — mission 確實失敗
                failed_nodes_qs = graph.nodes.filter(status=ExecutionNode.Status.FAILED)
                failed_nodes_data = [
                    {
                        "node_id": n.id,
                        "node_name": n.name,
                        "error": n.error,
                        "sequence": n.sequence,
                    }
                    for n in failed_nodes_qs.only("id", "name", "error", "sequence")
                ]
                return ExecutionService.fail_graph(
                    graph,
                    error="All execution nodes failed",
                    payload={"failed_nodes": failed_nodes_data},
                )
            else:
                # 部分失敗 — 記錄但不判死刑，graph 保持 RUNNING 讓 agent 繼續
                succeeded_count = sum(
                    1 for s in statuses
                    if s in [ExecutionNode.Status.SUCCEEDED, ExecutionNode.Status.SKIPPED]
                )
                ExecutionService.emit_event(
                    graph=graph,
                    event_type="partial_failure",
                    status=graph.status,
                    content=f"{failed_count}/{len(statuses)} nodes failed, {succeeded_count} succeeded — graph continues",
                    payload={
                        "failed_count": failed_count,
                        "succeeded_count": succeeded_count,
                        "total": len(statuses),
                    },
                )
                if graph.status != ExecutionGraph.Status.RUNNING:
                    graph.status = ExecutionGraph.Status.RUNNING
                    graph.save(update_fields=["status", "updated_at"])
                return graph

        # 所有 node 都 SUCCEEDED/SKIPPED：
        # 不要自動 complete_graph — 「async scanner 都完成」不等於「mission 完成」。
        # Graph 保留為 RUNNING，讓 wake_agent_on_scan_completion 喚醒 agent 繼續消化結果並決定下一步。
        # Mission 真正完成的 gate 由 Overview.status=COMPLETED 連動（update_overview_status / propose_next_steps）。
        if all(status in [ExecutionNode.Status.SUCCEEDED, ExecutionNode.Status.SKIPPED] for status in statuses):
            if graph.status != ExecutionGraph.Status.RUNNING:
                graph.status = ExecutionGraph.Status.RUNNING
                graph.save(update_fields=["status", "updated_at"])
            return graph

        return graph

    @staticmethod
    @transaction.atomic
    def set_node_external_task_id(execution_node_id: int | None, external_task_id: str | None) -> ExecutionNode | None:
        if not execution_node_id or not external_task_id:
            return None
        node = ExecutionNode.objects.select_for_update().filter(id=execution_node_id).first()
        if not node:
            return None
        node.external_task_id = str(external_task_id)
        node.save(update_fields=["external_task_id", "updated_at"])
        ExecutionService.emit_event(
            graph=node.graph,
            node=node,
            event_type="node_task_bound",
            status=node.status,
            content=f"Celery task bound: {external_task_id}",
            payload={"external_task_id": str(external_task_id)},
        )
        return node

    @staticmethod
    def complete_node_by_id(
        execution_node_id: int | None,
        *,
        output: dict[str, Any] | None = None,
        content: Any = "",
        payload: dict[str, Any] | None = None,
        reconcile_graph: bool = True,
    ) -> ExecutionNode | None:
        if not execution_node_id:
            return None
        node = ExecutionNode.objects.filter(id=execution_node_id).first()
        if node and node.status in [ExecutionNode.Status.RUNNING, ExecutionNode.Status.WAITING]:
            return ExecutionService.complete_node(node, output=output, content=content, payload=payload, reconcile_graph=reconcile_graph)
        return node

    @staticmethod
    def fail_node_by_id(
        execution_node_id: int | None,
        *,
        error: dict[str, Any] | None = None,
        content: Any = "",
        payload: dict[str, Any] | None = None,
        reconcile_graph: bool = True,
    ) -> ExecutionNode | None:
        if not execution_node_id:
            return None
        node = ExecutionNode.objects.filter(id=execution_node_id).first()
        if node and node.status in [ExecutionNode.Status.RUNNING, ExecutionNode.Status.WAITING]:
            return ExecutionService.fail_node(node, error=error, content=content, payload=payload, reconcile_graph=reconcile_graph)
        return node

    @staticmethod
    @transaction.atomic
    def emit_event(
        *,
        graph: ExecutionGraph,
        event_type: str,
        node: ExecutionNode | None = None,
        status: str | None = None,
        content: Any = "",
        payload: dict[str, Any] | None = None,
    ) -> ExecutionEvent:
        sequence = ExecutionService._next_event_sequence(graph)
        return ExecutionEvent.objects.create(
            graph=graph,
            node=node,
            event_type=event_type,
            status=status,
            content=str(content) if content is not None else "",
            payload=payload or {},
            sequence=sequence,
        )

    @staticmethod
    def attach_artifact(
        *,
        graph: ExecutionGraph,
        artifact_type: str,
        node: ExecutionNode | None = None,
        name: str = "",
        content: Any = "",
        data: dict[str, Any] | None = None,
        content_blob: Any | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionArtifact:
        return ExecutionArtifact.objects.create(
            graph=graph,
            node=node,
            artifact_type=artifact_type,
            name=name,
            content=str(content) if content is not None else "",
            data=data or {},
            content_blob=content_blob,
            metadata=metadata or {},
        )

    @staticmethod
    def _next_node_sequence(graph: ExecutionGraph) -> int:
        """全域 PostgreSQL SEQUENCE 取號（原子操作，無 TOCTOU race）。

        契約：sequence 在單一 graph 內單調遞增但**可能有跳號**（SEQUENCE 是全域的，
        非 per-graph）。不可假設密集連續。SSE resume 的 last_sequence 比較是 `<`，
        跳號不影響正確性。UniqueConstraint uniq_exec_node_graph_seq 保留為雙重防禦。
        """
        with connection.cursor() as cursor:
            cursor.execute("SELECT nextval('execution_graph_node_seq')")
            return cursor.fetchone()[0]

    @staticmethod
    def _next_event_sequence(graph: ExecutionGraph) -> int:
        """同 _next_node_sequence，但用 execution_node_event_seq。"""
        with connection.cursor() as cursor:
            cursor.execute("SELECT nextval('execution_node_event_seq')")
            return cursor.fetchone()[0]

    @staticmethod
    def _maybe_trigger_agent_wake(node: ExecutionNode) -> None:
        """若 node 是 ASYNC_CALLBACK（scanner dispatch），在 commit 後喚醒綁定 agent。

        on_commit 確保 wake task 在 DB commit 後才執行（看到最新的 node/graph 狀態）。
        Lazy import 避免循環依賴（apps.auto.tasks 會 import ExecutionService）。
        """
        if getattr(node, "wait_reason", None) != "ASYNC_CALLBACK":
            return
        if not node.graph_id:
            return
        # 重新取得 graph.thread_id（避免 graph 物件 stale）
        graph = ExecutionGraph.objects.filter(id=node.graph_id).only("thread_id").first()
        if not graph or not graph.thread_id:
            return
        node_id = node.id
        try:
            from django.db import transaction as _tx

            from apps.auto.tasks import wake_agent_on_scan_completion

            _tx.on_commit(lambda: wake_agent_on_scan_completion.delay(execution_node_id=node_id))
        except ImportError:
            # apps.auto.tasks 尚未載入（例如初始 migration）— 安全跳過
            pass
