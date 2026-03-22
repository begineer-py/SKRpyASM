# CAI Tool Integration Guide (協同 AI 工具集成指南)

本指南旨在說明如何利用 CAI (Collaborative AI) 框架，將平台工具與 AI Agent 進行深度集成，實現自動化滲透測試與資產分析。

## 核心概念

CAI 框架的核心是 **多輪工具調用 (Multi-turn Tool Calling)**。AI 不僅能產出文本，還能指揮系統執行指令並根據回傳結果進行下一輪決策。

### 1. Agent 執行核心 (`run_agent`)
位於 `apps/auto/cai/core/agent.py`，負責：
- 接收初始指令 (System & User Message)。
- 加載可用工具 Schema。
- 執行 **AI -> Tool -> AI** 的迭代循環。
- 解析最終的結構化分析結果 (JSON)。

### 2. 工具綁定 (Tool Binding)
所有與 AI 交出的工具必須經由 `Tool` 類裝飾。

```python
from apps.auto.cai.core.tool import tool

@tool
def generic_linux_command(command: str) -> str:
    """
    執行通用的 Linux 指令並回傳 stdout/stderr。
    """
    # 實作執行邏輯...
    return output
```

## 平台工具集成實踐

### 執行 Linux 指令
AI 最常使用的工具是 `generic_linux_command`。這使得 AI 可以直接調用系統中的 `nmap`, `nuclei`, `subfinder` 等二進制工具。

### 會話管理 (Session Management)
對於需要保持狀態或交互的工具，CAI 通過 `Session` 機制（`apps/auto/cai/core/session.py`）管理操作上下文，確保 AI 在多輪對話中能「記得」之前的執行環境。

## 自主循環 (Autonomous Loop)

系統實現了全自動化的「掃描-驗證-規劃」閉環：

1. **執行 (Execution)**: `run_step_execution` 驅動工具執行。
2. **驗證 (Verification)**: `process_verification` 根據策略（Regex, AI Judge）判斷結果。
3. **規劃 (Planning)**: 當所有 Step 完成後，`_check_and_trigger_continuation` 會觸發 **`propose_next_steps`**。
4. **續航**: AI 分析當前所有結果，並自動建立下一批 `Step`，重新進入循環。

## 配置建議

- **System Prompt**: 應明確定義 AI 的專家角色（如：高級滲透測試工程師）。
- **工具描述**: 工具的 `description` 是 AI 理解如何使用它的唯一來源，務必清晰描述參數意義。
- **Max Iterations**: 建議設置為 5-10 輪，以防止 AI 陷入無限思維循環。

---

> [!NOTE]
> 高階集成請參考 `apps/auto/tasks/evaluation/engine.py` 中的 `ai_judge` 實作方式，了解如何讓 AI 擔任漏洞裁判。
