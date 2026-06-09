from django.urls import path

from apps.ai_assistant.api.views import api
from apps.ai_assistant.api.stream_views import stream_thread_message
from apps.ai_assistant.api.thread_events_stream_views import stream_thread_events


urlpatterns = [
    # SSE streaming endpoints — MUST come before api.urls so Django matches them first
    path(
        "threads/<int:thread_id>/messages/stream/",
        stream_thread_message,
        name="stream_thread_message",
    ),
    path(
        "threads/<int:thread_id>/events/stream/",
        stream_thread_events,
        name="stream_thread_events",
    ),
    # Standard Ninja REST API (list/create threads, messages, etc.)
    path("", api.urls),
]
