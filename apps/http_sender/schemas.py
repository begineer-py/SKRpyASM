from ninja import Schema, Field
from typing import List, Optional, Literal

from sympy import N


# 1. 定義參數結構 (對應 URLParameter)
class ParameterPayload(Schema):
    key: str = Field(..., description="參數名稱")
    value: Optional[str] = Field(None, description="觀察到的範例值")
    location: Literal["query", "body"] = Field("query", description="參數位置")
    source_type: Optional[str] = Field(
        "querystring", description="來源類型: form, javascript, querystring"
    )
    data_type: str = Field("string", description="推斷型別: string, int, boolean, json")


# 2. 定義主要的匯入結構 (對應 URLResult + Endpoint)
class URLIngestSchema(Schema):
    url: str = Field(..., description="完整 URL")
    method: str = Field("GET", description="HTTP Method (GET, POST, etc.)")

    # 狀態與來源
    status_code: Optional[int] = Field(None, description="HTTP Status Code")
    discovery_source: str = Field(
        "API", description="對應 DISCOVERY_SOURCE_CHOICES (SCAN, API, BRUTE...)"
    )

    # 內容 (接受 request.tpl 但非必要)
    request_tpl: Optional[str] = Field(
        None, description="原始請求文本 (Request Template)"
    )
    response_text: Optional[str] = Field(
        None, description="回應內容 (用於存入 text 或 cleaned_html)"
    )
    title: Optional[str] = Field(None, description="網頁標題")

    # 標記
    is_important: bool = False

    # 巢狀參數清單 (直接在這裡定義參數，讓 API 一次處理)
    parameters: List[ParameterPayload] = Field(
        default_factory=list, description="此 URL 發現的參數列表"
    )


# 3. 定義回應結構 (讓前端知道建立了什麼)
class IngestResponse(Schema):
    success: bool
    url_result_id: int
    endpoint_id: int
    is_new_endpoint: bool
    message: str


class RemainEndpoint(Schema):
    id: int
    cookies: dict | str | None = None


class PayloadSchema(Schema):  # <--- 繼承 Schema
    method: str
    url: str
    headers: dict
    cookies: dict | str | None = None
    payload: dict
