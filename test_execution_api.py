from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core.models import ExecutionGraph, Overview, Target, Thread


class ExecutionGraphTargetFilterApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="execution_filter_tester")
        self.target = Target.objects.create(name="execution-filter-target")
        self.other_target = Target.objects.create(name="other-execution-filter-target")

    def _create_thread(self, name, target=None):
        return Thread.objects.create(
            name=name,
            created_by=self.user,
            assistant_id="api-assistant",
            bound_target_id=target,
        )

    def _create_graph(self, thread, title):
        return ExecutionGraph.objects.create(
            thread=thread,
            assistant_id="api-assistant",
            title=title,
        )

    def _list_target_graph_ids(self, target):
        response = self.client.get(f"/api/core/executions?target_id={target.id}")
        self.assertEqual(response.status_code, 200)
        return [item["id"] for item in response.json()]

    def test_target_filter_includes_direct_target_bound_thread_graph(self):
        # Given
        thread = self._create_thread("direct-target-thread", self.target)
        graph = self._create_graph(thread, "Direct target graph")

        # When
        graph_ids = self._list_target_graph_ids(self.target)

        # Then
        self.assertEqual(graph_ids, [graph.id])

    def test_target_filter_includes_overview_and_parent_thread_graphs(self):
        # Given
        overview_thread = self._create_thread("overview-thread")
        parent_thread = self._create_thread("overview-parent-thread")
        Overview.objects.create(
            target=self.target,
            thread=overview_thread,
            parent_thread=parent_thread,
        )
        overview_graph = self._create_graph(overview_thread, "Overview graph")
        parent_graph = self._create_graph(parent_thread, "Overview parent graph")

        # When
        graph_ids = self._list_target_graph_ids(self.target)

        # Then
        self.assertSetEqual(set(graph_ids), {overview_graph.id, parent_graph.id})

    def test_target_filter_deduplicates_graph_matching_multiple_paths(self):
        # Given
        thread = self._create_thread("duplicate-candidate-thread", self.target)
        Overview.objects.create(target=self.target, thread=thread, parent_thread=thread)
        Overview.objects.create(target=self.other_target, parent_thread=thread)
        graph = self._create_graph(thread, "Duplicate candidate graph")

        # When
        graph_ids = self._list_target_graph_ids(self.target)

        # Then
        self.assertEqual(graph_ids, [graph.id])

    def test_target_filter_returns_empty_list_for_empty_target(self):
        # Given
        self._create_graph(self._create_thread("unbound-thread"), "Unbound graph")

        # When
        graph_ids = self._list_target_graph_ids(self.target)

        # Then
        self.assertEqual(graph_ids, [])

    def test_target_filter_excludes_unrelated_target_graph(self):
        # Given
        target_graph = self._create_graph(
            self._create_thread("target-thread", self.target),
            "Target graph",
        )
        self._create_graph(
            self._create_thread("other-target-thread", self.other_target),
            "Other target graph",
        )

        # When
        graph_ids = self._list_target_graph_ids(self.target)

        # Then
        self.assertEqual(graph_ids, [target_graph.id])

    def test_other_target_filter_excludes_target_and_null_thread_graphs(self):
        # Given
        self._create_graph(
            self._create_thread("target-thread", self.target),
            "Target graph",
        )
        other_graph = self._create_graph(
            self._create_thread("other-target-thread", self.other_target),
            "Other target graph",
        )
        self._create_graph(None, "Null-thread graph")

        # When
        graph_ids = self._list_target_graph_ids(self.other_target)

        # Then
        self.assertEqual(graph_ids, [other_graph.id])

    def test_target_filter_excludes_null_thread_graph(self):
        # Given
        target_graph = self._create_graph(
            self._create_thread("bound-thread", self.target),
            "Bound graph",
        )
        self._create_graph(None, "Null-thread graph")

        # When
        graph_ids = self._list_target_graph_ids(self.target)

        # Then
        self.assertEqual(graph_ids, [target_graph.id])

    def test_no_target_filter_keeps_nullable_thread_graph(self):
        # Given
        graph = self._create_graph(None, "Null-thread graph")

        # When
        response = self.client.get("/api/core/executions")

        # Then
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], [graph.id])

    def test_target_filter_composes_with_existing_list_filters_and_pagination(self):
        # Given
        thread = self._create_thread("filtered-target-thread", self.target)
        older = self._create_graph(thread, "Matched older")
        newer = self._create_graph(thread, "Matched newer")
        archived = self._create_graph(thread, "Matched archived")
        wrong_status = self._create_graph(thread, "Matched failed")
        wrong_search = self._create_graph(thread, "Different title")
        for graph in (older, newer, archived, wrong_search):
            graph.status = ExecutionGraph.Status.SUCCEEDED
            graph.save(update_fields=["status"])
        archived.metadata = {"archived": True}
        archived.save(update_fields=["metadata"])
        wrong_status.status = ExecutionGraph.Status.FAILED
        wrong_status.save(update_fields=["status"])

        # When
        response = self.client.get(
            f"/api/core/executions?target_id={self.target.id}"
            "&status=SUCCEEDED&search=Matched&limit=1&offset=1"
        )

        # Then
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], [older.id])
