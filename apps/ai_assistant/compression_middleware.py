"""
Compression Middleware

Monitors message creation and flags threads when compression is needed.
The agent itself decides when and how to compress via compress_history tools.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.models import ThreadCompressionState

logger = logging.getLogger(__name__)

FLAG_THRESHOLD = 40


@receiver(post_save, sender="core.Message")
def on_message_created(sender, instance, created: bool, **kwargs):
    """Signal handler: flags thread when message threshold is exceeded."""
    if not created:
        return

    try:
        thread = instance.thread
        state, _ = ThreadCompressionState.objects.get_or_create(thread=thread)

        current_count = thread.messages.count()

        if current_count - state.total_message_count >= FLAG_THRESHOLD:
            state.requires_compression = True
            state.save(update_fields=["requires_compression"])
            logger.info(
                f"[CompressionMiddleware] Flagged Thread#{thread.id} "
                f"({current_count} messages, {current_count - state.total_message_count} since last compress)"
            )

    except Exception as e:
        logger.error(f"Error in compression signal handler: {e}", exc_info=True)


def register_compression_signals():
    """Register compression middleware signals."""
    logger.info("Registering compression middleware signals")
