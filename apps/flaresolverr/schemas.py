# flaresolverr/schemas.py

from ninja import (
    Schema,
    ModelSchema,
)  # <--- 媽的，Schema 要大寫，而且是從 ninja 進來的！
from typing import List, Optional

# --- API 觸發與狀態回報用的 Schema ---


class ErrorSchema(Schema):  # <--- 繼承 Schema
    detail: str
    status_code: int


class JSAnalyzeRequest(Schema):
    id: int
    type: str  # "external" or "inline"
