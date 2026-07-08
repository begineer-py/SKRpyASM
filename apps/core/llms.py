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
    Checks environment logs to choose between openai, mistral, deepseek, ollama or proxy.

    Can be called with an agent_id to get agent-specific configuration.
    _override_api_key / _override_api_base: bypass all key resolution (used by test endpoints).
    Unknown providers are treated as OpenAI-compatible APIs (requires api_base_url).
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
        logger.debug(
            "get_llm_instance: agent='%s' resolved config: provider=%s model=%s "
            "has_api_key=%s has_api_base=%s",
            agent_id, provider, model_name, bool(agent_api_key), bool(agent_api_base_url),
        )

    # If no agent or no auto config, fall back to env vars
    if not provider:
        provider = os.environ.get("AI_PROVIDER", "mistral").lower()

    default_model = os.environ.get("AI_MODEL_NAME")

    # AI_MODEL_NAME in env overrides the hardcoded class model
    final_model = model_name or default_model

    # _override_* 最優先（測試端點直接傳入，跳過 agent_id 查詢路徑）
    if _override_api_key is not None:
        api_key = _override_api_key
        api_base = _override_api_base or os.environ.get("AI_API_BASE_URL")
    else:
        # Get API keys and base URL
        # Priority: agent-specific > DB/env (via get_ai_provider_key) > global fallback
        api_key = agent_api_key or os.environ.get("AI_API_KEY")
        api_base = agent_api_base_url or os.environ.get("AI_API_BASE_URL")
        logger.debug(
            "get_llm_instance: Step 1 (agent_key || AI_API_KEY): api_key=%s",
            "***set***" if api_key else None,
        )

        if not agent_api_key:
            # 優先從 DB 查詢，DB 無值則自動回退到 env var（DB+env 二合一）
            try:
                from apps.api_keys.utils import get_ai_provider_key
                provider_key = get_ai_provider_key(provider)
            except Exception as e:
                logger.warning(f"get_ai_provider_key 查詢失敗 provider='{provider}': {e}")
                provider_key = None

            if provider_key:
                api_key = provider_key
                logger.debug(
                    "get_llm_instance: Step 2 (get_ai_provider_key): key resolved for '%s'",
                    provider,
                )
            else:
                logger.debug(
                    "get_llm_instance: Step 2 (get_ai_provider_key): no key for '%s', "
                    "trying per-provider env fallback",
                    provider,
                )
                # 備援：直接讀 env var（保持既有行為，防 api_keys app 不可用）
                if provider == "openai":
                    api_key = os.environ.get("OPENAI_API_KEY") or api_key
                    logger.debug(
                        "get_llm_instance: Step 3 (OPENAI_API_KEY): %s",
                        "***set***" if os.environ.get("OPENAI_API_KEY") else "not set",
                    )
                elif provider == "mistral":
                    api_key = os.environ.get("MISTRAL_API_KEY") or api_key
                    logger.debug(
                        "get_llm_instance: Step 3 (MISTRAL_API_KEY): %s",
                        "***set***" if os.environ.get("MISTRAL_API_KEY") else "not set",
                    )
                elif provider == "anthropic":
                    api_key = os.environ.get("ANTHROPIC_API_KEY") or api_key
                    logger.debug(
                        "get_llm_instance: Step 3 (ANTHROPIC_API_KEY): %s",
                        "***set***" if os.environ.get("ANTHROPIC_API_KEY") else "not set",
                    )
                elif provider == "deepseek":
                    api_key = os.environ.get("DEEPSEEK_API_KEY") or api_key
                    logger.debug(
                        "get_llm_instance: Step 3 (DEEPSEEK_API_KEY): %s",
                        "***set***" if os.environ.get("DEEPSEEK_API_KEY") else "not set",
                    )

    logger.info(f"Initializing LLM with provider={provider}, model={final_model}, base_url={api_base}, temperature={temperature}, agent_id={agent_id}")

    if api_key is None and provider not in ("ollama",):
        _env_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }
        logger.warning(
            "api_key 仍為 None，provider=%s, agent_id=%s。\n"
            "請檢查：\n"
            "  1. APIKey DB 表是否有 service_name='%s' 且 is_active=True 的紀錄\n"
            "  2. 該紀錄的 key_value 是否為空字串（非 null 但為空）\n"
            "  3. 環境變數 %s 是否已設定（或 AI_API_KEY）\n"
            "  4. AgentLLMConfig.api_key_ref（若有設定）是否指向有效的 APIKey",
            provider, agent_id,
            provider,
            _env_map.get(provider, "<no env mapping>"),
        )

    if provider in ["openai", "proxy"]:
        from langchain_openai import ChatOpenAI
        if not final_model:
            final_model = "gpt-4o"
        # max_retries=5:讓 OpenAI SDK 自動重試 APIConnectionError / 429 / 5xx。
        # SDK 預設只重試 5xx/429，不包含連線層錯誤；顯式設高值確保瞬態網路故障能撐過去。
        kwargs.setdefault("max_retries", 5)
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
            final_model = "claude-sonnet-4-6"
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
        if not final_model:
            final_model = "deepseek-chat"
        kwargs.setdefault("max_retries", 5)
        cls = _make_deepseek_with_reasoning()
        return cls(
            model=final_model,
            temperature=temperature,
            api_key=api_key,
            api_base=api_base or "https://api.deepseek.com/v1",
            **kwargs,
        )
    elif provider == "mistral":
        from langchain_mistralai import ChatMistralAI
        if not final_model:
            final_model = "mistral-small-2603"
        return ChatMistralAI(
            model=final_model,
            temperature=temperature,
            mistral_api_key=api_key,
            **kwargs
        )
    else:
        # 未知 provider → 視為 OpenAI-compatible API
        # 適用：Groq、Together AI、vLLM、LM Studio、LocalAI、自建 proxy 等
        from langchain_openai import ChatOpenAI
        if not final_model:
            final_model = provider
        kwargs.setdefault("max_retries", 5)
        return ChatOpenAI(
            model=final_model,
            temperature=temperature,
            api_key=api_key,
            base_url=api_base,
            **kwargs
        )
