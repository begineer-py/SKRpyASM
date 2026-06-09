from typing import Any

from django.contrib.auth import get_user_model
from django.test import TestCase
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from apps.ai_assistant.helpers.assistants import AIAssistant
from apps.ai_assistant.langchain.tools import method_tool
from apps.ai_assistant.api.thread_events_stream_views import _event_payload, _sse_event
from apps.core.models import ExecutionEvent, ExecutionGraph, ExecutionNode, Thread, ThreadEvent


class BindableFakeMessagesListChatModel(FakeMessagesListChatModel):
    def bind_tools(self, tools: Any, **kwargs: Any):
        return self


class GraphNativeToolLifecycleTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="tooltester")
        self.thread = Thread.objects.create(
            name="tool lifecycle",
            created_by=self.user,
            assistant_id="graph_native_test_assistant",
        )

    def test_tool_success_creates_started_and_finished_events(self):
        class TestAssistant(AIAssistant):
            id = "graph_native_test_assistant"
            name = "Graph Native Test Assistant"
            instructions = "test"

            def get_llm(self):
                return BindableFakeMessagesListChatModel(
                    responses=[
                        AIMessage(
                            content="",
                            tool_calls=[
                                {
                                    "name": "read_thread_id",
                                    "args": {"message": "check"},
                                    "id": "call_1",
                                }
                            ],
                        ),
                        AIMessage(content="done"),
                    ]
                ).bind_tools(self.get_tools())

            @method_tool
            def read_thread_id(self, message: str, config: RunnableConfig = None) -> str:
                """Return the current thread id from RunnableConfig."""
                return str((config or {}).get("configurable", {}).get("thread_id"))

        assistant = TestAssistant(user=self.user)
        result = assistant.invoke({"input": "run tool"}, thread=self.thread, thread_id=self.thread.id)

        self.assertEqual(result["output"], "done")
        graph = ExecutionGraph.objects.get(thread=self.thread)
        nodes = list(ExecutionNode.objects.filter(graph=graph).order_by("sequence"))
        events = list(ExecutionEvent.objects.filter(graph=graph).order_by("sequence"))
        self.assertEqual(graph.status, ExecutionGraph.Status.SUCCEEDED)
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].name, "read_thread_id")
        self.assertEqual(nodes[0].status, ExecutionNode.Status.SUCCEEDED)
        self.assertEqual([event.event_type for event in events], ["graph_started", "node_started", "node_completed", "graph_completed"])
        self.assertEqual(events[2].content, str(self.thread.id))

    def test_tool_error_is_persisted_and_returned_to_agent(self):
        class TestAssistant(AIAssistant):
            id = "graph_native_error_test_assistant"
            name = "Graph Native Error Test Assistant"
            instructions = "test"

            def get_llm(self):
                return BindableFakeMessagesListChatModel(
                    responses=[
                        AIMessage(
                            content="",
                            tool_calls=[
                                {
                                    "name": "explode",
                                    "args": {"message": "boom"},
                                    "id": "call_1",
                                }
                            ],
                        ),
                        AIMessage(content="recovered"),
                    ]
                ).bind_tools(self.get_tools())

            @method_tool
            def explode(self, message: str) -> str:
                """Raise an error for lifecycle testing."""
                raise ValueError(message)

        self.thread.assistant_id = "graph_native_error_test_assistant"
        self.thread.save(update_fields=["assistant_id"])

        assistant = TestAssistant(user=self.user)
        result = assistant.invoke({"input": "run tool"}, thread=self.thread, thread_id=self.thread.id)

        self.assertEqual(result["output"], "recovered")
        graph = ExecutionGraph.objects.get(thread=self.thread)
        node = ExecutionNode.objects.get(graph=graph)
        events = list(ExecutionEvent.objects.filter(graph=graph).order_by("sequence"))
        self.assertEqual(graph.status, ExecutionGraph.Status.SUCCEEDED)
        self.assertEqual(node.status, ExecutionNode.Status.FAILED)
        self.assertEqual([event.event_type for event in events], ["graph_started", "node_started", "node_failed", "graph_completed"])
        self.assertEqual(events[2].status, ExecutionNode.Status.FAILED)
        self.assertIn("ValueError: boom", events[2].content)

    def test_unknown_tool_is_persisted_as_tool_error(self):
        class TestAssistant(AIAssistant):
            id = "graph_native_unknown_tool_test_assistant"
            name = "Graph Native Unknown Tool Test Assistant"
            instructions = "test"

            def get_llm(self):
                return BindableFakeMessagesListChatModel(
                    responses=[
                        AIMessage(
                            content="",
                            tool_calls=[
                                {
                                    "name": "missing_tool",
                                    "args": {"message": "check"},
                                    "id": "call_1",
                                }
                            ],
                        ),
                        AIMessage(content="handled"),
                    ]
                ).bind_tools(self.get_tools())

        self.thread.assistant_id = "graph_native_unknown_tool_test_assistant"
        self.thread.save(update_fields=["assistant_id"])

        assistant = TestAssistant(user=self.user)
        result = assistant.invoke({"input": "run missing tool"}, thread=self.thread, thread_id=self.thread.id)

        self.assertEqual(result["output"], "handled")
        graph = ExecutionGraph.objects.get(thread=self.thread)
        node = ExecutionNode.objects.get(graph=graph)
        events = list(ExecutionEvent.objects.filter(graph=graph).order_by("sequence"))
        self.assertEqual(node.status, ExecutionNode.Status.FAILED)
        self.assertEqual([event.event_type for event in events], ["graph_started", "node_started", "node_failed", "graph_completed"])
        self.assertEqual(events[2].payload["error_type"], "ToolNotFound")


class ExecutionServiceTests(TestCase):
    def test_start_graph_and_complete_node_write_lifecycle_events(self):
        from apps.core.services import ExecutionService

        user_model = get_user_model()
        user = user_model.objects.create_user(username="executiontester")
        thread = Thread.objects.create(name="execution", created_by=user)

        graph = ExecutionService.start_graph(thread=thread, assistant_id="test", title="Execution Test")
        node = ExecutionService.start_node(graph=graph, name="scan", kind=ExecutionNode.Kind.SCANNER)
        ExecutionService.complete_node(node, output={"ok": True}, content="scan complete")

        events = list(ExecutionEvent.objects.filter(graph=graph).order_by("sequence"))
        node.refresh_from_db()
        graph.refresh_from_db()
        self.assertEqual(graph.status, ExecutionGraph.Status.SUCCEEDED)
        self.assertEqual(node.status, ExecutionNode.Status.SUCCEEDED)
        self.assertEqual([event.event_type for event in events], ["graph_started", "node_started", "node_completed", "graph_completed"])


class ThreadEventStreamFormattingTests(TestCase):
    def test_event_payload_and_sse_format_include_sequence_id(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(username="streamtester")
        thread = Thread.objects.create(name="stream", created_by=user)
        event = ThreadEvent.objects.create(
            thread=thread,
            run_id="run-1",
            event_type="tool_started",
            tool_name="scan",
            status="started",
            content="scan started",
            payload={"execution_node_id": 123},
            sequence=7,
        )

        payload = _event_payload(event)
        self.assertEqual(payload["sequence"], 7)
        self.assertEqual(payload["payload"], {"execution_node_id": 123})

        sse = _sse_event(payload, event=event.event_type, event_id=event.sequence)
        self.assertIn("id: 7", sse)
        self.assertIn("event: tool_started", sse)
        self.assertIn('"execution_node_id": 123', sse)
