from django.urls import path

from apps.ai_assistant.api.views import api
from apps.ai_assistant.api.stream_views import stream_thread_message
from apps.ai_assistant.api.logs_stream_views import stream_step_logs


urlpatterns = [
    # SSE streaming endpoints — MUST come before api.urls so Django matches them first
    path(
        "threads/<int:thread_id>/messages/stream/",
        stream_thread_message,
        name="stream_thread_message",
    ),
    # StepLog streaming endpoint (framework-level, available to all agents)
    path(
        "v1/steps/<int:step_id>/logs/stream/",
        stream_step_logs,
        name="stream_step_logs",
    ),
    # Standard Ninja REST API (list/create threads, messages, etc.)
    path("", api.urls),
]

