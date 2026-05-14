"""
Django AI Assistant Callback Infrastructure

This module provides callback handlers for monitoring and logging AI agent execution.
Callbacks hook into the LangChain execution pipeline to capture tool calls, agent actions,
and errors without requiring the AI model to actively log events.
"""

from .base import DjangoAIAssistantCallbackHandler

__all__ = ["DjangoAIAssistantCallbackHandler"]
