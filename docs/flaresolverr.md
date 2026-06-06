# FlareSolverr App

`apps/flaresolverr` 是受保護頁面抓取、反機器人繞過與內容回寫的專用 app。

## 實際職責

- 啟動 FlareSolverr crawler
- 發送單次 HTTP request 並支援 session reuse
- 觸發 JavaScript 內容分析
- 驗證 URL/hostname 是否能關聯到有效 `Target`

## 公開 API 現況

來源：`apps/flaresolverr/api.py`

- `POST /api/flaresolverr/start_scanner`
- `POST /api/flaresolverr/check_flaresolverr`
- `POST /api/flaresolverr/json_analyze`
- `POST /api/flaresolverr/send_request`

## 背景任務

主要任務包括：

- `perform_scan_for_url`
- `perform_flaresolverr_request`
- `perform_js_scan`
- `download_external_js`

## 實作細節

### 資產所有權驗證

不論 crawler 或單次 request，API 都會先嘗試從以下來源取得 `target_id`：

- 顯式 `target_id`
- `seed_id`
- URL hostname 對應的 `Subdomain`

若無法映射到有效 `Target`，請求會被拒絕。

### crawler 路徑

`start_scanner` 會：

- 派發 `perform_scan_for_url`
- 由 task 進一步建立/更新 `Subdomain`、`URLResult` 等資料
- 呼叫 orchestrator 進行內容擷取與資產回寫

### 單次 request 路徑

`send_request` 會：

- 派發 `perform_flaresolverr_request`
- 支援：
  - headers
  - cookies
  - body
  - content-type
  - host header
  - `session_key`
  - `refresh_session`

這條路徑特別適合 AI workflow 在登入、多步驟表單或 CF/WAF 保護下重複使用同一 session。

### 健康檢查

- `check_flaresolverr` 透過 `httpx.AsyncClient` 檢查 FlareSolverr 是否可連線

## 文檔注意事項

- 應明確區分 crawler 與 send_request 兩條路徑
- 應強調 session reuse 是當前實作的一個重要能力

## 相關檔案

- `apps/flaresolverr/api.py`
- `apps/flaresolverr/tasks/spider.py`
- `apps/flaresolverr/tasks/http_action.py`
- `apps/flaresolverr/tasks/js_trigger.py`

---

_最后更新：2026-06-06_
