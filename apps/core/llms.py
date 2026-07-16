import os
import logging
from pathlib import Path
from typing import Optional
from functools import lru_cache
from dotenv import load_dotenv

# Explicitly load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

from langchain_core.language_models.chat_models import BaseChatModel

logger = logging.getLogger(__name__)


def _get_request_payload_with_reasoning(self, input_, *, stop=None, **kwargs):
    """
    DeepSeek 官方 API 規格：tool-call 流程中，assistant message 的 reasoning_content
    必須在後續請求中原樣傳回，否則 API 回 400。

    ChatDeepSeek 捕獲 reasoning_content 到 additional_kwargs，
    但繼承的 _convert_message_to_dict 不會把它放回請求 dict。
    此 wrapper 在 payload 建構後把 reasoning_content 補回每個 assistant message。
    """
    from langchain_core.messages import AIMessage

    payload = self._original_get_request_payload(input_, stop=stop, **kwargs)
    messages = self._convert_input(input_).to_messages()
    msg_dicts = payload.get("messages", [])

    for lc_msg, msg_dict in zip(messages, msg_dicts):
        if isinstance(lc_msg, AIMessage) and msg_dict.get("role") == "assistant":
            rc = lc_msg.additional_kwargs.get("reasoning_content")
            if rc:
                msg_dict["reasoning_content"] = rc

    return payload


def _make_deepseek_with_reasoning():
    """建立 ChatDeepSeek 子類，覆寫 _get_request_payload 以保留 reasoning_content。"""
    from langchain_deepseek import ChatDeepSeek

    class ChatDeepSeekWithReasoning(ChatDeepSeek):
        def _get_request_payload(self, input_, *, stop=None, **kwargs):
            return _get_request_payload_with_reasoning(self, input_, stop=stop, **kwargs)

        _original_get_request_payload = ChatDeepSeek._get_request_payload

    return ChatDeepSeekWithReasoning


# ──────────────────────────────────────────────────────────────
# API Key 解析：DB (APIKey model) → 環境變數
# ──────────────────────────────────────────────────────────────

_ENV_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "opencode": "OPENCODE_API_KEY",
}

@lru_cache(maxsize=32)
def _get_active_db_key(provider: str) -> Optional[str]:
    """
    從 DB 讀取啟用中的 API Key（最新建立優先，id 降序）。
    以 provider 為 key 緩存，避免重複查 DB。
    """
    try:
        from apps.core.models import APIKey
        key_obj = APIKey.objects.filter(  # type: ignore[attr-defined]
            service_name=provider,
            is_active=True
        ).order_by('-id').first()
        if key_obj:
            return key_obj.get_key()
    except Exception as e:
        # DB 尚未遷移、AppRegistryNotReady 等 → 靜默失敗，回退 env
        logger.debug(f"_get_active_db_key: provider={provider} failed: {e}")
    return None


def _resolve_api_key(provider: str, override_key: Optional[str] = None) -> Optional[str]:
    """
    統一的 API Key 解析順序：
    1. 明確傳入 override_key
    2. DB 查詢 (APIKey model, is_active=True, priority 降序)
    3. 環境變數 {PROVIDER}_API_KEY
    4. 通用環境變數 AI_API_KEY
    """
    if override_key is not None:
        return override_key

    # DB 優先
    db_key = _get_active_db_key(provider)
    if db_key:
        logger.debug(f"_resolve_api_key: provider={provider} resolved from DB")
        return db_key

    # 環境變數備援
    env_key = _ENV_KEY_MAP.get(provider)
    if env_key:
        val = os.environ.get(env_key)
        if val:
            logger.debug(f"_resolve_api_key: provider={provider} resolved from env {env_key}")
            return val

    # 通用 fallback
    val = os.environ.get("AI_API_KEY")
    if val:
        logger.debug(f"_resolve_api_key: provider={provider} resolved from AI_API_KEY")
        return val

    return None


def _resolve_api_base(provider: str, override_base: Optional[str] = None) -> Optional[str]:
    """統一的 API Base URL 解析。"""
    if override_base is not None:
        return override_base
    return os.environ.get("AI_API_BASE_URL")


def get_llm_instance(
    model_name: Optional[str] = None,
    temperature: float = 0,
    provider: Optional[str] = None,
    agent_id: Optional[str] = None,
    _override_api_key: Optional[str] = None,
    _override_api_base: Optional[str] = None,
    **kwargs
) -> BaseChatModel:
    """
    Factory pattern to generate a LangChain Chat Model dynamically.
    
    Priority for config:
    1. Explicit args (model_name, provider, _override_*)
    2. Agent config (AgentLLMConfig via auto_config)
    3. Environment variables (AI_PROVIDER, AI_MODEL_NAME, etc.)
    
    API Key resolution (in _resolve_api_key):
    1. _override_api_key
    2. DB (APIKey model, is_active=True)
    3. Per-provider env var (OPENAI_API_KEY, etc.)
    4. AI_API_KEY (generic fallback)
    
    Unknown providers are treated as OpenAI-compatible APIs (requires api_base_url).
    """
    # Import here to avoid circular imports
    has_auto_config = False
    auto_config = None
    try:
        from apps.auto.settings import config as auto_config
        has_auto_config = True
    except ImportError:
        pass

    # Initialize variables
    agent_api_key: Optional[str] = None
    agent_api_base_url: Optional[str] = None

    # Get configuration based on agent_id if provided
    if agent_id and has_auto_config and auto_config is not None:
        agent_config = auto_config.get_agent_config(agent_id)
        if not provider:
            provider = agent_config["provider"]
        if not model_name:
            model_name = agent_config["model"]
        if temperature == 0 and agent_config["temperature"] is not None:
            temperature = agent_config["temperature"]
        agent_api_key = agent_config.get("api_key")
        agent_api_base_url = agent_config.get("api_base_url")
        logger.debug(
            "get_llm_instance: agent='%s' resolved config: provider=%s model=%s "
            "has_api_key=%s has_api_base=%s",
            agent_id, provider, model_name, bool(agent_api_key), bool(agent_api_base_url),
        )

    # If no agent or no auto config, fall back to env vars
    if not provider:
        provider = os.environ.get("AI_PROVIDER", "mistral").lower()

    default_model = os.environ.get("AI_MODEL_NAME")
    final_model = model_name or default_model

    # Resolve API key & base (override > agent > DB > env)
    api_key = _resolve_api_key(provider, _override_api_key or agent_api_key)
    api_base = _resolve_api_base(provider, _override_api_base or agent_api_base_url)

    logger.info(
        "Initializing LLM: provider=%s model=%s base_url=%s temp=%.1f agent_id=%s key_source=%s",
        provider, final_model, api_base, temperature, agent_id,
        "override" if _override_api_key else ("agent" if agent_api_key else ("db" if _get_active_db_key.cache_info().hits > 0 else "env"))
    )

    if api_key is None and provider not in ("ollama",):
        _env_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "opencode": "OPENCODE_API_KEY",
        }
        logger.warning(
            "api_key 仍為 None，provider=%s, agent_id=%s。\n"
            "請檢查：\n"
            "  1. APIKey DB 表是否有 service_name='%s' 且 is_active=True 的紀錄\n"
            "  2. 該紀錄的 key_value 是否為空字串\n"
            "  3. 環境變數 %s 或 AI_API_KEY 是否已設定\n"
            "  4. AgentLLMConfig.api_key_ref（若有設定）是否指向有效的 APIKey",
            provider, agent_id, provider, _env_map.get(provider, "<no env mapping>"),
        )

    # ──────────────────────────────────────────────────────────────
    # Provider 實例化
    # ──────────────────────────────────────────────────────────────

    if provider in ("openai", "proxy"):
        from langchain_openai import ChatOpenAI
        if not final_model:
            final_model = "gpt-4o"
        kwargs.setdefault("max_retries", 2)  # 降低重試，避免長等待
        kwargs.setdefault("timeout", 60)
        return ChatOpenAI(
            model=final_model,
            temperature=temperature,
            api_key=api_key,  # type: ignore[arg-type]
            base_url=api_base,
            **kwargs,
        )
    elif provider == "opencode":
        from langchain_openai import ChatOpenAI
        if not final_model:
            final_model = "deepseek-v4-flash"
        kwargs.setdefault("max_retries", 2)
        kwargs.setdefault("timeout", 60)
        return ChatOpenAI(
            model=final_model,
            temperature=temperature,
            api_key=api_key,  # type: ignore[arg-type]
            base_url=api_base or "https://opencode.ai/zen/go/v1",
            **kwargs,
        )
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        if not final_model:
            final_model = "claude-sonnet-4-6"
        kwargs.setdefault("timeout", 60)
        return ChatAnthropic(
            model=final_model,
            temperature=temperature,
            api_key=api_key,  # type: ignore[arg-type]
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
            **kwargs,
        )
    elif provider == "deepseek":
        if not final_model:
            final_model = "deepseek-chat"
        kwargs.setdefault("max_retries", 2)
        kwargs.setdefault("timeout", 60)
        cls = _make_deepseek_with_reasoning()
        return cls(
            model=final_model,
            temperature=temperature,
            api_key=api_key,  # type: ignore[arg-type]
            api_base=api_base or "https://api.deepseek.com/v1",
            **kwargs,
        )
    elif provider == "mistral":
        from langchain_mistralai import ChatMistralAI
        if not final_model:
            final_model = "mistral-small-2603"
        kwargs.setdefault("timeout", 60)
        return ChatMistralAI(
            model=final_model,
            temperature=temperature,
            mistral_api_key=api_key,  # type: ignore[arg-type]
            **kwargs,
        )
    else:
        # 未知 provider → 視為 OpenAI-compatible API
        from langchain_openai import ChatOpenAI
        if not final_model:
            final_model = provider
        kwargs.setdefault("max_retries", 2)
        kwargs.setdefault("timeout", 60)
        return ChatOpenAI(
            model=final_model,
            temperature=temperature,
            api_key=api_key,  # type: ignore[arg-type]
            base_url=api_base,
            **kwargs,
        )


# ──────────────────────────────────────────────────────────────
# 測試/管理用：清除緩存、強制重讀 DB
# ──────────────────────────────────────────────────────────────

def clear_api_key_cache():
    """清除 DB key 緩存（APIKey 更新後呼叫）。"""
    _get_active_db_key.cache_clear()
    logger.info("API key cache cleared")
