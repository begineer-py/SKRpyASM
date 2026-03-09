# CAI 工具實作與底層整合指南 (Tool Implementation Internals)

此文件詳細說明了 CAI (Collaborative AI) 系統中「工具 (Tools)」的底層運作機制。這份技術筆記可作為後續開發平臺工具接入、將平臺既有 API 開放給 AI 調用時的參考。

*(註：根據需求，本文件不包含 Guardrails 相關的實作討論)*

---

## 1. 工具註冊與 Schema 自動化 (`@function_tool`)

AI 要能「理解」並「選擇」調用某個工具，依賴於將程式碼抽象為 JSON Schema。在 CAI 中，這是由 `cai.sdk.agents.tool.py` 的 `@function_tool` 裝飾器自動完成的。

### 核心機制：
- **Schema 萃取**：啟動時，`@function_tool` 內部會利用 Python 內建的 `inspect` 模組讀取函數的 Type Hints (型別提示) 以及 Docstring。
- **Pydantic 驗證**：它會即時產生一個 Pydantic Model，並導出嚴格的 OpeAI JSON Schema (`params_json_schema`)，確保 AI 回傳的參數結構一定是正確的。
- **異步/同步相容**：
  - 如果被裝飾的函數是 `async def`，直接在 Event Loop 中等待。
  - 如果是普通的 `def` (同步函數)，SDK 會利用 `asyncio.get_event_loop().run_in_executor` 將其丟進 ThreadPool 背景執行，**避免單一工具執行太久卡死整個 Agent 的協程**。

**👉 開發平臺工具接入時：**
你只需要寫一個普通的 Python Function（標明 Type Hints 跟清楚的 Docstring），冠上 `@function_tool`，再加入 Agent 的 `tools` 陣列即可，無需手寫冗長的 JSON Schema。

---

## 2. 互動式進程與 PTY 管理 (`common.py`)

為了讓 AI 能執行像 `nmap`、`ssh` 或反彈 Shell (`nc`) 這種長輩命、且需要互動的工具，CAI 實作了一個強大的 `ShellSession` 類別 (位於 `cai/tools/common.py`)。

### 核心機制：
- **虛擬終端 (PTY) 分配**：
  使用 `pty.openpty()` 取代標準的 Subprocess 管道。給予程式一個真實的 PTY (master/slave)，讓工具以為自己跑在 Terminal 裡面。這樣可以繞過許多工具 (如 Python REPL 或是 ssh) 會把輸出 Buffer 起來不吐出的問題。
- **非阻塞式輸出攔截**：
  在獨立的 daemon Thread 中啟動 `_read_output()`，利用 `select.select` 搭配 `0.5` 秒的 timeout 進行非阻塞讀取 (`os.read(self.master, 4096)`)，持續把最新的標準輸出灌進 `output_buffer`。
- **互動式輸入 (Stdin)**：
  當 AI 提供 `session_id` 調用工具時，系統能將字串透過 `os.write(self.master, input_data)` 直接塞進還活著的進程 PTY。

---

## 3. 核心橋樑：`generic_linux_command` 工具

這個工具 (位於 `cai/tools/reconnaissance/generic_linux_command.py`) 是 AI 觸及底層的主要入口。

### 核心機制：
- **指令型態自動判定**：
  工具內部會有一套簡單的 heuristic (啟發式規則)，檢查指令開頭是不是 `ssh`, `python`, `nc`, `bash`，或者是帶有 `-it`, `tail -f` 參數。如果判斷為「互動式」，則會實例化上述的 `ShellSession` 提供一個長駐生命週期。
- **Session 指令擴寫**：
  AI 被提示可以透過相同工具傳入 `session output <id>`、`session kill <id>` 或是帶入 `session_id="..."` 來管理運作中的工具。
- **Streaming 機制**：
  如果是執行時間較長的指令，它會調用 `cai.util` 中的串流工具 (`start_tool_streaming`, `update_tool_streaming`)，把 PTY 即時讀出的 buffer 即時傳給前端 UI 或控制台顯示。

---

## 🎉 總結：後續平台接入建議

當下個 AI 準備把 C2 平台的原生工具（如 Subdomain Scan API、Nuclei Task）開放給 Agent 協作時，有兩種路徑：

1. **指令封裝法**：直接依賴上述 `generic_linux_command`，讓 Agent 呼叫系統內對應的 CLI 工具。
2. **API 綁定法 (推薦)**：寫幾個 `@function_tool` 裝飾的 Wrapper 函數，內部直接呼叫 C2 Django 的 ORM 或是 Celery Task (如 `create_steps_from_analysis`)，Agent 只要回傳參數即可發起漏洞掃描任務。
