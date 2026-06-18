# Auto App

`apps/auto` 目前應視為內部自動化框架，而不是對外主要 API 模組。

## 實際職責

- 驅動 `Overview` 的自動執行循環
- 管理 `AutomationAgent` 執行上下文
- 提供 skill verification / merge 相關任務
- 提供 agent registry 與 agent 設定整合入口
- 提供 agent 驅動的記憶壓縮（MemoryMixin：review_chunks → decide_chunk → apply_compression）
- 提供 ExecutionGraph 節點建立與事件發送（ExecutionService.create_node / ExecutionService.emit_event）

## 公開 API 現況

目前 `apps/auto/api.py` 只保留一個已廢棄端點：

- `POST /api/auto/convert/{asset_type}`

此端點會直接回 `410 Gone`，原因是舊的 `IPAIAnalysis/SubdomainAIAnalysis/URLAIAnalysis` 流程已被 `InitialAIAnalysis + Overview` 取代。

## 真正活躍的執行入口

### Celery tasks

`apps/auto/tasks/__init__.py`：

- `apps.auto.tasks.preprocess_data`
  - 已廢棄，現在只是委託到 `analyze_ai.tasks.periodic_initial_analysis_bootstrapper`
- `apps.auto.tasks.auto_execute_plan`
  - 目前最重要的自動執行入口
  - 會處理 `PLANNING`、`EXECUTING`、`NEEDS_GUIDANCE` 狀態的 `Overview`
- `apps.auto.tasks.run_automation_agent_async`
  - 非同步執行 `AutomationAgent`

`apps/auto/tasks/skill_tasks.py`：

- skill verification
- merge evaluation
- pending merge execution

## 與其他 app 的關係

- 依賴 `apps/analyze_ai` 先建立 `InitialAIAnalysis` 與 `Overview`
- 依賴 `apps/core` 提供 `Overview`、`ExecutionGraph`/`ExecutionNode`、`Thread`、`ThreadEvent` 等核心模型
- 透過 `apps/ai_assistant` 的 thread/message/event 能力承載 agent 對話與 ExecutionGraph 事件

## 關鍵實作細節

### `auto_execute_plan()` 的行為

- 對卡住在 `PLANNING` 且沒有待執行 node 的 `Overview` 自動補觸發 planning
- 對 `NEEDS_GUIDANCE` 狀態自動生成戰略指導並回寫 thread
- 對 `EXECUTING` 狀態建立 `ExecutionNode`，然後啟動 `AutomationAgent`
- 會先收集真實的 asset IDs，避免 agent 幻覺捏造 ID

### thread 建立方式

若 `Overview` 尚未綁定 thread，`auto_execute_plan()` 會自動建立：

- thread 名稱格式：`Auto-Pentest: <target> (Overview <id>)`
- assistant_id：`automation_agent`

### 記憶壓縮（MemoryMixin）

```python
class MemoryMixin:
    """Agent 自管理 context，透過 3 個工具處理記憶壓縮"""
```

三階段流程：
1. **review_chunks()** — 讀取所有訊息，經 LLM 生成 GlobalContextOverview，分割為 THINK→ACT→RESULT chunks
2. **decide_chunk(chunk_index, strategy)** — Agent 選擇 RETAIN / TEXTUALIZE / DISCARD（使用 `compressed_content` + `compression_applied` 欄位，不刪除原始訊息）
3. **apply_compression()** — 最終確認決策，更新 `ThreadCompressionState`

觸發條件：`CompressionStateEvaluator`（`compression_middleware.py`）在 40+ 新訊息後標記 `requires_compression=True`

### Auto-ID Injection

所有註冊到 agent 的工具都會經過雙層 ID 注入處理（`apps/ai_assistant/helpers/assistants.py`）：

1. **Schema 層**：從 `args_schema` 自動移除 `overview_id`/`thread_id`/`parent_thread_id`，LLM 無法在 tool call 中捏造 ID
2. **Runtime 層**：`as_graph().with_structured_output()` 檢查原始函式簽名，若含 `overview_id` 則使用閉包注入 Agent 實例屬性值

### Skill 系統（僅 `agent_skill` 模式）

`apps/auto/assistants/assistants.py` 中的 `SkillMixin` 提供技能管理工具：

- `request_skill_creation(skill_template_id, reasoning)` — 請求將 SkillTemplate 提升為正式技能
- `has_io_contract` — `SkillTemplate` 欄位，標記模板是否具備輸入輸出協議

舊的 `promote_successful_script()` 已廢棄，全面改用 `request_skill_creation`。

### TaskNode / AgentNode 模式

- **TaskNode**：透過 `_is_tool_mode()` 檢查工具類別；`_run_bootstrapped()` 啟動子 agent，`_get_tools()` 封裝工具註冊
- **AgentNode**：繼承自 TaskNode，在 Planning 階段預覽子 agent 行動，對 `EXECUTING` 階段委託給 TaskNode 的 `aresume`

## 文檔注意事項

- 不要再把 `/api/auto` 寫成當前主要操作入口
- 對外文檔應明確區分：
  - 公開 API 已廢棄
  - 內部自動化框架仍然是活躍功能

## 相關檔案

- `apps/auto/api.py`
- `apps/auto/tasks/__init__.py`
- `apps/auto/tasks/skill_tasks.py`
- `apps/auto/agent_registry.py`
- `apps/auto/assistants/planning_agent.py`
- `apps/auto/assistants/assistants.py`
- `apps/auto/tools/memory_tools.py`
- `apps/auto/tools/execution_tools.py`

---

_最后更新：2026-06-15_
