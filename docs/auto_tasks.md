# 自動化任務系統 (Auto Tasks)

`auto` 應用程式負責將 AI 的分析結果（`command_actions`）轉換為系統可執行的 `Step`、`Method`、`Payload` 與 `Verification` 鏈。

## 核心引擎：Step 建立

詳見 `apps/auto/tasks/start/common.py`。

### `create_steps_from_analysis`
此函數是自動化的核心，它接收 AI 產出的 `command_actions` 列表，並執行以下動作：
1. **正規化 (Normalize)**: 將不同格式的 action 統一為標準字典格式。
2. **工具偵測 (Tool Detection)**: 自動從指令字串中識別使用的工具（如 `nmap`, `nuclei`, `sqlmap` 等）。
3. **建立模型實例**:
    - **Step**: 儲存執行順序與指令模板。
    - **Method**: 儲存發送方法。
    - **Payload**: 儲存完整 action 內容。
    - **Verification**: 儲存驗證條件（Pattern, Match Type）。

## 自動化任務流程

系統採用 **工廠配置 (Registry-based)** 實作，針對不同資產類型提供統一的啟動邏輯：

### 1. 通用啟動助手 (`_start_asset_steps`)
- **輸入**: 資產類型 (`ip`, `subdomain`, `url`) 與分析記錄 ID。
- **流程**: 
    1. 從 **AssetStartRegistry** 取得對應模型的設定。
    2. 驗證記錄狀態，讀取 `command_actions`。
    3. 透過 GraphQL 查詢該資產的最新的快照資料。
    4. 呼叫核心引擎建立 `Step` 鏈。

### 2. 資產專屬 Tasks
以下任務皆為薄封裝 (Thin wrappers)，將實際工作委派給 `_start_asset_steps`：
- **`start_ip_ai_analysis`**: 處理 `IP` 資產。
- **`start_subdomain_ai_analysis`**: 處理 `Subdomain` 資產。
- **`start_url_ai_analysis`**: 處理 `URLResult` 資產。


## 驗證機制 (Verification)

自動化系統支援 AI 提供的驗證模式：
- **Pattern**: 匹配字串或正則表達式。
- **Match Type**: 支援 `contains`, `regex` 等。
- **自動漏洞建立**: 若驗證通過，可配置為自動建立漏洞記錄。

## 自主化循環與戰略規劃 (Autonomous Loop)

系統實現了全自動化的「執行-驗證-再規劃」的閉環邏輯，主要由以下機制驅動：

### 1. 驗證接續 (`_check_and_trigger_continuation`)
詳見 `apps/auto/tasks/evaluation/engine.py`。
當一個 `Step` 的所有驗證任務（Verification）都完成後，系統會自動檢查：
- 是否有下一個待執行的 `Step`？如果有，則調用 `run_step_execution`。
- 如果所有預定步驟皆已完成，則觸發 **戰略規劃引擎 (`propose_next_steps`)**。

### 2. 戰略規劃引擎 (`propose_next_steps`)
詳見 `apps/auto/tasks/start/planning.py`。
此任務使用 `apps/auto/cai/core/agent.py` 中的 `run_agent` 核心：
- **輸入**: 當前 Target 的所有掃描結果、漏洞發現與已執行歷史。
- **決策**: AI 分析下一步應該執行什麼動作（例如：發現 80 端口開放，建議啟動目錄爆破）。
- **產出**: 自動建立一組新的 `Step` 鏈，重新啟動執行循環。

### 3. AI Agent 核心 (`run_agent`)
- 支援 **多輪工具調用 (Tool Calling)**。
- 能自動調用平台內建工具（如 `generic_linux_command`）獲取更多現場資訊。
- 回傳結構化的 JSON 行動方案，由自動化引擎解析並落實。
