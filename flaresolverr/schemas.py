# flaresolverr/schemas.py

from pydantic import BaseModel
from ninja import ModelSchema
from typing import List, Optional

# 媽的，把所有要序列化的 Model 一次性 import 進來！
from core.models import (
    URLResult,
    Form,
    JavaScriptFile,
    AnalysisFinding,
    Link,
    Comment,
    MetaTag,
    Iframe,
)


# --- API 觸發與狀態回報用的 Schema (保持不變) ---


class FlaresolverrTriggerSchema(BaseModel):
    url: str
    method: str
    use_tool: str | None = None
    seed_id: int | None = None


class check_flaresolverr(BaseModel):
    detail: str
    status_code: int
    if_run: bool


class ErrorSchema(BaseModel):
    detail: str
    status_code: int


class PayloadSchema(BaseModel):
    method: str
    url: str
    headers: dict
    cookies: dict
    payload: dict


# --- 操，這裡是我們新建的軍火庫說明書 (逐個修正) ---
