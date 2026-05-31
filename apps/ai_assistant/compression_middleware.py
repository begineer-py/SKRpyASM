"""
Compression Middleware

Automatically triggers compression when messages are added to a thread.
Integrates at the Message model level using Django signals.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.core.models import Thread, Message, ThreadCompressionState

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Message)
def on_message_created(sender, instance: Message, created: bool, **kwargs):
    """
    Signal handler triggered when a Message is created or updated.
    
    Determines if compression is needed and schedules/runs it.
    
    Args:
        sender: Message model class
        instance: The Message instance being saved
        created: Boolean indicating if this is a new message
        **kwargs: Additional signal arguments
    """
    if not created:
        # Only process new messages
        return
    
    try:
        thread = instance.thread
        
        # Lazy import to avoid circular dependencies
        from apps.auto.compression import ContextCompressionManager
        from apps.core.llms import get_llm_instance
        
        # Check if compression should be triggered
        should_compress = _check_compression_needed(thread)
        
        if should_compress:
            logger.info(f"Triggering compression for thread {thread.id} (message {instance.id})")
            
            # For now, run synchronously
            # In production, consider using Celery tasks for async compression
            _compress_thread_async(thread)
    
    except Exception as e:
        logger.error(f"Error in compression signal handler: {e}", exc_info=True)
        # Don't raise - we don't want to break message creation


def _check_compression_needed(thread: Thread) -> bool:
    """
    Check if thread needs compression.
    
    Criteria:
    1. Every 50 messages
    2. When context exceeds 128K tokens
    3. When explicitly flagged
    
    Args:
        thread: Thread to check
    
    Returns:
        True if compression is needed
    """
    try:
        state = thread.compression_state
    except ThreadCompressionState.DoesNotExist:
        # First time - create state but don't compress yet
        ThreadCompressionState.objects.create(thread=thread)
        return False
    
    current_count = thread.messages.count()
    
    # Check message threshold
    if current_count - state.total_message_count >= 50:
        return True
    
    # Check context window flag
    if state.requires_compression:
        return True
    
    return False


def _compress_thread_async(thread: Thread):
    """
    Compress a thread asynchronously or synchronously.
    
    In production, this should use Celery or similar task queue.
    For now, running synchronously with proper error handling.
    
    Args:
        thread: Thread to compress
    """
    try:
        from apps.auto.compression import ContextCompressionManager
        from apps.core.llms import get_llm_instance
        
        # Get LLM instances using factory pattern
        # Using single configured LLM for compression tasks
        # In the future, could use different models based on task complexity
        llm_main = get_llm_instance()  # Use default configured model
        llm_cheap = get_llm_instance()  # Same model for now (cheap variant logic handled in compression)
        
        # Create compression manager
        manager = ContextCompressionManager(
            thread=thread,
            llm_main=llm_main,
            llm_cheap=llm_cheap
        )
        
        # Run compression
        result = manager.compress()
        logger.info(f"Compression result for thread {thread.id}: {result}")
    
    except Exception as e:
        logger.error(f"Error during thread compression: {e}", exc_info=True)


def register_compression_signals():
    """
    Register compression middleware signals.
    
    Call this in apps.py AppConfig.ready() method.
    """
    logger.info("Registering compression middleware signals")
    # Signals are already registered via @receiver decorator
    pass
