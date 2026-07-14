# C2 KeyError 'data' Diagnosis — Decision Gate

## 調查日期: 2026-06-30

## 背景

Agent Tree 在執行 AutomationAgent 子流程時，前端偶發噴出 `KeyError: 'data'`。
本文件記錄針對此症狀的全面搜尋、防禦審查與根因判定，作為後續修復的 decision gate。

## 搜尋範圍

**後端 Python** (`apps/`, `--include="*.py"`, 排除 `__pycache__` 與測試):

| Pattern | 用途 |
|---------|------|
| `\['data'\]` / `\["data"\]` | 直接 dict 存取（高風險） |
| `result['data']` / `response['data']` / `payload['data']` / `json['data']` / `data['data']` | 常見變數名組合 |
| `.get('data')` / `.get("data")` | 安全存取（需檢查是否有預設值） |
| `.json()['data']` / `.json()["data"]` | HTTP 回應直接取 data |
| `serialized[...]` / `serialized.get(...)` | 序列化輸出存取 |

**Agent 執行路徑額外審查** (`apps/auto/`):
- 全部 `.get(` 呼叫逐一比對（40 處）— 全為 ORM `objects.get()` 或帶預設值的 dict `.get()`，無風險。

**前端 TypeScript** (Prometheus 預先審查):
- `useExecutionEventStream.ts` `parseSSEEvent()` (L46-76): 完整 try/catch + null guard，所有路徑皆有回傳值。
- L118 `typeof data.sequence === 'number'` type guard 存在。
- `AICenterPage.tsx` GQL subscription `buildTreeNodes`: T3 已加 `Array.isArray` guard，無 `.data` 存取。

**SSE event 發送路徑**:
- `apps/core/execution_stream_views.py` `_sse_event()`: 只做 JSON 序列化，無 `['data']` 存取。
- `apps/core/overview_api.py`, `apps/core/api.py`: 無 `['data']` 存取。

## 發現的路徑

### 已有 guard（安全，无需修改）

| 檔案:行 | 程式碼 | Guard 機制 |
|---------|--------|-----------|
| `apps/ai_assistant/api/views.py:151` | `serialized.get("data")` | `isinstance(serialized, dict)` check + 返回 None + try/except wrap (L149,152) + missing key 時 log warning 並 skip (L157-160) |
| `apps/auto/compression/message_utils.py:46` | `raw.get("data") or {}` | `or {}` fallback + L47-48 `isinstance(inner, dict)` defensive check + 整個函式 try/except (L36) + 註解「Never raises」(L34) |

### 不在 agent 執行路徑上（不在症狀範圍）

| 檔案:行 | 程式碼 | 判定 |
|---------|--------|------|
| `apps/scanners/nuclei_scanner/flat.py:238` | `result["data"]["core_urlresult"]` | **Orphaned reference script**。模組層級立即執行的批次匯入腳本，無 `def`/`class`/import 宣告。全 repo grep `nuclei_scanner.flat` / `from .flat` / `import flat` / `flat.py` — **0 imports**。不在 Celery task、不在 API view、不在 agent tool。與 C2 KeyError 症狀無關。 |

### 需要加防禦的路徑

**無。** 所有 agent 執行路徑與 SSE 路徑上的 `['data']` / `.get('data')` 存取皆已有 guard。

## 已加的防禦

**零變更。** 現有 guard 已涵蓋所有相關路徑：
- `views.py:151` 已是 textbook 級別的防禦（isinstance + try/except + log + skip）。
- `message_utils.py:46` 已有 `or {}` + isinstance + 函式級 try/except，且註解明示 "Never raises"。

## 結論

KeyError 'data' 是否為 C1（sequence TOCTOU race）症狀：

> **[x] PARTIAL**

### 理由

1. **後端不可能噴 KeyError 'data'**: 全面審查後，所有 agent 執行 / SSE / serialization 路徑上的 `data` 存取都已有 guard。後端 Python 端找不到可重現 `KeyError: 'data'` 的程式路徑。

2. **前端不可能噴 Python KeyError**: `useExecutionEventStream.ts` 與 GQL subscription 都有 try/catch + null guard + type guard。前端即使收到 malformed payload 也只會 silent return，不會丟 KeyError。

3. **症狀歸屬判定**:
   - 若使用者回報的 "KeyError 'data'" 是 **Python traceback**（後端 log），則在現有 codebase 找不到來源 — 可能是：
     - (a) 歷史 bug 已被先前修復（`views.py:151` 的 guard 可能就是該修復的遺留）。
     - (b) 來自已被刪除的舊路徑（legacy `Step`/`ScriptExecution` 已全數移除）。
     - (c) 來自協力廠商套件內部，非本專案程式碼。
   - 若 "KeyError 'data'" 是 **JavaScript 錯誤訊息**（如 `data is undefined`）的口語描述，則與 C1 (sequence TOCTOU race) **高度相關** — incomplete graph 在前端試圖存取不存在的 node/event 欄位時，可能出現此類錯誤。

4. **與 C1 的關係**: C1 的 race 條件（graph 剛建到一半就被前端讀取）可能讓前端拿到不完整的 node/event，但**現有前端防禦已能吞掉這類 malformed payload**（parseSSEEvent 的 try/catch + type guard）。因此即使 C1 race 發生，也不該在 **當前 codebase** 噴出 KeyError。

### 行動建議

- **不需在 T2 再加防禦** — 現有 guard 已完備。
- **C1 修復仍應進行** — sequence TOCTOU race 是真實存在的一致性缺陷（見 C1 diagnosis）。
- **若未來再次出現 KeyError 'data' traceback**:
  1. 先確認 traceback 完整 stack（判定是 Python 還是 JS）。
  2. 若 Python，grep 該 stack frame 對應檔案的最新內容（可能新增了未加 guard 的存取點）。
  3. 若 JS，檢查前端是否新增了未加 guard 的 `.data` 存取。

## 證據

### Grep 輸出（2026-06-30）

**搜尋 1**: `\['data'\]` across `apps/` (*.py):
```
apps/ai_assistant/tests.py:1467: Previously: `[message_to_dict(m)["data"] for m in messages]` would raise
apps/scanners/nuclei_scanner/flat.py:238: ids = [item["id"] for item in result["data"]["core_urlresult"]]
```
- tests.py: 為壓縮 deadlock fix 的測試文件，描述歷史 bug。
- flat.py: orphaned script（見上表）。

**搜尋 2**: `\["data"\]` across `apps/` (*.py): No matches found.

**搜尋 3**: `.get('data')` / `.get("data")` across `apps/` (*.py):
```
apps/auto/compression/message_utils.py:46: inner = raw.get("data") or {}
apps/ai_assistant/api/views.py:151: data = serialized.get("data") if isinstance(serialized, dict) else None
```
兩者皆已 guard。

**搜尋 4**: `result['data']` / `response['data']` / `payload['data']` / `json['data']` / `data['data']` across `apps/` (*.py): No matches found.

**搜尋 5**: `['data']` across `apps/auto/` (*.py): No matches found.

**搜尋 6**: `.json()['data']` / `.json()["data"]` across `apps/` (*.py): No matches found.

**搜尋 7**: `nuclei_scanner.flat` / `from .flat` / `import flat` / `flat.py` across repo: No matches found (orphaned).

### 已存在測試覆蓋

- `apps/ai_assistant/tests.py:1467` — `CompressionDeadlockFixTests` 明確覆蓋 `message_to_dict(m)["data"]` 在缺 key 情境下的行為（19 tests pass per CLAUDE.md）。
- `apps/auto/compression/message_utils.py` 函式註解明示 "Never raises. Returns a safe empty-shape dict on any error." (L34)。

## 相關文件

- T1/T3: 前端 SSE / GQL guard（useExecutionEventStream.ts, AICenterPage.tsx buildTreeNodes）
- C1: sequence TOCTOU race diagnosis（見 C1 decision gate）
- CLAUDE.md 「Anchored Summary」段：Compression Deadlock Fix、Thread FK Cascade Fix
