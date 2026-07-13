"""AI Workbench API tests — Graph CRUD, SubAgentDispatch list, ContentBlob pages, G1 dispatch record."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core.models import (
    ContentBlob,
    ExecutionArtifact,
    ExecutionGraph,
    Overview,
    SubAgentDispatch,
    Target,
    Thread,
)
from apps.core.services import ExecutionService


class ExecutionGraphCrudApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="graph_crud_tester")
        self.thread = Thread.objects.create(
            name="crud", created_by=self.user, assistant_id="api-assistant"
        )
        self.graph = ExecutionService.start_graph(
            thread=self.thread,
            assistant_id="api-assistant",
            run_id="run-crud",
            title="CRUD graph",
        )

    def test_patch_title_and_archive(self):
        response = self.client.patch(
            f"/api/core/executions/{self.graph.id}",
            data={"title": "Renamed", "archived": True},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["title"], "Renamed")
        self.assertTrue(payload["metadata"].get("archived"))

        listed = self.client.get(f"/api/core/executions?thread_id={self.thread.id}")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json(), [])

        listed_all = self.client.get(
            f"/api/core/executions?thread_id={self.thread.id}&include_archived=true"
        )
        self.assertEqual(listed_all.status_code, 200)
        self.assertEqual(len(listed_all.json()), 1)

    def test_delete_graph(self):
        response = self.client.delete(f"/api/core/executions/{self.graph.id}")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ExecutionGraph.objects.filter(id=self.graph.id).exists())

    def test_list_supports_offset_and_search(self):
        ExecutionService.start_graph(
            thread=self.thread, assistant_id="api-assistant", title="Alpha"
        )
        ExecutionService.start_graph(
            thread=self.thread, assistant_id="api-assistant", title="Beta"
        )
        response = self.client.get(
            f"/api/core/executions?thread_id={self.thread.id}&search=Beta&limit=10&offset=0"
        )
        self.assertEqual(response.status_code, 200)
        titles = [g["title"] for g in response.json()]
        self.assertIn("Beta", titles)
        self.assertNotIn("Alpha", titles)


class SubAgentDispatchApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="dispatch_api_tester")
        self.caller = Thread.objects.create(
            name="caller",
            created_by=self.user,
            assistant_id="hacker_assistant_agent",
        )
        self.sub = Thread.objects.create(
            name="subagent_auto",
            created_by=self.user,
            assistant_id="automation_agent",
            is_hidden=True,
        )
        self.target = Target.objects.create(name="dispatch-api-target")
        self.overview = Overview.objects.create(target=self.target, status="EXECUTING")
        self.graph = ExecutionService.start_graph(
            thread=self.sub,
            assistant_id="automation_agent",
            title="auto run",
        )
        self.blob = ContentBlob.objects.create(
            source_type="other",
            raw_content="x" * 100,
            content_size=100,
            ai_summary="summary of sub-agent output",
            page_breakdown=[
                {"title": "Page 1", "content": "hello page one"},
                {"title": "Page 2", "content": "hello page two"},
            ],
        )
        ExecutionArtifact.objects.create(
            graph=self.graph,
            artifact_type="content_blob",
            name="blob",
            data={"blob_id": self.blob.id},
            content_blob=self.blob,
        )
        self.dispatch = SubAgentDispatch.objects.create(
            overview=self.overview,
            dispatcher_thread=self.caller,
            sub_agent_type="automation_agent",
            sub_thread=self.sub,
            objective="Pentest example.com",
            status="RUNNING",
        )

    def test_list_dispatches_includes_graph_and_blobs(self):
        response = self.client.get(f"/api/core/threads/{self.caller.id}/dispatches/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        item = payload[0]
        self.assertEqual(item["dispatch_id"], self.dispatch.id)
        self.assertEqual(item["sub_agent_type"], "automation_agent")
        self.assertEqual(item["callee_thread_id"], self.sub.id)
        self.assertIsNotNone(item["graph"])
        self.assertEqual(item["graph"]["graph_id"], self.graph.id)
        self.assertEqual(len(item["content_blobs"]), 1)
        self.assertEqual(item["content_blobs"][0]["blob_id"], self.blob.id)
        self.assertEqual(item["content_blobs"][0]["page_count"], 2)

    def test_blob_page_endpoint(self):
        response = self.client.get(f"/api/core/blobs/{self.blob.id}/page/1/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["title"], "Page 1")
        self.assertEqual(payload["content"], "hello page one")
        self.assertEqual(payload["total_pages"], 2)

        missing = self.client.get(f"/api/core/blobs/{self.blob.id}/page/99/")
        self.assertEqual(missing.status_code, 404)


class AutomationDispatchRecordTests(TestCase):
    """G1: run_automation_agent_async 應建立 SubAgentDispatch 記錄。"""

    def test_record_automation_dispatch_helper(self):
        from apps.auto.tasks import _record_automation_dispatch

        user_model = get_user_model()
        user = user_model.objects.create_user(username="auto_dispatch_tester")
        caller = Thread.objects.create(
            name="ha", created_by=user, assistant_id="hacker_assistant_agent"
        )
        sub = Thread.objects.create(
            name="aa", created_by=user, assistant_id="automation_agent", is_hidden=True
        )
        target = Target.objects.create(name="auto-dispatch-target")
        overview = Overview.objects.create(target=target, status="EXECUTING")

        class _FakeAgent:
            _agent_overview_id = overview.id
            _thread = sub

        dispatch = _record_automation_dispatch(
            _FakeAgent(),
            "scan example.com thoroughly",
            caller.id,
            status="COMPLETED",
            result_summary="done",
        )
        self.assertIsNotNone(dispatch)
        self.assertEqual(dispatch.sub_agent_type, "automation_agent")
        self.assertEqual(dispatch.dispatcher_thread_id, caller.id)
        self.assertEqual(dispatch.sub_thread_id, sub.id)
        self.assertEqual(dispatch.status, "COMPLETED")
        self.assertTrue(dispatch.objective.startswith("scan example"))
