from typing import TYPE_CHECKING

from django.db import connections, transaction

from langchain_core.messages import (
    BaseMessage,
    message_to_dict,
)


if TYPE_CHECKING:
    from django_ai_assistant.models import Message as DjangoMessage
    from django_ai_assistant.models import Thread


@transaction.atomic
def save_django_messages(messages: list[BaseMessage], thread: "Thread") -> list["DjangoMessage"]:
    """
    Save a list of messages to the Django database.
    Note: Changes the message objects in place by changing each message.id to the Django ID.

    Args:
        messages (list[BaseMessage]): The list of messages to save.
        thread (Thread): The thread to save the messages to.
    """

    from django_ai_assistant.models import Message as DjangoMessage

    existing_message_ids = [
        str(i)
        for i in DjangoMessage.objects.filter(thread=thread)
        .order_by("created_at")
        .values_list("id", flat=True)
    ]

    messages_to_create = [m for m in messages if m.id not in existing_message_ids]

    # Insert in bulk only if primary keys are then assigned by the DB.
    # Please check https://docs.djangoproject.com/en/4.0/ref/models/querysets/#django.db.models.query.QuerySet.bulk_create
    # for more context on why this is required
    can_bulk_insert = connections[
        DjangoMessage.objects.db
    ].features.can_return_rows_from_bulk_insert
    if can_bulk_insert:
        created_messages = DjangoMessage.objects.bulk_create(
            [DjangoMessage(thread=thread, message={}) for _ in messages_to_create],
        )
    else:
        for message in (
            created_messages := [
                DjangoMessage(thread=thread, message={}) for _ in messages_to_create
            ]
        ):
            message.save()

    # Update langchain message IDs with Django message IDs
    for idx, created_message in enumerate(created_messages):
        message_with_id = messages_to_create[idx]
        message_with_id.id = str(created_message.id)
        created_message.message = message_to_dict(message_with_id)

    DjangoMessage.objects.bulk_update(created_messages, ["message"])
    return created_messages
