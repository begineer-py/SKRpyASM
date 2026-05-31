"""
Step Log Callback Handler for Automation Agent

This module implements a callback handler that automatically logs all tool
calls, agent actions, and errors to the StepLog model.
"""

import logging
from typing import Any, Optional

from apps.ai_assistant.callbacks.base import DjangoAIAssistantCallbackHandler
from apps.core.models import StepLog

logger = logging.getLogger(__name__)


class StepLogCallbackHandler(DjangoAIAssistantCallbackHandler):
    """
    Automatically monitors AI tool execution and records to StepLog model.
    
    This handler hooks into the LangChain execution pipeline to capture:
    - Tool start events: When a tool begins execution
    - Tool end events: When a tool completes successfully
    - Tool errors: When a tool raises an exception
    - Agent actions: When the agent chooses an action to perform
    
    Each event is automatically recorded to the StepLog model without requiring
    the AI to actively call logging methods.
    
    Args:
        step_id: The ID of the Step model to log entries to
    """
    
    def __init__(self, step_id: int):
        """Initialize the callback handler with a step ID.
        
        Args:
            step_id: The ID of the Step instance to associate logs with
            
        Raises:
            ValueError: If step_id is not a valid integer
        """
        super().__init__()
        if not isinstance(step_id, int) or step_id <= 0:
            raise ValueError(f"step_id must be a positive integer, got {step_id}")
        self.step_id = step_id
    
    def on_tool_start(self, serialized: dict[str, Any], input_str: str, **kwargs: Any) -> None:
        """Called when a tool begins execution.
        
        Records an ACTION log entry indicating which tool is being executed.
        
        Args:
            serialized: Serialized tool definition containing 'name' and 'description'
            input_str: String representation of the tool input
            **kwargs: Additional LangChain callback arguments
        """
        try:
            tool_name = serialized.get("name", "unknown_tool")
            tool_description = serialized.get("description", "")
            
            # Log the tool invocation
            StepLog.objects.create(
                step_id=self.step_id,
                level="INFO",
                tag="ACTION",
                message=f"[ACTION] Started execution of tool: {tool_name}",
                action_status="RUNNING"
            )
            
            logger.debug(
                f"[StepLog] Tool START: step_id={self.step_id}, "
                f"tool={tool_name}, input={input_str[:100]}"
            )
        except Exception as e:
            logger.error(f"[StepLog] Failed to log tool start for step {self.step_id}: {e}")
    
    def on_tool_end(self, output: Any, **kwargs: Any) -> None:
        """Called when a tool completes successfully.
        
        Records a RESULT log entry with the tool's output.
        
        Args:
            output: The return value from the tool
            **kwargs: Additional LangChain callback arguments
        """
        try:
            output_str = str(output)
            # Truncate very long outputs to prevent bloating the database
            if len(output_str) > 2000:
                output_str = output_str[:2000] + "... [truncated]"
            
            StepLog.objects.create(
                step_id=self.step_id,
                level="INFO",
                tag="RESULT",
                message=f"[RESULT] Tool execution completed successfully. Output: {output_str}",
                action_status="SUCCESS"
            )
            
            logger.debug(f"[StepLog] Tool END: step_id={self.step_id}, output_len={len(str(output))}")
        except Exception as e:
            logger.error(f"[StepLog] Failed to log tool end for step {self.step_id}: {e}")
    
    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when a tool raises an exception.
        
        Records an ERROR log entry with the exception details.
        
        Args:
            error: The exception raised by the tool
            **kwargs: Additional LangChain callback arguments
        """
        try:
            error_str = str(error)
            # Truncate very long error messages
            if len(error_str) > 2000:
                error_str = error_str[:2000] + "... [truncated]"
            
            StepLog.objects.create(
                step_id=self.step_id,
                level="ERROR",
                tag="ERROR",
                message=f"[ERROR] Tool execution failed: {error_str}",
                action_status="FAILED"
            )
            
            logger.warning(f"[StepLog] Tool ERROR: step_id={self.step_id}, error={error_str[:100]}")
        except Exception as e:
            logger.error(f"[StepLog] Failed to log tool error for step {self.step_id}: {e}")
    
    def on_agent_action(self, action: Any, **kwargs: Any) -> None:
        """Called when the agent chooses an action to perform.
        
        Records an AI_THOUGHT log entry capturing the agent's decision-making.
        
        Args:
            action: The action object chosen by the agent, containing 'tool' and 'tool_input'
            **kwargs: Additional LangChain callback arguments
        """
        try:
            tool_name = getattr(action, "tool", "unknown")
            tool_input = getattr(action, "tool_input", {})
            
            # Convert tool_input to string representation
            input_str = str(tool_input)
            if len(input_str) > 500:
                input_str = input_str[:500] + "... [truncated]"
            
            StepLog.objects.create(
                step_id=self.step_id,
                level="DEBUG",
                tag="AI_THOUGHT",
                message=f"[AI_THOUGHT] Agent chose action: tool={tool_name}, input={input_str}"
            )
            
            logger.debug(f"[StepLog] Agent ACTION: step_id={self.step_id}, tool={tool_name}")
        except Exception as e:
            logger.error(f"[StepLog] Failed to log agent action for step {self.step_id}: {e}")
    
    def on_chain_start(self, serialized: dict[str, Any], inputs: dict[str, Any], **kwargs: Any) -> None:
        """Called when a chain begins execution.
        
        Can be used for additional observability if needed. Currently logs at DEBUG level.
        
        Args:
            serialized: Serialized chain definition
            inputs: Input to the chain
            **kwargs: Additional LangChain callback arguments
        """
        try:
            chain_name = serialized.get("name", "unknown_chain") if serialized else "unknown_chain"
            logger.debug(f"[StepLog] Chain START: step_id={self.step_id}, chain={chain_name}")
        except Exception as e:
            logger.error(f"[StepLog] Failed to log chain start for step {self.step_id}: {e}")
    
    def on_chain_end(self, outputs: dict[str, Any], **kwargs: Any) -> None:
        """Called when a chain completes successfully.
        
        Can be used for additional observability if needed. Currently logs at DEBUG level.
        
        Args:
            outputs: Output from the chain
            **kwargs: Additional LangChain callback arguments
        """
        try:
            logger.debug(f"[StepLog] Chain END: step_id={self.step_id}")
        except Exception as e:
            logger.error(f"[StepLog] Failed to log chain end for step {self.step_id}: {e}")
