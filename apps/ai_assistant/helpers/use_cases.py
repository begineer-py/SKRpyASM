from typing import Any

from django.http import HttpRequest

from langchain_core.messages import BaseMessage
from langchain_core.messages import HumanMessage

from apps.ai_assistant.exceptions import (
    AIAssistantNotDefinedError,
    AIUserNotAllowedError,
)
from apps.ai_assistant.helpers.assistants import AIAssistant
from apps.ai_assistant.helpers.django_messages import save_django_messages
from apps.core.models import Message, Thread
from apps.ai_assistant.permissions import (
    can_create_message,
    can_create_thread,
    can_delete_message,
    can_delete_thread,
    can_run_assistant,
    can_update_thread,
    can_view_thread,
)


def get_assistant_cls(
    assistant_id: str,
    user: Any,
    request: HttpRequest | None = None,
) -> type[AIAssistant]:
    """Get assistant class by id.\n
    Uses `AI_ASSISTANT_CAN_RUN_ASSISTANT_FN` permission to check if user can run the assistant.

    Args:
        assistant_id (str): Assistant id to get
        user (Any): Current user
        request (HttpRequest | None): Current request, if any
    Returns:
        type[AIAssistant]: Assistant class with the given id
    Raises:
        AIAssistantNotDefinedError: If assistant with the given id is not found
        AIUserNotAllowedError: If user is not allowed to use the assistant
    """
    if assistant_id not in AIAssistant.get_cls_registry():
        raise AIAssistantNotDefinedError(f"Assistant with id={assistant_id} not found")
    assistant_cls = AIAssistant.get_cls(assistant_id)
    if not can_run_assistant(
        assistant_cls=assistant_cls,
        user=user,
        request=request,
    ):
        raise AIUserNotAllowedError("User is not allowed to use this assistant")
    return assistant_cls


def get_single_assistant_info(
    assistant_id: str,
    user: Any,
    request: HttpRequest | None = None,
) -> dict[str, str]:
    """Get assistant info id. Returns a dictionary with the assistant id and name.\n
    Uses `AI_ASSISTANT_CAN_RUN_ASSISTANT_FN` permission to check if user can see the assistant.

    Args:
        assistant_id (str): Assistant id to get
        user (Any): Current user
        request (HttpRequest | None): Current request, if any
    Returns:
        dict[str, str]: dict like `{"id": "personal_ai", "name": "Personal AI"}`
    Raises:
        AIAssistantNotDefinedError: If assistant with the given id is not found
        AIUserNotAllowedError: If user is not allowed to see the assistant
    """
    assistant_cls = get_assistant_cls(assistant_id, user, request)

    return {
        "id": assistant_id,
        "name": assistant_cls.name,
    }


def get_assistants_info(
    user: Any,
    request: HttpRequest | None = None,
) -> list[dict[str, str]]:
    """Get all assistants info. Returns a list of dictionaries with the assistant id and name.\n
    Uses `AI_ASSISTANT_CAN_RUN_ASSISTANT_FN` permission to check the assistants the user can see,
    and returns only the ones the user can see.

    Args:
        user (Any): Current user
        request (HttpRequest | None): Current request, if any
    Returns:
        list[dict[str, str]]: List of dicts like `[{"id": "personal_ai", "name": "Personal AI"}, ...]`
    """
    assistant_info_list = []
    for assistant_id in AIAssistant.get_cls_registry().keys():
        try:
            info = get_single_assistant_info(assistant_id, user, request)
            assistant_info_list.append(info)
        except AIUserNotAllowedError:
            continue
    return assistant_info_list


def create_message(
    assistant_id: str,
    thread: Thread,
    user: Any,
    content: Any,
    request: HttpRequest | None = None,
) -> dict:
    """Create a message in a thread, and right after runs the assistant to get the AI response.\n
    Uses `AI_ASSISTANT_CAN_RUN_ASSISTANT_FN` permission to check if user can run the assistant.\n
    Uses `AI_ASSISTANT_CAN_CREATE_MESSAGE_FN` permission to check if user can create a message in the thread.

    Args:
        assistant_id (str): Assistant id to use to get the AI response
        thread (Thread): Thread where to create the message
        user (Any): Current user
        content (Any): Message content, usually a string
        request (HttpRequest | None): Current request, if any
    Returns:
        dict: The output of the assistant,
            structured like `{"output": "assistant response", "history": ...}`
    Raises:
        AIUserNotAllowedError: If user is not allowed to create messages in the thread
    """
    assistant_cls = get_assistant_cls(assistant_id, user, request)

    if not can_create_message(thread=thread, user=user, request=request):
        raise AIUserNotAllowedError("User is not allowed to create messages in this thread")

    # Store the user's input before graph execution so failed runs remain visible.
    save_django_messages([HumanMessage(content=content)], thread=thread)

    assistant = assistant_cls(user=user, request=request)
    assistant_message = assistant.invoke(
        {"input": content},
        thread_id=thread.id,
    )
    return assistant_message


def create_thread(
    name: str,
    user: Any,
    assistant_id: str | None = None,
    request: HttpRequest | None = None,
    is_hidden: bool = False,
) -> Thread:
    """Create a thread.\n
    Uses `AI_ASSISTANT_CAN_CREATE_THREAD_FN` permission to check if user can create a thread.

    Args:
        name (str): Thread name
        assistant_id (str | None): Assistant ID to associate the thread with.
            If empty or None, the thread is not associated with any assistant.
        user (Any): Current user
        request (HttpRequest | None): Current request, if any
        is_hidden (bool): Whether this thread is an internal/system thread hidden from the UI by default
    Returns:
        Thread: Created thread model instance
    Raises:
        AIUserNotAllowedError: If user is not allowed to create threads
    """
    if not can_create_thread(user=user, request=request):
        raise AIUserNotAllowedError("User is not allowed to create threads")

    thread = Thread.objects.create(name=name, created_by=user, assistant_id=assistant_id or "", is_hidden=is_hidden)
    return thread


def get_single_thread(
    thread_id: Any,
    user: Any,
    request: HttpRequest | None = None,
) -> Thread:
    """Get a single thread by id.\n
    Uses `AI_ASSISTANT_CAN_VIEW_THREAD_FN` permission to check if user can view the thread.

    Args:
        thread_id (str): Thread id to get
        user (Any): Current user
        request (HttpRequest | None): Current request, if any
    Returns:
        Thread: Thread model instance
    Raises:
        AIUserNotAllowedError: If user is not allowed to view the thread
    """
    thread = Thread.objects.get(id=thread_id)

    if not can_view_thread(thread=thread, user=user, request=request):
        raise AIUserNotAllowedError("User is not allowed to view this thread")

    return thread


def get_threads(
    user: Any,
    assistant_id: str | None = None,
    bound_target_id: int | None = None,
    request: HttpRequest | None = None,
    include_hidden: bool = False,
) -> list[Thread]:
    """Get all threads for the user.\n
    Uses `AI_ASSISTANT_CAN_VIEW_THREAD_FN` permission to check the threads the user can see,
    and returns only the ones the user can see.

    Args:
        user (Any): Current user
        assistant_id (str | None): Assistant ID to filter threads by.
            If empty or None, all threads for the user are returned.
        bound_target_id (int | None): Target ID to filter threads by.
        request (HttpRequest | None): Current request, if any
        include_hidden (bool): Whether to include internal/hidden threads.
    Returns:
        list[Thread]: List of thread model instances
    """
    threads = Thread.objects.filter(created_by=user)

    if not include_hidden:
        threads = threads.filter(is_hidden=False)

    if assistant_id:
        threads = threads.filter(assistant_id=assistant_id)
    
    if bound_target_id:
        threads = threads.filter(bound_target_id=bound_target_id)

    return list(
        threads.filter(
            id__in=[
                thread.id
                for thread in threads
                if can_view_thread(thread=thread, user=user, request=request)
            ]
        )
    )


def update_thread(
    thread: Thread,
    name: str,
    user: Any,
    request: HttpRequest | None = None,
) -> Thread:
    """Update thread name.\n
    Uses `AI_ASSISTANT_CAN_UPDATE_THREAD_FN` permission to check if user can update the thread.

    Args:
        thread (Thread): Thread model instance to update
        name (str): New thread name
        user (Any): Current user
        request (HttpRequest | None): Current request, if any
    Returns:
        Thread: Updated thread model instance
    Raises:
        AIUserNotAllowedError: If user is not allowed to update the thread
    """
    if not can_update_thread(thread=thread, user=user, request=request):
        raise AIUserNotAllowedError("User is not allowed to update this thread")

    thread.name = name
    thread.save()
    return thread


def delete_thread(
    thread: Thread,
    user: Any,
    request: HttpRequest | None = None,
) -> None:
    """Delete a thread.\n
    Uses `AI_ASSISTANT_CAN_DELETE_THREAD_FN` permission to check if user can delete the thread.

    Args:
        thread (Thread): Thread model instance to delete
        user (Any): Current user
        request (HttpRequest | None): Current request, if any
    Raises:
        AIUserNotAllowedError: If user is not allowed to delete the thread
    """
    if not can_delete_thread(thread=thread, user=user, request=request):
        raise AIUserNotAllowedError("User is not allowed to delete this thread")

    thread.delete()


def get_thread_messages(
    thread: Thread,
    user: Any,
    request: HttpRequest | None = None,
    include_extra_messages: bool = False,
) -> list[BaseMessage]:
    """Get all messages in a thread.

    Uses `AI_ASSISTANT_CAN_VIEW_THREAD_FN` permission to check if user can view the thread.
    By default, excludes system and tool messages (include_extra_messages=False).
    Pass include_extra_messages=True (API: ?include_tools=true) to include tool_call / tool_result.

    Args:
        thread (Thread): Thread model instance to get messages from
        user (Any): Current user
        request (HttpRequest | None): Current request, if any
        include_extra_messages (bool): Whether to include tool/system messages
    Returns:
        list[BaseMessage]: List of message instances
    """
    # TODO: have more permissions for threads? View thread permission?
    if user != thread.created_by:
        raise AIUserNotAllowedError("User is not allowed to view messages in this thread")

    return thread.get_messages(include_extra_messages=include_extra_messages)


def delete_message(
    message: Message,
    user: Any,
    request: HttpRequest | None = None,
):
    """Delete a message.\n
    Uses `AI_ASSISTANT_CAN_DELETE_MESSAGE_FN` permission to check if user can delete the message.

    Args:
        message (Message): Message model instance to delete
        user (Any): Current user
        request (HttpRequest | None): Current request, if any
    Raises:
        AIUserNotAllowedError: If user is not allowed to delete the message
    """
    if not can_delete_message(message=message, user=user, request=request):
        raise AIUserNotAllowedError("User is not allowed to delete this message")

    return message.delete()
