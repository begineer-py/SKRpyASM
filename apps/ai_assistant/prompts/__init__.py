"""AgentSpec / PromptSpec — 結構化 prompt 框架。

將 Agent 的五欄位任務定義（Goal/Background/Materials/Boundary/DoD）
與基本資訊（名稱/角色）以 dataclass 形式宣告，由框架統一 render 成系統提示。

兩種 Spec：
  - AgentSpec : 供 AIAssistant 子類（多輪、有工具）使用
  - PromptSpec: 供 utility agent（一次性 LLM 呼叫、.format() 樣板）使用
"""

from apps.ai_assistant.prompts.spec import (
    AgentSpec,
    PromptSpec,
    TaskDefinition,
    extract_json,
)

__all__ = [
    "AgentSpec",
    "PromptSpec",
    "TaskDefinition",
    "extract_json",
]
