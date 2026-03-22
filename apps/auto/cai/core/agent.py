"""
apps/auto/cai/core/agent.py

AI Agent 執行核心 (Orchestrator)
──────────────────────────────────────
核心職責:
  1. 接收 Agent 配置、用戶指令與系統指令
  2. 實現 Tool Calling 循環 (支持多輪工具調用)
  3. 解析 AI 回傳的結構化數據 (JSON)
"""

import json
import logging
import requests
import os
from typing import List, Dict, Any, Optional
from django.conf import settings
from .tool import Tool

logger = logging.getLogger(__name__)

def run_agent(
    config: Dict[str, Any], 
    user_message: str, 
    system_message: str = "", 
    max_iterations: int = 10
) -> Dict[str, Any]:
    """
    驅動 AI Agent 執行任務。支持 Tool Calling 循環。
    """
    from c2_core.config.config import Config
    
    # 1. 獲取 AI API URL
    ai_url = getattr(Config, "gemini_json_ai", None) or os.getenv("AI_API_URL")
    if not ai_url:
        logger.error("[AgentCore] 未設定 AI API URL。")
        return {"type": "error", "error": "AI API URL not configured"}

    # 2. 獲取可用工具
    # 支援兩種格式：
    #   (a) @function_tool 裝飾過的 wrapper 函數：透過 t_func.tool 取得 Tool instance
    #   (b) 直接的 Tool dataclass instance（來自 api_tool_factory.build_tools_from_openapi）
    raw_tools = config.get("tools", [])
    tools_map: Dict[str, Any] = {}
    tools_schema = []

    for t_func in raw_tools:
        # (a) @function_tool wrapper：有 .tool attribute
        tool_inst = getattr(t_func, "tool", None)
        # (b) 直接的 Tool dataclass instance
        if tool_inst is None and isinstance(t_func, Tool):
            tool_inst = t_func
        if tool_inst:
            tools_map[tool_inst.name] = tool_inst
            tools_schema.append({
                "name": tool_inst.name,
                "description": tool_inst.description,
                "parameters": tool_inst.parameters
            })

    # 3. 初始消息
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": user_message})

    # 4. 執行循環
    for i in range(max_iterations):
        logger.debug(f"[AgentCore] 開始第 {i+1} 輪迭代...")
        
        try:
            # 調用 AI
            payload = {
                "messages": messages,
                "tools": tools_schema if tools_schema else None
            }
            
            resp = requests.post(ai_url, json=payload, timeout=120)
            resp.raise_for_status()
            ai_data = resp.json()
            
            # AI 回應解析 (假設格式包含 content 和可選的 tool_calls)
            content = ai_data.get("content") or ""
            tool_calls = ai_data.get("tool_calls", [])
            
            # 更新消息歷史 (Assistant)
            messages.append({
                "role": "assistant", 
                "content": content,
                "tool_calls": tool_calls if tool_calls else None
            })

            # 如果沒有工具調用，則視為最終輸出
            if not tool_calls:
                logger.debug("[AgentCore] AI 未發送工具調用，迭代結束。")
                try:
                    # 嘗試解析為 JSON (AutomationAgent 預期格式)
                    return _parse_json_result(content)
                except Exception as e:
                    logger.warning(f"[AgentCore] 最終回應非標準 JSON: {e}")
                    return {"type": "sync_done", "output": content, "analysis": "AI 結束對話"}

            # 處理工具調用
            for tc in tool_calls:
                tool_name = tc.get("name")
                tool_args = tc.get("arguments")
                if isinstance(tool_args, str):
                    tool_args = json.loads(tool_args)
                
                logger.info(f"[AgentCore] 執行工具: {tool_name}({tool_args})")
                
                if tool_name in tools_map:
                    try:
                        tool_result = tools_map[tool_name].func(**tool_args)
                        # 將結果轉為字串
                        if not isinstance(tool_result, str):
                            tool_result = json.dumps(tool_result, ensure_ascii=False)
                    except Exception as e:
                        logger.error(f"[AgentCore] 工具 {tool_name} 執行失敗: {e}")
                        tool_result = f"Error: {str(e)}"
                else:
                    tool_result = f"Error: Tool '{tool_name}' not found."

                # 更新消息歷史 (Tool Result)
                messages.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": tool_result,
                    "tool_call_id": tc.get("id")
                })
            
            # 繼續下一輪迭代 (讓 AI 分析工具結果)
            
        except Exception as e:
            logger.exception(f"[AgentCore] API 請求或處理異常: {e}")
            return {"type": "error", "error": str(e)}

    return {"type": "error", "error": "Reached maximum iterations"}

def _parse_json_result(content: str) -> Dict[str, Any]:
    """提取並解析 AI 回應中的 JSON 區塊。"""
    content = content.strip()
    # 嘗試尋找 markdown json 區塊
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
         content = content.split("```")[1].split("```")[0].strip()
    
    return json.loads(content)
