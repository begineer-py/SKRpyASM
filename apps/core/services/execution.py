from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import Max
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

        if any(status == ExecutionNode.Status.FAILED for status in statuses):
            return ExecutionService.fail_graph(graph, error="One or more execution nodes failed")

        if all(status in [ExecutionNode.Status.SUCCEEDED, ExecutionNode.Status.SKIPPED] for status in statuses):
            return ExecutionService.complete_graph(graph, content="All execution nodes completed")

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
        return (ExecutionNode.objects.filter(graph=graph).aggregate(value=Max("sequence"))["value"] or 0) + 1

    @staticmethod
    def _next_event_sequence(graph: ExecutionGraph) -> int:
        return (ExecutionEvent.objects.filter(graph=graph).aggregate(value=Max("sequence"))["value"] or 0) + 1
