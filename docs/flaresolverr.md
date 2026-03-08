# FlareSolverr App 網頁抓取與解析

`flaresolverr` 應用結合了 FlareSolverr 服務與自定義爬蟲，負責處理受 Cloudflare 等防護的站點，並分析網頁中的 JavaScript 資源。

## 功能概論

- **反爬蟲繞過**: 利用 FlareSolverr 獲取受保護網頁的渲染內容。
- **深度爬取**: 使用定製的 `Spider` 遞歸提取頁面中的鏈接、表單、注釋與 Meta 標籤。
- **JS 分析**: 提取並下載網頁引用的外部或內聯 JavaScript 文件，供進一步安全分析或 Fuzzing 使用。

## API 接口

詳見 `apps/flaresolverr/api.py`：

- **`POST /flaresolverr/start_scanner`**: 對目標 URL 啟動深度偵察（含 FlareSolverr 渲染）。
    - **參數 (Payload)**:
        - `url` (string, 必填): 目標 URL。
        - `method` (string, 必填): HTTP 方法（如 `GET`, `POST`）。
        - `seed_id` (int, 選填): 關聯的種子 ID。
        - `auto_create` (boolean, 預設 `false`): 若域名不存在是否自動創建資產。
- **`POST /flaresolverr/json_analyze`**: 發起 JS 智能審計。
    - **參數 (Payload)**:
        - `id` (int, 必填): JavaScriptFile 記錄的 ID。
        - `type` (string, 必填): 可選 `external` 或 `inline`。
- **`POST /flaresolverr/check_flaresolverr`**: 檢查支撐服務（FlareSolverr）是否在線。

## 內部 Tasks

- **`perform_scan_for_url`**: 核心深度偵察任務。
    1. **內容抓取**: 利用 `ReconOrchestrator` 決定是否調用 FlareSolverr 繞過防護並獲取渲染後的 HTML。
    2. **數據提取**: 提取並儲存 Form, Links, Comments, Meta Tags, Iframes 等安全特徵。
    3. **資產膨脹 (Asset Inflation)**: 自動發現頁面中的新 URL，並根據域名範圍自動關聯至 `Target` 並建立 `URLResult` 記錄。
- **`perform_js_scan`**: JS 智能審計任務。
    1. **下載與去重**: 下載外部 JS 並根據內容 Hash 進行全局去重。
    2. **AI 結構分析**: 使用 `ChompJS` 解析並配合 AI 模型對敏感變數/函數進行評分。
    3. **參數提取**: 調用 `SecurityAnalyzer` 自動枚舉 JS 中的隱蔽 Endpoint 與參數。
