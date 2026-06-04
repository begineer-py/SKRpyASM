import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Explicitly load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

from langchain_core.language_models.chat_models import BaseChatModel

logger = logging.getLogger(__name__)


def get_llm_instance(
    model_name: Optional[str] = None, 
    temperature: float = 0, 
    provider: Optional[str] = None, 
    agent_id: Optional[str] = None, 
    **kwargs
) -> BaseChatModel:
    """
    Factory pattern to generate a LangChain Chat Model dynamically.
    Checks environment logs to choose between openai, mistral, deepseek, ollama or proxy.
    
    Can be called with an agent_id to get agent-specific configuration.
    """
    # Import here to avoid circular imports
    try:
        from apps.auto.settings import config as auto_config
        has_auto_config = True
    except ImportError:
        has_auto_config = False
    
    # Initialize variables
    agent_api_key = None
    agent_api_base_url = None
    
    # Get configuration based on agent_id if provided
    if agent_id and has_auto_config:
        agent_config = auto_config.get_agent_config(agent_id)
        if not provider:
            provider = agent_config["provider"]
        if not model_name:
            model_name = agent_config["model"]
        if temperature == 0 and agent_config["temperature"] is not None:
            temperature = agent_config["temperature"]
        # Get agent-specific API configuration
        agent_api_key = agent_config.get("api_key")
        agent_api_base_url = agent_config.get("api_base_url")
    
    # If no agent or no auto config, fall back to env vars
    if not provider:
        provider = os.environ.get("AI_PROVIDER", "mistral").lower()
    
    default_model = os.environ.get("AI_MODEL_NAME")
    
    # AI_MODEL_NAME in env overrides the hardcoded class model
    final_model = model_name or default_model
    
    # Get API keys and base URL
    # Priority: agent-specific > DB/env (via get_ai_provider_key) > global fallback
    api_key = agent_api_key or os.environ.get("AI_API_KEY")
    api_base = agent_api_base_url or os.environ.get("AI_API_BASE_URL")

    if not agent_api_key:
        # 優先從 DB 查詢，DB 無值則自動回退到 env var（DB+env 二合一）
        try:
            from apps.api_keys.utils import get_ai_provider_key
            provider_key = get_ai_provider_key(provider)
        except Exception:
            provider_key = None

        if provider_key:
            api_key = provider_key
        else:
            # 備援：直接讀 env var（保持既有行為，防 api_keys app 不可用）
            if provider == "openai":
                api_key = os.environ.get("OPENAI_API_KEY") or api_key
            elif provider == "mistral":
                api_key = os.environ.get("MISTRAL_API_KEY") or api_key
            elif provider == "anthropic":
                api_key = os.environ.get("ANTHROPIC_API_KEY") or api_key
            elif provider == "deepseek":
                api_key = os.environ.get("DEEPSEEK_API_KEY") or api_key
    
    logger.info(f"Initializing LLM with provider={provider}, model={final_model}, base_url={api_base}, temperature={temperature}, agent_id={agent_id}")

    if provider in ["openai", "proxy"]:
        from langchain_openai import ChatOpenAI
        if not final_model:
            final_model = "gpt-4o"
        return ChatOpenAI(
            model=final_model, 
            temperature=temperature, 
            api_key=api_key, 
            base_url=api_base,
            **kwargs,
        )
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        if not final_model:
            final_model = "claude-3-opus-20240229"
        return ChatAnthropic(
            model=final_model,
            temperature=temperature,
            api_key=api_key,
            **kwargs
        )
    elif provider == "ollama":
        from langchain_community.chat_models import ChatOllama
        if not final_model:
            final_model = "llama3"
        return ChatOllama(
            model=final_model,
            temperature=temperature,
            base_url=api_base or "http://localhost:11434",
            **kwargs
        )
    elif provider == "deepseek":
        from langchain_openai import ChatOpenAI
        if not final_model:
            final_model = "deepseek-chat"
        # DeepSeek uses OpenAI schema
        return ChatOpenAI(
            model=final_model, 
            temperature=temperature, 
            api_key=api_key, 
            base_url=api_base or "https://api.deepseek.com/v1",
            **kwargs
            )
    else:  # fallback to mistral
        from langchain_mistralai import ChatMistralAI
        if not final_model:
            final_model = "mistral-small-2603"
        return ChatMistralAI(
            model=final_model,
            temperature=temperature,
            mistral_api_key=api_key,
            **kwargs
        )
