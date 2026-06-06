# AI Assistant App

`apps/ai_assistant` 提供 assistant/thread/message 的 REST API，以及 message 與 step log 的 SSE 串流介面。

## 實際職責

- 列出可用 assistant
- 建立與管理 thread
- 建立、列出、刪除 message
- 支援 thread 綁定 target
- 提供 token streaming 與 step log streaming

## 公開 API 現況

路由由 `apps/ai_assistant/urls.py` 掛在 `/api/assistant/`。

### REST endpoints

來源：`apps/ai_assistant/api/views.py`

- `GET /api/assistant/assistants/`
- `GET /api/assistant/assistants/{assistant_id}/`
- `GET /api/assistant/threads/`
- `POST /api/assistant/threads/`
- `GET /api/assistant/threads/{thread_id}/`
- `PATCH /api/assistant/threads/{thread_id}/`
- `DELETE /api/assistant/threads/{thread_id}/`
- `GET /api/assistant/threads/{thread_id}/messages/`
- `POST /api/assistant/threads/{thread_id}/messages/`
- `DELETE /api/assistant/threads/{thread_id}/messages/{message_id}/`
- `PATCH /api/assistant/threads/{thread_id}/bind_target/`
- `DELETE /api/assistant/threads/{thread_id}/bind_target/`

### SSE endpoints

來源：`apps/ai_assistant/urls.py`

- `GET /api/assistant/threads/{thread_id}/messages/stream/`
- `GET /api/assistant/v1/steps/{step_id}/logs/stream/`

## 實作細節

### 模型位置

雖然 app 名稱是 `ai_assistant`，但實際 `Thread` / `Message` 模型已位於 `apps/core`。

這表示：

- `ai_assistant` 是 API / assistant framework 層
- `core` 是資料模型承載層

### auth 現況

`apps/ai_assistant/api/views.py` 目前使用 `dummy_auth()`：

- 會注入第一個 user
- 若沒有 user，會建立 `anonymous_dummy`

這代表目前這組 API 的認證邏輯偏向開發/測試模式，對外文檔不應誤寫成正式的多租戶安全接口。

### streaming 行為

- message stream 會先持久化 human message，再開始 token streaming
- step log stream 會將 `StepLog` 以 SSE 持續推送給前端

## 文檔注意事項

- 不要再把它寫成舊的 `django_ai_assistant`
- 應明確區分：
  - REST API
  - SSE endpoints
  - 資料模型實際在 `core`

## 相關檔案

- `apps/ai_assistant/urls.py`
- `apps/ai_assistant/api/views.py`
- `apps/ai_assistant/api/stream_views.py`
- `apps/ai_assistant/api/logs_stream_views.py`

---

_最后更新：2026-06-06_
