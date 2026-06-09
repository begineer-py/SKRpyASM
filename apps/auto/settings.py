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
import logging
from typing import List, Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


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
    # Options: "openai", "anthropic", "litellm", "mistral", "deepseek", "ollama"
    DEFAULT_LLM_PROVIDER: str = os.getenv("AUTO_DEFAULT_LLM_PROVIDER", "openai")
    
    # Default model for each provider
    DEFAULT_MODELS: Dict[str, str] = {
        "openai": os.getenv("AUTO_OPENAI_MODEL", "gpt-4-turbo-preview"),
        "anthropic": os.getenv("AUTO_ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        "litellm": os.getenv("AUTO_LITELLM_MODEL", "gpt-4-turbo-preview"),
        "mistral": os.getenv("AUTO_MISTRAL_MODEL", "mistral-small-2603"),
        "deepseek": os.getenv("AUTO_DEEPSEEK_MODEL", "deepseek-chat"),
        "ollama": os.getenv("AUTO_OLLAMA_MODEL", "llama3"),
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
    def get_agent_config(cls, agent_id: str) -> Dict[str, Any]:
        """
        取得指定 agent 的有效配置。

        優先級：DB (AgentLLMConfig UI 設定) > 全域默認值
        Agent 定義在代碼中，無需 per-agent env var。
        """
        db_provider = db_model = db_temperature = db_api_base_url = db_api_key = None
        try:
            from apps.api_keys.models import AgentLLMConfig
            db_cfg = (
                AgentLLMConfig.objects
                .filter(agent_id=agent_id, is_active=True)
                .select_related("api_key_ref")
                .first()
            )
            if db_cfg:
                db_provider = db_cfg.provider or None
                db_model = db_cfg.model_name or None
                db_temperature = db_cfg.temperature
                db_api_base_url = db_cfg.api_base_url or None
                if db_cfg.api_key_ref and db_cfg.api_key_ref.is_active:
                    db_api_key = db_cfg.api_key_ref.get_key()
                    if db_api_key:
                        logger.debug(
                            "get_agent_config: agent='%s' using api_key_ref (id=%s) with non-empty key",
                            agent_id, db_cfg.api_key_ref.pk,
                        )
                    else:
                        logger.warning(
                            "get_agent_config: agent='%s' api_key_ref (id=%s) exists but key_value is empty",
                            agent_id, db_cfg.api_key_ref.pk,
                        )
                else:
                    logger.debug(
                        "get_agent_config: agent='%s' has no api_key_ref, will fall back to global key",
                        agent_id,
                    )
            else:
                logger.debug(
                    "get_agent_config: No AgentLLMConfig row for agent='%s', using class defaults",
                    agent_id,
                )
        except Exception as e:
            logger.warning(f"get_agent_config: DB 查詢失敗 agent_id='{agent_id}': {e}")

        provider = db_provider or cls.DEFAULT_LLM_PROVIDER
        model = db_model or cls.DEFAULT_MODELS.get(provider)
        temperature = db_temperature if db_temperature is not None else cls.DEFAULT_TEMPERATURE

        # 若 agent 未直接綁定 APIKey（api_key_ref=None），從全域 provider key store 補齊
        if not db_api_key:
            try:
                from apps.api_keys.utils import get_ai_provider_key
                provider_key = get_ai_provider_key(provider)
                db_api_key = provider_key or None
                if db_api_key:
                    logger.debug(
                        "get_agent_config: agent='%s' resolved global key for provider='%s'",
                        agent_id, provider,
                    )
                else:
                    logger.warning(
                        "get_agent_config: agent='%s' no global key for provider='%s'",
                        agent_id, provider,
                    )
            except Exception as e:
                logger.warning(f"get_agent_config: 全域金鑰查詢失敗 provider='{provider}': {e}")

        return {
            "model": model,
            "provider": provider,
            "temperature": temperature,
            "api_key": db_api_key,
            "api_base_url": db_api_base_url,
        }

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
    def get_all_agent_configs(cls) -> Dict[str, Dict[str, Any]]:
        from apps.auto.agent_registry import discover_agent_ids
        return {agent_id: cls.get_agent_config(agent_id) for agent_id in discover_agent_ids()}

    @classmethod
    def validate_config(cls) -> List[str]:
        messages = []
        if cls.USE_LANGSMITH_TRACING and not cls.LANGCHAIN_API_KEY:
            messages.append(
                "WARNING: USE_LANGSMITH_TRACING is enabled but LANGCHAIN_API_KEY is not set."
            )
        valid_agents = {"ReconAgent", "ExploitAgent", "AutomationAgent", "StrategyAgent"}
        for agent in cls.LANGCHAIN_AGENTS:
            if agent not in valid_agents:
                messages.append(f"WARNING: Unknown agent '{agent}' in LANGCHAIN_AGENTS.")
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
