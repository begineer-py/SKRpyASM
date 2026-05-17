import logging
from typing import Any, Set

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage, ToolMessage
from django_ai_assistant.helpers.django_messages import save_django_messages
from django_ai_assistant.models import Thread, Message

logger = logging.getLogger(__name__)


class ThreadCheckpointHandler(BaseCallbackHandler):
    """
    Incrementally saves AI conversation messages to the Django Thread after each step.
    
    Without this handler, messages are only saved when the entire LangGraph finishes
    (in 'record_response'). If the graph errors or times out mid-execution, all 
    messages from that session are lost — the AI forgets everything it did.
    
    This handler saves messages after EVERY agent and tool step, so even if the
    graph is interrupted later, partial progress is preserved in the Thread.
    """

    def __init__(self, thread: Thread):
        super().__init__()
        self.thread = thread
        self.run_name = "thread_checkpoint"
        self._saved_ids: Set[str] = set(
            str(i) for i in Message.objects.filter(thread=thread).values_list("id", flat=True)
        )

    def _save_new_messages(self, messages: list) -> None:
        new_msgs = [m for m in messages if hasattr(m, 'id') and m.id not in self._saved_ids]
        if not new_msgs:
            return
        try:
            saved = save_django_messages(new_msgs, thread=self.thread)
            for s in saved:
                self._saved_ids.add(str(s.id))
            logger.debug(f"[Checkpoint] Saved {len(saved)} new message(s) to thread {self.thread.id}")
        except Exception as e:
            logger.warning(f"[Checkpoint] Failed to save messages: {e}")

    def on_chain_end(self, outputs: Any, **kwargs: Any) -> None:
        if not isinstance(outputs, dict):
            return
        messages = outputs.get("messages", [])
        if not messages:
            return
        # Only save AI and Tool messages — skip Human/System-only batches
        has_ai_or_tool = any(isinstance(m, (AIMessage, ToolMessage)) for m in messages)
        if has_ai_or_tool:
            self._save_new_messages(messages)

    def on_chain_error(self, error: BaseException, **kwargs: Any) -> None:
        logger.warning(f"[Checkpoint] Chain error (preserving previously saved messages): {error}")
