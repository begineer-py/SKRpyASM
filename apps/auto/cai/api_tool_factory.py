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


def _resolve_schema(schema_obj: dict, spec: dict) -> dict:
    """如果 schema_obj 中包含 $ref，則從 spec 解析出實際的 schema 內容，支援 recursive。"""
    if not schema_obj:
        return {}
    if "$ref" in schema_obj:
        ref_path = schema_obj["$ref"]
        # e.g., "#/components/schemas/AddSeedSchema"
        if ref_path.startswith("#/components/schemas/"):
            schema_name = ref_path.split("/")[-1]
            return spec.get("components", {}).get("schemas", {}).get(schema_name, {})
    return schema_obj

def _operation_to_pydantic(op: dict, model_name: str, spec: dict) -> type:
    """
    動態轉換 OpenAPI operation (Body + Path/Query params) 成 Pydantic Model，
    讓 LangChain StructuredTool 知道除了 Body 之外還要填路徑參數 (如 {target_id})。
    """
    fields = {}

    # 1. 處理 Request Body
    content = op.get("requestBody", {}).get("content", {})
    body_schema = content.get("application/json", {}).get("schema", {})
    
    # 這裡必須解析 $ref，否則會抓不到 properties
    actual_body_schema = _resolve_schema(body_schema, spec)
    
    props = actual_body_schema.get("properties", {})
    required_body = actual_body_schema.get("required", [])

    for field_name, field_info in props.items():
        python_type = str
        field_schema_type = field_info.get("type", "string")
        if field_schema_type == "integer": python_type = int
        elif field_schema_type == "boolean": python_type = bool
        elif field_schema_type == "array": python_type = list
        elif field_schema_type == "object": python_type = dict

        description = field_info.get("description", "")
        if field_name in required_body:
            fields[field_name] = (python_type, Field(description=description))
        else:
            fields[field_name] = (Optional[python_type], Field(default=None, description=description))

    # 2. 處理 Parameters (Path / Query)
    parameters = op.get("parameters", [])
    for param in parameters:
        param_name = param.get("name")
        param_schema_type = param.get("schema", {}).get("type", "string")
        is_required = param.get("required", False)

        python_type = str
        if param_schema_type == "integer": python_type = int
        elif param_schema_type == "boolean": python_type = bool

        description = param.get("description", f"Parameter passed in {param.get('in', 'url')}")
        if is_required:
            fields[param_name] = (python_type, Field(description=description))
        else:
            fields[param_name] = (Optional[python_type], Field(default=None, description=description))

    if not fields:
        return BaseModel
        
    return create_model(model_name, **fields)


def _build_tool_for_endpoint(path: str, method: str, op: dict, requests_wrapper: TextRequestsWrapper, spec: dict) -> StructuredTool:
    """
    為單個 API 端點建立一個 StructuredTool。
    使用 requests_wrapper.run(url, data) 發送 HTTP 請求，
    完全依賴 LangChain 的 TextRequestsWrapper，不額外使用 requests 套件。
    """
    base = API_BASE_URL.rstrip('/')
    if path.startswith("/api/") and base.endswith("/api"):
        base = base[:-4]
    full_url = f"{base}{path}"

    raw_path_name = f"{method}_{path}".replace("/api/", "").replace("/", "_").replace("{", "").replace("}", "").replace("-", "_").strip("_").lower()
    tool_name = raw_path_name
    description = op.get("summary", "") or op.get("description", tool_name)

    # 動態生成 Pydantic Schema (包含 Body + Path 參數)
    ArgsModel = _operation_to_pydantic(op, model_name=f"{tool_name}_args", spec=spec)

    def _validate_result(res: str, t_name: str) -> str:
        if isinstance(res, str) and res.strip().startswith("<!DOCTYPE html>"):
            raise ValueError("Received HTML instead of JSON. Ensure the endpoint path is correct (avoid 404).")
        return res

    if method.upper() in ("GET", "DELETE"):
        def _run(**kwargs) -> str:
            import requests
            try:
                import re
                url = full_url
                matches = re.findall(r'\{([a-zA-Z0-9_]+)\}', url)
                for m in matches:
                    if m in kwargs:
                        url = url.replace(f"{{{m}}}", str(kwargs.pop(m)))
                
                query_str = "&".join(f"{k}={v}" for k, v in kwargs.items() if v is not None)
                final_url = f"{url}?{query_str}" if query_str else url
                resp = requests.request(method.upper(), final_url, headers=requests_wrapper.headers)
                if resp.status_code >= 400:
                    return f"CRITICAL_FAILURE: API Returns HTTP {resp.status_code} ({tool_name}): {resp.text}. DO NOT BLINDLY RETRY."
                return _validate_result(resp.text, tool_name)
            except Exception as e:
                # 回傳明確的系統失敗提示，阻止 AI 無限重試
                return f"CRITICAL_FAILURE: API 調用失敗 ({tool_name}): {e}. DO NOT RETRY THIS ACTION."
    else:
        def _run(**kwargs) -> str:
            import requests
            try:
                import re
                url = full_url
                matches = re.findall(r'\{([a-zA-Z0-9_]+)\}', url)
                for m in matches:
                    if m in kwargs:
                        url = url.replace(f"{{{m}}}", str(kwargs.pop(m)))
                        
                payload = {k: v for k, v in kwargs.items() if v is not None}
                resp = requests.request(method.upper(), url, json=payload, headers=requests_wrapper.headers)
                if resp.status_code >= 400:
                    return f"CRITICAL_FAILURE: API Returns HTTP {resp.status_code} ({tool_name}): {resp.text}. DO NOT BLINDLY RETRY."
                return _validate_result(resp.text, tool_name)
            except Exception as e:
                return f"CRITICAL_FAILURE: API 調用失敗 ({tool_name}): {e}. DO NOT RETRY THIS ACTION."

    # 從 OpenAPI schema 提取欄位資訊並附加到 description，避免 AI 亂填參數
    field_hints = []
    content = op.get("requestBody", {}).get("content", {})
    body_schema = content.get("application/json", {}).get("schema", {})
    
    actual_body_schema = _resolve_schema(body_schema, spec)
    props = actual_body_schema.get("properties", {})
    required_body = actual_body_schema.get("required", [])
    for field_name, field_info in props.items():
        ftype = field_info.get("type", "string")
        is_req = field_name in required_body
        fdesc = field_info.get("description", "")
        marker = "REQUIRED" if is_req else "optional"
        hint = f"  - {field_name} ({ftype}, {marker})"
        if fdesc:
            hint += f": {fdesc}"
        field_hints.append(hint)
    # Path params
    for param in op.get("parameters", []):
        pname = param.get("name", "")
        ptype = param.get("schema", {}).get("type", "string")
        preq = param.get("required", False)
        pdesc = param.get("description", "")
        marker = "REQUIRED path param" if preq else "optional param"
        hint = f"  - {pname} ({ptype}, {marker})"
        if pdesc:
            hint += f": {pdesc}"
        field_hints.append(hint)
    if field_hints:
        description = description + "\nFields:\n" + "\n".join(field_hints)

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
                tool = _build_tool_for_endpoint(path, method, operation, requests_wrapper, spec)
                tools.append(tool)
                logger.debug(f"[CAI] 成功生成工具: {tool.name} ({method.upper()} {path})")
            except Exception as e:
                logger.warning(f"[CAI] 無法為 {method.upper()} {path} 生成工具: {e}")

    logger.info(f"[CAI] 共成功生成 {len(tools)} 個 API 工具。")
    return tools
