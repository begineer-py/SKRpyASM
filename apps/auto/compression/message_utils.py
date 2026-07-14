"""
Shared utilities for parsing LangChain message dicts stored in Message.message JSONField.

LangChain's `message_to_dict()` produces a *nested* shape:
    {"type": "tool", "data": {"content": "...", "name": "nmap", ...}}

Historically, many consumers in this codebase read `msg_data.get('content')` at the
top level — which silently returns '' because the real content lives under `data`.
This helper centralizes correct parsing and is backwards-compatible with legacy
messages that may have been written with flat shapes.
"""

from typing import Any, Dict, Optional


def extract_msg_fields(msg) -> Dict[str, Any]:
    """
    Uniformly extract fields from a Message instance's `message` JSONField.

    Args:
        msg: A Message model instance (expected to have `.message` JSONField),
             or a raw dict (in which case it is treated as the message JSON).

    Returns:
        Dict with keys:
            - type: str — top-level message type ('human' / 'ai' / 'tool' / 'system' / 'tool_call')
            - content: str — the message content (from data.content, falling back to top-level)
            - name: Optional[str] — tool name (for tool messages)
            - tool_calls: list — tool call invocations on an AIMessage
            - id: Optional[str] — message id (from data.id)
            - tool_call_id: Optional[str] — tool_call_id (for ToolMessage, required by LangChain reconstruction)
            - role: Optional[str] — convenience marker:
                      'tool_result' if type=='tool',
                      'tool_call'   if type=='ai' AND tool_calls present
        Never raises. Returns a safe empty-shape dict on any error.
    """
    try:
        if hasattr(msg, "message"):
            raw = msg.message or {}
        else:
            raw = msg or {}

        if not isinstance(raw, dict):
            return _empty_fields()

        msg_type = raw.get("type", "unknown") or "unknown"
        inner = raw.get("data") or {}
        if not isinstance(inner, dict):
            inner = {}

        content = inner.get("content")
        if content is None:
            content = raw.get("content", "")
        if not isinstance(content, str):
            # LangChain may store content as a list of blocks (e.g. multimodal);
            # collapse to a best-effort string.
            try:
                content = str(content)
            except Exception:
                content = ""

        name = inner.get("name") or raw.get("name")

        tool_calls = inner.get("tool_calls") or raw.get("tool_calls") or []
        if not isinstance(tool_calls, list):
            tool_calls = []

        msg_id = inner.get("id") or raw.get("id")
        tool_call_id = inner.get("tool_call_id") or raw.get("tool_call_id")

        role: Optional[str] = None
        if msg_type == "tool":
            role = "tool_result"
        elif msg_type == "ai" and tool_calls:
            role = "tool_call"

        return {
            "type": msg_type,
            "content": content,
            "name": name,
            "tool_calls": tool_calls,
            "id": msg_id,
            "tool_call_id": tool_call_id,
            "role": role,
        }
    except Exception:
        return _empty_fields()


def build_compressed_tool_dict(original_msg, compressed_content_str: str, tool_name: Optional[str] = None) -> dict:
    """
    建構 LangChain 相容的巢狀 dict 用於壓縮後的 ToolMessage。

    LangChain 的 `_message_from_dict` 期望巢狀格式：
        {"type": "tool", "data": {"content": "...", "tool_call_id": "...", ...}}

    `ToolMessage` 強制要求 `tool_call_id` 欄位（無預設值），
    因此本函式從原始訊息中保留 `tool_call_id`，若不存在則生成佔位符。

    Args:
        original_msg: 原始 Message model 實例（或 dict），用於提取 tool_call_id / name / id
        compressed_content_str: 壓縮後的內容字串
        tool_name: (選填) 覆寫工具名稱；若未提供則從 original_msg 提取

    Returns:
        LangChain 巢狀格式的 dict，可直接存入 Message.compressed_content
        並被 messages_from_dict() 正確重構為 ToolMessage
    """
    fields = extract_msg_fields(original_msg)
    if tool_name is None:
        tool_name = fields.get("name") or "unknown"

    # tool_call_id 是 ToolMessage 的必填欄位 — 從原始訊息保留或生成佔位符
    tool_call_id = fields.get("tool_call_id") or f"compressed_{getattr(original_msg, 'id', 'unknown')}"

    return {
        "type": "tool",
        "data": {
            "content": compressed_content_str,
            "name": tool_name,
            "tool_call_id": tool_call_id,
            "id": fields.get("id"),
            "additional_kwargs": {},
            "response_metadata": {},
            "type": "tool",
            "artifact": None,
            "status": "success",
        },
    }


def _empty_fields() -> Dict[str, Any]:
    return {
        "type": "unknown",
        "content": "",
        "name": None,
        "tool_calls": [],
        "id": None,
        "tool_call_id": None,
        "role": None,
    }
