from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core.execution_stream_views import _event_payload, _sse_event
from apps.core.models import ExecutionEvent, ExecutionGraph, ExecutionNode, Thread
from apps.core.services import ExecutionService


class ExecutionApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="execution_api_tester")
        self.thread = Thread.objects.create(name="api", created_by=self.user, assistant_id="api-assistant")
        self.graph = ExecutionService.start_graph(
            thread=self.thread,
            assistant_id="api-assistant",
            run_id="run-api",
            title="API graph",
        )
        self.node = ExecutionService.start_node(
            graph=self.graph,
            name="scan",
            kind=ExecutionNode.Kind.SCANNER,
            input={"target": "example.com"},
        )
        ExecutionService.complete_node(self.node, output={"ok": True}, content="scan complete")
        ExecutionService.attach_artifact(
            graph=self.graph,
            node=self.node,
            artifact_type="scan_result",
            name="result.json",
            data={"count": 1},
        )

    def test_list_execution_graphs_filters_by_thread(self):
        response = self.client.get(f"/api/core/executions?thread_id={self.thread.id}")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["id"], self.graph.id)
        self.assertEqual(payload[0]["thread_id"], self.thread.id)

    def test_execution_graph_detail_includes_nodes_events_and_artifacts(self):
        response = self.client.get(f"/api/core/executions/{self.graph.id}")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["id"], self.graph.id)
        self.assertEqual(payload["nodes"][0]["id"], self.node.id)
        self.assertEqual([event["event_type"] for event in payload["events"]], ["graph_started", "node_started", "node_completed", "graph_completed"])
        self.assertEqual(payload["artifacts"][0]["artifact_type"], "scan_result")

    def test_list_execution_events_supports_sequence_resume(self):
        response = self.client.get(f"/api/core/executions/{self.graph.id}/events?after=1")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([event["sequence"] for event in payload], [2, 3, 4])


class ExecutionEventStreamFormattingTests(TestCase):
    def test_event_payload_and_sse_format_include_sequence_id(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(username="execution_stream_tester")
        thread = Thread.objects.create(name="stream", created_by=user)
        graph = ExecutionGraph.objects.create(thread=thread, assistant_id="stream-assistant")
        event = ExecutionEvent.objects.create(
            graph=graph,
            event_type="node_started",
            status=ExecutionNode.Status.RUNNING,
            content="scan started",
            payload={"node_name": "scan"},
            sequence=7,
        )

        payload = _event_payload(event)
        self.assertEqual(payload["graph_id"], graph.id)
        self.assertEqual(payload["sequence"], 7)
        self.assertEqual(payload["payload"], {"node_name": "scan"})

        sse = _sse_event(payload, event=event.event_type, event_id=event.sequence)
        self.assertIn("id: 7", sse)
        self.assertIn("event: node_started", sse)
        self.assertIn('"node_name": "scan"', sse)


class ExecutionServiceLifecycleTests(TestCase):
    def test_set_external_task_id_and_fail_by_id_write_events(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(username="execution_lifecycle_tester")
        thread = Thread.objects.create(name="lifecycle", created_by=user)
        graph = ExecutionService.start_graph(thread=thread, assistant_id="tester")
        node = ExecutionService.start_node(graph=graph, name="scanner", kind=ExecutionNode.Kind.SCANNER)

        ExecutionService.set_node_external_task_id(node.id, "celery-task-1")
        ExecutionService.fail_node_by_id(
            node.id,
            content="scanner failed",
            error={"error_type": "RuntimeError", "message": "boom"},
        )

        node.refresh_from_db()
        events = list(ExecutionEvent.objects.filter(graph=graph).order_by("sequence"))

        self.assertEqual(node.external_task_id, "celery-task-1")
        self.assertEqual(node.status, ExecutionNode.Status.FAILED)
        self.assertEqual(
            [event.event_type for event in events],
            ["graph_started", "node_started", "node_task_bound", "node_failed", "graph_failed"],
        )
        self.assertEqual(events[2].payload["external_task_id"], "celery-task-1")
        self.assertEqual(events[3].payload, {})
        self.assertEqual(node.error["message"], "boom")

    def test_waiting_graph_completes_after_async_node_callback(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(username="execution_async_tester")
        thread = Thread.objects.create(name="async", created_by=user)
        graph = ExecutionService.start_graph(thread=thread, assistant_id="tester")
        node = ExecutionService.start_node(graph=graph, name="scanner", kind=ExecutionNode.Kind.SCANNER)

        ExecutionService.wait_node(node, wait_reason="ASYNC_CALLBACK", content="waiting")
        graph.refresh_from_db()
        self.assertEqual(graph.status, ExecutionGraph.Status.WAITING)

        ExecutionService.complete_node_by_id(node.id, output={"ok": True}, content="scanner complete")
        graph.refresh_from_db()
        events = list(ExecutionEvent.objects.filter(graph=graph).order_by("sequence"))

        self.assertEqual(graph.status, ExecutionGraph.Status.SUCCEEDED)
        self.assertEqual(events[-1].event_type, "graph_completed")
