"""
Base callback handler for Django AI Assistant framework.

This module defines the abstract base class that all Django AI Assistant callbacks
should inherit from. It provides a standard interface for monitoring and logging
AI agent execution without requiring the AI model to actively call logging methods.
"""

from typing import Any, Optional
from langchain_core.callbacks import BaseCallbackHandler


class DjangoAIAssistantCallbackHandler(BaseCallbackHandler):
    """
    Abstract base class for Django AI Assistant callbacks.
    
    This handler extends LangChain's BaseCallbackHandler to provide a standard
    interface for monitoring AI agent execution in Django projects.
    
    Subclasses should override specific methods to implement custom logging,
    monitoring, or observability logic:
    
    - on_tool_start(): Called when a tool begins execution
    - on_tool_end(): Called when a tool completes successfully
    - on_tool_error(): Called when a tool raises an exception
    - on_agent_action(): Called when an agent chooses an action
    - on_chain_start(): Called when a chain begins execution
    - on_chain_end(): Called when a chain completes
    - on_llm_start(): Called when LLM begins generating
    
    Example:
        class MyCustomHandler(DjangoAIAssistantCallbackHandler):
            def on_tool_start(self, serialized, input_str, **kwargs):
                tool_name = serialized.get("name")
                print(f"Tool started: {tool_name}")
    """
    
    def __init__(self):
        """Initialize the callback handler."""
        super().__init__()
        # Set a descriptive run name for this callback
        self.run_name = "ai_assistant"


class AsyncDjangoAIAssistantCallbackHandler(DjangoAIAssistantCallbackHandler):
    """
    Base class for async-capable Django AI Assistant callbacks.
    
    Subclasses can implement async versions of callback methods.
    """
    pass
