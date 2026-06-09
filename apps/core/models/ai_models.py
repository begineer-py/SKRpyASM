import json
from typing import Any, Sequence, cast

from django.conf import settings
from django.db import models
from django.db.models import F, Index, Manager

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ChatMessage,
    HumanMessage,
    messages_from_dict,
)


class Thread(models.Model):
    """Thread model. A thread is a collection of messages between a user and the AI assistant.
    Also called conversation or session."""

    id: Any  # noqa: A003
    messages: Manager["Message"]
    name = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="ai_assistant_threads",
        null=True,
    )
    assistant_id = models.CharField(max_length=255, blank=True)
    bound_target_id = models.IntegerField(
        null=True, blank=True,
        help_text="The Target ID this thread is currently focused on. Set by the AI agent via bind_to_target tool."
    )
    bound_overview_id = models.IntegerField(
        null=True, blank=True,
        help_text="The Overview ID this thread is currently focused on. Automatically set when binding to a target."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_hidden = models.BooleanField(
        default=False,
        help_text="If True, this thread is internal/ephemeral and hidden from the main chat list."
    )

    class Meta:
        app_label = "core"
        db_table = "ai_assistant_thread"
        verbose_name = "Thread"
        verbose_name_plural = "Threads"
        ordering = ("-created_at",)
        indexes = (Index(F("created_at").desc(), name="thread_created_at_desc"),)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Thread {self.name}>"

    def get_messages(self, include_extra_messages: bool = False, use_compressed: bool = True) -> list[BaseMessage]:
        """
        Get LangChain messages objects from the thread.

        Args:
            include_extra_messages (bool): Whether to include non-chat messages (like tool calls).
            use_compressed (bool): If True, use compressed messages when available to optimize context window.

        Returns:
            list[BaseMessage]: List of messages, with compression applied where available
        """
        message_records = Message.objects.filter(thread=self).order_by("created_at")

        message_dicts = []
        for record in message_records:
            if use_compressed and record.compression_applied and record.compressed_content:
                message_dicts.append(record.compressed_content)
            else:
                message_dicts.append(record.message)

        messages = messages_from_dict(
            cast(
                Sequence[dict[str, BaseMessage]],
                message_dicts,
            )
        )
        if not include_extra_messages:
            messages = [
                m
                for m in messages
                if isinstance(m, HumanMessage | ChatMessage)
                or (isinstance(m, AIMessage) and not m.tool_calls)
            ]
        return cast(list[BaseMessage], messages)


class Message(models.Model):
    """Message model. A message is a text that is part of a thread.
    A message can be sent by a user or the AI assistant.\n
    The message data is stored as a JSON field called `message`."""

    id: Any  # noqa: A003
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="messages")
    thread_id: Any
    message = models.JSONField()

    compressed_content = models.JSONField(
        null=True,
        blank=True,
        help_text="Compressed version of message for context optimization"
    )

    compression_applied = models.BooleanField(
        default=False,
        help_text="Whether compression has been applied to this message"
    )

    is_tool_output = models.BooleanField(
        default=False,
        help_text="Whether this message is a tool call output"
    )

    ROLE_CHOICES = [
        ("human", "Human"),
        ("ai", "AI"),
        ("tool_call", "Tool Call"),
        ("tool_result", "Tool Result"),
        ("system", "System"),
    ]
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="ai",
        help_text="The role/type of the message (human, ai, tool_call, tool_result, system)",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "core"
        db_table = "ai_assistant_message"
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ("created_at",)
        indexes = (
            Index(F("created_at"), name="message_created_at"),
            Index(F("thread"), name="message_thread"),
            Index(F("compression_applied"), name="message_compression_applied"),
            Index(F("role"), name="message_role"),
        )

    def __str__(self) -> str:
        return json.dumps(self.message)

    def __repr__(self) -> str:
        return f"<Message {self.id} at {self.thread_id}>"


class ThreadEvent(models.Model):
    """Durable realtime event log for a thread-level AI run."""

    id: Any  # noqa: A003
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="events")
    thread_id: Any
    run_id = models.CharField(max_length=128, db_index=True)
    parent_run_id = models.CharField(max_length=128, blank=True, null=True, db_index=True)
    event_type = models.CharField(max_length=64, db_index=True)
    node_name = models.CharField(max_length=128, blank=True, null=True)
    tool_name = models.CharField(max_length=128, blank=True, null=True)
    status = models.CharField(max_length=32, blank=True, null=True)
    content = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)
    sequence = models.BigIntegerField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = "core"
        db_table = "ai_assistant_thread_event"
        verbose_name = "Thread Event"
        verbose_name_plural = "Thread Events"
        ordering = ("sequence",)
        indexes = (
            Index(fields=["thread", "sequence"], name="thread_event_thread_seq"),
            Index(fields=["thread", "created_at"], name="thread_event_thread_created"),
            Index(fields=["event_type"], name="thread_event_type"),
            Index(fields=["run_id"], name="thread_event_run"),
        )

    def __str__(self) -> str:
        return f"{self.sequence}:{self.event_type}:{self.status or ''}"
