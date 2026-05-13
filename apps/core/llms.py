import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

from langchain_core.language_models.chat_models import BaseChatModel

logger = logging.getLogger(__name__)

def get_llm_instance(model_name=None, temperature=0, **kwargs) -> BaseChatModel:
    """
    Factory pattern to generate a LangChain Chat Model dynamically.
    Checks environment logs to choose between openai, mistral, deepseek, ollama or proxy.
    """
    provider = os.environ.get("AI_PROVIDER", "mistral").lower()
    default_model = os.environ.get("AI_MODEL_NAME")
    
    # AI_MODEL_NAME in env overrides the hardcoded class model
    final_model = default_model or model_name
    api_key = os.environ.get("AI_API_KEY")
    api_base = os.environ.get("AI_API_BASE_URL")
    
    logger.info(f"Initializing LLM with provider={provider}, model={final_model}, base_url={api_base}")

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
