# Auto App

`apps/auto` 目前應視為內部自動化框架，而不是對外主要 API 模組。

## 實際職責

- 驅動 `Overview` 的自動執行循環
- 管理 `AutomationAgent` 執行上下文
- 提供 skill verification / merge 相關任務
- 提供 agent registry 與 agent 設定整合入口

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
- 依賴 `apps/core` 提供 `Overview`、`Step`、`Thread` 等核心模型
- 透過 `apps/ai_assistant` 的 thread/message 能力承載 agent 對話

## 關鍵實作細節

### `auto_execute_plan()` 的行為

- 對卡住在 `PLANNING` 且沒有待執行 step 的 `Overview` 自動補觸發 planning
- 對 `NEEDS_GUIDANCE` 狀態自動生成戰略指導並回寫 thread
- 對 `EXECUTING` 狀態建立執行 step，然後啟動 `AutomationAgent`
- 會先收集真實的 asset IDs，避免 agent 幻覺捏造 ID

### thread 建立方式

若 `Overview` 尚未綁定 thread，`auto_execute_plan()` 會自動建立：

- thread 名稱格式：`Auto-Pentest: <target> (Overview <id>)`
- assistant_id：`automation_agent`

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

---

_最后更新：2026-06-06_
