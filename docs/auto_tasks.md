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

系統針對不同資產類型提供專屬的自動化啟動任務：

### 1. IP 自動化 (`start_ip_ai_analysis`)
- **輸入**: `IPAIAnalysis` ID。
- **流程**: 讀取分析記錄中的 `command_actions` -> GraphQL 查詢 IP 最新快照 -> 呼叫核心引擎建立 Step 鏈。

### 2. 子域名自動化 (`start_subdomain_ai_analysis`)
- **輸入**: `SubdomainAIAnalysis` ID。
- **流程**: 同上，針對 `Subdomain` 資產進行操作。

### 3. URL 自動化 (`start_url_ai_analysis`)
- **輸入**: `URLAIAnalysis` ID。
- **流程**: 同上，針對 `URLResult` 資產進行操作。

## 驗證機制 (Verification)

自動化系統支援 AI 提供的驗證模式：
- **Pattern**: 匹配字串或正則表達式。
- **Match Type**: 支援 `contains`, `regex` 等。
- **自動漏洞建立**: 若驗證通過，可配置為自動建立漏洞記錄。
