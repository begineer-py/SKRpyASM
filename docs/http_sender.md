# HTTP Sender App 網絡工具

`http_sender` 應用提供通用的 HTTP 發送能力與基礎的模糊測試（Fuzzing）支持。

## 功能概論

- **通用請求**: 作為系統內部發送 Web 請求的統一接口（在某些場景下）。
- **Endpoint Fuzzing**: 針對識別出的 Web 端點執行基礎的 API 或參數 Fuzzing。

## API 接口

詳見 `apps/http_sender/api.py`：

- **`POST /http_sender/fuzz`**: 對指定端點發起模糊測試與主動探測。
    - **參數 (Payload)**:
        - `id` (int, 必填): Endpoint 的 ID。
        - `cookies` (string/dict, 選填): 掃描時使用的會話 Cookie。
- **`POST /http_sender/ingest_url`**: （內部接口）手動匯入或更新 URL 與端點。
    - **參數 (Payload)**: `URLIngestSchema` (包含 `url`, `method`, `parameters` 列表等)。

## 內部 Tasks

- **`fuzz_endpoint(endpoint_id, cookies)`**: 
    1. 獲取 Endpoint 定義。
    2. 使用字典或預設模式發送 Fuzzing 請求。
    3. 紀錄回應結果中的異常或敏感發現。
