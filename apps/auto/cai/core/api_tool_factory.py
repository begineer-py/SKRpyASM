"""
apps/auto/cai/core/api_tool_factory.py

OpenAPI Schema 驅動的 AI 工具自動工廠。

從 Django Ninja 的內建 OpenAPI 3.0 Schema 讀取所有平台 API 端點，
動態生成 AI Agent 可調用的 Tool 列表。

不需要手寫任何 @function_tool wrapper。每當新增 API 端點，
只需確保對應的 Router prefix 在 include_prefixes 內，Agent 便自動獲得該工具。

用法:
    from apps.auto.cai.core.api_tool_factory import build_tools_from_openapi

    tools = build_tools_from_openapi(
        include_prefixes=["/subfinder", "/nmap", "/nuclei", "/analyze_ai"],
        exclude_prefixes=["/auto/resume"],
    )
"""

import json
import logging
import requests
from typing import Any, Callable, Dict, List, Optional

from django.conf import settings

from .tool import Tool

logger = logging.getLogger(__name__)

# 平台 REST API 的內部 Base URL
API_BASE_URL = getattr(settings, "INTERNAL_API_BASE_URL", "http://127.0.0.1:8000/api")


# =============================================================================
# 工具名稱生成
# =============================================================================

def _path_to_name(method: str, path: str) -> str:
    """
    將 HTTP method + path 轉換為合法的工具名稱。

    例如:
        POST  /subfinder/start_subfinder  →  post_subfinder_start_subfinder
        GET   /targets/{id}/seeds         →  get_targets_id_seeds
    """
    # 去除路徑參數符號 {} 並標準化分隔符
    clean = (
        path.strip("/")
        .replace("/", "_")
        .replace("-", "_")
        .replace("{", "")
        .replace("}", "")
    )
    return f"{method.lower()}_{clean}"


# =============================================================================
# 動態 HTTP 執行器生成
# =============================================================================

def _make_executor(method: str, path: str) -> Callable:
    """
    為指定的 method + path 生成一個 HTTP 請求執行函數。

    使用閉包綁定 method 和 path，讓每個 Tool 持有獨立且正確的執行器。
    路徑參數（如 {id}）需透過 kwargs 提供，自動注入到 URL 中。
    """
    def executor(**kwargs) -> str:
        # 處理路徑參數（path params），將 kwargs 中匹配的 key 注入到 URL
        resolved_path = path
        remaining_kwargs = {}
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            if placeholder in resolved_path:
                resolved_path = resolved_path.replace(placeholder, str(value))
            else:
                remaining_kwargs[key] = value

        url = f"{API_BASE_URL}{resolved_path}"

        try:
            if method.upper() in ("GET", "DELETE"):
                resp = requests.request(
                    method, url, params=remaining_kwargs, timeout=30
                )
            else:
                resp = requests.request(
                    method, url, json=remaining_kwargs, timeout=30
                )
            resp.raise_for_status()
            return json.dumps(resp.json(), ensure_ascii=False, indent=2)
        except requests.HTTPError as e:
            logger.error(f"API call HTTP error [{method.upper()} {url}]: {e}")
            try:
                return f"Error {e.response.status_code}: {e.response.text[:500]}"
            except Exception:
                return f"HTTP Error: {str(e)}"
        except Exception as e:
            logger.error(f"API call failed [{method.upper()} {url}]: {e}")
            return f"Error: {str(e)}"

    executor.__name__ = _path_to_name(method, path)
    return executor


# =============================================================================
# OpenAPI Schema 解析
# =============================================================================

def _resolve_ref(ref: str, components: Dict) -> Dict:
    """解析 OpenAPI $ref，從 components/schemas 中取得實際 schema。"""
    # ref 格式: "#/components/schemas/SchemaName"
    parts = ref.lstrip("#/").split("/")
    result = components
    for part in parts:
        result = result.get(part, {})
    return result


def _extract_parameters(spec: Dict, schema_dict: Dict) -> Dict:
    """
    從 OpenAPI 端點 spec 中提取參數 schema，統一格式為：
    { "type": "object", "properties": {...}, "required": [...] }
    """
    components = schema_dict.get("components", {})
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    # Path / Query 參數
    for param in spec.get("parameters", []):
        pname = param["name"]
        param_schema = param.get("schema", {"type": "string"})

        # 若 param schema 本身是 $ref，先解析
        if "$ref" in param_schema:
            param_schema = _resolve_ref(param_schema["$ref"], components)

        parameters["properties"][pname] = param_schema
        if param.get("required"):
            parameters["required"].append(pname)

    # Request Body（POST / PUT / PATCH）
    body = spec.get("requestBody", {})
    body_schema = (
        body.get("content", {})
        .get("application/json", {})
        .get("schema", {})
    )

    # 解析 $ref
    if "$ref" in body_schema:
        body_schema = _resolve_ref(body_schema["$ref"], components)

    # allOf 模式（Ninja 有時使用）
    if "allOf" in body_schema:
        merged: Dict = {"properties": {}, "required": []}
        for sub in body_schema["allOf"]:
            resolved = _resolve_ref(sub["$ref"], components) if "$ref" in sub else sub
            merged["properties"].update(resolved.get("properties", {}))
            merged["required"].extend(resolved.get("required", []))
        body_schema = merged

    if body_schema.get("properties"):
        parameters["properties"].update(body_schema["properties"])
        # 合併 required（去重）
        existing = set(parameters["required"])
        for r in body_schema.get("required", []):
            if r not in existing:
                parameters["required"].append(r)

    return parameters


# =============================================================================
# 主工廠函數
# =============================================================================

def build_tools_from_openapi(
    include_prefixes: Optional[List[str]] = None,
    exclude_prefixes: Optional[List[str]] = None,
    schema_dict: Optional[Dict] = None,
) -> List[Tool]:
    """
    從 OpenAPI schema 自動生成 AI 可調用的 Tool 列表。

    核心邏輯：
    1. 從 Django Ninja API 物件直接讀取 OpenAPI schema（無需 HTTP）
    2. 按 include_prefixes / exclude_prefixes 過濾路徑
    3. 為每個 (method, path) 動態生成 Tool 物件：
       - name:  由 method + path 自動推導
       - description: 優先取 OpenAPI summary，退而求其次用 description
       - parameters: 從 path params + request body 合併
       - func:  由 _make_executor 動態生成的 HTTP 請求函數

    Args:
        include_prefixes:  只匹配指定前綴的路徑（如 ["/subfinder", "/nmap"]）
                           若為 None 則包含全部路徑
        exclude_prefixes:  排除指定前綴的路徑（如 ["/auto/resume"]）
                           若為 None 則不排除任何路徑
        schema_dict:       可直接傳入 schema dict（用於測試），
                           不傳則自動從 Django Ninja API 物件取得

    Returns:
        List[Tool]: 可直接插入 agent_configs.py tools 列表的工具物件列表

    Example:
        >>> tools = build_tools_from_openapi(
        ...     include_prefixes=["/subfinder", "/nmap", "/nuclei", "/analyze_ai",
        ...                       "/targets", "/scheduler", "/get_all_url"],
        ...     exclude_prefixes=["/auto/resume"],
        ... )
        >>> print(len(tools))
        27
    """
    # ── 1. 取得 Schema ──────────────────────────────────────────────────────────
    if schema_dict is None:
        try:
            # 直接從 Django Ninja API 物件取 schema，不發 HTTP request
            from c2_core.urls import api
            schema_dict = api.get_openapi_schema()
            logger.info("APIToolFactory: 已從 Django Ninja API 物件讀取 OpenAPI Schema")
        except Exception as e:
            logger.error(f"APIToolFactory: 無法讀取 OpenAPI Schema: {e}")
            return []

    tools: List[Tool] = []
    paths = schema_dict.get("paths", {})
    skipped = 0

    # ── 2. 遍歷路徑 ────────────────────────────────────────────────────────────
    for path, methods in paths.items():
        # 過濾 include
        if include_prefixes and not any(path.startswith(p) for p in include_prefixes):
            skipped += 1
            continue
        # 過濾 exclude
        if exclude_prefixes and any(path.startswith(p) for p in exclude_prefixes):
            skipped += 1
            continue

        # ── 3. 遍歷 HTTP Methods ────────────────────────────────────────────────
        for method, spec in methods.items():
            if not isinstance(spec, dict):
                # OpenAPI path-level parameters 是 list，跳過
                continue
            if method.lower() in ("head", "options"):
                continue

            # 提取描述（優先 summary → description → fallback）
            description = (
                spec.get("summary")
                or spec.get("description")
                or f"{method.upper()} {path}"
            )

            # 取得標籤作為提示（可選）
            tags = spec.get("tags", [])
            if tags:
                description = f"[{', '.join(tags)}] {description}"

            # 提取參數
            parameters = _extract_parameters(spec, schema_dict)

            # 生成工具
            tool = Tool(
                name=_path_to_name(method, path),
                description=description,
                parameters=parameters,
                func=_make_executor(method, path),
            )
            tools.append(tool)

    logger.info(
        f"APIToolFactory: 自動生成 {len(tools)} 個工具 "
        f"（已跳過 {skipped} 個路徑）"
    )
    return tools


# =============================================================================
# 預設平台工具集（常用白名單）
# =============================================================================

# 平台核心掃描與分析 API 的 prefix 白名單
PLATFORM_API_PREFIXES = [
    "/targets",
    "/subfinder",
    "/nmap",
    "/nuclei",
    "/get_all_url",
    "/flaresolverr",
    "/analyze_ai",
    "/scheduler",
    "/http_sender",
]

# 不應暴露給 AI 的路徑
EXCLUDED_API_PREFIXES = [
    "/auto/resume",   # 異步回調入口，不由 AI 直接調用
    "/api_keys",      # 金鑰管理，安全敏感
]


def get_platform_tools() -> List[Tool]:
    """
    返回平台標準工具集（使用內建白名單，排除敏感路徑）。
    等效於:
        build_tools_from_openapi(
            include_prefixes=PLATFORM_API_PREFIXES,
            exclude_prefixes=EXCLUDED_API_PREFIXES,
        )
    """
    return build_tools_from_openapi(
        include_prefixes=PLATFORM_API_PREFIXES,
        exclude_prefixes=EXCLUDED_API_PREFIXES,
    )
