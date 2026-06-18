from typing import Any, List

from django.http import Http404
from django.shortcuts import get_object_or_404

from langchain_core.messages import message_to_dict
from ninja import NinjaAPI, Schema
from ninja.operation import Operation
from ninja.security import django_auth

from apps.ai_assistant import PACKAGE_NAME, VERSION
from apps.ai_assistant.api.schemas import (
    Assistant,
    Thread,
    ThreadIn,
    ThreadMessage,
    ThreadMessageIn,
)
from apps.ai_assistant.conf import app_settings
from apps.ai_assistant.decorators import with_cast_id
from apps.ai_assistant.exceptions import AIAssistantNotDefinedError, AIUserNotAllowedError
from apps.ai_assistant.helpers import use_cases
from apps.core.models import Message as MessageModel
from apps.core.models import Thread as ThreadModel
from apps.core.models import ThreadEvent
from apps.core.schemas import ThreadEventSchema


class API(NinjaAPI):
    # Force "operationId" to be like "ai_delete_thread"
    def get_openapi_operation_id(self, operation: Operation) -> str:
        name = operation.view_func.__name__
        return ("ai_" + name).replace(".", "_")


def dummy_auth(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.first()
        if not user:
            user = User.objects.create(username="anonymous_dummy")
        request.user = user
    except Exception:
        pass
    return "anonymous"


def init_api():
    return API(
        title=PACKAGE_NAME,
        version=VERSION,
        urls_namespace="ai_assistant",
        # Remove auth completely for testing as requested
        auth=dummy_auth,
    )


api = app_settings.call_fn("INIT_API_FN")


@api.exception_handler(AIUserNotAllowedError)
def ai_user_not_allowed_handler(request, exc):
    return api.create_response(
        request,
        {"message": str(exc)},
        status=403,
    )


@api.exception_handler(AIAssistantNotDefinedError)
def ai_assistant_not_defined_handler(request, exc):
    return api.create_response(
        request,
        {"message": str(exc)},
        status=404,
    )


@api.get("assistants/", response=List[Assistant], url_name="assistants_list")
def list_assistants(request):
    return list(use_cases.get_assistants_info(user=request.user, request=request))


@api.get("assistants/{assistant_id}/", response=Assistant, url_name="assistant_detail")
def get_assistant(request, assistant_id: str):
    return use_cases.get_single_assistant_info(
        assistant_id=assistant_id, user=request.user, request=request
    )


@api.get("threads/", response=List[Thread], url_name="threads_list_create")
def list_threads(request, assistant_id: str | None = None, target_id: int | None = None, include_hidden: bool = True):
    return list(use_cases.get_threads(user=request.user, assistant_id=assistant_id, bound_target_id=target_id, include_hidden=include_hidden))


@api.post("threads/", response=Thread, url_name="threads_list_create")
def create_thread(request, payload: ThreadIn):
    name = payload.name
    assistant_id = payload.assistant_id
    return use_cases.create_thread(
        name=name, assistant_id=assistant_id, user=request.user, request=request
    )


@api.get("threads/{thread_id}/", response=Thread, url_name="thread_detail_update_delete")
@with_cast_id
def get_thread(request, thread_id: Any):
    try:
        thread = use_cases.get_single_thread(
            thread_id=thread_id, user=request.user, request=request
        )
    except ThreadModel.DoesNotExist:
        raise Http404(f"No Thread with id={thread_id} found") from None
    return thread


@api.patch("threads/{thread_id}/", response=Thread, url_name="thread_detail_update_delete")
@with_cast_id
def update_thread(request, thread_id: Any, payload: ThreadIn):
    thread = get_object_or_404(ThreadModel, id=thread_id)
    name = payload.name
    return use_cases.update_thread(thread=thread, name=name, user=request.user, request=request)


@api.delete("threads/{thread_id}/", response={204: None}, url_name="thread_detail_update_delete")
@with_cast_id
def delete_thread(request, thread_id: Any):
    thread = get_object_or_404(ThreadModel, id=thread_id)
    use_cases.delete_thread(thread=thread, user=request.user, request=request)
    return 204, None


@api.get(
    "threads/{thread_id}/messages/",
    response=List[ThreadMessage],
    url_name="messages_list_create",
)
@with_cast_id
def list_thread_messages(request, thread_id: Any):
    thread = get_object_or_404(ThreadModel, id=thread_id)
    messages = use_cases.get_thread_messages(thread=thread, user=request.user, request=request)
    return [message_to_dict(m)["data"] for m in messages]


# TODO: Support content streaming
@api.post(
    "threads/{thread_id}/messages/",
    response={201: None},
    url_name="messages_list_create",
)
@with_cast_id
def create_thread_message(request, thread_id: Any, payload: ThreadMessageIn):
    thread = ThreadModel.objects.get(id=thread_id)

    use_cases.create_message(
        assistant_id=payload.assistant_id,
        thread=thread,
        user=request.user,
        content=payload.content,
        request=request,
    )
    return 201, None


@api.delete(
    "threads/{thread_id}/messages/{message_id}/", response={204: None}, url_name="messages_delete"
)
@with_cast_id
def delete_thread_message(request, thread_id: Any, message_id: Any):
    message = get_object_or_404(MessageModel, id=message_id, thread_id=thread_id)
    use_cases.delete_message(
        message=message,
        user=request.user,
        request=request,
    )
    return 204, None


# ── Thread Events ────────────────────────────────────────────────────────


@api.get(
    "threads/{thread_id}/events/",
    response=List[ThreadEventSchema],
    url_name="thread_events_list",
)
@with_cast_id
def list_thread_events(request, thread_id: Any, after: int = 0, limit: int = 500):
    get_object_or_404(ThreadModel, id=thread_id)
    limit = max(1, min(limit, 500))
    return list(
        ThreadEvent.objects.filter(
            thread_id=thread_id,
            sequence__gt=max(after, 0),
        )
        .order_by("sequence", "id")[:limit]
    )


# ── Target Binding Endpoints ───────────────────────────────────────────────

class BindTargetIn(Schema):
    target_id: int


@api.patch(
    "threads/{thread_id}/bind_target/",
    response=Thread,
    url_name="thread_bind_target",
)
@with_cast_id
def bind_target(request, thread_id: Any, payload: BindTargetIn):
    """Bind a target to a thread. The AI agent will use this target by default."""
    thread = get_object_or_404(ThreadModel, id=thread_id)
    thread.bound_target_id = payload.target_id
    thread.save(update_fields=["bound_target_id", "updated_at"])
    return thread


@api.delete(
    "threads/{thread_id}/bind_target/",
    response={200: Thread},
    url_name="thread_unbind_target",
)
@with_cast_id
def unbind_target(request, thread_id: Any):
    """Remove the target binding from a thread."""
    thread = get_object_or_404(ThreadModel, id=thread_id)
    thread.bound_target_id = None
    thread.save(update_fields=["bound_target_id", "updated_at"])
    return 200, thread
