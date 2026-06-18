# AI Assistant App

`apps/ai_assistant` 提供 assistant/thread/message 的 REST API，以及多種 SSE 串流介面（token streaming、ThreadEvent、MessageEvent）。

## 實際職責

- 列出可用 assistant
- 建立與管理 thread
- 建立、列出、刪除 message
- 支援 thread 綁定 target
- 提供 token streaming、ThreadEvent SSE、MessageEvent SSE
- Support 7 LLM providers：OpenAI, Anthropic (Claude), Google (Gemini), Mistral, Groq, Ollama, Together

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
- `GET /api/assistant/threads/{thread_id}/events/` — 查詢 ThreadEvent 列表（`after` 序列游標, `limit` 最多 500 筆）

### SSE endpoints

來源：`apps/ai_assistant/urls.py`

- `GET /api/assistant/threads/{thread_id}/messages/stream/` — LLM token streaming（一次性的請求-串流）
- `GET /api/assistant/threads/{thread_id}/messages/events/stream/` — MessageEvent SSE（持久訂閱，監聽新訊息寫入 DB，輪詢間隔 0.8s，10 分鐘閒置超時）
- `GET /api/assistant/threads/{thread_id}/events/stream/` — ThreadEvent SSE（持久訂閱，監聽 ThreadEvent 表，輪詢 0.5s，5 分鐘閒置超時，事件名稱對應 `event_type`）

## 實作細節

### 模型位置

雖然 app 名稱是 `ai_assistant`，但實際 `Thread` / `Message` / `ThreadEvent` 模型已位於 `apps/core`。

這表示：

- `ai_assistant` 是 API / assistant framework 層
- `core` 是資料模型承載層

### ThreadEvent 模型

```python
# apps/core/models/ai_models.py
class ThreadEvent(models.Model):
    thread = ForeignKey(Thread, on_delete=CASCADE)
    run_id = CharField(128, db_index=True)
    parent_run_id = CharField(128, null=True, db_index=True)
    event_type = CharField(64, db_index=True)   # 事件類型（如 scanner_dispatched, tool_call）
    node_name = CharField(128, null=True)        # ExecutionGraph 節點名稱
    tool_name = CharField(128, null=True)
    status = CharField(32, null=True)            # started/running/completed/succeeded/failed/error
    content = TextField()
    payload = JSONField(default=dict)
    sequence = BigIntegerField(db_index=True)    # 單調遞增序號（執行緒級別鎖保證無間隙）
    created_at = DateTimeField(auto_now_add=True)
```

`AgentEventService.emit()`（`apps/ai_assistant/services/events.py`）使用 `select_for_update` 執行緒鎖定 + `MAX(sequence)` 計算序號，保證每個 Thread 內的 `sequence` 嚴格遞增不重複。

### auth 現況

`apps/ai_assistant/api/views.py` 目前使用 `dummy_auth()`：

- 會注入第一個 user
- 若沒有 user，會建立 `anonymous_dummy`

這代表目前這組 API 的認證邏輯偏向開發/測試模式，對外文檔不應誤寫成正式的多租戶安全接口。

### streaming 行為

- **Message token stream**：先持久化 human message，再開始 `assistant.astream()` token streaming
- **MessageEvent stream**：輪詢 `Message` 表 `id > last_message_id` 的新記錄，用於頁面重新整理後重新獲取 AI 回覆
- **ThreadEvent stream**：輪詢 `ThreadEvent` 表 `sequence > last_sequence` 的新事件，用於即時顯示 agent 工具呼叫、掃描派遣等生命周期事件

### Provider 支援

`apps/ai_assistant/helpers/assistants.py` 中的 `PROVIDER_LLM_LOOKUP` 支援 7 個供應商：

| Provider | LangChain 模組 | 用途 |
|----------|---------------|------|
| `openai` | `langchain_openai.ChatOpenAI` | GPT-4 / GPT-4o |
| `anthropic` | `langchain_anthropic.ChatAnthropic` | Claude Sonnet / Haiku |
| `google` | `langchain_google_genai.ChatGoogleGenerativeAI` | Gemini Pro |
| `groq` | `langchain_groq.ChatGroq` | 極速推論（Llama 3, Mixtral） |
| `ollama` | `langchain_ollama.ChatOllama` | 本地開源模型（Llama 3, Qwen） |
| `mistral` | `langchain_mistralai.ChatMistralAI` | Mistral / Mixtral |
| `together` | `langchain_together.ChatTogether` | 雲端開源模型託管 |

### Auto-ID Injection

`assistants.py` 實作雙層 ID 自動注入：

1. **Schema 剝離**（`_set_method_tools()`）：從工具 `args_schema` 移除 `overview_id`/`thread_id`/`parent_thread_id`，LLM 無法幻覺這些 ID
2. **Runtime 注入**（`as_graph()`）：檢查原始函式簽名，若含 `overview_id` 則用閉包強制注入 Agent 實例屬性值

## 文檔注意事項

- 不要再把它寫成舊的 `django_ai_assistant`
- 應明確區分：
  - REST API
  - SSE endpoints（3 種不同用途）
  - 資料模型實際在 `core`

## 相關檔案

- `apps/ai_assistant/urls.py`
- `apps/ai_assistant/api/views.py`
- `apps/ai_assistant/api/stream_views.py`
- `apps/ai_assistant/api/message_events_stream_views.py`
- `apps/ai_assistant/services/events.py`
- `apps/ai_assistant/helpers/assistants.py`

---

_最后更新：2026-06-15_
