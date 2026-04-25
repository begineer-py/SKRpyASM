"""
Auto App Configuration and Feature Flags

This module contains configuration and feature flags for the Auto app,
including the LangChain migration feature flags for progressive rollout.

Phase 0 - Foundation Setup
- Feature flags for enabling LangChain components
- Configuration for selective agent migration
- LangSmith tracing controls
"""

from __future__ import annotations

import os
from typing import List, Dict, Any
from django.conf import settings


class AutoAppConfig:
    """
    Auto App Configuration
    
    Controls feature flags for LangChain migration and other experimental features.
    Uses environment variables for configuration with sensible defaults.
    """
    
    # ============================================================================
    # LangChain Migration Feature Flags (Phase 0)
    # ============================================================================
    
    # Main feature flag - Enable LangChain integration
    # When True, allows use of new LangChain-based agents alongside existing CAI agents
    USE_LANGCHAIN: bool = os.getenv("AUTO_USE_LANGCHAIN", "false").lower() == "true"
    
    # Enable LangSmith tracing for observability
    # Provides detailed tracing of agent decision-making processes
    USE_LANGSMITH_TRACING: bool = os.getenv("AUTO_USE_LANGSMITH_TRACING", "false").lower() == "true"
    
    # Enable LangGraph workflow orchestration
    # For multi-agent state machine workflows (Phase 4 feature)
    USE_LANGGRAPH_WORKFLOW: bool = os.getenv("AUTO_USE_LANGGRAPH_WORKFLOW", "false").lower() == "true"
    
    # Selective agent migration - list of agents to use LangChain for
    # Options: "ReconAgent", "ExploitAgent", "AutomationAgent", "StrategyAgent"
    # Empty list = use CAI for all agents
    # ["ReconAgent"] = use LangChain only for ReconAgent, CAI for others
    LANGCHAIN_AGENTS: List[str] = [
        agent.strip() 
        for agent in os.getenv("AUTO_LANGCHAIN_AGENTS", "").split(",") 
        if agent.strip()
    ]
    
    # ============================================================================
    # LangChain/LangSmith Configuration
    # ============================================================================
    
    # LangSmith API configuration
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "c2-django-ai-auto")
    LANGCHAIN_ENDPOINT: str = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    
    # LangSmith tracing configuration
    LANGCHAIN_TRACING_V2: bool = USE_LANGSMITH_TRACING
    
    # ============================================================================
    # Existing CAI Framework Configuration (Preserved)
    # ============================================================================
    
    # Default LLM provider for CAI agents
    # Options: "openai", "anthropic", "litellm"
    DEFAULT_LLM_PROVIDER: str = os.getenv("AUTO_DEFAULT_LLM_PROVIDER", "openai")
    
    # Default model for each provider
    DEFAULT_MODELS: Dict[str, str] = {
        "openai": os.getenv("AUTO_OPENAI_MODEL", "gpt-4-turbo-preview"),
        "anthropic": os.getenv("AUTO_ANTHROPIC_MODEL", "claude-3-opus-20240229"),
        "litellm": os.getenv("AUTO_LITELLM_MODEL", "gpt-4-turbo-preview"),
    }
    
    # Temperature for AI responses
    DEFAULT_TEMPERATURE: float = float(os.getenv("AUTO_DEFAULT_TEMPERATURE", "0.7"))
    
    # Maximum tokens for AI responses
    DEFAULT_MAX_TOKENS: int = int(os.getenv("AUTO_DEFAULT_MAX_TOKENS", "4096"))
    
    # Tool calling configuration
    MAX_TOOL_ITERATIONS: int = int(os.getenv("AUTO_MAX_TOOL_ITERATIONS", "10"))
    TOOL_EXECUTION_TIMEOUT: int = int(os.getenv("AUTO_TOOL_EXECUTION_TIMEOUT", "300"))  # seconds
    
    # ============================================================================
    # Helper Methods
    # ============================================================================
    
    @classmethod
    def is_langchain_enabled_for_agent(cls, agent_name: str) -> bool:
        """
        Check if LangChain is enabled for a specific agent.
        
        Args:
            agent_name: Name of the agent (e.g., "ReconAgent")
            
        Returns:
            True if LangChain should be used for this agent, False otherwise
        """
        if not cls.USE_LANGCHAIN:
            return False
        
        # If no agents specified, don't use LangChain for any
        if not cls.LANGCHAIN_AGENTS:
            return False
        
        # Check if this specific agent is in the list
        return agent_name in cls.LANGCHAIN_AGENTS
    
    @classmethod
    def get_langchain_config(cls) -> Dict[str, Any]:
        """
        Get LangChain configuration as a dictionary.
        
        Returns:
            Dictionary with LangChain configuration
        """
        return {
            "use_langchain": cls.USE_LANGCHAIN,
            "use_langsmith_tracing": cls.USE_LANGSMITH_TRACING,
            "use_langgraph_workflow": cls.USE_LANGGRAPH_WORKFLOW,
            "langchain_agents": cls.LANGCHAIN_AGENTS,
            "langchain_api_key": cls.LANGCHAIN_API_KEY,
            "langchain_project": cls.LANGCHAIN_PROJECT,
            "langchain_endpoint": cls.LANGCHAIN_ENDPOINT,
        }
    
    @classmethod
    def get_cai_config(cls) -> Dict[str, Any]:
        """
        Get CAI framework configuration as a dictionary.
        
        Returns:
            Dictionary with CAI configuration
        """
        return {
            "default_llm_provider": cls.DEFAULT_LLM_PROVIDER,
            "default_models": cls.DEFAULT_MODELS,
            "default_temperature": cls.DEFAULT_TEMPERATURE,
            "default_max_tokens": cls.DEFAULT_MAX_TOKENS,
            "max_tool_iterations": cls.MAX_TOOL_ITERATIONS,
            "tool_execution_timeout": cls.TOOL_EXECUTION_TIMEOUT,
        }
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """
        Validate configuration and return list of warnings/errors.
        
        Returns:
            List of validation messages (empty if all valid)
        """
        messages = []
        
        # Check LangSmith configuration if tracing is enabled
        if cls.USE_LANGSMITH_TRACING and not cls.LANGCHAIN_API_KEY:
            messages.append(
                "WARNING: USE_LANGSMITH_TRACING is enabled but LANGCHAIN_API_KEY is not set. "
                "Tracing will not work."
            )
        
        # Check if agents are valid
        valid_agents = {"ReconAgent", "ExploitAgent", "AutomationAgent", "StrategyAgent"}
        for agent in cls.LANGCHAIN_AGENTS:
            if agent not in valid_agents:
                messages.append(
                    f"WARNING: Unknown agent '{agent}' in LANGCHAIN_AGENTS. "
                    f"Valid options: {valid_agents}"
                )
        
        return messages


# Export configuration instance
config = AutoAppConfig()

# Validate on import and log warnings
validation_messages = config.validate_config()
if validation_messages:
    import logging
    logger = logging.getLogger(__name__)
    for msg in validation_messages:
        logger.warning(msg)
