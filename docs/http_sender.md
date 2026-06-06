# HTTP Sender App

`apps/http_sender` 目前的實際功能重心是 endpoint fuzzing，而不是通用 HTTP client 平台。

## 實際職責

- 接收指定 `Endpoint` 的 fuzzing 請求
- 透過 Hasura GraphQL 讀取 endpoint 與 parameter metadata
- 使用 `ffuf` 對參數逐一進行 payload 測試
- 在需要時嘗試透過 FlareSolverr 取得 Cloudflare clearance cookies

## 公開 API 現況

目前僅暴露一個端點：

- `POST /api/http_sender/fuzz`

來源：`apps/http_sender/api.py`

這個 API 會：

- 驗證 `Endpoint` 是否存在
- 將任務交給 Celery task `http_sender.fuzz_endpoint`

## 背景任務

來源：`apps/http_sender/tasks/fuzzer.py`

- `http_sender.fuzz_endpoint`

主要流程：

1. 透過 Hasura GraphQL 查出 `Endpoint`、對應 `URLResult`、以及所有參數
2. 根據參數資訊選擇 payload / wordlist
3. 若目標有 Cloudflare/WAF，嘗試透過 FlareSolverr 取得 cookies 與 user-agent
4. 使用 `ffuf` 對每個參數逐一 fuzz
5. 解析 `ffuf` JSON 輸出

## 實作細節

### 依賴項

- Hasura GraphQL
- `ffuf`
- FlareSolverr
- `apps/http_sender/payload_mapping.py`

### payload 與字典

- `payload_mapping.py` 用於根據參數類型選擇 payload
- `WORDLIST_MAP` 為 fallback 路徑配置

### cookies 處理

- API 允許傳入使用者 cookies
- task 會把使用者 cookies 與 FlareSolverr 取得的 clearance cookies 合併

## 文檔注意事項

- 不要再把此 app 寫成「HTTP request, fuzzing, and URL ingestion helpers」
- 目前更準確的描述是：
  - endpoint fuzzing entrypoint
  - ffuf + Hasura + FlareSolverr 整合層

## 相關檔案

- `apps/http_sender/api.py`
- `apps/http_sender/tasks/fuzzer.py`
- `apps/http_sender/payload_mapping.py`
- `apps/http_sender/PayloadMapping.md`

---

_最后更新：2026-06-06_
