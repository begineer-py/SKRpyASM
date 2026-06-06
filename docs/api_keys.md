# API Keys App

`apps/api_keys` 不只是 API key CRUD。它同時承載工具配置匯出、Agent LLM config 管理與 LLM 連線測試。

## 實際職責

- 儲存與管理外部服務 API keys
- 匯出 Subfinder/Amass/GAU/Nuclei 配置檔
- 管理 `AgentLLMConfig`
- 測試任意 LLM 配置與指定 Agent 的有效配置

## 公開 API 現況

來源：`apps/api_keys/api.py`

### API Key 相關

- `GET /api/api_keys/supported-services`
- `POST /api/api_keys/`
- `GET /api/api_keys/`
- `POST /api/api_keys/bulk`
- `GET /api/api_keys/{api_key_id}`
- `PATCH /api/api_keys/{api_key_id}`
- `DELETE /api/api_keys/{api_key_id}`

### 工具配置下載

- `GET /api/api_keys/download?tool=subfinder|amass|gau|nuclei`

### Agent LLM Config

- `GET /api/api_keys/agent-configs/`
- `GET /api/api_keys/agent-configs/db/`
- `POST /api/api_keys/agent-configs/`
- `GET /api/api_keys/agent-configs/{agent_id}`
- `PUT /api/api_keys/agent-configs/{agent_id}`
- `DELETE /api/api_keys/agent-configs/{agent_id}`

### 測試端點

- `POST /api/api_keys/test-llm`
- `POST /api/api_keys/agent-configs/{agent_id}/test`

## 實作細節

### supported services

支援的 service 同時涵蓋：

- 掃描服務：如 `shodan`、`securitytrails`、`chaos`、`nvd`
- AI provider：如 `openai`、`anthropic`、`mistral`、`gemini`、`deepseek`

### AgentLLMConfig 合併邏輯

有效配置的優先級為：

- DB 記錄
- 全域預設值

目前程式中的註解也明確說明：不再依賴 per-agent env var override。

### 配置下載行為

- 下載端點會動態生成暫存檔
- 回傳後即刪除暫存檔

### agent 清單來源

- 透過 `apps.auto.agent_registry.discover_agent_ids()` 自動發現
- 新增含 `assistant_id` 的 agent 類別後，相關配置會自動進入可管理清單

## 文檔注意事項

- 不要只把這個 app 寫成「外部 API Key 管理」
- 對外文檔至少應補上：
  - AgentLLMConfig
  - config download
  - LLM connectivity test

## 相關檔案

- `apps/api_keys/api.py`
- `apps/api_keys/models.py`
- `apps/api_keys/utils.py`

---

_最后更新：2026-06-06_
