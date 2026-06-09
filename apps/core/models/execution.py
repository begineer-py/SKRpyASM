from typing import Any

from django.db import models
from django.db.models import F, Index, UniqueConstraint


class ExecutionGraph(models.Model):
    class Status(models.TextChoices):
        RUNNING = "RUNNING", "Running"
        WAITING = "WAITING", "Waiting"
        SUCCEEDED = "SUCCEEDED", "Succeeded"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"
        BLOCKED = "BLOCKED", "Blocked"

    id: Any  # noqa: A003
    thread = models.ForeignKey(
        "core.Thread",
        on_delete=models.CASCADE,
        related_name="execution_graphs",
        null=True,
        blank=True,
    )
    thread_id: Any
    assistant_id = models.CharField(max_length=255, blank=True)
    run_id = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    title = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.RUNNING, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "core"
        db_table = "execution_graph"
        ordering = ("-started_at",)
        indexes = (
            Index(fields=["thread", "status"], name="exec_graph_thread_status"),
            Index(F("started_at").desc(), name="exec_graph_started_desc"),
            Index(fields=["run_id"], name="exec_graph_run"),
        )

    def __str__(self) -> str:
        return f"ExecutionGraph#{self.id}:{self.status}"


class ExecutionNode(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        WAITING = "WAITING", "Waiting"
        SUCCEEDED = "SUCCEEDED", "Succeeded"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"
        SKIPPED = "SKIPPED", "Skipped"
        BLOCKED = "BLOCKED", "Blocked"

    class Kind(models.TextChoices):
        GRAPH = "GRAPH", "Graph"
        LLM = "LLM", "LLM"
        TOOL = "TOOL", "Tool"
        SCANNER = "SCANNER", "Scanner"
        TASK = "TASK", "Task"
        SYSTEM = "SYSTEM", "System"

    id: Any  # noqa: A003
    graph = models.ForeignKey(ExecutionGraph, on_delete=models.CASCADE, related_name="nodes")
    graph_id: Any
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
    )
    parent_id: Any
    name = models.CharField(max_length=255)
    kind = models.CharField(max_length=32, choices=Kind.choices, default=Kind.TASK, db_index=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING, db_index=True)
    tool_call_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    external_task_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    wait_reason = models.CharField(max_length=64, blank=True, null=True)
    input = models.JSONField(default=dict, blank=True)
    output = models.JSONField(default=dict, blank=True)
    error = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    sequence = models.BigIntegerField(db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        db_table = "execution_node"
        ordering = ("sequence", "id")
        indexes = (
            Index(fields=["graph", "sequence"], name="exec_node_graph_seq"),
            Index(fields=["graph", "status"], name="exec_node_graph_status"),
            Index(fields=["graph", "kind"], name="exec_node_graph_kind"),
        )
        constraints = (
            UniqueConstraint(fields=["graph", "sequence"], name="uniq_exec_node_graph_seq"),
        )

    def __str__(self) -> str:
        return f"ExecutionNode#{self.id}:{self.name}:{self.status}"


class ExecutionEvent(models.Model):
    id: Any  # noqa: A003
    graph = models.ForeignKey(ExecutionGraph, on_delete=models.CASCADE, related_name="events")
    graph_id: Any
    node = models.ForeignKey(
        ExecutionNode,
        on_delete=models.CASCADE,
        related_name="events",
        null=True,
        blank=True,
    )
    node_id: Any
    event_type = models.CharField(max_length=96, db_index=True)
    status = models.CharField(max_length=32, blank=True, null=True, db_index=True)
    content = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)
    sequence = models.BigIntegerField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "core"
        db_table = "execution_event"
        ordering = ("sequence", "id")
        indexes = (
            Index(fields=["graph", "sequence"], name="exec_event_graph_seq"),
            Index(fields=["node", "sequence"], name="exec_event_node_seq"),
            Index(fields=["event_type"], name="exec_event_type"),
        )
        constraints = (
            UniqueConstraint(fields=["graph", "sequence"], name="uniq_exec_event_graph_seq"),
        )

    def __str__(self) -> str:
        return f"{self.sequence}:{self.event_type}:{self.status or ''}"


class ExecutionArtifact(models.Model):
    id: Any  # noqa: A003
    graph = models.ForeignKey(ExecutionGraph, on_delete=models.CASCADE, related_name="artifacts")
    graph_id: Any
    node = models.ForeignKey(
        ExecutionNode,
        on_delete=models.CASCADE,
        related_name="artifacts",
        null=True,
        blank=True,
    )
    node_id: Any
    artifact_type = models.CharField(max_length=96, db_index=True)
    name = models.CharField(max_length=255, blank=True)
    content = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    content_blob = models.ForeignKey(
        "core.ContentBlob",
        on_delete=models.SET_NULL,
        related_name="execution_artifacts",
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "core"
        db_table = "execution_artifact"
        ordering = ("created_at", "id")
        indexes = (
            Index(fields=["graph", "artifact_type"], name="exec_art_graph_type"),
            Index(fields=["node", "artifact_type"], name="exec_art_node_type"),
        )

    def __str__(self) -> str:
        return f"ExecutionArtifact#{self.id}:{self.artifact_type}"
