from ninja import Schema
from typing import Optional
from datetime import datetime


# ── 現有 APIKey schemas ────────────────────────────────────────────────────────

class APIKeyOut(Schema):
    id: int
    service_name: str
    key_value: str
    is_active: bool
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class APIKeyIn(Schema):
    service_name: str
    key_value: str
    is_active: bool = True
    description: Optional[str] = None

class APIKeyUpdate(Schema):
    service_name: Optional[str] = None
    key_value: Optional[str] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


# ── AgentLLMConfig schemas ────────────────────────────────────────────────────

class APIKeyBriefOut(Schema):
    """在 AgentLLMConfigOut 中嵌套顯示 APIKey 摘要（不暴露 key_value）。"""
    id: int
    service_name: str
    description: Optional[str] = None


class AgentLLMConfigOut(Schema):
    """AgentLLMConfig DB 記錄的完整回應。"""
    id: int
    agent_id: str
    provider: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    api_base_url: Optional[str] = None
    api_key_ref: Optional[APIKeyBriefOut] = None
    is_active: bool
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AgentLLMConfigIn(Schema):
    """建立 AgentLLMConfig 的請求 body。"""
    agent_id: str
    provider: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    api_base_url: Optional[str] = None
    api_key_id: Optional[int] = None   # 對應 APIKey.id
    is_active: bool = True
    description: Optional[str] = None


class AgentLLMConfigUpdate(Schema):
    """部分更新 AgentLLMConfig 的請求 body（所有欄位可選）。"""
    provider: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    api_base_url: Optional[str] = None
    api_key_id: Optional[int] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class AgentEffectiveConfigOut(Schema):
    """合並 DB + env var + 全域默認值後的有效配置視圖。"""
    agent_id: str
    effective_provider: str
    effective_model: str
    effective_temperature: float
    effective_api_base_url: Optional[str] = None
    has_db_config: bool      # 是否在 DB 中有記錄
    has_env_override: bool   # 是否有 env var 覆蓋（非 None）
    db_config: Optional[AgentLLMConfigOut] = None
