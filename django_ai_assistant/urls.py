from django.urls import path

from django_ai_assistant.api.views import api
from django_ai_assistant.api.stream_views import stream_thread_message


urlpatterns = [
    # SSE streaming endpoint — MUST come before api.urls so Django matches it first
    path(
        "threads/<int:thread_id>/messages/stream/",
        stream_thread_message,
        name="stream_thread_message",
    ),
    # Standard Ninja REST API (list/create threads, messages, etc.)
    path("", api.urls),
]

