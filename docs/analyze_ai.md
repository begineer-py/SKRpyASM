# Analyze AI App 智能分析

`analyze_ai` 是系統的智能大腦，利用生成式 AI 模型（如 Gemini, Mistral）對收集到的資產數據進行深度分析與風險評估。

## 功能概論

- **自動化評估**: 自動對發現的子域名、端口服務與網頁內容進行安全威脅評估。
- **資產分類**: 根據 AI 分析結果將資產標記為「重要」或進行分類。
- **多模型支持**: 通過代理服務支持多個 AI 提供商，確保分析過程的穩定性與備選方案。
- **批量處理**: 優化的批量分析機制，提高與 AI 交互的效率。

## API 接口

詳見 `apps/analyze_ai/api.py`：

- **`POST /analyze_ai/ips`**: 對完成 Nmap 掃描的 IP 發起 AI 分析。
    - **參數 (Payload)**: `ids` (List[int], 必填): IP 記錄的 ID 列表。
- **`POST /analyze_ai/subdomains`**: 對子域名發起 AI 分析。
    - **參數 (Payload)**: `ids` (List[int], 必填): 子域名記錄的 ID 列表。
- **`POST /analyze_ai/urls`**: 對完成 URL 掃描的 URL 結果發起 AI 分析。
    - **參數 (Payload)**: `ids` (List[int], 必填): URLResult 記錄的 ID 列表。

## 內部 Tasks

- **`trigger_ai_analysis_for_*`**: 任務調度器，負責批量初始化。
- **`perform_ai_analysis_for_*_batch`**: 
    - 採用 **工廠模式 (Factory Pattern)** 實作。
    - 核心邏輯封裝於 `_execute_ai_batch`。
    1. 根據 **Asset Registry** 取得特定的資產配置（如 model, prompt, GraphQL fetcher）。
    2. 自動處理狀態標記 (PENDING -> RUNNING)。
    3. 聚合資產詳細數據。
    4. 調用 AI 代理獲取分析結果。
    5. 解析 JSON 回應並寫入對應的分析模型。
