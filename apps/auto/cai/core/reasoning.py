"""
apps/auto/cai/core/reasoning.py

A simple tool for the agent to log its reasoning steps.
"""

import logging
from .tool import function_tool

logger = logging.getLogger(__name__)

@function_tool
def reasoning(thought: str) -> str:
    """
    Log a thought or reasoning step.
    
    Args:
        thought: The thought to record.
        
    Returns:
        A confirmation message.
    """
    logger.info(f"Agent Reasoning: {thought}")
    return f"Reasoning recorded: {thought[:50]}..."
