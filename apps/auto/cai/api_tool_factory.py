"""
apps/auto/cai/api_tool_factory.py

動態將本平台所有 Django Ninja API 端點轉換成 LangChain 可調用的工具。

原理：
1. 向本地 Django 伺服器請求 OpenAPI JSON schema (/api/openapi.json)
2. 解析 schema 並從中提取所有的 paths（端點）
3. 利用 LangChain 的內建 RequestsToolkit 製作標準的 GET/POST 工具
4. 使用 StructuredTool.from_function 將每個 API 端點動態注入成獨立工具

使用 LangChain 原生工具，告別臃腫的手工 wrapper！
"""

import json
import logging
from typing import List, Optional

import requests
from django.conf import settings

from langchain_core.tools import StructuredTool
from langchain_community.utilities import TextRequestsWrapper
from pydantic import BaseModel, create_model, Field

logger = logging.getLogger(__name__)

# 平台本機 API 基礎路徑
API_BASE_URL: str = getattr(settings, "INTERNAL_API_BASE_URL", "http://127.0.0.1:8000/api")


def _fetch_openapi_spec(openapi_url: str) -> Optional[dict]:
    """從指定 URL 取得 OpenAPI JSON Schema。"""
    try:
        resp = requests.get(openapi_url, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"[CAI] 無法取得 OpenAPI spec: {e}")
        return None


def _schema_to_pydantic(schema: dict, model_name: str) -> type:
    """
    把 OpenAPI requestBody 的 JSON schema 動態轉換成 Pydantic Model。
    讓 LangChain StructuredTool 能自動驗證輸入。
    """
    fields = {}
    props = schema.get("properties", {})
    required = schema.get("required", [])

    for field_name, field_info in props.items():
        python_type = str  # default
        field_schema_type = field_info.get("type", "string")
        if field_schema_type == "integer":
            python_type = int
        elif field_schema_type == "boolean":
            python_type = bool
        elif field_schema_type == "array":
            python_type = list
        elif field_schema_type == "object":
            python_type = dict

        description = field_info.get("description", "")
        if field_name in required:
            fields[field_name] = (python_type, Field(description=description))
        else:
            fields[field_name] = (Optional[python_type], Field(default=None, description=description))

    return create_model(model_name, **fields)


def _build_tool_for_endpoint(path: str, method: str, op: dict, requests_wrapper: TextRequestsWrapper) -> StructuredTool:
    """
    為單個 API 端點建立一個 StructuredTool。
    使用 requests_wrapper.run(url, data) 發送 HTTP 請求，
    完全依賴 LangChain 的 TextRequestsWrapper，不額外使用 requests 套件。
    """
    full_url = f"{API_BASE_URL.rstrip('/')}{path}"
    tool_name = op.get("operationId") or f"{method}_{path}".replace("/", "_").strip("_")
    description = op.get("summary", "") or op.get("description", tool_name)

    # 嘗試解析 Request Body schema
    body_schema = {}
    content = op.get("requestBody", {}).get("content", {})
    if "application/json" in content:
        body_schema = content["application/json"].get("schema", {})

    # 動態生成 Pydantic Schema
    ArgsModel = _schema_to_pydantic(body_schema, model_name=f"{tool_name}_args") if body_schema else BaseModel

    if method.upper() in ("GET", "DELETE"):
        def _run(**kwargs) -> str:
            try:
                query_str = "&".join(f"{k}={v}" for k, v in kwargs.items() if v is not None)
                url = f"{full_url}?{query_str}" if query_str else full_url
                result = requests_wrapper.run(url)
                return result
            except Exception as e:
                return f"API 調用失敗 ({tool_name}): {e}"
    else:
        def _run(**kwargs) -> str:
            try:
                payload = {k: v for k, v in kwargs.items() if v is not None}
                result = requests_wrapper.run(full_url, json.dumps(payload))
                return result
            except Exception as e:
                return f"API 調用失敗 ({tool_name}): {e}"

    return StructuredTool(
        name=tool_name,
        description=description,
        args_schema=ArgsModel,
        func=_run,
    )


def build_tools_from_openapi(
    openapi_url: Optional[str] = None,
    custom_headers: Optional[dict] = None,
    include_paths: Optional[List[str]] = None,
    exclude_paths: Optional[List[str]] = None,
) -> List[StructuredTool]:
    """
    【核心工廠函式】

    從 Django Ninja 的 OpenAPI schema 自動生成所有 API 端點的 LangChain 工具。
    每個端點 → 一個 StructuredTool，可直接 attach 到任意 LangChain Agent。

    Args:
        openapi_url: OpenAPI schema 的 URL，預設為本地 /api/openapi.json
        custom_headers: 附加的 HTTP header（如 Authorization）
        include_paths: 只包含這些路徑前綴的工具
        exclude_paths: 排除這些路徑前綴的工具

    Returns:
        List[StructuredTool] - 可直接傳入 LangChain Agent 的工具列表
    """
    if openapi_url is None:
        # Django Ninja 的 OpenAPI schema 路徑
        base = API_BASE_URL.rstrip("/")
        # 往上一層取 /api/openapi.json
        openapi_url = base.rsplit("/api", 1)[0] + "/api/openapi.json"

    spec = _fetch_openapi_spec(openapi_url)
    if not spec:
        logger.warning("[CAI] 無法載入 OpenAPI Spec，返回空工具列表。")
        return []

    headers = {"Content-Type": "application/json"}
    if custom_headers:
        headers.update(custom_headers)

    requests_wrapper = TextRequestsWrapper(headers=headers)
    tools: List[StructuredTool] = []

    paths = spec.get("paths", {})
    for path, methods in paths.items():
        # 過濾邏輯
        if include_paths and not any(path.startswith(p) for p in include_paths):
            continue
        if exclude_paths and any(path.startswith(p) for p in exclude_paths):
            continue

        for method, operation in methods.items():
            if method.lower() not in ("get", "post", "put", "patch", "delete"):
                continue
            try:
                tool = _build_tool_for_endpoint(path, method, operation, requests_wrapper)
                tools.append(tool)
                logger.debug(f"[CAI] 成功生成工具: {tool.name} ({method.upper()} {path})")
            except Exception as e:
                logger.warning(f"[CAI] 無法為 {method.upper()} {path} 生成工具: {e}")

    logger.info(f"[CAI] 共成功生成 {len(tools)} 個 API 工具。")
    return tools
