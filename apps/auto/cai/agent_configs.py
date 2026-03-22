"""
apps/auto/cai/agent_configs.py

為 auto app 內不同的 AI Agent 角色進行配置。

升級記錄（2026-03-22）：
  - 平台 API 工具改由 APIToolFactory 從 OpenAPI Schema 自動生成
  - 不再需要手動 import 每個 wrapper 函數
  - 新增平台 API 時，只要 prefix 在白名單內就自動生效
"""

import logging

from .core.api_tool_factory import build_tools_from_openapi, PLATFORM_API_PREFIXES, EXCLUDED_API_PREFIXES
from .core.generic_linux import generic_linux_command
from .core.reasoning import reasoning

logger = logging.getLogger(__name__)

# =============================================================================
# 工廠生成平台工具集
# =============================================================================
# 在模組載入時（Django 啟動後）從 OpenAPI schema 自動讀取所有平台 API 工具。
# 若 Django 尚未就緒，工廠會返回空列表並記錄錯誤（不阻塞啟動）。

_PLATFORM_TOOLS = build_tools_from_openapi(
    include_prefixes=PLATFORM_API_PREFIXES,
    exclude_prefixes=EXCLUDED_API_PREFIXES,
)

logger.info(
    f"[AgentConfigs] 平台工具集已載入，共 {len(_PLATFORM_TOOLS)} 個自動生成工具"
)

# 特殊工具：需手寫的非 HTTP 工具（CLI 執行、推理鏈）
_SPECIAL_TOOLS = [generic_linux_command, reasoning]

# GraphQL 工具（仍使用 @function_tool，因為需要 Hasura admin header）
from apps.auto.tools import (
    query_graphql,
    mutate_graphql,
    get_graphql_schema_info,
)
_GRAPHQL_TOOLS = [query_graphql, mutate_graphql, get_graphql_schema_info]


# =============================================================================
# Agent 角色配置
# =============================================================================

RECON_AGENT_CONFIG = {
    "name": "偵察代理 (ReconAgent)",
    "instructions": (
        "您是一個專門的偵察代理。您的目標是發現並詳細列出目標資產。"
        "使用平台 API 工具查詢子域名與 IP 資訊，"
        "並觸發 Subfinder 或 Nuclei tech scan 發現更多資產。"
        "如果您需要更深入的分析，請調用 analyze_ai 相關工具。"
    ),
    "tools": _SPECIAL_TOOLS + _PLATFORM_TOOLS,
}

EXPLOIT_AGENT_CONFIG = {
    "name": "漏洞評估代理 (ExploitAgent)",
    "instructions": (
        "您是一個漏洞評估與利用代理。您的目標是識別並驗證安全風險。"
        "審查資產詳情，並使用 Nuclei 工具探測風險。"
        "對於可疑資產，調用 analyze_ai 工具獲取 AI 深度洞察。"
    ),
    "tools": _SPECIAL_TOOLS + _PLATFORM_TOOLS,
}

AUTOMATION_AGENT_CONFIG = {
    "name": "自動化執行代理 (AutomationAgent)",
    "instructions": (
        "你是一個專業的滲透測試自動化執行代理。"
        "你的任務是依據給定的 Step 命令模板，選擇最合適的方式執行它。\n\n"
        "執行規則：\n"
        "1. **CLI 指令** (nmap, nuclei, curl 等): 使用 `generic_linux_command` 直接執行。\n"
        "2. **大規模系統工具** (subfinder, nuclei 全站掃描): 使用平台 API 工具觸發，"
        "   並在 payload 中添加 callback_step_id 以便異步回調。\n"
        "3. **需要更多上下文**: 先用 `query_graphql` 查詢所需資產資訊，"
        "   或用 `get_graphql_schema_info` 了解可用欄位。\n"
        "4. **記錄發現**: 執行後，用 `mutate_graphql` 更新 Step.note 欄位記錄關鍵發現。\n\n"
        "回傳格式：\n"
        '- 同步指令完成: {"type": "sync_done", "output": "...", "analysis": "..."}\n'
        '- 異步工具已觸發: {"type": "async_dispatched", "dispatched_tool": "...", "callback_step_id": step_id}\n'
        '- 執行失敗: {"type": "error", "error": "..."}'
    ),
    "tools": _SPECIAL_TOOLS + _GRAPHQL_TOOLS + _PLATFORM_TOOLS,
}

STRATEGY_AGENT_CONFIG = {
    "name": "戰略規劃代理 (StrategyAgent)",
    "instructions": (
        "你是一個資深的安全滲透測試架構師。"
        "你的任務是根據當前的目標資產清單、歷史執行記錄與已發現的漏洞，"
        "制定接下來的行動計畫。\n\n"
        "你的目標是：\n"
        "1. 擴展攻擊面 (發現更多子域名、IP 或 URL)。\n"
        "2. 深入挖掘已知漏洞 (嘗試驗證或橫向移動)。\n"
        "3. 確保測試覆蓋率。\n\n"
        "如果認為目前已有足夠發現或無進度空間，請回傳標註任務完成的報告。\n"
        "否則，請擬定一個或多個具體的操作步驟 (command_actions)。"
    ),
    "tools": [reasoning] + _GRAPHQL_TOOLS + _PLATFORM_TOOLS,
}
