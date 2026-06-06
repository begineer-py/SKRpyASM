from django.db import models
from django.utils import timezone
import json
from typing import Any, Optional


class ThreadCompressionState(models.Model):
    """Tracks compression state of a Thread to manage incremental compression."""

    thread = models.OneToOneField(
        'core.Thread',
        on_delete=models.CASCADE,
        related_name='compression_state'
    )
    total_message_count = models.IntegerField(default=0)
    last_compressed_at = models.DateTimeField(null=True, blank=True)
    last_compressed_message_id = models.BigIntegerField(null=True, blank=True)

    compression_summary = models.JSONField(
        default=dict,
        help_text="Metadata about compression operations: {compression_count, chunks_count, last_overview_update}"
    )

    context_window_used_tokens = models.IntegerField(
        default=0,
        help_text="Estimated tokens currently in context window"
    )
    requires_compression = models.BooleanField(
        default=False,
        help_text="Flag set when context exceeds 128K tokens"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        db_table = "ai_assistant_threadcompressionstate"
        verbose_name = "Thread Compression State"
        verbose_name_plural = "Thread Compression States"

    def __str__(self):
        return f"CompressionState({self.thread.id})"


class GlobalContextOverview(models.Model):
    """Stores the global strategic overview of a thread's conversation."""

    thread = models.OneToOneField(
        'core.Thread',
        on_delete=models.CASCADE,
        related_name='global_overview'
    )

    mission = models.TextField(
        help_text="High-level mission objective"
    )

    confirmed_vulnerabilities = models.JSONField(
        default=list,
        help_text="List of confirmed vulnerabilities: [{title, cve, severity, location}]"
    )
    excluded_paths = models.JSONField(
        default=list,
        help_text="Attack vectors ruled out: [{path, reason, timestamp}]"
    )

    critical_artifacts = models.JSONField(
        default=list,
        help_text="Important artifacts to retain: [{type, value_hash, location, importance}]"
    )

    attempted_exploits = models.JSONField(
        default=list,
        help_text="Past exploits attempted: [{tool, target, result, timestamp}]"
    )

    current_phase = models.CharField(
        max_length=50,
        choices=[
            ('RECONNAISSANCE', 'Reconnaissance'),
            ('SCANNING', 'Scanning'),
            ('ENUMERATION', 'Enumeration'),
            ('EXPLOITATION', 'Exploitation'),
            ('POST_EXPLOITATION', 'Post-Exploitation'),
            ('CLEANUP', 'Cleanup'),
            ('COMPLETED', 'Completed'),
        ],
        default='RECONNAISSANCE'
    )

    metrics = models.JSONField(
        default=dict,
        help_text="Metrics: {hosts_discovered, ports_found, services_identified, exploits_successful}"
    )

    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        db_table = "ai_assistant_globalcontextoverview"
        verbose_name = "Global Context Overview"
        verbose_name_plural = "Global Context Overviews"

    def __str__(self):
        return f"Overview({self.thread.id})"


class MessageCompressionChunk(models.Model):
    """Represents a logical chunk of messages for compression."""

    STRATEGY_CHOICES = [
        ('PENDING', 'Pending'),
        ('RETAIN', 'Retain Full Content'),
        ('TEXTUALIZE', 'Textualize'),
        ('DISCARD', 'Discard Entirely'),
    ]

    thread = models.ForeignKey(
        'core.Thread',
        on_delete=models.CASCADE,
        related_name='compression_chunks'
    )

    chunk_index = models.IntegerField(
        help_text="Sequential index of this chunk"
    )

    start_message_id = models.BigIntegerField()
    end_message_id = models.BigIntegerField()

    original_content = models.JSONField(
        help_text="Original uncompressed messages in chunk"
    )
    compressed_content = models.JSONField(
        null=True,
        blank=True,
        help_text="Compressed version of messages"
    )

    compression_ratio = models.FloatField(
        default=0.0,
        help_text="Compression ratio: (1 - compressed_size/original_size) * 100"
    )

    tool_calls = models.JSONField(
        default=list,
        help_text="List of tools called in this chunk"
    )

    strategy = models.CharField(
        max_length=20,
        choices=STRATEGY_CHOICES,
        default='PENDING',
        help_text="Agent-decided retention strategy for this chunk"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "core"
        db_table = "ai_assistant_messagecompressionchunk"
        verbose_name = "Message Compression Chunk"
        verbose_name_plural = "Message Compression Chunks"
        unique_together = ('thread', 'chunk_index')
        ordering = ('thread', 'chunk_index')

    def __str__(self):
        return f"Chunk({self.thread.id}, index={self.chunk_index})"


class ToolOutputLifecycle(models.Model):
    """Tracks the lifecycle state of tool outputs."""

    STRATEGY_CHOICES = [
        ('DISCARD', 'Discard Entirely'),
        ('TEXTUALIZE', 'Textualize'),
        ('RETAIN', 'Retain Full Content'),
    ]

    message = models.OneToOneField(
        'core.Message',
        on_delete=models.CASCADE,
        related_name='tool_lifecycle'
    )

    tool_name = models.CharField(max_length=255)

    strategy = models.CharField(
        max_length=20,
        choices=STRATEGY_CHOICES,
        default='TEXTUALIZE'
    )

    original_output_size = models.IntegerField(
        help_text="Original output size in characters"
    )
    compressed_size = models.IntegerField(
        default=0,
        help_text="Compressed output size"
    )

    compressed_output = models.TextField(
        null=True,
        blank=True,
        help_text="Textual summary if strategy=TEXTUALIZE"
    )

    reason = models.TextField(
        help_text="Why this strategy was selected"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"
        db_table = "ai_assistant_tooloutputlifecycle"
        verbose_name = "Tool Output Lifecycle"
        verbose_name_plural = "Tool Output Lifecycles"

    def __str__(self):
        return f"ToolLifecycle({self.tool_name}, {self.strategy})"
