from typing import Any

from django.db import transaction
from django.db.models import Max


def _shorten(value: Any, limit: int = 4000) -> str:
    text = value if isinstance(value, str) else str(value)
    return text[:limit] + "... [truncated]" if len(text) > limit else text


class AgentEventService:
    """Graph-native persistence for realtime assistant events."""

    @staticmethod
    def emit(
        *,
        thread: Any | None,
        event_type: str,
        status: str | None = None,
        content: Any = "",
        payload: dict[str, Any] | None = None,
        run_id: str = "",
        parent_run_id: str | None = None,
        node_name: str | None = None,
        tool_name: str | None = None,
    ) -> Any | None:
        if thread is None:
            return None

        from apps.core.models import Thread, ThreadEvent

        with transaction.atomic():
            Thread.objects.select_for_update().get(id=thread.id)
            latest = (
                ThreadEvent.objects.filter(thread=thread)
                .aggregate(max_sequence=Max("sequence"))["max_sequence"]
            )
            sequence = (latest or 0) + 1
            return ThreadEvent.objects.create(
                thread=thread,
                run_id=str(run_id or ""),
                parent_run_id=str(parent_run_id) if parent_run_id else None,
                event_type=event_type,
                node_name=node_name,
                tool_name=tool_name,
                status=status,
                content=_shorten(content),
                payload=payload or {},
                sequence=sequence,
            )
