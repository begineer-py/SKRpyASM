"""
apps/auto/cai/core/tool.py

簡化的工具註冊和架構生成邏輯，靈感來自 CAI。
"""

import inspect
import json
import logging
import functools
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type, ForwardRef

from pydantic import BaseModel, Field, create_model

logger = logging.getLogger(__name__)

@dataclass
class Tool:
    """工具類，包含名稱、描述、參數架構和函數引用"""
    name: str
    description: str
    parameters: Dict[str, Any]
    func: Callable

def _parse_docstring(doc: str) -> str:
    """簡單提取 Docstring 的第一段作為描述。"""
    if not doc:
        return ""
    lines = [L.strip() for L in doc.strip().splitlines()]
    if not lines:
        return ""
    # Find the end of the first paragraph
    summary_lines = []
    for line in lines:
        if not line:
            break
        summary_lines.append(line)
    return " ".join(summary_lines)

def function_tool(func: Callable) -> Tool:
    """
    裝飾器：將 Python 函數轉換為帶有 JSON Schema 的 Tool。
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    # 1. 提取名稱和描述
    name = func.__name__
    description = _parse_docstring(func.__doc__ or "")

    # 2. 使用 inspect 和 Pydantic 提取參數
    sig = inspect.signature(func)
    fields = {}
    
    for param_name, param in sig.parameters.items():
        if param_name in ('self', 'cls'):
            continue
            
        # 如果有類型提示則使用，否則默認為 Any
        hint = param.annotation if param.annotation is not inspect._empty else Any
        
        # 處理默認值
        if param.default is not inspect._empty:
            fields[param_name] = (hint, Field(default=param.default))
        else:
            fields[param_name] = (hint, Field(...))

    # 動態創建 Pydantic 模型以生成 JSON Schema
    DynamicModel = create_model(f"{name}_Params", **fields)
    schema = DynamicModel.model_json_schema()

    # 清理架構以便 LLM 消耗（如果需要可以移除 pydantic 特有的欄位）
    # 通常 LLM 期望 "parameters": { "type": "object", "properties": { ... }, "required": [...] }
    
    tool_instance = Tool(
        name=name,
        description=description,
        parameters=schema,
        func=func
    )
    
    # 將工具實例附加到包裝後的函數上
    wrapper.tool = tool_instance
    return wrapper
