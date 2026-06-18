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


class CompressionDeadlockFixTests(TestCase):
    """Tests for compression deadlock fixes in compress_tool_outputs node.

    Covers:
      Fix B — threshold raised 2500 → 8000
      Fix A — whitelist read_content_blob / save_long_content from Stage 1 & 2
      Fix D — page_breakdown + read_content_blob(blob_id, page=N)
    """

    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="compressionfix")
        self.thread = Thread.objects.create(
            name="compression fix test",
            created_by=self.user,
            assistant_id="compression_fix_test",
        )

    def test_threshold_8000_skips_compression_for_5000_chars(self):
        """Fix B: 5000-char output stays below 8000 threshold → no ContentBlob."""
        _next_id = iter(range(1, 100))

        class TestAssistant(AIAssistant):
            id = "compression_fix_B_skip"
            name = "Compression Fix Test"
            instructions = "test"
            max_consecutive_same_tool = 0
            stop_on_waiting_async = False

            def get_llm(self):
                return BindableFakeMessagesListChatModel(
                    responses=[
                        AIMessage(content="", tool_calls=[{"name": "return_output", "args": {"size": 5000}, "id": f"call_{next(_next_id)}"}]),
                        AIMessage(content="done"),
                    ]
                ).bind_tools(self.get_tools())

            @method_tool
            def return_output(self, size: int = 100) -> str:
                """Return a string of given size for threshold testing."""
                return "X" * size

        assistant = TestAssistant(user=self.user)
        result = assistant.invoke({"input": "run"}, thread=self.thread, thread_id=self.thread.id)
        self.assertEqual(result["output"], "done")
        from apps.core.models.analyze.ContentBlob import ContentBlob
        self.assertEqual(ContentBlob.objects.count(), 0)

    def test_threshold_8000_compresses_9000_chars(self):
        """Fix B: 9000-char output exceeds 8000 threshold → ContentBlob created."""
        _next_id = iter(range(1, 100))

        class TestAssistant(AIAssistant):
            id = "compression_fix_B_compress"
            name = "Compression Fix Test"
            instructions = "test"
            max_consecutive_same_tool = 0
            stop_on_waiting_async = False

            def get_llm(self):
                return BindableFakeMessagesListChatModel(
                    responses=[
                        AIMessage(content="", tool_calls=[{"name": "return_output", "args": {"size": 9000}, "id": f"call_{next(_next_id)}"}]),
                        AIMessage(content="done"),
                    ]
                ).bind_tools(self.get_tools())

            @method_tool
            def return_output(self, size: int = 100) -> str:
                """Return a string of given size for threshold testing."""
                return "X" * size

        from apps.core.models.analyze.ContentBlob import ContentBlob
        assistant = TestAssistant(user=self.user)
        result = assistant.invoke({"input": "run"}, thread=self.thread, thread_id=self.thread.id)
        self.assertEqual(result["output"], "done")
        self.assertEqual(ContentBlob.objects.count(), 1)
        blob = ContentBlob.objects.first()
        self.assertGreaterEqual(blob.content_size, 9000)

    def test_whitelist_read_content_blob_prefix(self):
        """Fix A: output starting with '=== ContentBlob #' skips Stage 1 compression."""
        _next_id = iter(range(1, 100))

        class TestAssistant(AIAssistant):
            id = "compression_fix_A_blob"
            name = "Compression Fix Test"
            instructions = "test"
            max_consecutive_same_tool = 0
            stop_on_waiting_async = False

            def get_llm(self):
                return BindableFakeMessagesListChatModel(
                    responses=[
                        AIMessage(content="", tool_calls=[{"name": "return_blob_output", "args": {"prefix": "=== ContentBlob #"}, "id": f"call_{next(_next_id)}"}]),
                        AIMessage(content="done"),
                    ]
                ).bind_tools(self.get_tools())

            @method_tool
            def return_blob_output(self, prefix: str = "") -> str:
                """Return output that looks like a read_content_blob result."""
                return prefix + "999 Summary ===\nSource: test | Size: 9000 chars\n\n" + "X" * 9000

        from apps.core.models.analyze.ContentBlob import ContentBlob
        assistant = TestAssistant(user=self.user)
        assistant.invoke({"input": "run"}, thread=self.thread, thread_id=self.thread.id)
        self.assertEqual(ContentBlob.objects.count(), 0)

    def test_whitelist_save_long_content_prefix(self):
        """Fix A: output starting with '[Long Output Saved] blob_id=' skips compression."""
        _next_id = iter(range(1, 100))

        class TestAssistant(AIAssistant):
            id = "compression_fix_A_long"
            name = "Compression Fix Test"
            instructions = "test"
            max_consecutive_same_tool = 0
            stop_on_waiting_async = False

            def get_llm(self):
                return BindableFakeMessagesListChatModel(
                    responses=[
                        AIMessage(content="", tool_calls=[{"name": "return_long_output", "args": {}, "id": f"call_{next(_next_id)}"}]),
                        AIMessage(content="done"),
                    ]
                ).bind_tools(self.get_tools())

            @method_tool
            def return_long_output(self) -> str:
                """Return output that looks like a save_long_content result."""
                return "[Long Output Saved] blob_id=999 | Size: 9000 chars\nSummary: test\n" + "X" * 9000

        from apps.core.models.analyze.ContentBlob import ContentBlob
        assistant = TestAssistant(user=self.user)
        assistant.invoke({"input": "run"}, thread=self.thread, thread_id=self.thread.id)
        self.assertEqual(ContentBlob.objects.count(), 0)

    def test_whitelist_focused_analysis_prefix(self):
        """Fix A: output starting with '=== Focused Analysis for Blob #' skips compression."""
        _next_id = iter(range(1, 100))

        class TestAssistant(AIAssistant):
            id = "compression_fix_A_focus"
            name = "Compression Fix Test"
            instructions = "test"
            max_consecutive_same_tool = 0
            stop_on_waiting_async = False

            def get_llm(self):
                return BindableFakeMessagesListChatModel(
                    responses=[
                        AIMessage(content="", tool_calls=[{"name": "return_focus_output", "args": {}, "id": f"call_{next(_next_id)}"}]),
                        AIMessage(content="done"),
                    ]
                ).bind_tools(self.get_tools())

            @method_tool
            def return_focus_output(self) -> str:
                """Return output that looks like a focused analysis result."""
                return "=== Focused Analysis for Blob #999 ===\nQuery: test\n\n" + "X" * 9000

        from apps.core.models.analyze.ContentBlob import ContentBlob
        assistant = TestAssistant(user=self.user)
        assistant.invoke({"input": "run"}, thread=self.thread, thread_id=self.thread.id)
        self.assertEqual(ContentBlob.objects.count(), 0)

    def test_read_content_blob_page_param(self):
        """Fix D: read_content_blob(blob_id=X, page=N) returns structured page content."""
        from apps.core.models.analyze.ContentBlob import ContentBlob
        from apps.auto.tools.memory_tools import MemoryMixin

        blob = ContentBlob.objects.create(
            raw_content="Test " * 3000,
            content_size=12000,
            ai_summary="Test summary",
            source_type="other",
            page_breakdown=[
                {"title": "Overview", "content": "Target: example.com\nOpen ports: 80, 443"},
                {"title": "Vulnerabilities", "content": "SQL injection at /login\nXSS at /search"},
            ],
        )

        class TestAssistant(AIAssistant, MemoryMixin):
            id = "compression_fix_D_page"
            name = "Page Test Assistant"
            instructions = "test"
            max_consecutive_same_tool = 0
            stop_on_waiting_async = False

            def get_llm(self):
                return BindableFakeMessagesListChatModel(
                    responses=[
                        AIMessage(content="done"),
                    ]
                ).bind_tools(self.get_tools())

        assistant = TestAssistant(user=self.user)

        result = assistant.read_content_blob(blob_id=blob.id, page=1)
        self.assertIn("Page 1/2", result)
        self.assertIn("Overview", result)
        self.assertIn("Open ports", result)

        result = assistant.read_content_blob(blob_id=blob.id, page=2)
        self.assertIn("Page 2/2", result)
        self.assertIn("Vulnerabilities", result)

        result = assistant.read_content_blob(blob_id=blob.id, page=999)
        self.assertIn("out of range", result)
        self.assertIn("Page 1", result)

    def test_read_content_blob_page_missing_breakdown(self):
        """Fix D: page param on blob without page_breakdown returns helpful message."""
        from apps.core.models.analyze.ContentBlob import ContentBlob
        from apps.auto.tools.memory_tools import MemoryMixin

        blob = ContentBlob.objects.create(
            raw_content="Small content",
            content_size=15,
            ai_summary="Small summary",
            source_type="other",
        )

        class TestAssistant(AIAssistant, MemoryMixin):
            id = "compression_fix_D_nopage"
            name = "Page Test Assistant"
            instructions = "test"
            max_consecutive_same_tool = 0
            stop_on_waiting_async = False

            def get_llm(self):
                return BindableFakeMessagesListChatModel(
                    responses=[
                        AIMessage(content="done"),
                    ]
                ).bind_tools(self.get_tools())

        assistant = TestAssistant(user=self.user)

        result = assistant.read_content_blob(blob_id=blob.id, page=1)
        self.assertIn("no page_breakdown", result)
        self.assertIn("without `page`", result)

    def test_read_content_blob_no_page_shows_summary(self):
        """Fix D: read_content_blob without page shows summary + page count."""
        from apps.core.models.analyze.ContentBlob import ContentBlob
        from apps.auto.tools.memory_tools import MemoryMixin

        blob = ContentBlob.objects.create(
            raw_content="Test " * 3000,
            content_size=12000,
            ai_summary="Test summary content",
            source_type="other",
            page_breakdown=[
                {"title": "Overview", "content": "Port scanning results"},
            ],
        )

        class TestAssistant(AIAssistant, MemoryMixin):
            id = "compression_fix_D_summary"
            name = "Page Test Assistant"
            instructions = "test"
            max_consecutive_same_tool = 0
            stop_on_waiting_async = False

            def get_llm(self):
                return BindableFakeMessagesListChatModel(
                    responses=[
                        AIMessage(content="done"),
                    ]
                ).bind_tools(self.get_tools())

        assistant = TestAssistant(user=self.user)

        result = assistant.read_content_blob(blob_id=blob.id)
        self.assertIn("Test summary content", result)
        self.assertIn("Pages available: 1", result)
