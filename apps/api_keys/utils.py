from apps.core.models.api_key import APIKey
import logging
import yaml
import os
import tempfile
import configparser

import random

logger = logging.getLogger(__name__)


def get_rotated_key(service: str) -> str | None:
    """
    隨機輪轉取得某個 service 的其中一個啟用金鑰。
    用於 subfinder / amass 等工具每次呼叫時隨機挑選不同 key。
    """
    keys = get_active_api_keys().get(service.lower(), [])
    if not keys:
        return None
    return random.choice(keys)

def get_active_api_keys():
    """
    從資料庫抓取所有啟用的 API 金鑰，返回格式為 {service_name.lower(): [key1, key2, ...]} 的字典。
    支援同一個 service 多個金鑰，用於輪轉 (例如多個 shodan)。
    """
    from collections import defaultdict
    keys_qs = APIKey.objects.filter(is_active=True)
    result = defaultdict(list)
    for k in keys_qs:
        result[k.service_name.lower()].append(k.key_value)

    summary = {svc: f"{len(v)} key(s)" for svc, v in result.items()}
    logger.info(f"🔑 使用中的 API 金鑰: {summary}")
    return dict(result)

_AI_PROVIDER_ENV_MAP = {
    "openai":    "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "mistral":   "MISTRAL_API_KEY",
    "gemini":    "GEMINI_API_KEY",
    "deepseek":  "DEEPSEEK_API_KEY",
    "langchain": "LANGCHAIN_API_KEY",
    "nvd":       "NVD_API_KEY",
    "vulncheck": "VULNCHECK_API_KEY",
    "ollama":    None,  # 本地服務，無需 API 鍵
}


def get_ai_provider_key(provider: str) -> str | None:
    """
    取得 AI 提供商 API 密鑰，DB 優先、env var 備援。

    查詢順序：
      1. DB：APIKey.objects.filter(service_name=provider, is_active=True)
      2. 環境變量：依 _AI_PROVIDER_ENV_MAP 映射
      3. 兩者均無則回傳 None

    Args:
        provider: 提供商名稱（小寫），例如 "openai"、"anthropic"。
    """
    provider = provider.lower()

    # 1. DB 查詢（module 頂層已 import APIKey；try/except 防早期啟動異常）
    try:
        record = APIKey.objects.filter(
            service_name__iexact=provider, is_active=True
        ).first()
        if record:
            return record.key_value
    except Exception as exc:
        logger.warning(f"get_ai_provider_key: DB lookup failed for '{provider}': {exc}")

    # 2. env var 備援
    env_var = _AI_PROVIDER_ENV_MAP.get(provider)
    if env_var:
        value = os.environ.get(env_var)
        if value:
            return value

    return None


def generate_subfinder_config(keys):
    """
    生成 subfinder 的 provider-config.yaml。
    支援多個金鑰 (列表形式)。
    """
    config = {}
    for service, values in keys.items():
        if isinstance(values, list):
            config[service] = values
        else:
            config[service] = [values]
    
    svc_summary = {s: len(v) for s, v in config.items()}
    logger.info(f"  └─ subfinder config 含 {svc_summary}")
    fd, path = tempfile.mkstemp(suffix=".yaml", prefix="subfinder_")
    with os.fdopen(fd, 'w') as f:
        yaml.dump(config, f)
    return path

def generate_amass_config(keys):
    """
    生成 amass 的 config.ini。
    支援多個金鑰 (為每個金鑰建立獨立 section)。
    """
    config = configparser.ConfigParser()
    svc_count = {}
    for service, values in keys.items():
        if not isinstance(values, list):
            values = [values]
        svc_count[service] = len(values)
        for idx, value in enumerate(values):
            suffix = f"_{idx}" if idx > 0 else ""
            section = f"data_sources.{service.capitalize()}{suffix}"
            config[section] = {}
            cred_section = f"{section}.credentials"
            config[cred_section] = {"apikey": value}
    
    logger.info(f"  └─ amass config 含 {svc_count}")
    fd, path = tempfile.mkstemp(suffix=".ini", prefix="amass_")
    with os.fdopen(fd, 'w') as f:
        config.write(f)
    return path

def generate_gau_config(keys):
    """
    生成 gau 的 .gau.toml。
    支援多個金鑰 (為每個金鑰建立獨立 section)。
    """
    lines = []
    svc_count = {}
    for service, values in keys.items():
        if not isinstance(values, list):
            values = [values]
        svc_count[service] = len(values)
        for idx, value in enumerate(values):
            suffix = f"_{idx}" if idx > 0 else ""
            section_name = f"{service}{suffix}"
            lines.append(f"[{section_name}]")
            lines.append(f'apikey = "{value}"')
            lines.append("")
    
    logger.info(f"  └─ gau config 含 {svc_count}")
    fd, path = tempfile.mkstemp(suffix=".toml", prefix="gau_")
    with os.fdopen(fd, 'w') as f:
        f.write("\n".join(lines))
    return path

def generate_nuclei_secrets(keys):
    """
    生成 nuclei 的 secrets.yaml。
    支援多個金鑰 (為每個金鑰建立獨立 entry)。
    """
    secrets = []
    svc_count = {}
    for service, values in keys.items():
        if not isinstance(values, list):
            values = [values]
        svc_count[service] = len(values)
        for idx, value in enumerate(values):
            suffix = f"_{idx}" if idx > 0 else ""
            secrets.append({
                "name": f"{service}{suffix}_token",
                "value": value
            })
    
    logger.info(f"  └─ nuclei secrets 含 {svc_count}")
    fd, path = tempfile.mkstemp(suffix=".yaml", prefix="nuclei_")
    with os.fdopen(fd, 'w') as f:
        yaml.dump(secrets, f)
    return path
