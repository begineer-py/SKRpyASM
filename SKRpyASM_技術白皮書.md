# SKRpyASM 技術白皮書

> **Authorized Attack-Surface Management & AI-Assisted Security Workflow Platform**
> 授權攻擊面管理與 AI 輔助安全自動化平台

---

## 目錄

1. [系統概述](#一系統概述)
2. [核心技術特點](#二核心技術特點)
3. [解決的行業痛點](#三解決的行業痛點)
4. [鏈式利用架構](#四鏈式利用架構)
5. [可能衝擊修飾系統](#五可能衝擊修飾系統)
6. [Celery 非同步任務與規模化排程](#六celery-非同步任務與規模化排程)
7. [PostgreSQL 資料庫設計](#七postgresql-資料庫設計)
8. [Hasura GraphQL 即時查詢層](#八hasura-graphql-即時查詢層)
9. [網站架構 vs CLI 工具](#九網站架構-vs-cli-工具)
10. [AI 生成技能系統升級](#十ai-生成技能系統升級)
11. [Target 級別實時監控](#十一target-級別實時監控)
12. [附錄：完整 API 路由映射](#十二附錄完整-api-路由映射)

---

## 一、系統概述

SKRpyASM 是一套面向開發者與安全研究人員的資產偵察、安全掃描、AI 分析與自動化工作流平台。系統以 Django 後端、React 前端、Celery 任務隊列與 PostgreSQL 資料庫為核心，整合 Nmap、Subfinder、Nuclei、FlareSolverr 等業界標準工具，用於授權環境中的攻擊面管理與安全測試。

### 1.1 技術棧

| 層級          | 技術                                                             |
| ------------- | ---------------------------------------------------------------- |
| 後端框架      | Django 5.2.4, Django Ninja 1.4.5, DRF 3.16.0                     |
| AI 框架       | LangChain, LangGraph, LiteLLM                                    |
| 非同步任務    | Celery 5.5.3, django-celery-beat 2.8.1, Redis                    |
| 資料庫        | PostgreSQL 14                                                    |
| 前端          | React 19.1, TypeScript 5.8, Vite 7                               |
| GraphQL       | Hasura GraphQL Engine                                            |
| 安全工具      | Nmap, Subfinder, Amass, dnsx, httpx, naabu, Nuclei, wafw00f, GAU |
| 反機器人繞過  | FlareSolverr, FlareProxyGo                                       |
| AI 模型供應商 | OpenAI, Anthropic (Claude), Google (Gemini), Mistral             |

### 1.2 主要執行流程

```text
React 前端 (Vite :5173)
  → Django Ninja API / Django Admin (:8000/api/)
    → PostgreSQL 14
    → Celery Workers (prefork, 8 併發)
      → Nmap / Subfinder / Amass / Nuclei / FlareSolverr / AI Providers
    → Hasura GraphQL (:8085) / NocoDB (:8081)
```

---

## 二、核心技術特點

### 2.1 三層 AI Agent 階層架構

```
Layer 1: apps.ai_assistant（框架層）
  AIAssistant 抽象基類
    ├── as_graph() → LangGraph 狀態機（setup→history→retriever→agent→tools→respond）
    ├── as_tool()  → Agent 自我包裝為工具，供上層調用
    ├── get_callbacks() → 自動注入 LangChain Callback Handler
    └── _run_as_tool() → 自動建立子線程（subagent_<id>_for_thread_<parent_id>）

Layer 2: HackerAssistant / Orchestrator（策略層）
    負責戰略規劃、任務拆解、結果審閱
    └── as_tool(description) → StructuredTool → Celery 非同步委派

Layer 3: AutomationAgent（執行層）
    AutomationAgent(AIAssistant, DBToolsMixin, ScannerToolsMixin, ...)
    8 個 Mixin 組合出超過 30 個 @method_tool
    迭代執行 THINK → QUERY → ACT → NOTE 迴圈
```

### 2.2 LangGraph 狀態機驅動

每個 AIAssistant 建構的 LangGraph 包含以下節點：

```python
# apps/ai_assistant/helpers/assistants.py:560-667
def as_graph(self, thread_id=None, thread=None):
    workflow = StateGraph(AgentState)
    workflow.add_node("setup", setup)       # 注入 System Prompt
    workflow.add_node("history", history)   # 載入對話歷史
    workflow.add_node("retriever", retriever) # RAG 檢索（可選）
    workflow.add_node("agent", agent)       # LLM 推理 + 工具呼叫
    workflow.add_node("tools", ToolNode)    # 執行工具
    workflow.add_node("respond", record_response) # 儲存對話 + 結構化輸出
    # 狀態轉換
    workflow.set_entry_point("setup")
    workflow.add_edge("setup", "history")
    workflow.add_edge("history", "retriever")
    workflow.add_edge("retriever", "agent")
    workflow.add_conditional_edges("agent", tool_selector, {
        "call_tool": "tools",   # 有工具呼叫 → 執行工具
        "continue": "respond",  # 無工具呼叫 → 回應
    })
    workflow.add_edge("tools", "agent")  # 工具結果送回 LLM
    workflow.add_edge("respond", END)
```

### 2.3 Mixin 工具組合模式

工具按職責分離為獨立 Mixin，動態組合進 Agent 類別：

| Mixin                 | 核心工具                                                                                                                                                | 原始碼位置                 |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| `ReconnaissanceMixin` | `get_target_context`, `create_overview`, `notify_caller_agent`, `escalate_to_orchestrator`, `read_orchestrator_guidance`                                | `reconnaissance_tools.py`  |
| `ScannerToolsMixin`   | `run_flaresolverr_crawler`, `run_subfinder_discovery`, `run_nuclei_*`, `run_nmap_port_scan`, `analyze_javascript_file`                                  | `scanner_tools.py`         |
| `StepManagementMixin` | `update_overview_status`, `update_step_note`, `query_steps`, `create_step`, `update_step_status`, `create_verification`, `get_exhausted_attack_vectors` | `step_management_tools.py` |
| `AssetCreationMixin`  | `create_discovered_url`, `create_discovered_subdomain`, `create_discovered_ip`                                                                          | `asset_creation_tools.py`  |
| `EndpointMixin`       | `query_endpoints`, `create_endpoint`, `add_endpoint_parameter`, `get_url_intelligence`                                                                  | `endpoint_tools.py`        |
| `MemoryMixin`         | `save_long_content`, `read_content_blob`, `write_recon_note`                                                                                            | `memory_tools.py`          |
| `SkillMixin`          | `search_skills`, `load_skill`, `create_or_update_skill`, `delete_skill`, `execute_skill_script`, `install_sandbox_dependency`                           | `skill_tools.py`           |
| `SandboxMixin`        | `run_command` → Kali Docker 沙箱                                                                                                                        | `sandbox_tools.py`         |

### 2.4 自我學習技能系統（RAG）

```python
# apps/core/models/analyze/SkillTemplate.py
class SkillTemplate(models.Model):
    name = models.CharField(unique=True)        # django-csrf-bypass
    description = models.TextField()            # RAG 檢索用摘要
    instructions = models.TextField()           # 執行指南（等同 SKILL.md）
    script_content = models.TextField()         # Python/Bash 腳本
    language = models.CharField(default="python")
    tags = models.JSONField(default=list)       # ["django", "csrf", "bypass"]
    usage_count = models.IntegerField(default=0) # 使用次數排序
```

技能生命週期：

```
search_skills(query) → load_skill(name → instructions + script)
  → execute_skill_script(name, args) → Kali Docker Sandbox 執行
    → create_or_update_skill() → 永久儲存，跨目標重用
      → delete_skill() → 清理無效技能
```

### 2.5 內容壓縮與長期記憶

```python
# apps/core/models/analyze/ContentBlob.py
class ContentBlob(models.Model):
    raw_content = models.TextField()        # 完整原始內容（如 8 萬字 HTML）
    content_size = models.IntegerField()    # 字元數
    ai_summary = models.TextField()         # 自動產生的 AI 摘要
```

AI 工作記憶中只保留 `blob_id` + 摘要（約 500 字），需要時再透過 `read_content_blob(blob_id, focus_query)` 針對原文進行聚焦式提取。

### 2.6 全面可觀測性系統

**StepLog 模型** — 7 種日誌等級 × 9 種分類標籤：

```python
# apps/core/models/analyze/StepLog.py
LEVEL_CHOICES = [
    ("INFO", "Info"), ("DEBUG", "Debug"), ("WARN", "Warning"),
    ("ERROR", "Error"), ("AI_THOUGHT", "AI Thought Process"),
    ("ACTION", "Action Started"), ("RESULT", "Action Result"),
]
TAG_CHOICES = [
    ("SKILL_EXEC", "Skill Execution"), ("COMMAND", "Shell Command"),
    ("API_CALL", "API Call"), ("SCAN", "Scanning Tool"),
    ("PARSE", "Result Parsing"), ("DECISION", "Decision Making"),
    ("ERROR_HANDLING", "Error Handling"),
    ("STATE_UPDATE", "State Update"), ("CHECKPOINT", "Checkpoint"),
]
```

**StepLogCallbackHandler** — 自動攔截 LangChain 事件，無需 AI 手動呼叫：

```
on_tool_start()  → StepLog(level=ACTION, tag="ACTION", action_status=RUNNING)
on_tool_end()    → StepLog(level=INFO,  tag="RESULT", action_status=SUCCESS)
on_tool_error()  → StepLog(level=ERROR, tag="ERROR",  action_status=FAILED)
on_agent_action()→ StepLog(level=DEBUG, tag="AI_THOUGHT")
```

**ThreadCheckpointHandler** — 每步 LangGraph 都增量保存 Thread 訊息，防止中途崩潰導致對話遺失。

### 2.7 反幻覺防火牆

| 機制                                  | 位置                           | 說明                           |
| ------------------------------------- | ------------------------------ | ------------------------------ |
| `get_target_context()` 必須第一個呼叫 | `reconnaissance_tools.py:15`   | 否則無可用 ID                  |
| `CRITICAL_FAILURE` 回傳               | `scanner_tools.py:62`          | 告訴 AI 不要重試無效 ID        |
| ID 存在性預驗證                       | `step_management_tools.py:33`  | 不存在的 ID 直接拒絕           |
| `create_overview` 冪等性              | `reconnaissance_tools.py:170`  | SELECT FOR UPDATE 防止重複建立 |
| StepNote 保留第一行摘要               | `step_management_tools.py:313` | Append 而非覆蓋                |

---

## 三、解決的行業痛點

### 痛點 1：掃描仰賴時效性，不具備可擴展性

**傳統困境**：安全人員必須手動排程掃描器，等待結果輸出後再手動分析。掃描 100 個目標和 1 個目標所需人力幾乎線性增長。

**解決方案**：

| 機制                          | 實作位置                                                        |
| ----------------------------- | --------------------------------------------------------------- |
| Celery 非同步任務隊列         | `c2_core/celery.py` — 所有掃描器以 Celery task 執行             |
| ScannerLifecycle 上下文管理器 | `apps/scanners/base_task.py` — PENDING→RUNNING→COMPLETED/FAILED |
| `callback_step_id` 注入       | `scanner_tools.py:37` — 掃描完成自動回呼對應 Step               |
| 批量資產處理                  | Seed → Subdomain → IP → URL 全自動擴散探索                      |
| Prefork Worker 池            | `-P prefork -c 8` — 目前專案預設的穩定 Celery 執行模式         |

### 痛點 2：仰賴人力，安全掌管在特定人事手上

**傳統困境**：特定專家的經驗無法傳承，人員離職導致知識斷層。

**解決方案**：

| 機制                               | 實作位置                                                      |
| ---------------------------------- | ------------------------------------------------------------- |
| Layer 3 AutomationAgent 全自動執行 | `planning_agent.py:12` — THINK→QUERY→ACT→NOTE 迭代            |
| 升級與指導迴圈                     | `reconnaissance_tools.py:290-401` — 卡住時自動向 Layer 2 請教 |
| SkillTemplate RAG 技能庫           | `SkillTemplate.py` — 跨目標知識重用，`usage_count` 排序       |
| ContentBlob 長期記憶               | `ContentBlob.py` — 自動摘要，知識不隨人員離職消失             |

### 痛點 3：內部盲區 — 無法繪製完整攻擊面

**傳統困境**：Nmap 只看 IP、Subfinder 只看域名、Nuclei 只看漏洞 — 各自為政。

**解決方案** — 多維度資產關聯模型：

```
Seed(DOMAIN/IP_RANGE/URL)
  → Subfinder/Amass → Subdomain → DNSRecord
    → GAU / FlareSolverr → URL → Form / Endpoint / Parameter
    → Nmap → IP → Port (service / version)
    → Nuclei → TechStack + Vulnerability
    → AI 初篩 → InitialAIAnalysis → Overview（戰略主體）
```

每個 Overview 可同時關聯 IPs、Subdomains、URLResults（多對多），從任何入口皆可展開完整攻擊面。

### 痛點 3.1：初步 AI 分流若上下文不足，容易錯過高價值入口

**傳統困境**：如果 AI 初篩只看到 `url + status_code + title` 這類薄資訊，登入頁、管理後台、受保護 API、帶有上傳/密碼欄位的表單頁，常被錯判成普通 Web 資產。

**SKRpyASM 的做法**：初步分析任務在 `InitialAIAnalysis` 階段直接從資產圖中抽取摘要化上下文，而不是只餵單一欄位。

| 資產類型    | 初篩輸入重點欄位                                                                                                                                  | 價值                                                                 |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| IP          | `ip_address`, `ip_version`, `ports`, `related_subdomains`                                                                                        | 快速辨識 Web、管理介面、資料庫、遠端存取等暴露面                     |
| Subdomain   | `is_resolvable`, `is_active`, `is_cdn`, `cdn_name`, `is_waf`, `waf_name`, `resolved_ips`, `dns_records`, `technologies`, `related_url_count` | 區分真實應用、CDN 邊緣節點、WAF 保護入口、技術棧聚集點               |
| URL         | `status_code`, `title`, `content_fetch_status`, `final_url`, `response_header_summary`, `technologies`, `forms_summary`, `text_preview`       | 直接辨識登入頁、後台、Swagger/GraphQL、表單工作流、舊版框架與應用特徵 |
| 戰略上下文  | `strategic_context`：`overview_summary`, `overview_knowledge`, `overview_plan`, `recent_steps_execution`                                       | 讓初篩不脫離既有攻擊脈絡，避免與前面步驟結論互相矛盾                 |

**設計原則**：

- 初篩 payload 以摘要化資料為主，不直接塞完整 HTML 或超長原始回應
- `forms_summary` 僅保留 `action`、`method`、欄位名、是否含密碼/上傳/CSRF 類欄位
- `response_header_summary` 只取 `server`、`content-type`、`location`、`x-powered-by`、`www-authenticate`、`set-cookie_present`
- 目標是提高 `worth_deep_analysis` 的判斷品質，而不是在初篩階段直接宣告已確認漏洞

### 痛點 4：模式單一，大量時間浪費在無效掃描

**傳統困境**：跑完整套掃描流程（Nmap→Nuclei→...），卻發現目標根本沒用對應技術。

**解決方案**：

| 機制                             | 說明                                                           |
| -------------------------------- | -------------------------------------------------------------- |
| `get_url_intelligence(url_id)`   | 一次查回 Forms/Endpoints/TechStack/Vulnerabilities，不盲目掃描 |
| 先查後掃原則                     | "Your job is to attack, not fetch." — 禁止盲目掃描             |
| `check_scanned_*` 三兄弟         | 執行前先確認 url/subdomain/ip 是否已掃過                       |
| `get_exhausted_attack_vectors()` | 跳過已失敗的攻擊路徑                                           |
| Verification AI 驗證             | 用 AI 判斷是否成功，而非「跑過就算數」                         |

### 痛點 5：對抗反機器人能力差

**傳統困境**：CF/WAF/Akamai 保護頁面，標準工具完全失效。

**解決方案**：

| 機制              | 說明                                              |
| ----------------- | ------------------------------------------------- |
| FlareSolverr 整合 | Headless browser（Puppeteer）渲染 JS              |
| Session 復用      | `session_key` + `refresh_session`                 |
| 多種請求方法      | GET/POST + body + headers + cookies + host_header |
| JavaScript 分析   | Nuclei JS 模板掃描 inline/external JS             |
| 沙箱命令繞過      | Kali sandbox 內 curl/wget 手動操作                |

---

## 四、鏈式利用架構

### 4.1 AutomationAgent 迭代攻防迴圈（TQA 機制）

Agent 的核心決策模式為 **TQA（Triage, Question, Answer）**：基於資料庫「已經知道的」推導出「想知道的」，據此規劃下一個行動步奏。

```python
# apps/auto/assistants/planning_agent.py:40-51
LOOP ITERATION:
1. THINK:  What do I know? What intelligence does the DB already have? Pick the most promising attack target.
2. QUERY:  get_url_intelligence(url_id) → Forms/Endpoints/TechStack/Findings/Vulnerabilities
3. ACT:    Perform ONE concrete action (curl a form, submit an injection payload, run a scanner tool)
4. NOTE:   write_recon_note + update_overview_status(new_knowledge=...) 保存觀察
5. REPEAT: Based on findings, pick the next target and loop again
```

| TQA 階段                 | Agent 思維                                                                            | 對應工具/DB                                                                            | 實際範例                                                                                                      |
| ------------------------ | ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Triage（知道的）**     | 資料庫已有什麼情報？哪些資產已掃過？哪些攻擊已嘗試過且失敗？                          | `get_target_context`, `get_url_intelligence`, `get_exhausted_attack_vectors`           | 查到 URL id=5 的 tech_stack = "Django 4.2"、`is_vuln_scanned = False`、已嘗試過 2 個 SQLi payload 但被 WAF 擋 |
| **Question（想知道的）** | 有哪些攻擊面尚未探索？該目標是否有已知漏洞的關聯 CVE？這類型的 Known-Unknown 是什麼？ | `check_scanned_urls`, `check_scanned_subdomains`, `check_scanned_ips`, `search_skills` | Django 4.2 可能有 CVE-2024-...，且 CVSS > 7.5。有無現成 skill 腳本可用？                                      |
| **Action（規劃下一步）** | 基於已知 + 未知差距，決定：選哪個攻擊向量、用什麼工具、送什麼 payload                 | 綜合判斷 → 調用 scanner_tools 或 sandbox command                                       | 執行 `run_nuclei_url(url_id=5, template="cves/2024/CVE-2024-...")`                                            |

**智慧核心**：Agent 不照固定 pipeline 執行，而是每次迭代問自己「我還不知道什麼？」，再從 DB 中 `is_*_analyzed = False` 或 `status = PENDING` 的資產中選擇差異最大的下手。這使掃描順序動態適應目標實際狀況，而非線性跑完所有步驟。

### 4.2 Step 樹狀結構

```python
# apps/core/models/analyze/Step.py
class Step(models.Model):
    overview = ForeignKey(Overview)      # 所屬戰略概覽
    parent_step = ForeignKey("self")     # 父步驟（支援樹狀攻擊鏈）
    order = PositiveIntegerField()       # 自動遞增
    status = [PENDING / RUNNING / COMPLETED / FAILED / WAITING_FOR_ASYNC / ENDED]
    ip / subdomain / url_result = ManyToManyField  # 關聯資產
```

### 4.3 非同步掃描回呼鏈

```python
# apps/auto/tools/scanner_tools.py:18-67
_dispatch_scanner(overview_id, tool_name, endpoint, payload):
  1. Step.create_next(overview_id, status="WAITING_FOR_ASYNC")
  2. payload['callback_step_id'] = step.id  # 自動注入回呼 ID
  3. POST → 內部掃描 API
  4. 掃描完成 → Celery callback → 更新 Step 狀態
```

### 4.4 升級與指導迴圈

```
AutomationAgent 卡住（同一向量失敗 3 次以上）
  → escalate_to_orchestrator(overview_id, question)
    → Overview.status = NEEDS_GUIDANCE
    → 發訊息到 parent_thread（HackerAssistant）
  → 輪詢 read_orchestrator_guidance(overview_id)
    → 讀取 parent 回覆，恢復 EXECUTING
```

### 4.5 父通知機制（防止 Agent 遺忘回報）

```python
# apps/auto/assistants/planning_agent.py:133-169
_auto_notify_parent(result=None, error=None):
    # 在 Celery task 完成後自動呼叫
    # 即使 AI 忘記呼叫 notify_caller_agent
    # 系統仍會自動回報給上層 Agent
```

### 4.6 持續滲透攻擊循環（完整流程圖）

持續滲透是 AutomationAgent 的核心運作模式，系統不執行一次性掃描，而是透過反覆的「偵察 → 分析 → 攻擊 → 記錄」循環，逐漸深入目標。

```
┌─────────────────────────────────────────────────────────────┐
│                   持續滲透攻擊循環                             │
│            (Continuous Pentesting Loop)                      │
└─────────────────────────────────────────────────────────────┘

                           ▼
              ┌─────────────────────────┐
              │   INIT: get_target_context │
              │   取得 overview_id + assets│
              └──────────┬──────────────┘
                         ▼
              ┌─────────────────────────┐
         ┌───▶│  THINK: 分析當前情報       │
         │    │  - 哪些資產尚未偵察？       │
         │    │  - 哪個攻擊向量最有希望？   │
         │    │  - 過去失敗過什麼？        │
         │    └──────────┬──────────────┘
         │               ▼
         │    ┌─────────────────────────┐
         │    │  QUERY: get_url_intelligence │
         │    │  - Forms / Endpoints     │
         │    │  - TechStack / Findings  │
         │    │  - Vulnerabilities       │
         │    │  - Headers / Parameters  │
         │    └──────────┬──────────────┘
         │               ▼
         │    ┌─────────────────────────┐
         │    │  判斷：是否已掃過此目標？   │
         │    │  check_scanned_url()     │
         │    │  check_scanned_subdomain()│
         │    │  check_scanned_ip()      │
         │    ├─────────────────────────┤
         │    │  是 ──→ THINK (跳過)     │
         │    │  否 ──→ ACT              │
         │    └──────────┬──────────────┘
         │               ▼
         │    ┌─────────────────────────┐
         │    │  ACT: 執行具體動作         │
         │    │  ┌───────────────────┐  │
         │    │  │ 同步工具:           │  │
         │    │  │  run_command       │  │
         │    │  │  execute_skill     │  │
         │    │  │  curl / sqlmap     │  │
         │    │  └───────────────────┘  │
         │    │  ┌───────────────────┐  │
         │    │  │ 非同步工具:         │  │
         │    │  │  run_nmap          │  │
         │    │  │  run_nuclei        │  │
         │    │  │  run_subfinder     │  │
         │    │  │  run_gau          │  │
         │    │  │ → WAITING_FOR_ASYNC│  │
         │    │  │ → Celery callback  │  │
         │    │  └───────────────────┘  │
         │    └──────────┬──────────────┘
         │               ▼
         │    ┌─────────────────────────┐
         │    │  NOTE: 記錄觀察結果       │
         │    │  write_recon_note()     │
         │    │  update_overview_status()│
         │    │  - 更新 knowledge (JSON) │
         │    │  - 更新 plan (JSON)     │
         │    │  - 更新 risk_score      │
         │    │  - 建立 Vulnerability   │
         │    └──────────┬──────────────┘
         │               ▼
         │    ┌─────────────────────────┐
         │    │  VERIFY: AI 驗證結果     │
         │    │  - Verification 記錄     │
         │    │  - PASSED → auto-create │
         │    │  - FAILED → 標記 EXHAUSTED│
         │    └──────────┬──────────────┘
         │               ▼
         │    ┌─────────────────────────┐
         │    │  DECIDE: 下一步？         │
         │    │  ├─ 有更多資產 → THINK   │──┐
         │    │  ├─ 卡住3次 → ESCALATE  │  │
         │    │  └─ 任務完成 → NOTIFY   │  │
         │    └─────────────────────────┘  │
         └─────────────────────────────────┘
```

### 4.7 持續滲透層級與對應工具

| 滲透層級           | 目標                              | 對應工具                                                   | 資料來源                     |
| ------------------ | --------------------------------- | ---------------------------------------------------------- | ---------------------------- |
| **L1: 被動偵察**   | 收集公開資訊，建立初始資產清單    | `run_subfinder_discovery`, `run_gau_url_discovery`         | Subdomain, URLResult         |
| **L2: 主動偵察**   | 確認存活主機、開放端口、服務版本  | `run_nmap_port_scan`, `run_nuclei_tech_scan`               | IP, Port, TechStack          |
| **L3: 深度分析**   | 提取表單、端點、JS 分析、參數枚舉 | `get_url_intelligence`, `run_js_scan`, `run_gobuster`      | URLResult, extracted_results |
| **L4: 漏洞驗證**   | 針對性測試已知漏洞類型            | `run_nuclei_vuln_scan`, `sqlmap`, `nikto`, `execute_skill` | Vulnerability, AttackVector  |
| **L5: 利用與橫向** | 實際利用、提權、橫向移動          | `run_command`（Kali 沙箱）, `execute_skill_script`         | CommandExecution, StepLog    |

### 4.8 持續滲透 vs 傳統一次性掃描

| 面向     | 傳統一次性掃描         | SKRpyASM 持續滲透                               |
| -------- | ---------------------- | ----------------------------------------------- |
| 執行方式 | 依序跑完整個 pipeline  | THINK→QUERY→ACT→NOTE 迭代循環                   |
| 決策引擎 | 工程師手動決定下一步   | AI Agent 根據當前情報動態選擇                   |
| 中斷處理 | 重新從頭掃描           | 可從中斷點繼續（knowledge JSON 快照）           |
| 重複偵測 | 同一工具反覆掃同一目標 | `check_scanned_*` + `is_*_analyzed` 狀態標記    |
| 驗證機制 | 無（跑過就算）         | AI Verification（PASSED/FAILED/INCONCLUSIVE）   |
| 記憶能力 | 無                     | `Overview.knowledge` + `ContentBlob.ai_summary` |
| 升級機制 | 人工介入               | `escalate_to_orchestrator` → `NEEDS_GUIDANCE`   |
| 橫向移動 | 手動切換目標           | 自動根據發現決定下一個攻擊目標                  |

### 4.9 持續滲透的例外處理整合

系統透過「排程任務背景處理 + Agent 層級預防」兩種模式，處理持續滲透中的各種實際例外情況。

#### 4.9.1 六層防呆機制總覽

| 層級                     | 機制                        | 觸發時機                                         | 處理方式                                                                                          | 涉及工具/排程                                                                                 |
| ------------------------ | --------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| **L0: Agent 事前預防**   | 先查後掃原則                | 每次 ACT 前                                      | 強制呼叫 `check_scanned_*` + `get_url_intelligence` 確認 DB 狀態，禁止盲目掃描                    | `check_scanned_urls`, `check_scanned_subdomains`, `check_scanned_ips`, `get_url_intelligence` |
| **L1: Agent 自我修復**   | 沙箱依賴安裝                | `run_command` 回傳 ImportError                   | `install_sandbox_dependency(package_manager, package_name)` 自動安裝缺失套件                      | `sandbox_tools.py`                                                                            |
| **L2: 非同步逾時保護**   | Watchdog 每 5 分鐘檢查      | 非同步掃描 > 30 分鐘無 callback                  | Step 強制 FAILED + `[SYSTEM Watchdog]` 救援訊息                                                   | `watchdog.py:69-77`                                                                           |
| **L3: 身分驗證會話管理** | Session 復用 + 先註冊後操作 | FlareSolverr 請求需通過 CF/WAF                   | `session_key` 參數復用瀏覽器 Session，`refresh_session` 刷新過期 Session                          | `FlareSolverrRequest` (`scanner_tools.py:86-124`)                                             |
| **L4: 複雜流程腳本化**   | Skill 系統儲存可重用腳本    | 遇到重複性複雜操作（如 CSRF bypass、多步驟登入） | `search_skills` → `load_skill` → `execute_skill_script`，成功後 `create_or_update_skill` 永久儲存 | `skill_tools.py`                                                                              |
| **L5: 上層指導**         | Escalation 到 Orchestrator  | 同一向量失敗 3+ 種方法                           | `escalate_to_orchestrator` → `NEEDS_GUIDANCE` → `read_orchestrator_guidance` 輪詢                 | `reconnaissance_tools.py:290-401`                                                             |

#### 4.9.2 先查後掃 — Agent 事前預防

系統在 Agent 指令中強制要求「先查 DB，再決定行動」，避免重複掃描與資源浪費：

```
Agent 指令原文 (planning_agent.py:58-62):
"**Reading URLs from DB:**
When you receive a context listing URL IDs, call get_url_intelligence(url_id=<id>) for each one.
This is cheaper than guessing and more accurate than curl.
Your job is to attack, not fetch."
```

**實際流程（三種資產類型皆適用）**：

| 資產類型  | 查詢工具                              | 回傳內容                                                            | 判斷依據                                                                           |
| --------- | ------------------------------------- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| URL       | `get_url_intelligence(url_id)`        | Forms, Endpoints, TechStack, Vulnerabilities, Headers, Content 預覽 | `content_fetch_status`, `used_flaresolverr`, `is_tech_analyzed`, `is_vuln_scanned` |
| Subdomain | `check_scanned_subdomains(target_id)` | 解析狀態、技術分析狀態、最後掃描類型                                | `is_resolvable`, `is_tech_analyzed`                                                |
| IP        | `check_scanned_ips(target_id)`        | 端口數量、最後掃描類型                                              | `last_scan_type`, `ports` 關聯數量                                                 |

**Agent 判斷邏輯**：

1. 取得 Target Context（含所有資產 IDs）
2. 依目標資產類型呼叫對應查詢工具
3. 分析回傳的 `is_*_analyzed` / `content_fetch_status` 等標記
4. 僅對狀態為 False / PENDING 的目標執行 ACT
5. 對已掃過的目標直接讀取 DB 情報，不重複掃描

#### 4.9.3 Session 復用 — CF/WAF 繞過與身分保持

```python
# scanner_tools.py:86-124
def run_flaresolverr_request(
    self,
    overview_id, target_url,
    method="GET",
    session_key=None,       # 復用先前 Session
    refresh_session=False,  # 強制刷新
    headers=None, cookies=None,
    ...
) -> str:
    """Send HTTP request via FlareSolverr with session reuse.
    Designed for AI-driven form submission / API probing under CF/WAF."""
```

| 情境         | session_key   | refresh_session | 行為                                                          |
| ------------ | ------------- | --------------- | ------------------------------------------------------------- |
| 首次請求     | `None`        | `False`         | 自動建立新 Session，回傳 `session_key` 供後續使用             |
| 登入後操作   | `"fs_abc123"` | `False`         | 復用登入後的 Session，保持已認證狀態                          |
| Session 過期 | `"fs_abc123"` | `True`          | 刷新瀏覽器 Session（清除 cookies 重新建立）                   |
| 多步驟表單   | `"fs_def456"` | `False`         | 同一 Session 依序提交多個表單（如 register → login → action） |

**典型 Agent 操作順序**（以需登入的目標為例）：

```
1. get_url_intelligence(url_id=123)
   → 發現 Forms: [POST /register, POST /login, POST /profile]

2. run_flaresolverr_request(
       overview_id=OV1, target_url="https://target.com/register",
       method="POST", body="username=test&password=test123",
       session_key=None)  # 建立新 Session
   → 回傳 session_key="fs_session_xxx"

3. run_flaresolverr_request(
       overview_id=OV1, target_url="https://target.com/login",
       method="POST", body="username=test&password=test123",
       session_key="fs_session_xxx")  # 復用已註冊 Session
   → 登入成功，Session 保持已認證狀態

4. run_flaresolverr_request(
       overview_id=OV1, target_url="https://target.com/profile",
       method="GET",
       session_key="fs_session_xxx")  # 已認證 Session
   → 取得受保護頁面內容

5. update_overview_status(
       overview_id=OV1,
       new_knowledge={
           "registered_accounts": [
               {"username": "test", "password": "test123", "session_key": "fs_session_xxx"}
           ],
           "notes": "已註冊並登入 target.com，Session 有效可存取 /profile"
       })
   → 將帳密與 Session 存入 Overview.knowledge（JSONB）
   → 後續迭代直接讀取，不需重新註冊
```

**AI 記憶機制**：`update_overview_status(new_knowledge=...)` 將帳號密碼、session_key、表單結構等寫入 `Overview.knowledge`（JSONB 欄位），跨迭代循環持久化。即使 Agent 重新啟動或切換目標，下次呼叫 `get_target_context` 時仍可讀取先前儲存的憑證，無需重新註冊。

#### 4.9.4 Skill 系統 — 複雜流程腳本化

當 Agent 遇到重複性複雜操作（如 CSRF token 繞過、多步驟登入流程），先搜尋既有技能：

```python
# Agent 指令原文 (planning_agent.py:67-76)
"1. First, call search_skills (e.g. query='django csrf') to see if reusable script exists.
2. If it exists, call load_skill → execute_skill_script.
3. If NO skill exists, write a temporary Python script yourself,
   and when successful, IMMEDIATELY call create_or_update_skill to save it."
```

| 步驟 | Agent 動作          | 對應 API                                                            |
| ---- | ------------------- | ------------------------------------------------------------------- |
| 1    | 搜尋既有技能        | `search_skills(query="django login")`                               |
| 2    | 載入技能指令        | `load_skill(skill_id=5)`                                            |
| 3    | 執行腳本            | `execute_skill_script(skill_id=5, target_url=..., credentials=...)` |
| 4    | 成功後儲存新技能    | `create_or_update_skill(name=..., script=..., tags=[...])`          |
| 5    | 後續 Agent 自動復用 | 從 DB 查詢到同標籤技能直接使用                                      |

#### 4.9.5 被動快取 — 避免重複請求

`check_scanned_urls` 工具讓 Agent 在執行任何 FlareSolverr 請求前先查看 DB 狀態：

```
# reconnaissance_tools.py:244-245
"在執行任何 Flaresolverr 爬蟲、Katana 掃描或其他 URL 掃描與抽取前，
請務必先使用此工具，以確認該 URL 是否已經被抓取過"
```

| 資料庫欄位                               | 意義                | Agent 判斷                        |
| ---------------------------------------- | ------------------- | --------------------------------- |
| `content_fetch_status='SUCCESS_FETCHED'` | 已成功抓取          | 跳過，直接 `get_url_intelligence` |
| `used_flaresolverr=True`                 | 已用過 FlareSolverr | 不再重複爬取                      |
| `is_tech_analyzed=True`                  | 技術棧已分析        | 跳過技術掃描                      |
| `is_vuln_scanned=True`                   | 漏洞已掃描          | 跳過漏洞掃描                      |

#### 4.9.6 非同步不回堵 — Scanner Dispatch 模式

所有掃描工具皆採用 `_dispatch_scanner` 模式，確保 Agent 不論後續結果如何，都能立即繼續執行：

```python
# scanner_tools.py:18-67
_dispatch_scanner(overview_id, tool_name, endpoint, payload):
    1. Step.create_next(overview_id, status="WAITING_FOR_ASYNC")
    2. payload['callback_step_id'] = step.id  # 自動注入回呼 ID
    3. POST → 內部掃描 API
    4. 若 API 回傳 4xx → Step 立即 FAILED + StepNote 記錄錯誤
    5. 回傳 → Agent 繼續 THINK 下一目標
    6. 掃描完成 → Celery callback → 更新 Step 狀態
```

這保證了：

- Agent 不會因為等待非同步掃描結果而停滯
- Watchdog 作為最終防線，逾時 30 分鐘自動標記 FAILED
- 每個掃描都有 StepLog 完整追蹤

#### 4.9.7 實際例外情境與處理流程

| 例外情境               | Agent 層級處理                                                  | 排程/系統層級處理                   | 成功路徑                       |
| ---------------------- | --------------------------------------------------------------- | ----------------------------------- | ------------------------------ |
| URL 受 CF 保護無法直連 | 呼叫 `run_flaresolverr_request` 帶 FlareSolverr 渲染            | 無需排程                            | 內容被 Puppeteer 渲染後回傳    |
| 表單需 CSRF token      | `search_skills("csrf")` → `execute_skill_script` 自動提取 token | 技能儲存在 DB，Agent 間共享         | token 自動提取 + 帶入請求      |
| 需註冊才能測試         | `get_url_intelligence` 發現 `/register` → FlareSolverr 先註冊   | `session_key` 復用同一 Session      | 註冊 → 登入 → 測試同一 Session |
| Session 過期           | `refresh_session=True` 強制刷新                                 | FlareSolverr 重新建立瀏覽器 Session | 新的 Session cookies           |
| 掃描工具依賴缺失       | `install_sandbox_dependency('pip', 'pymysql')`                  | Kali 沙箱內安裝套件                 | 自動安裝後重試                 |
| 非同步掃描死信         | Agent 跳過繼續下一目標                                          | Watchdog 30 分鐘後 FAILED           | 救援訊息傳入 Thread            |
| Agent 卡在嘗試路徑     | `escalate_to_orchestrator` 請求上層指導                         | Overview 標記 NEEDS_GUIDANCE        | Orbistrator 提供戰略方針       |

#### 4.9.8 排程任務背景處理（例外處理專用）

以下排程任務專門負責持續滲透中的例外情況處理，在 Agent 視線之外自動運行：

| 排程任務                             | 執行頻率   | 處理的例外                                                        | 行為                                                                                 |
| ------------------------------------ | ---------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `watchdog_stalled_overviews`         | 每 5 分鐘  | Agent 卡在 PLANNING >15min / EXECUTING >30min / 非同步工具 >30min | 自動補觸發規劃、修正狀態或強制 FAILED 逾時 Step，並發送 `[SYSTEM Watchdog]` 救援訊息 |
| `scan_ips_without_nmap_results`      | 每 5 分鐘  | IP 尚未被 Nmap 掃描（`discovered_by_scans` 數量 = 0）             | 自動呼叫 Nmap API 批次掃描至多 10 個 IP                                            |
| `trigger_nuclei_tech_scan_url`       | 每 5 分鐘  | URL 尚未分析技術棧（`is_tech_analyzed=False`）                    | Nuclei `tech-detect` 模板掃描，批量標記已處理                                      |
| `trigger_nuclei_tech_scan_subdomain` | 每 5 分鐘  | Subdomain 尚未分析技術棧（`is_tech_analyzed=False`）              | 同上，每批 100 個 subdomain                                                        |
| `trigger_scan_js`                    | 每 15 分鐘 | URL 尚未分析 JavaScript（`is_js_analyzed=False`）                 | Nuclei JS 模板掃描 inline & external JavaScript                                    |

**排程任務與 Agent 的協作流程**：

```
Agent ACT ──發送掃描請求──▶ Celery Worker ──掃描執行──▶ 結果寫入 DB
                              │
                         [Callback Step ID]
                              │
                              ▼
                     Agent 繼續 THINK 下一目標
                              │
                   ┌──────────┴──────────┐
                   ▼                      ▼
            [掃描成功]               [掃描逾時 >30min]
            Celery callback           Watchdog 偵測
            Step → COMPLETED          Step → FAILED
                                      Thread → 救援訊息
                                           │
                                           ▼
                                     Agent 下次輪詢讀取
                                     重新規劃攻擊路徑
```

**排程任務處理的例外情境**：

| 情境                                                         | Agent 無需知道                               | 排程默默處理                                     |
| ------------------------------------------------------------ | -------------------------------------------- | ------------------------------------------------ |
| Agent 送出的 Nmap 掃描卡住 40 分鐘                           | Agent 已在處理其他目標                       | Watchdog 標記 Step FAILED，發送救援訊息          |
| 另一 Target 有新 IP 未被掃描                                 | Agent 專注當前目標                           | `scan_ips_without_nmap_results` 自動補掃         |
| URL 的 content body 已在 DB 但 `is_tech_analyzed` 仍為 False | Agent 查 `get_url_intelligence` 回傳完整情報 | 排程自動補掃 tech-detect                         |

### 4.9.9 持續學習機制

系統具備四層持續學習能力，每次執行都讓後續攻擊更有效率：

#### 學習層級總覽

| 層級               | 機制                                                                 | 儲存位置                                                 | 跨会话                 | 學習內容                                      |
| ------------------ | -------------------------------------------------------------------- | -------------------------------------------------------- | ---------------------- | --------------------------------------------- |
| **L1: 技能資料庫** | Agent 成功執行複雜操作後呼叫 `create_or_update_skill` 儲存腳本       | `SkillTemplate` 模型（DB）                               | ✅ 跨 Agent、跨 Target | CSRF bypass 腳本、多步驟登入、API 呼叫模式    |
| **L2: 會話記憶**   | Agent 每次 NOTE 階段呼叫 `update_overview_status(new_knowledge=...)` | `Overview.knowledge`（JSONB）                            | ❌ 僅當前 Overview     | 已註冊帳密、session_key、已探索路徑、失敗記錄 |
| **L3: 長期摘要**   | `compress_long_threads` 壓縮舊對話為 Mistral Small 摘要              | `ContentBlob.ai_summary`（Text）                         | ✅ 壓縮後永久保留      | 已完成的掃描結果、已發現的漏洞、關鍵 ID       |
| **L4: 失敗記憶**   | EXHAUSTED/MITIGATED 狀態的 AttackVector                              | `AttackVector.status` + `get_exhausted_attack_vectors()` | ✅ 跨迭代              | 已失敗的攻擊方法與 payload，不再重複嘗試      |

#### L1: 技能資料庫（跨会话學習）

```python
# Agent 指令原文 (planning_agent.py:70-74)
"when successful, IMMEDIATELY call create_or_update_skill to save this script
 into the database so you (and future agents) can reuse it."
```

**學習流程**：

1. Agent 遇到複雜操作（如 Django CSRF bypass、GraphQL 查詢包裝）
2. 搜尋既有技能：`search_skills(query="django csrf")`
3. 無匹配 → 撰寫臨時 Python 腳本並執行
4. 成功 → `create_or_update_skill(name=..., script=..., tags=["csrf", "django"])`
5. 後續 Agent（同一或不同 Target）查詢到相同標籤直接復用

技能使用次數追蹤（`SkillTemplate.usage_count`），熱門技能排序優先，低使用率技能自動下沉。

#### L2: 會話記憶（迭代間學習）

`Overview.knowledge` 是所有 Agent 迭代間的「便條紙」，結構完全由 Agent 自行決定：

```python
# Agent 每次 NOTE 階段累積知識
update_overview_status(
    overview_id=OV1,
    new_knowledge={
        "registered_accounts": [
            {"username": "test@example.com", "password": "Test123!", "session_key": "fs_abc"}
        ],
        "csrf_bypass": {"method": "extract from /csrf endpoint", "token_name": "csrfmiddlewaretoken"},
        "discovered_paths": ["/admin", "/api/v1/users", "/.git/config"],
        "failed_approaches": ["sqlmap on /login (no injection)", "dirb common.txt (no hits)"],
        "current_target": {"type": "subdomain", "id": 42, "url": "admin.example.com"},
    }
)
```

每次新迭代開始 THINK 階段時，Agent 透過 `get_target_context` 即可讀取先前累積的 knowledge，從中斷點繼續而非從頭開始。

#### L3: 長期摘要（壓縮保留）

```python
# watchdog.py:103-206
# Message > 40 條觸發壓縮
# Mistral Small 產生摘要保留：已知資產、已完成的掃描、已發現漏洞、關鍵 ID
# 刪除舊 Message，在 Thread 開頭插入摘要
# Agent 繼續執行時摘要仍在 Context 中，不會遺忘
```

| 壓縮前                       | 壓縮後                                                         |
| ---------------------------- | -------------------------------------------------------------- |
| 60 條完整對話（~12K tokens） | 摘要（~2K tokens）+ 保留最近 18 條原訊息                       |
| Token 視窗接近極限           | 釋放 10K+ tokens 空間                                          |
| 舊訊息包含已完成的掃描細節   | 摘要保留「已 Nmap 掃過 1.2.3.4（port 80/443 open）」等關鍵事實 |

#### L4: 失敗記憶

```python
# step_management_tools.py:366-386
get_exhausted_attack_vectors(overview_id):
    # 回傳所有 EXHAUSTED / MITIGATED 狀態的向量及已嘗試的指令
    # Agent 在規劃下一步前先呼叫，避免重複失敗方法
```

**實際效果**：

- Agent A 嘗試 SQLi 於 `/api/user?id=1` 失敗（參數非注入點）
- 該向量標記為 EXHAUSTED
- Agent B 接手同一 Target 時呼叫 `get_exhausted_attack_vectors`
- 直接跳過該參數，節省一次測試

#### 持續學習閉環

```
Agent A 執行 ──→ 發現新攻擊模式 ──→ create_or_update_skill ──→ SkillTemplate DB
                                     ↑                               │
                                     └── search_skills ◀── Agent B 搜尋
                                                                     │
                                                                     ▼
                                                            execute_skill_script
                                                             （零學習成本直接使用）

```

### 4.9.10 非同步呼叫鏈：Go 外部工具與 FlareSolverr 的 callback_step 機制

外部服務（FlareSolverr / FlareProxyGo）透過 Celery 非同步執行，並經由 `callback_step_id` 機制喚醒等待中的 AI Agent。整個鏈路由四層組成：

#### 架構總覽

```
AI Agent (LangChain) ──→ ① _dispatch_scanner ──→ ② Ninja API ──→ ③ Celery Task ──→ ④ Callback
                                │                    │               │
                                │ Step(status=       │ async def     │ perform_scan
                                │   WAITING_FOR_     │ .delay(       │ @with_auto_
                                │   ASYNC)           │ callback_     │ callback
                                │ callback_step_id   │ step_id=…)    │
                                │ = step.id inject   │               │
```

#### ① Agent 工具層：`_dispatch_scanner`

所有需要非同步執行的掃描工具（FlareSolverr 爬蟲/請求、Subfinder、GAU、Nuclei、Nmap、JS 分析）統一透過 `ScannerToolsMixin._dispatch_scanner()` 派遣（`apps/auto/tools/scanner_tools.py:18-67`）：

```python
def _dispatch_scanner(self, overview_id, tool_name, endpoint, payload, description=""):
    step = Step.create_next(overview_id=overview_id, status="WAITING_FOR_ASYNC")
    payload['callback_step_id'] = step.id       # ← 自動注入 step.id
    resp = requests.post(url, json=payload)      # POST 到內部 Ninja API
```

| 參數          | 說明                                                  |
| ------------- | ----------------------------------------------------- |
| `overview_id` | 所屬 Overview（讓 callback 知道去哪個 Thread 發訊息） |
| `tool_name`   | 工具辨識名稱                                          |
| `endpoint`    | 內部 API 路徑（如 `/api/flaresolverr/start_scanner`） |
| `payload`     | API payload，會自動注入 `callback_step_id`            |
| `step.id`     | 整個 callback 鏈的核心識別碼                          |

#### ② Ninja API 層：Uvicorn 接收 + Celery 派遣

Ninja API endpoint 接收 HTTP POST，執行驗證後立即回傳 HTTP 200（不等待掃描完成）：

**FlareSolverr 爬蟲** — `apps/flaresolverr/api.py:31-86`：

```python
@router.post("/start_scanner", ...)
async def start_crawl(request, trigger_data: FlaresolverrTriggerSchema):
    target = await sync_to_async(Target.objects.get)(id=trigger_data.target_id)
    perform_scan_for_url.delay(                         # ← 非同步派遣
        url=url, target_id=target_id,
        callback_step_id=trigger_data.callback_step_id,  # ← 傳遞給 Celery
    )
    return {"success": True, "message": "Task dispatched"}
```

**FlareSolverr 單一請求** — `apps/flaresolverr/api.py:135-191`：

```python
@router.post("/send_request", ...)
async def send_request(request, payload: FlaresolverrSingleRequestSchema):
    perform_flaresolverr_request.delay(
        url=payload.url, method=payload.method,
        session_key=payload.session_key,                    # ← 連線重用
        callback_step_id=payload.callback_step_id,          # ← callback 鏈
    )
    return {"success": True, "message": "Request dispatched"}
```

| API            | Uvicorn 行為                | Celery 行為                                           |
| -------------- | --------------------------- | ----------------------------------------------------- |
| `start_crawl`  | 驗證 Target 存在 → 立即回傳 | `perform_scan_for_url.delay()` 背景爬整站             |
| `send_request` | 驗證參數 → 立即回傳         | `perform_flaresolverr_request.delay()` 背景發單一請求 |

#### ③ Celery Task 層：實際執行 + `@with_auto_callback`

所有外部呼叫皆包裝為 Celery `@shared_task`，並加上 `@with_auto_callback` 裝飾器：

**核心裝飾器** — `apps/core/utils.py`（全文 138 行）：

| 階段          | 動作                                                                               |
| ------------- | ---------------------------------------------------------------------------------- |
| 任務開始前    | Step 狀態更新為 `RUNNING`                                                          |
| 任務完成後    | Step 設為 `COMPLETED` + `completed_at` 時間戳                                      |
| Callback 訊息 | 查詢該 Step 所屬 Overview → 找到關聯 Thread → 呼叫 `create_message()` 注入系統訊息 |
| 訊息內容      | 包含掃描摘要 + 新 URL ID 提示，Agent 收到後可繼續分析                              |

**Callback 回覆的 Thread 查找優先順序**：

1. `overview.thread_id` — 當前會話線程
2. `overview.parent_thread_id` — 父 Agent 線程（Orchestrator → Agent）
3. 最新的 `automation_agent` Thread — 備用

**FlareSolverr 爬蟲 Task** — `apps/flaresolverr/tasks/spider.py:27-355`：

```python
@shared_task(bind=True, name="flaresolverr.tasks.perform_scan_for_url")
@with_auto_callback
@log_function_call()
def perform_scan_for_url(self, url, target_id, callback_step_id=None, ...):
    # ReconOrchestrator.run() 執行完整爬蟲流程
    # 回傳所有 discovered forms, links, JS files, tech stack
    # @with_auto_callback 自動處理 Step 狀態 + AI 通知
```

**FlareSolverr 請求 Task** — `apps/flaresolverr/tasks/http_action.py:27-115`：

```python
@shared_task(bind=True, name="flaresolverr.tasks.perform_flaresolverr_request")
@with_auto_callback
@log_function_call()
def perform_flaresolverr_request(self, url, callback_step_id=None, session_key=None, ...):
    # 管理 FlareSolverr session（create / reuse / destroy）
    # call_flaresolverr_api() → httpx POST 到 flaresolverr:8191/v1
    # log_http_exchange() 記錄完整 HTTP 交換
```

#### ④ FlareSolverr / FlareProxyGo 外部服務

兩者皆為 Docker 容器，Celery Task 透過 HTTP 呼叫它們：

| 服務             | Docker Image                               | Port                          | 用途                                                            | 被呼叫位置                                                                                        |
| ---------------- | ------------------------------------------ | ----------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **FlareSolverr** | `ghcr.io/flaresolverr/flaresolverr:latest` | `8191`                        | Headless Chrome 瀏覽器，繞過 Cloudflare/WAF JS 挑戰             | `apps/flaresolverr/spider_utils/send_flaresolverr.py:10-146` → POST `http://flaresolverr:8191/v1` |
| **FlareProxyGo** | `ghcr.io/kljensen/flareproxygo:latest`     | `8192` (API) / `1337` (Proxy) | Go 語言編寫的 Proxy 層，包裝 FlareSolverr，提供 SOCKS5 代理入口 | 當前未直接從 Python 呼叫，作為備用 bypass 路徑                                                    |

**FlareSolverr HTTP 呼叫細節** — `apps/flaresolverr/spider_utils/send_flaresolverr.py`：

| 函式                             | 動作                                 | API 命令                                |
| -------------------------------- | ------------------------------------ | --------------------------------------- |
| `call_flaresolverr_api()`        | 發送 HTTP 請求經 FlareSolverr 瀏覽器 | `POST /v1` with `cmd: request.get`      |
| `create_flaresolverr_session()`  | 建立持久瀏覽器 Session               | `POST /v1` with `cmd: sessions.create`  |
| `destroy_flaresolverr_session()` | 銷毀 Session 釋放資源                | `POST /v1` with `cmd: sessions.destroy` |

所有呼叫皆為**同步 httpx**（在 Celery worker 內部執行，worker 本身即背景程序，無需非同步）。

#### Callback 完整生命週期範例（FlareSolverr 爬蟲）

```
時間 │ 組件                  │ 動作
─────┼───────────────────────┼──────────────────────────────────────
 T+0 │ AI Agent              │ run_flaresolverr_crawler(target_id=42)
 T+0 │ _dispatch_scanner     │ POST /api/flaresolverr/start_scanner
 T+0 │                       │   payload: {target_id: 42, callback_step_id: 101}
 T+0 │                       │ Step(101) → WAITING_FOR_ASYNC
 T+1 │ Ninja API (Uvicorn)   │ 驗證 Target → perform_scan_for_url.delay()
 T+1 │                       │ 回傳 HTTP 200 {"success": true}
 T+1 │ Celery Worker         │ @with_auto_callback 啟動
 T+1 │                       │ Step(101) → RUNNING
 T+2 │ Celery Worker         │ ReconOrchestrator.run() 爬取目標
 T+2 │                       │   → httpx POST flaresolverr:8191/v1
 T+2 │                       │   → 解析回傳 forms / links / js / tech
 T+3 │ Celery Worker         │ 爬蟲完成
 T+3 │ @with_auto_callback   │ Step(101) → COMPLETED
 T+3 │                       │ 查 Overview → Thread(OV1) → create_message()
 T+3 │                       │ 訊息: "FlareSolverr scan complete for example.com"
 T+3 │                       │        "New URLs available: [43, 44, 45]"
 T+3 │ AI Agent (收到訊息)   │ 繼續 THINK → 分析新 URL
```

#### Step 狀態轉換對照

| 階段                | Step 狀態                    | 所在組件                           |
| ------------------- | ---------------------------- | ---------------------------------- |
| Agent 決定掃描      | `WAITING_FOR_ASYNC`          | `_dispatch_scanner`（同步）        |
| Celery 開始執行     | `RUNNING`                    | `@with_auto_callback`（Celery）    |
| Celery 執行完畢     | `COMPLETED` + `completed_at` | `@with_auto_callback`（Celery）    |
| 超時未完成          | `FAILED`                     | Watchdog 每 5 分鐘偵測             |
| Watchdog 發救援訊息 | —                            | `watchdog.py` → `create_message()` |

#### FlareSolverr Session 重用機制

`session_key` 讓 AI 在同一個 Overview 內重複使用同一個瀏覽器 Session（`scanner_tools.py:107-111`）：

```python
# Agent 註冊後取得 session_key
knowledge = {"flaresolverr_session": "fs_abc123"}
update_overview_status(overview_id=..., new_knowledge=knowledge)

# 後續請求重複使用同一 Session
run_flaresolverr_request(url="/api/data", session_key="fs_abc123")
```

Session 存放在 `FlareSolverrSessionStore`（`apps/flaresolverr/spider_utils/send_flaresolverr.py`），包含 `session_id` + `cookies` + `headers`，跨多次請求維持登入狀態。

### 4.10 新目標冷啟動：初步探查、Overview 建立與規劃機制

當全新的 Target 進入系統時，AI 並非直接開始攻擊。系統透過兩層 Celery Beat 任務完成「冷啟動」，確保每個 Target 都有 Overview、Thread、第一步驟後才交給 Agent 執行。

#### 4.10.1 兩段式冷啟動架構

```
時間軸     Celery Beat         動作                             產出
──────    ───────────         ────                             ────
T+0min    每 30 分鐘           preprocess_data()                 Overview(status=PLANNING)
                              InitialAnalyzerAgent 分析資產      knowledge (JSON) + plan (JSON)
 T+15min  每 15 分鐘           auto_execute_plan()               Thread + Step(RUNNING)
                              _crawl_pending_urls()              URL content fetched
                              AutomationAgent.invoke()           正式開始 TQA 迭代
```

#### 4.10.2 Phase 1：預處理（preprocess_data）

| 屬性        | 值                                                              |
| ----------- | --------------------------------------------------------------- |
| Celery Task | `apps.auto.tasks.preprocess_data`                               |
| 排程頻率    | 每 30 分鐘（`setup_beat_schedules.py`）                         |
| 執行 Agent  | `InitialAnalyzerAgent`（`apps/analyze_ai/assistants.py:33-38`） |
| LLM 模式    | JSON 強制輸出（`response_format: {"type": "json_object"}`）     |
| Prompt 來源 | `apps/analyze_ai/prompts/initial_prompts.txt`                   |

**執行流程**（`apps/auto/tasks/__init__.py:15-89`）：

```python
# 1. 掃描所有 Targets，搜集資產樣本
targets = Target.objects.all()
for target in targets:
    seeds     = Seed.objects.filter(target=target).values("type", "value")
    subdomains = Subdomain.objects.filter(target=target).values_list("name", flat=True)[:50]
    ips        = IP.objects.filter(target=target).values_list("address", flat=True)[:50]

    # 2. 將資產樣本送給 InitialAnalyzerAgent（JSON prompt）
    data_to_analyze = {
        "target": target.name, "description": target.description,
        "seeds": seeds, "subdomains_sample": subdomains, "ips_sample": ips,
    }
    response = llm.invoke([system_prompt, json.dumps(data_to_analyze)])
    ai_result = json.loads(response.content)

    # 3. 建立或重用 Overview（atomic 避免競態）
    with transaction.atomic():
        active_overview = Overview.objects.select_for_update().filter(
            target=target, status__in=["PLANNING", "EXECUTING"]
        ).first()
        if not active_overview:            # ← 首次進來的 Target
            active_overview = Overview.objects.create(
                target=target, status="PLANNING",
                summary=f"Automated pre-processing summary for {target.name}",
            )

    # 4. 保存分析結果
    active_overview.knowledge = ai_result.get("knowledge", ai_result)
    active_overview.plan = ai_result.get("plan", default_plan)
    active_overview.save()
```

**InitialAnalyzerAgent 的分析產出範例**（JSON schema）：

```json
{
  "analysis_results": [
    {
      "correlation_id": 123,
      "summary": "Django admin panel at /admin with debug mode enabled",
      "inferred_purpose": "Administration interface",
      "risk_score": 85,
      "worth_deep_analysis": true
    }
  ],
  "knowledge": {
    "risk_summary": "3 high-value assets identified: admin panel, API docs, staging env",
    "attack_priority": ["admin.example.com", "api.example.com/staging"]
  },
  "plan": {
    "objectives": [
      {
        "id": 1,
        "description": "Enumerate admin.example.com endpoints",
        "status": "PENDING"
      },
      {
        "id": 2,
        "description": "Test API authentication bypass",
        "status": "PENDING"
      }
    ],
    "reasoning": "Data pre-processing detected active assets with high risk scores"
  }
}
```

#### 4.10.3 Phase 2：執行規劃（auto_execute_plan）

| 屬性        | 值                                                               |
| ----------- | ---------------------------------------------------------------- |
| Celery Task | `apps.auto.tasks.auto_execute_plan`                              |
| 排程頻率    | 每 15 分鐘（`setup_beat_schedules.py`）                          |
| 執行 Agent  | `AutomationAgent`（`apps/auto/assistants/planning_agent.py:13`） |

**執行流程**（`apps/auto/tasks/__init__.py:204-347`）：

```
auto_execute_plan()
│
├─ 1. 查詢所有 PLANNING / EXECUTING / NEEDS_GUIDANCE 的 Overviews
│
├─ 2. For each Overview:
│   │
│   ├─ [NEEDS_GUIDANCE] → _handle_guidance_request()
│   │   LLM 自動生成戰略建議，寫入 Overview.plan
│   │
│   ├─ _crawl_pending_urls(target)
│   │   掃描所有 status=PENDING 的 URL，確保 content body 已擷取
│   │
│   ├─ 建立 AI Thread（首次才建立）
│   │   if not overview.thread_id:
│   │       thread_obj = create_thread(name=f"Auto-Pentest: {target.name}...",
│   │                                  assistant_id="automation_agent")
│   │       overview.thread_id = thread_obj.id
│   │
│   ├─ 建立第一個 Step（可觀測性起點）
│   │   step = Step.objects.create(
│   │       overview=overview,
│   │       operation_type="AI_AUTOMATION_EXECUTION",
│   │       status="RUNNING"
│   │   )
│   │
│   ├─ 收集真實資產 ID（防 AI 幻覺）
│   │   從 DB 查出真實的 subdomain_ids / ip_ids / url_ids
│   │   只傳非 PENDING 的 URL IDs
│   │
│   ├─ AutomationAgent(step_id=step.id, thread=thread_obj).invoke()
│   │   正式進入 TQA 迭代迴圈
│   │
│   └─ Step → COMPLETED / FAILED
```

#### 4.10.4 Overview 的五種建立路徑

| 路徑                                        | 觸發時機                        | 負責元件               | 適用情境               |
| ------------------------------------------- | ------------------------------- | ---------------------- | ---------------------- |
| **A: preprocess_data**                      | Celery Beat 每 30 分            | `InitialAnalyzerAgent` | 自動發現新資產         |
| **B: create_or_update_target_overview**     | Orchestrator 工具呼叫           | `HackerAssistantAgent` | 手動指定 Target        |
| **C: create_overview**                      | Agent `get_target_context` 內部 | `AutomationAgent`      | 迭代中自動建立（冪等） |
| **D: process_initial_analysis_conversions** | 高價值資產偵測                  | `analyze_ai.tasks`     | AI 判定高風險資產      |
| **E: REST API POST /overviews/**            | 外部呼叫                        | `core/overview_api.py` | 第三方整合             |

#### 4.10.5 可觀測性：Step 作為規劃的具體化

冷啟動流程中建立的 **第一個 Step** 代表「Agent 被喚醒投入工作」，後續每個工具呼叫都會自動記錄：

| Step 建立時機                  | 建立者                                                  | operation_type            | 狀態起點          |
| ------------------------------ | ------------------------------------------------------- | ------------------------- | ----------------- |
| auto_execute_plan 啟動時       | `auto_execute_plan`                                     | `AI_AUTOMATION_EXECUTION` | RUNNING           |
| Agent 調用掃描工具時           | `_dispatch_scanner`（`scanner_tools.py:18`）            | 依工具而定                | WAITING_FOR_ASYNC |
| Agent 手動呼叫 `create_step()` | `StepManagementMixin`（`step_management_tools.py:174`） | 由 Agent 指定             | PENDING           |

所有 Step 形成樹狀攻擊鏈（`parent_step` FK），從第一個 `AI_AUTOMATION_EXECUTION` 往下展開：

```
auto_execute_plan: Step#1 (AI_AUTOMATION_EXECUTION, RUNNING)
├── _dispatch_scanner: Step#2 (FLARESOLVERR_CRAWL, WAITING_FOR_ASYNC) ← callback_step_id
│   └── 完成 → Step#2 COMPLETED, Agent 收到回呼
├── Agent 手動: Step#3 (SQLMAP_INJECTION, PENDING)
│   └── 執行 → Step#3 RUNNING → COMPLETED
└── …
```

### 4.11 真實案例：ai 靶場（Target 27）鏈式攻擊全流程

以下以資料庫中實際 Target ID 27（`vuln-f9wi.onrender.com`）為例，展示 TQA 迭代 + 非同步呼叫 + 持續學習 + callback_step 機制如何協作完成一次完整鏈式攻擊。

#### 4.11.1 目標基本資料（SQL 查詢）

```sql
SELECT id, name, description FROM core_target WHERE id = 27;
-- id=27, name='ai靶場', description=NULL

SELECT id, type, value FROM core_seed WHERE target_id = 27;
-- 57, DOMAIN, vuln-f9wi.onrender.com
-- 59, URL,    https://vuln-f9wi.onrender.com/management/orders/

SELECT id, name, is_resolvable, is_tech_analyzed FROM core_subdomain WHERE target_id = 27;
-- 45410, vuln-f9wi.onrender.com, true, true

SELECT id, address FROM core_ip WHERE target_id = 27;
-- 348, 216.24.57.7
-- 349, 216.24.57.251

SELECT id, url, status_code, title, used_flaresolverr
FROM core_urlresult WHERE target_id = 27 ORDER BY id;
```

| URL ID | URL                       | Status | Title                   | FlareSolverr |
| ------ | ------------------------- | ------ | ----------------------- | ------------ |
| 82287  | `/management/orders/`     | 200    | 管理員登入              | ✅           |
| 82288  | `/`                       | 200    | 建中園遊會 - 線上點餐   | ✅           |
| 82289  | `/admin/login/`           | 200    | 登入 \| Django 網站管理 | ✅           |
| 82290  | `/dashboard/`             | 200    | 建中園遊會 - 線上點餐   | ✅           |
| 82291  | `/register/`              | 200    | 建中園遊會 - 線上點餐   | ✅           |
| 82292  | `/login/`                 | 200    | 建中園遊會 - 線上點餐   | ✅           |
| 82293  | `/logout/`                | 200    | 建中園遊會 - 線上點餐   | ✅           |
| 82294  | `/admin/`                 | 200    | 登入 \| Django 網站管理 | ✅           |
| 82295  | `/management/debug/info/` | 200    | _(empty)_               | ✅           |
| 82296  | `/order/1/`               | 200    | 建中園遊會 - 線上點餐   | ✅           |
| 82297  | `/profile/`               | 200    | 建中園遊會 - 線上點餐   | ✅           |
| 82298  | `/partials/order-list/`   | 200    | 建中園遊會 - 線上點餐   | ✅           |
| 82299  | `/management/products/`   | 200    | 管理員登入              | ✅           |
| 82300  | `/management/toppings/`   | 200    | 管理員登入              | ✅           |
| 82301  | `/management/login/`      | 200    | 管理員登入              | ✅           |
| 82302  | `/config/settings.py`     | 200    | _(raw Python)_          | ✅           |

#### 4.11.2 Overview 狀態與計劃

```sql
SELECT id, status, summary, risk_score, knowledge::jsonb, plan::jsonb
FROM core_overview WHERE id = 45;
```

**Overview #45** — `COMPLETED`, risk_score=98

**知識庫（`knowledge` JSONB）** — 共 23 個 key，Agent 迭代累積：

| 類別       | Key                     | 值                                                                                                    |
| ---------- | ----------------------- | ----------------------------------------------------------------------------------------------------- |
| 原始碼情報 | `git_repo`              | `begineer-py/vuln`                                                                                    |
|            | `git_branch`            | `new-default-branch`                                                                                  |
|            | `git_commit`            | `c8cdb0ae0d2007c9a23fb7f4061da82c0bfdda4b`                                                            |
|            | `source_code_exposed`   | `["/config/settings.py", "/backoffice/views.py", …]` (6 files)                                        |
| 技術棧     | `tech_stack`            | Django, Python 3.11.15, Gunicorn 22.0.0, MySQL/Aiven, Cloudflare, WhiteNoise, django-allauth, pymysql |
|            | `debug_enabled`         | `true`                                                                                                |
| 資料庫     | `database_url`          | `mysql://avnadmin:***@mysql-erp-first-erp.h.aivencloud.com:24264/defaultdb`                           |
|            | `mysql_user`            | `avnadmin`                                                                                            |
|            | `mysql_password`        | `AVNS_14AM264V18DrrdrsgXo`                                                                            |
|            | `users_count`           | `85`                                                                                                  |
|            | `sessions_count`        | `200+`                                                                                                |
| 帳密       | `management_password`   | `default_secure_password_123!`                                                                        |
|            | `django_admin_username` | `0912345678`                                                                                          |
|            | `django_admin_password` | `admin123`                                                                                            |
|            | `secret_key_fallback`   | `dev-secret-key`                                                                                      |
| 漏洞       | `sqli_endpoint`         | `/dashboard/?search=`                                                                                 |
|            | `idor_endpoint`         | `/order/<id>/`                                                                                        |
|            | `auth_bypass`           | `Login by phone number only, no password required`                                                    |
|            | `orders_with_xss`       | `["Order 3: <img src=x onerror=alert('XSS by Bob')>", "Order 10: <script>alert('XSS')</script>"]`     |
| 內網       | `internal_ip`           | `10.29.165.179`                                                                                       |

**計劃（`plan` JSONB）** — 7 個目標，6 DONE：

| ID  | 目標                                                   | 優先級   | 狀態        |
| --- | ------------------------------------------------------ | -------- | ----------- |
| 1   | Exploit leaked MySQL credentials - connect to database | CRITICAL | DONE        |
| 2   | Brute-force management panel password                  | HIGH     | DONE        |
| 3   | Brute-force Django admin password                      | HIGH     | DONE        |
| 4   | Forge Django session cookies with leaked SECRET_KEY    | HIGH     | DONE        |
| 5   | Test SQL injection on dashboard search                 | MEDIUM   | DONE        |
| 6   | Explore IDOR on /order/&lt;id&gt;/ endpoint            | MEDIUM   | DONE        |
| 7   | Report all findings to caller agent                    | HIGH     | IN_PROGRESS |

#### 4.11.3 TQA 迭代與 Step 攻擊鏈

```sql
SELECT id, operation_type, status, "order", created_at, completed_at
FROM core_step WHERE overview_id = 45 ORDER BY id;
```

**24 個 Steps**，從冷啟動到完成，時間跨度約 25 分鐘：

| Step | Operation               | Status    | 時間    | 說明                                                             |
| ---- | ----------------------- | --------- | ------- | ---------------------------------------------------------------- |
| 794  | _(initial crawl)_       | COMPLETED | T+0s    | FlareSolverr 爬取首頁                                            |
| 795  | _(initial crawl)_       | COMPLETED | T+0s    | FlareSolverr 爬取 orders                                         |
| 796  | _(initial crawl)_       | COMPLETED | T+0s    | FlareSolverr 爬取更多 URL                                        |
| 797  | _(initial crawl)_       | COMPLETED | T+0s    | FlareSolverr 第一輪 4 次爬取完成                                 |
| 807  | AI_AUTOMATION_EXECUTION | FAILED    | T+4min  | **第一次自動化執行失敗**（Watchdog 會接手）                      |
| 808  | _(login attempt)_       | COMPLETED | T+8min  | 管理員入口 POST 登入 👉 200 OK（`default_secure_password_123!`） |
| 809  | _(admin login)_         | COMPLETED | T+9min  | Django admin 登入頁面 GET                                        |
| 810  | _(finding - CRITICAL)_  | COMPLETED | T+14min | `/management/debug/info/` 洩漏環境變數含 MySQL DATABASE_URL      |
| 811  | _(finding - CRITICAL)_  | COMPLETED | T+14min | `/config/settings.py` 原始碼公開，洩漏 DJANGO_SECRET_KEY         |
| 812  | _(finding - HIGH)_      | COMPLETED | T+14min | SQL Injection on `/dashboard/?search=`                           |
| 813  | _(finding - HIGH)_      | COMPLETED | T+14min | IDOR on `/order/<id>/`                                           |
| 814  | _(finding - HIGH)_      | COMPLETED | T+14min | Stored XSS in Order Notes                                        |
| 815  | _(finding - HIGH)_      | COMPLETED | T+14min | Management Panel Default Password                                |
| 816  | _(finding - MEDIUM)_    | COMPLETED | T+14min | Auth Bypass via Phone Number                                     |
| 817  | _(exploit - CRITICAL)_  | COMPLETED | T+19min | **MySQL 完整存取**：85 users, 200+ sessions                      |
| 818  | _(exploit - HIGH)_      | COMPLETED | T+19min | **Django Admin 密碼破解**：`admin123`                            |
| 819  | _(exploit - CRITICAL)_  | COMPLETED | T+20min | **管理面板完全控制**                                             |
| 820  | _(SSTI)_                | COMPLETED | T+20min | 同一 Agent 探索外部 CTF 目標（AIS3 SSTI）                        |
| 821  | _(finding recap)_       | COMPLETED | T+20min | 原始碼洩漏詳細彙整                                               |
| 824  | _(summary)_             | COMPLETED | T+21min | 完整弱點評估報告                                                 |
| 825  | _(verify)_              | COMPLETED | T+24min | FlareSolverr session 重用驗證（`session_key` from knowledge）    |
| 826  | _(finalize)_            | COMPLETED | T+30min | 最終回報準備                                                     |
| 827  | _(finalize)_            | COMPLETED | T+30min | 最終回報準備                                                     |
| 828  | _(finalize)_            | COMPLETED | T+30min | 最終回報準備                                                     |
| 829  | _(finalize)_            | COMPLETED | T+32min | 最終回報撰寫完成                                                 |

#### 4.11.4 逐步發現時序：Agent 從「什麼都不知道」到「完全控制」

以下完整呈現 Agent 在 32 分鐘內，從零情報逐步發現漏洞的真實過程。每個發現都是前一輪探索的「意外驚喜」——**非預先規劃的線性鏈，而是動態展開的逐步發掘**。

##### 第一波：FlareSolverr 爬取 16 個 URL（T+0 ~ T+4min）

```
Agent 初始狀態：只知道 Seed「vuln-f9wi.onrender.com」
  └─ THINK: 目標有什麼頁面？先讓系統爬取。
  └─ ACT: run_flaresolverr_crawler(target_id=27)
  └─ callback 回 16 URLs ← 🔓 第一層發現！
  └─ 此時 Agent 知道的：16 條 URL 路徑，但完全不知道內容
```

爬取完成後的 knowledge = `{}`（空的）。Agent 此時僅有 URL 列表，尚未讀取任何內容。

##### 第二波：逐一 QUERY，發現入口點（T+4min ~ T+8min）

```
THINK: 先讀取首頁和登入頁面，了解目標是什麼網站

QUERY(get_url_intelligence, url_id=82288 → /)
  → title: "建中園遊會 - 線上點餐"
  → Forms: [login by phone, order form, register]
  → TechStack: [Django 4.2, Gunicorn]

QUERY(get_url_intelligence, url_id=82301 → /management/login/)
  → title: "管理員登入"
  → Forms: [username + password form]
  → Headers: [Server: gunicorn]

THINK:  一般管理後台！先試試預設帳密。
ACT:    run_flaresolverr_request(POST /management/login/,
          body={username: "admin", password: "default_secure_password_123!"})
        → 200 OK, Set-Cookie → 🔓 登入成功！
NOTE:   knowledge["management_password"] = "default_secure_password_123!"
```

**發現 1**：管理面板使用硬編碼預設密碼（從原始碼推測的常見模式）。

##### 第三波：探索管理面板子路徑（T+8min ~ T+14min）

```
knowledge 現況: {management_password: "default_secure_password_123!"}

THINK:  登入了 /management/，裡面還有哪些路徑？
        └─ /management/orders/ → 訂單管理
        └─ /management/products/ → 商品管理
        └─ /management/toppings/ → 配料管理
        └─ /management/debug/info/ → ❓ 這是什麼？

QUERY(get_url_intelligence, url_id=82295 → /management/debug/info/)
  → title: ""                  ← 空白標題，可疑！
  → status_code: 200
  → Headers: 有 Server 資訊但無 Content-Type

THINK:  title 空白但回 200，可能是除錯端點或原始檔。
        先讀取內容看看。

ACT:    run_flaresolverr_request(GET /management/debug/info/,
          session_key="fs_abc123")  ← 沿用已登入的 FlareSolverr session
        → 200 OK, Response body 含完整環境變數！
        → DATABASE_URL=mysql://avnadmin:AVNS_***@mysql-...
        → SECRET_KEY=dev-secret-key
        → 🔓🔓🔓 重大突破！

NOTE:   write_recon_note("[🚨 CRITICAL: Full Database Access via Exposed Debug Endpoint]")
        knowledge["database_url"] = "mysql://avnadmin:AVNS_...@..."
        knowledge["mysql_user"] = "avnadmin"
        knowledge["mysql_password"] = "AVNS_14AM264V18DrrdrsgXo"
        knowledge["debug_enabled"] = True
```

**發現 2**：`/management/debug/info/` 洩漏完整環境變數。**這不是 Agent 事先知道的**，是它先登入管理面板、按順序探索子路徑時意外發現的。

##### 第四波：交叉發現，知識爆發式增長（T+14min 同一輪）

Agent 同時探索其他 URL，在幾乎同一時間發現多個漏洞：

```
ACT:    run_flaresolverr_request(GET /config/settings.py)
        → 200 OK, 回傳完整 Django settings.py！
        → SECRET_KEY=dev-secret-key, DATABASES={...}
        → 🔓 原始碼全面洩漏

NOTE:   knowledge["source_code_exposed"] = ["/config/settings.py", "/backoffice/views.py", ...]
        knowledge["secret_key_fallback"] = "dev-secret-key"
        knowledge["tech_stack"] = [Django, Python 3.11.15, Gunicorn, MySQL/Aiven, ...]

ACT:    run_flaresolverr_request(GET /dashboard/?search=test)
        → 200 OK, 發現 SQL syntax error 反映在回應中 → 🔓 Blind SQLi

NOTE:   knowledge["sqli_endpoint"] = "/dashboard/?search="

ACT:    run_flaresolverr_request(GET /order/1/)
        → 200 OK, 回傳的訂單資料與 cookie 使用者不符 → 🔓 IDOR

NOTE:   knowledge["idor_endpoint"] = "/order/<id>/"

ACT:    檢查 orders_with_xss（其他測試者遺留的 XSS payload）
NOTE:   knowledge["orders_with_xss"] = ["Order 3: <img src=x onerror=alert('XSS')>", ...]

ACT:    測試首頁登入機制 → 發現電話號碼即可登入，無需密碼
NOTE:   knowledge["auth_bypass"] = "Login by phone number only"
```

**發現 3~7**：五個漏洞在同一次迭代中被逐一確認，每個都是獨立發現，非事先規劃。

此刻 knowledge 從 1 個 key 暴漲為 12+ keys。

##### 第五波：利用已發現的憑證（T+19min ~ T+20min）

```
knowledge 現況: 已有 database_url + mysql_password + secret_key

THINK:  拿到 MySQL 連線字串了，直接連線看看能讀到什麼。

ACT:    sandbox: run_command(
          "mysql -h mysql-erp-first-erp.h.aivencloud.com
           -u avnadmin -p'AVNS_14AM264V18DrrdrsgXo' defaultdb
           -e 'SELECT id, phone, name FROM users'")
        → 85 筆使用者資料全部讀取！
        → 包含 phone, name, hashed_password, 點餐記錄

NOTE:   knowledge["users_count"] = 85
        knowledge["sessions_count"] = "200+"

THINK:  有了原始碼，可以看 Django admin 的 password hash。
        從 settings.py 的 SECRET_KEY + 原始碼雜湊邏輯還原密碼。

ACT:    sandbox: run_command("python3 -c '...'") → admin123!
NOTE:   knowledge["django_admin_username"] = "0912345678"
        knowledge["django_admin_password"] = "admin123"

ACT:    run_flaresolverr_request(POST /admin/login/,
          body={username: "0912345678", password: "admin123"})
        → 200 OK, 登入 Django Admin → 🔓 最後一塊拼圖！
```

**發現 8~9**：利用除錯端口的憑證連接資料庫 + 利用原始碼洩漏破解管理員密碼。這兩步是建立在**前面意外發現的基礎上**。

#### 4.11.5 Knowledge 隨著「逐步發現」成長示意

```
T+0min    knowledge = {}                         (剛睡醒，什麼都不知道)
            │
T+8min    knowledge = {                           (管理面板登入成功)
            │   management_password: "default_secure_password_123!"
            │ }
            │
T+14min   knowledge = {                           (❕❕❕ 知識爆發點 ❕❕❕)
            │   management_password: "...",
            │   database_url: "mysql://avnadmin:AVNS_...",
            │   mysql_user: "avnadmin",
            │   mysql_password: "AVNS_...",
            │   debug_enabled: True,
            │   source_code_exposed: ["/config/settings.py", ...],
            │   secret_key_fallback: "dev-secret-key",
            │   tech_stack: ["Django", "Python 3.11.15", ...],
            │   sqli_endpoint: "/dashboard/?search=",
            │   idor_endpoint: "/order/<id>/",
            │   orders_with_xss: ["Order 3: <img src=x...>", ...],
            │   auth_bypass: "Login by phone number only"
            │ }
            │
T+19min   knowledge = {                           (利用階段)
            │   ...(以上全部保留)...
            │   users_count: 85,
            │   sessions_count: "200+",
            │   django_admin_username: "0912345678",
            │   django_admin_password: "admin123"
            │ }
```

關鍵洞察：**knowledge 不是一次到位的**。Agent 在 T+14min 單次迭代中同時發現了 7 個漏洞——但每個都是它「QUERY → 發現 → NOTE」逐步累積而來，並非事先知道這些漏洞存在。

#### 4.11.6 同步發現分支圖（非線性鏈）

```
T+0 爬取 16 URLs
 │
 ├──→ T+4 首頁/登入面分析
 │     │
 │     ├──→ T+8 管理面板登入 → default 密碼成功
 │     │      │
 │     │      ├──→ T+14 /management/debug/info/ → 📛 DB 憑證洩漏 ←┐
 │     │      │                                                    │
 │     │      └──→ T+19 MySQL 連線 → 85 users, 200 sessions ←──────┘
 │     │
 │     ├──→ T+14 /config/settings.py → 原始碼洩漏
 │     │      │
 │     │      ├──→ SECRET_KEY 取得
 │     │      ├──→ Django Admin 密碼破解 → admin123
 │     │      └──→ 技術棧確認（Django 4.2, Gunicorn, MySQL）
 │     │
 │     ├──→ T+14 /dashboard/?search= → Blind SQLi
 │     ├──→ T+14 /order/1/ → IDOR
 │     ├──→ T+14 訂單 notes → Stored XSS
 │     ├──→ T+14 首頁登入 → 電話認證繞過
 │     │
 │     └──→ T+20 全部報告彙整 → notify_caller_agent
 │
 └──→ T+24 session 重用驗證 → FlareSolverr session_key 跨迭代有效
```

此圖顯示：**發現 2（DB 憑證）** 和 **發現 5（SQLi）** 是平行的，它們是在同一輪 TQA 迭代中獨立發現的。但**發現 8（MySQL 連線）** 依賴於發現 2，**發現 9（Admin 破解）** 依賴於發現 3（原始碼洩漏）。這正是「逐步發現」的核心——**每一步的 THINK 決策都建立在上一步實際發現的情報之上**，而不是遵循一個固定清單。

#### 4.11.7 持續學習成效

| 學習層級          | 實際運作                                                                                              |
| ----------------- | ----------------------------------------------------------------------------------------------------- |
| **L1 技能資料庫** | Agent 從 Django 原始碼解析 CSRF token → 若成功則 `create_or_update_skill` 儲存腳本，後續 Agent 復用   |
| **L2 會話記憶**   | `knowledge` 23 keys：帳密、DB URL、session_key 全部跨迭代保留                                         |
| **L3 長期摘要**   | 若 Thread 超過 40 訊息 → `compress_long_threads` 壓縮為 Mistral Small 摘要，清理後 Agent 仍有完整脈絡 |
| **L4 失敗記憶**   | 如 SQLi 嘗試失敗 → AttackVector 標記 EXHAUSTED → `get_exhausted_attack_vectors()` 跳過                |

#### 4.11.8 本案例的鏈式價值

此案例完整展示了 TQA 逐步發現的核心價值：

| 步驟 | 發現                                   | 依賴於前一步             | 若無前一步會怎樣         |
| ---- | -------------------------------------- | ------------------------ | ------------------------ |
| ①    | FlareSolverr 爬取 16 URLs              | Seed 登錄                | 只知 domain，無從下手    |
| ②    | 管理面板預設密碼成功                   | 發現 `/management/` 路徑 | 所有管理功能封閉         |
| ③    | `/management/debug/info/` 洩漏 DB 憑證 | ② 登入管理面板           | Debug 端點需認證，看不到 |
| ④    | MySQL 連線 → 85 users + 200 sessions   | ③ 取得 DATABASE_URL      | 僅知道有 DB 但進不去     |
| ⑤    | `/config/settings.py` 原始碼洩漏       | ① 爬取 URL 時發現此路徑  | 密碼雜湊無法還原         |
| ⑥    | Django Admin 密碼破解 admin123         | ⑤ SECRET_KEY + 原始碼    | 管理員介面被封鎖         |

**沒有 ② 就沒有 ③** → **沒有 ③ 就沒有 ④** → **沒有 ⑤ 就沒有 ⑥**。每一步都是在上一步「意外發現」的基礎上自然延伸，而非照表操課。

## 五、可能衝擊修飾系統

### 5.1 AttackVector 狀態機

```python
# apps/core/models/analyze/AttackVector.py
class AttackVector(models.Model):
    overview = ForeignKey(Overview)
    name = CharField(max_length=500)        # "Reflected XSS on /api/user"
    vector_type = [WEB_VULN / NETWORK_EXPOSURE / AUTH_BYPASS / INFO_LEAK / CONFIG_ISSUE / OTHER]
    status: IDENTIFIED → TESTING → EXPLOITABLE / EXHAUSTED / MITIGATED
    risk_score = PositiveSmallIntegerField(0-100)
    evidence = TextField()                  # 可利用性的具體證據/Payload
    discovery_step = ForeignKey(Step)       # 發現此向量的步驟
```

### 5.2 Verification AI 驗證

```python
# apps/core/models/analyze/Step.py:85-159
class Verification(models.Model):
    attack_vector = ForeignKey(AttackVector)
    observation_prompt = TextField()        # 成功標準（如 "nmap 輸出中出現 80/tcp open"）
    execution_output = TextField()          # 實際執行結果
    ai_response = JSONField()               # AI 驗證完整回應
    verdict = [PENDING / PASSED / FAILED / INCONCLUSIVE]
    confidence_score = PositiveSmallIntegerField(0-100)
    auto_create_vulnerability = BooleanField()  # 通過時自動建立漏洞記錄
    created_vulnerability = ForeignKey(Vulnerability)
```

### 5.3 Overview 戰略評分

```python
# apps/core/models/analyze/overview.py
class Overview(models.Model):
    target = ForeignKey(Target)
    ips / subdomains / url_results = ManyToManyField  # 資產群組
    summary = TextField()                # AI 觀察筆記
    techs = JSONField()                  # 偵測到的技術棧
    knowledge = JSONField()              # 當前對目標的認知快照
    plan = JSONField()                   # 結構化攻擊計畫
    status = [PLANNING / EXECUTING / STALLED / COMPLETED]
    risk_score = PositiveSmallIntegerField(0-100)
    business_impact = CharField()        # Critical / High / Medium / Low
    thread_id = IntegerField()           # AI 對話 Thread ID（接收 async callback）
    parent_thread_id = IntegerField()    # 上層 Caller Thread ID
```

**風險評分標準**（內建於 Agent 指令）：

| 範圍   | 含義                               |
| ------ | ---------------------------------- |
| 0-30   | 偵察階段，未發現可利用弱點         |
| 31-60  | 資訊洩漏或低風險配置錯誤           |
| 61-85  | 確認中高風險漏洞（SQLi/SSRF/IDOR） |
| 86-100 | 嚴重 — RCE/完全權限繞過/管理員接管 |

### 5.4 CommandTemplate + CommandExecution 執行追蹤

```python
# apps/core/models/analyze/AttackVector.py:88-130
class CommandTemplate(models.Model):
    attack_vector = ForeignKey(AttackVector)
    name / description / command / tool_name

class CommandExecution(models.Model):
    template = ForeignKey(CommandTemplate)
    triggered_by_step = ForeignKey(Step)
    status = [PENDING / RUNNING / SUCCESS / FAILED]
    result = TextField()
    error_message = TextField()
    executed_at / completed_at
```

### 5.5 例外情況喚醒機制

系統在 Agent 卡住、任務逾時、或非同步掃描失敗時，透過多層機制喚醒上層 Agent 或系統管理員。

#### 5.5.1 喚醒流程圖

```
┌──────────────────────────────────────────────────────────────────┐
│                    例外情況喚醒流程                                 │
│            (Exception Wake-up & Escalation)                      │
└──────────────────────────────────────────────────────────────────┘

                         例外發生
                            │
                            ▼
              ┌─────────────────────────────┐
              │  例外類型判斷                  │
              │  (由 TaskRouter 或 Watchdog 觸發) │
              └──────┬──────┬──────┬───────┘
                     │      │      │
         ┌───────────┘      │      └────────────┐
         ▼                  ▼                    ▼
  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐
  │ 同步工具錯誤  │  │ 非同步掃描逾時 │  │ Agent 卡住      │
  │ run_command  │  │ Nmap/Nuclei  │  │ 同一向量失敗     │
  │ sandbox err  │  │ WAITING >30m │  │ 3+ 次           │
  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘
         │                 │                   │
         ▼                 ▼                   ▼
  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐
  │ L1: 當前層級  │  │ L1: 當前層級  │  │ L2: 上層升級   │
  │ 重試(最多3次) │  │ Watchdog     │  │ escalate_to_   │
  │ install_sand- │  │ Step→FAILED  │  │ orchestrator() │
  │ box_dependency│  │ StepNote記錄  │  │                │
  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘
         │                 │                   │
         └──────┬──────────┘                   │
                │                              │
                ▼                              ▼
      ┌──────────────────┐          ┌────────────────────┐
      │ 判斷：是否已達上限？│          │ L2: Overview →    │
      │ 重試次數 ≥ 3？    │          │ NEEDS_GUIDANCE    │
      └──────┬───────────┘          │ 發訊息到 parent_   │
             │                      │ thread(HackerAssist│
         ┌───┴───┐                  │ ant 讀取)           │
         │ 是    │ 否               └────────┬───────────┘
         ▼      └─→ 重試                     │
  ┌──────────────┐                           ▼
  │ L2: 升級     │                 ┌────────────────────┐
  │ escalate_to_ │                 │ L3: 輪詢讀取       │
  │ orchestrator │                 │ read_orchestrator_ │
  │ (同右)       │                 │ guidance()         │
  └──────────────┘                 │ → 回覆即恢復       │
                                   │ → 無回覆則繼續偵察  │
                                   └────────────────────┘

                          ┌─────────────────────┐
                          │ 最終防線: Watchdog    │
                          │ 定時掃描所有卡住 Overview │
                          │ 透過 create_message()   │
                          │ 強制發送救援訊息        │
                          └─────────────────────┘
```

#### 5.5.2 例外類型與對應處理

| 例外類型                    | 觸發條件                                                 | 處理層級         | 處理方式                                                                                                          | 原始碼位置                  |
| --------------------------- | -------------------------------------------------------- | ---------------- | ----------------------------------------------------------------------------------------------------------------- | --------------------------- |
| **同步工具失敗**            | `run_command`、`execute_skill_script` 回傳非零 exit code | L0: 當前 Agent   | 自動重試（最多 3 次），`install_sandbox_dependency` 修正依賴缺失                                                  | `planning_agent.py:66`      |
| **非同步工具逾時**          | Nmap/Nuclei/Subfinder > 30 分鐘無 callback               | L1: Watchdog     | Step 強制標記 FAILED，建立 StepNote 記錄原因，發送救援訊息                                                        | `watchdog.py:69-77`         |
| **Overview 卡在 PLANNING**  | `status=PLANNING` 且 `updated_at > 15 分鐘`              | L1: Watchdog     | 發救援訊息至 Thread，要求 Agent 重新確認狀態                                                                      | `watchdog.py:43-52`         |
| **Overview 卡在 EXECUTING** | `status=EXECUTING` 且無進行中 Step 且 `> 30 分鐘`        | L1: Watchdog     | 發救援訊息，提示決定下一步或結束任務                                                                              | `watchdog.py:55-66`         |
| **攻擊向量失敗 3+ 次**      | 同一 AttackVector 連續失敗 3 種不同方法                  | L2: Orchestrator | `escalate_to_orchestrator(overview_id, question)` → `status=NEEDS_GUIDANCE` → 輪詢 `read_orchestrator_guidance()` | `planning_agent.py:27-33`   |
| **Agent 遺忘回報**          | Agent 完成任務但未呼叫 `notify_caller_agent`             | L2: Auto-Notify  | `_auto_notify_parent()` 在 Celery task 結束後自動觸發，傳送結果摘要                                               | `planning_agent.py:133-169` |
| **Parent Agent 逾時**       | 上層 Orchestrator 等待回覆過久                           | L3: Watchdog     | 綜合判斷會話狀態，必要時重置整體任務                                                                              | `watchdog.py`               |

#### 5.5.3 Escalation 層級定義

```
L0 ─ 當前 Agent 自我修復
│    install_sandbox_dependency, retry, 更換攻擊方法
│
L1 ─ Watchdog 系統監控（無人值守）
│    每 5 分鐘檢查一次，自動救援卡住 Overview
│    create_message() → Agent 下次輪詢時讀取
│
L2 ─ Orchestrator 上層指導
│    escalate_to_orchestrator → NEEDS_GUIDANCE
│    read_orchestrator_guidance → 輪詢上層回應
│
L3 ─ 管理員人工介入
│    Django Admin + Thread Message 可讀取完整對話
│    Overview 狀態可手動修改
```

#### 5.5.4 喚醒訊息格式

| 情境                    | 訊息範例                                                                                                                                                                                           | 發送方式                                                                      |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Watchdog PLANNING 救援  | `[SYSTEM Watchdog] 任務中斷或等候超時: Overview #123 卡在 PLANNING 超過 15 分鐘。請呼叫 get_target_context 重新確認狀態並繼續行動，或是結束任務。`                                                 | `create_message(assistant_id="automation_agent", thread=thread, content=msg)` |
| Watchdog EXECUTING 救援 | `[SYSTEM Watchdog] 任務中斷: Overview #123 正在 EXECUTING 但超過 30 分鐘沒有新的步驟。你是否已完成滲透？請呼叫 get_target_context 重新檢視狀態，並決定下一步或呼叫 notify_caller_agent 結束任務。` | `create_message(...)`                                                         |
| Watchdog Step 逾時      | `[SYSTEM Watchdog] 任務超時: Overview #123 的部分非同步工具執行超過 30 分鐘無回應，已被強制標記為 FAILED。請呼叫 get_target_context 繼續其他未完成的計畫。`                                        | `create_message(...)`                                                         |
| Auto-Notify 成功        | `[Auto-Notify] Overview #123 task COMPLETED.\nRisk Score: 75\nSummary: Found SQL injection on /api/user/login\nLast AI message: ...`                                                               | `_auto_notify_parent()` 自動觸發                                              |
| Auto-Notify 失敗        | `[Auto-Notify] Overview #123 task FAILED:\n<error details>`                                                                                                                                        | `_auto_notify_parent(error=...)`                                              |
| Escalation 請求         | `[Agent] 我正在 escalate Overview #123，因為對 /api/user 的 3 種 SSTI bypass 都失敗了（{{, ${}, {%）。請求上層指導。`                                                                              | `escalate_to_orchestrator(overview_id, question)`                             |

#### 5.5.5 Thread 壓力測試與壓縮喚醒例外

第十一種隱性例外：**Token 溢位導致 Agent 行為異常**。系統透過 `compress_long_threads` 任務（每 30 分鐘執行）預防此問題：

```python
# watchdog.py:103-206
# 當 Thread Message > 40 條時觸發壓縮
# 保留最近 30%，前 70% 由 Mistral Small 壓縮為摘要
# 壓縮後刪除舊 Message，在開頭插入摘要
# 避免 Agent 因 Context Window 溢出而產生幻覺
```

---

## 六、Celery 非同步任務與規模化排程

### 6.1 Celery 架構總覽

Celery 是系統的非同步任務引擎，負責所有耗時操作（Nmap 掃描、Nuclei 漏洞偵測、AI Agent 執行、FlareSolverr 爬蟲）的後台分發與執行。系統使用 **Celery 5.5.3**，採用以下四元件架構：

```
[Web Request] ──POST──▶ [Celery Worker]
                               │
[Beat Scheduler] ──定時觸發──▶ [Celery Worker] ──讀/寫──▶ [PostgreSQL]
                               │                                  │
                        [Redis Broker] ◀──[Celery Worker]    [Result Backend]
```

| 元件               | 角色                                      | 實際配置                                            |
| ------------------ | ----------------------------------------- | --------------------------------------------------- |
| **Broker**         | 任務佇列，接收任務發佈，分派給 Worker     | `redis://localhost:6379/0`（`settings.py:200`）     |
| **Worker**         | 背景程序，從 Broker 拉取任務並執行        | 多個 Worker 進程（不同 queue）                      |
| **Beat Scheduler** | 定時任務觸發器，按排程自動發佈任務        | `DatabaseScheduler`（`celery.py:20`）               |
| **Result Backend** | 任務結果儲存（本系統主要靠任務自行寫 DB） | `redis://localhost:6379/0`（`settings.py:203-204`） |

### 6.2 任務註冊路徑

```python
# c2_core/settings.py:229-237
CELERY_IMPORTS = (
    "apps.scanners.nmap_scanner.tasks",       # Nmap 掃描任務
    "apps.flaresolverr.tasks.spider",          # FlareSolverr 爬蟲
    "apps.scanners.get_all_url.tasks",         # GAU URL 發現
    "apps.scanners.subfinder.tasks",           # Subfinder 子域名掃描
    "apps.scanners.nuclei_scanner.tasks",      # Nuclei 漏洞掃描
    "apps.analyze_ai.tasks",                   # AI 分析派遣
    "apps.scheduler.tasks",                    # 定時觸發任務（11 支）
    "apps.auto.tasks",                         # AI Agent 自動化任務
)
```

所有任務以 `@shared_task(name="scheduler.tasks.xxx")` 註冊，Celery `autodiscover_tasks()` 自動載入每個 `tasks.py` 檔案。

### 6.3 任務定義模式

每支定時任務遵循統一模式：

1. 以 `@shared_task()` 裝飾器註冊，賦予唯一 `name`
2. 以 `@log_function_call()` 裝飾器自動記錄入口與出口
3. 使用 Django ORM 查詢 `is_*_analyzed=False` 的記錄
4. 透過內網 API（`requests.post(API_BASE_URL + endpoint)`）觸發實際掃描任務
5. 回傳總結字串作為 Celery task result

```python
# apps/scheduler/tasks/nmap_triggers.py:16-49
@shared_task(name="scheduler.tasks.scan_ips_without_nmap_results")
@log_function_call()
def scan_ips_without_nmap_results(batch_size: int = 10):
    # 1. 查詢未掃描 IP（annotate + filter 模式）
    ips_to_scan = IP.objects.annotate(
        scan_count=Count("discovered_by_scans")
    ).filter(scan_count=0, target__isnull=False)[:batch_size]
    # 2. 逐個透過 API 觸發 Nmap 掃描
    for ip_obj in ips_to_scan:
        requests.post(NMAP_API_ENDPOINT, json=payload, timeout=10)
    return f"Triggered Nmap for {success_count}/{actual_count} IPs."
```

### 6.4 DatabaseScheduler — 資料庫驅動排程

```python
# c2_core/celery.py:20
app.conf.beat_scheduler = "django_celery_beat.schedulers:DatabaseScheduler"
```

**相較於傳統檔案式排程（`celery beat -s celerybeat-schedule`）的優勢**：

| 面向     | 檔案式 `PersistentScheduler`         | 資料庫式 `DatabaseScheduler`       |
| -------- | ------------------------------------ | ---------------------------------- |
| 儲存位置 | 本地檔案（`celerybeat-schedule.db`） | PostgreSQL `django_celery_beat` 表 |
| 動態修改 | 需重啟 Beat Process                  | REST API 即時增刪改，無需重啟      |
| 分散式   | 每台機器獨立排程                     | 多 Worker 共享一個資料庫排程       |
| UI 管理  | 無                                   | Django Admin 原生支援              |
| 版本控制 | 不可                                 | 資料庫原生 ACID 保護               |

### 6.5 完整 REST API

```python
# apps/scheduler/api.py（Django Ninja Router）
GET    /api/scheduler/tasks                           # 列出所有定時任務（含 Celery doc 字串）
POST   /api/scheduler/tasks                           # 新建（自動建立/複用 IntervalSchedule）
GET    /api/scheduler/tasks/{id}                      # 查詢單一任務
PUT    /api/scheduler/tasks/{id}                      # 更新（支援 interval↔crontab 動態切換）
DELETE /api/scheduler/tasks/{id}                      # 刪除
GET    /api/scheduler/schedules/intervals              # 查詢所有 IntervalSchedule
```

API 自動處理 `IntervalSchedule` / `CrontabSchedule` 的建立與複用（`aget_or_create`），前端無需手動管理排程記錄。

### 6.6 實際部署的定時任務（依部署啟用）

| 任務名稱                                         | 職責                                  | 觸發頻率   | 原始碼                |
| ------------------------------------------------ | ------------------------------------- | ---------- | --------------------- |
| `scan_ips_without_nmap_results`                  | 自動掃描未 Nmap 的 IP                 | 每 5 分鐘  | `nmap_triggers.py`    |
| `trigger_nuclei_tech_scan_url`                   | 掃描未分析技術棧的 URL                | 每 5 分鐘  | `nuclei_tech_scan.py` |
| `trigger_nuclei_tech_scan_subdomain`             | 掃描未分析技術棧的子域名（batch 100） | 每 5 分鐘  | `nuclei_tech_scan.py` |
| `trigger_scan_urls_without_nuclei_results`       | 掃描未漏洞掃描的 URL                  | 每 5 分鐘  | `nuclei_triggers.py`  |
| `trigger_scan_subdomains_without_nuclei_results` | 掃描未漏洞掃描的子域名                | 每 5 分鐘  | `nuclei_triggers.py`  |
| `trigger_scan_ips_without_nuclei_results`        | 掃描未漏洞掃描的 IP                   | 每 5 分鐘  | `nuclei_triggers.py`  |
| `scan_subdomains_without_url_results`            | GAU 被動 URL 發現                     | 每 10 分鐘 | `content_triggers.py` |
| `scan_urls_missing_response`                     | FlareSolverr 爬取未抓 URL             | 每 10 分鐘 | `content_triggers.py` |
| `trigger_scan_js`                                | Nuclei JS 分析                        | 每 15 分鐘 | `js.py`               |
| `watchdog_stalled_overviews`                     | 監控卡住 Overview，自動救援           | 每 5 分鐘  | `watchdog.py`         |

### 6.7 Watchdog 自動救援機制

`watchdog_stalled_overviews`（`watchdog.py:31-93`）是三層防呆機制中最關鍵的一環：

```
┌─ 情境 1：Overview 卡在 PLANNING > 15 分鐘
│   → 若無待執行步驟：自動 `propose_next_steps.delay(overview_id)`
│   → 若已有 PENDING steps：直接把 Overview 從 PLANNING 修正為 EXECUTING
│   → 同時發送救援訊息至該 Overview 的 AI Thread
│
├─ 情境 2：Overview 卡在 EXECUTING > 30 分鐘且無進行中步驟
│   → Agent 可能已遺忘任務
│   → 發送提示要求決定下一步或結束任務
│
├─ 情境 3：非同步工具執行 > 30 分鐘無回應
│   → Step 強制標記為 FAILED
│   → 記錄 StepNote："[SYSTEM Watchdog] Step timed out (>30m). Forced FAILED."
│   → 發送救援訊息，要求 Agent 繼續其他未完成計畫
```

```python
# watchdog.py:47-52 — 救援訊息透過 apps.ai_assistant 發送
send_rescue_message(ov, "[SYSTEM Watchdog] 任務中斷或等候超時...")
# → 建立 Message 到該 Overview 的 AI Thread
# → Agent 下次輪詢時會讀到並採取行動
```

### 6.8 規模化關鍵設計

**增量處理 + 狀態標記去重**：

```python
# nuclei_tech_scan.py:19-47
# 1. 只選 is_tech_analyzed=False
# 2. DNS 失敗的直接標記跳過（不回傳）
# 3. 取出 batch_size 後立即更新標記（防止競爭條件）
triggered_ids = list(to_trigger.values_list("id", flat=True)[:batch_size])
URLResult.objects.filter(id__in=triggered_ids).update(is_tech_analyzed=True)
```

**內容指紋去重** — 同一 URL 內容不重複分析：

```python
# utils.py:8-56
is_content_already_analyzed(url_obj, analysis_type):
    # 1. 檢查 raw_response_hash 是否已被分析
    # 2. 檢查 final_url（跳轉終點）是否已被分析
```

**任務參數化** — 所有定時任務皆可接受 `batch_size` 參數，可依負載動態調整。

---

## 七、PostgreSQL 資料庫設計

### 7.1 模型分佈總覽

系統共 **36 個 Django Model**，分佈於三層 App 模組：

| 模組                 | 數量 | 管理對象                                                                           |
| -------------------- | ---- | ---------------------------------------------------------------------------------- |
| `apps/core/models/`  | 26   | Target → Seed → Subdomain → IP → Port → URL → TechStack → Vulnerability → 分析核心 |
| `apps/analyze/`      | 5    | Overview → Step → AttackVector → StepLog → ContentBlob                             |
| `apps/scans_record/` | 5    | NucleiScan / CommandExecution 等掃描記錄                                           |

### 7.2 核心資產模型詳細欄位

#### Target & Seed — 根節點

```python
# apps/core/models/base.py
class Target(models.Model):
    id = AutoField(primary_key=True)
    name = CharField(max_length=255, unique=True)    # 目標唯一名稱
    description = TextField(blank=True)               # 描述
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    # relationships:
    #   seeds -> Seed (ForeignKey reverse)

class Seed(models.Model):
    id = AutoField(primary_key=True)
    target = ForeignKey(Target, on_delete=CASCADE, related_name="seeds")
    value = CharField(max_length=500)                  # "example.com" / "192.168.1.0/24"
    seed_type = CharField(choices=[DOMAIN / CIDR / URL])  # 種子類型
    source = CharField(max_length=50, default="manual")    # manual/subfinder/flaresolverr
    created_at = DateTimeField(auto_now_add=True)
```

所有資產最終歸屬於 Target，Seed 是資產發現的起點。

#### Subdomain — 子域名

```python
# apps/core/models/domain.py
class Subdomain(models.Model):
    id = AutoField(primary_key=True)
    target = ForeignKey(Target, on_delete=CASCADE)       # 直接歸屬 Target
    subdomain = CharField(max_length=255, unique=True)    # "admin.example.com"
    source = CharField(max_length=50, default="subfinder") # 發現來源
    is_dns_resolved = BooleanField(default=False)          # DNS 解析狀態
    dns_a_records = JSONField(default=list)                # ["1.2.3.4"]
    is_tech_analyzed = BooleanField(default=False)          # Nuclei 技術掃描標記
    is_vuln_scanned = BooleanField(default=False)           # Nuclei 漏洞掃描標記
    is_crawled = BooleanField(default=False)                # 被動 URL 發現標記
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        indexes = [Index(fields=["target", "subdomain"])]
        # 每 Target 下的子域名唯一
        unique_together = ("target", "subdomain")
```

**設計要點**：

- 五個布林標記 (`is_dns_resolved` / `is_tech_analyzed` / `is_vuln_scanned` / `is_crawled`) = **增量處理狀態機**，排程器只掃 `=False` 的記錄，處理完立即更新
- `dns_a_records`（JSONB）儲存多個解析 IP，無需另建關聯表

#### IP — IP 地址

```python
# apps/core/models/network.py
class IP(models.Model):
    id = AutoField(primary_key=True)
    target = ForeignKey(Target, on_delete=CASCADE)
    ip_address = GenericIPAddressField()                  # "1.2.3.4"
    is_cdn = BooleanField(default=False)                   # CDN 辨識
    reverse_dns = CharField(max_length=255, blank=True)    # PTR 記錄
    asn = CharField(max_length=50, blank=True)             # ASN 編號
    is_nmap_scanned = BooleanField(default=False)          # Nmap 掃描標記
    is_vuln_scanned = BooleanField(default=False)          # Nuclei 掃描標記
    os_info = CharField(max_length=255, blank=True)        # OS 偵測結果
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        indexes = [Index(fields=["target", "ip_address"])]
        unique_together = ("target", "ip_address")
```

#### Port — 端口發現

```python
# apps/core/models/network.py
class Port(models.Model):
    id = AutoField(primary_key=True)
    ip = ForeignKey(IP, on_delete=CASCADE, related_name="ports")
    port = IntegerField()                                   # 443
    protocol = CharField(max_length=10, default="tcp")      # tcp/udp
    state = CharField(max_length=20, default="open")        # open/filtered/closed
    service = CharField(max_length=100, blank=True)          # http/ssh/mysql
    version = CharField(max_length=255, blank=True)          # "Apache 2.4.41"
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("ip", "port", "protocol")
        indexes = [Index(fields=["ip", "state"])]
```

#### URLResult — URL 資產

```python
# apps/core/models/url_assets.py
class URLResult(models.Model):
    id = AutoField(primary_key=True)
    target = ForeignKey(Target, on_delete=CASCADE)
    subdomain = ForeignKey(Subdomain, null=True, on_delete=SET_NULL)
    ip = ForeignKey(IP, null=True, on_delete=SET_NULL)
    url = TextField()                                        # "https://admin.example.com/login"
    final_url = TextField(blank=True)                        # 跳轉後最終 URL
    response_body = TextField(blank=True)                    # HTTP 回應內容
    content_type = CharField(max_length=255, blank=True)     # "text/html"
    status_code = IntegerField(null=True)                    # 200
    raw_response_hash = CharField(max_length=64, unique=True, db_index=True)
    # SHA256 指紋，去重依據
    is_tech_analyzed = BooleanField(default=False)
    is_vuln_scanned = BooleanField(default=False)
    is_crawled = BooleanField(default=False)
    is_js_analyzed = BooleanField(default=False)
    response_headers = JSONField(default=dict)               # HTTP 回應標頭
    extracted_results = JSONField(default=dict)              # Forms/Endpoints/Inputs
    techs = JSONField(default=dict)                          # Wappalyzer 風格技術偵測結果
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            Index(fields=["target", "subdomain"]),
            Index(fields=["raw_response_hash"]),
        ]
```

**設計要點**：

- `response_body` TextField 直接存 HTML body（非檔案），對應 Django core 的 TextField 極限（~4GB），足夠儲存大型頁面
- `response_headers` / `extracted_results` / `techs` 三個 JSONB 欄位=去正規化的快取層，避免 JOIN

#### Vulnerability — 漏洞記錄

```python
# apps/core/models/Vulnerability.py
class Vulnerability(models.Model):
    id = AutoField(primary_key=True)
    target = ForeignKey(Target, on_delete=CASCADE)
    ip = ForeignKey(IP, null=True, on_delete=SET_NULL)
    subdomain = ForeignKey(Subdomain, null=True, on_delete=SET_NULL)
    url_result = ForeignKey(URLResult, null=True, on_delete=SET_NULL)
    name = CharField(max_length=500)                         # "Reflected XSS in search parameter"
    severity = CharField(choices=[CRITICAL / HIGH / MEDIUM / LOW / INFO])
    cvss_score = FloatField(null=True)                       # CVSS 評分
    description = TextField(blank=True)
    evidence = TextField(blank=True)                         # 利用 PoC
    remediation = TextField(blank=True)                      # 修復建議
    hash = CharField(max_length=64, unique=True, db_index=True) # SHA256 去重
    discovered_by = CharField(max_length=100, blank=True)    # nuclei/manual/ai
    ai_summary = TextField(blank=True)                       # AI 生成摘要
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            Index(fields=["target", "severity"]),
            Index(fields=["hash"]),
        ]
```

**設計要點**：

- **Polymorphic FK 模式**：同時保留 `ip_id` / `subdomain_id` / `url_result_id` 三個可空 FK，比 GenericForeignKey 查詢效能更好（直接 JOIN）
- `hash`（SHA256）保證同一漏洞不會重複入庫

#### TechStack — 技術棧偵測

```python
# apps/core/models/techstack.py
class TechStack(models.Model):
    id = AutoField(primary_key=True)
    target = ForeignKey(Target, on_delete=CASCADE)
    subdomain = ForeignKey(Subdomain, null=True, on_delete=SET_NULL)
    url_result = ForeignKey(URLResult, null=True, on_delete=SET_NULL)
    ip = ForeignKey(IP, null=True, on_delete=SET_NULL)
    name = CharField(max_length=200)                         # "React"
    version = CharField(max_length=100, blank=True)          # "18.2.0"
    category = CharField(max_length=100, blank=True)         # "JavaScript Framework"
    confidence = PositiveSmallIntegerField(default=100)      # 0-100
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [Index(fields=["target", "name"])]
```

#### JavaScriptFile & ExtractedJS — JS 分析

```python
# apps/core/models/js_files.py
class JavaScriptFile(models.Model):
    id = AutoField(primary_key=True)
    target = ForeignKey(Target, on_delete=CASCADE)
    url_result = ForeignKey(URLResult, on_delete=CASCADE)
    url = TextField()                                        # "https://example.com/js/app.js"
    hash = CharField(max_length=64, unique=True, db_index=True) # SHA256 去重

class ExtractedJS(models.Model):
    id = AutoField(primary_key=True)
    target = ForeignKey(Target, on_delete=CASCADE)
    js_file = ForeignKey(JavaScriptFile, on_delete=CASCADE)
    url = TextField()
    extracted_urls = JSONField(default=list)                  # JS 中發現的 URL
    extracted_endpoints = JSONField(default=list)             # JS 中發現的 API endpoint
    extracted_secrets = JSONField(default=list)               # JS 中發現的敏感資訊
    hash = CharField(max_length=64, unique=True, db_index=True)
```

### 7.3 掃描記錄模型詳細欄位

```python
# apps/core/models/scans_record_models.py
class NucleiScan(models.Model):
    id = AutoField(primary_key=True)
    target = ForeignKey(Target, on_delete=CASCADE)
    ip = ForeignKey(IP, null=True, on_delete=SET_NULL)
    subdomain_id = IntegerField(null=True)  # 不設 FK（非同步寫入，性能優先）
    url_result_id = IntegerField(null=True)
    template_id = CharField(max_length=255)    # "tech-detect"
    type = CharField(max_length=50)            # "nuclei-tech-scan"
    matcher_name = CharField(max_length=255, blank=True)
    extracted_results = JSONField(default=dict)
    matched_at = CharField(max_length=500, blank=True)  # 匹配位置
    severity = CharField(max_length=50, blank=True)
    is_timely = BooleanField(default=True)                # 是否已過時
    is_real = BooleanField(default=True)                  # AI 過濾 False Positive
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            Index(fields=["target", "template_id"]),
            Index(fields=["subdomain_id"]),
            Index(fields=["url_result_id"]),
        ]
```

**設計要點**：

- `subdomain_id` / `url_result_id` 使用 `IntegerField(null=True)` 而非 ForeignKey — 因為 Nuclei 掃描結果透過 Celery task 非同步回寫，不存在即時外鍵約束即可寫入
- `is_timely` 標記掃描時效（新掃描直接標舊記錄為 False）
- `is_real` = AI Verification 結果過濾 False Positive

```python
class URLParameter(models.Model):
    id = AutoField(primary_key=True)
    target = ForeignKey(Target, on_delete=CASCADE)
    url_result = ForeignKey(URLResult, on_delete=CASCADE)
    parameter = CharField(max_length=255)       # "id"
    parameter_type = CharField(max_length=50)   # "query" / "path" / "body"
    sample_value = TextField(blank=True)        # "123"
    hash = CharField(max_length=64, unique=True, db_index=True)

    class Meta:
        indexes = [Index(fields=["target", "parameter_type"])]
```

### 7.4 AI 分析模型詳細欄位

#### Overview — 戰略概覽（AI 中樞）

```python
# apps/core/models/analyze/overview.py
class Overview(models.Model):
    id = AutoField(primary_key=True)
    target = ForeignKey(Target, on_delete=CASCADE, related_name="overviews")
    # 資產群組（M2M 關聯目前偵察範圍）
    ips = ManyToManyField(IP, blank=True)
    subdomains = ManyToManyField(Subdomain, blank=True)
    url_results = ManyToManyField(URLResult, blank=True)
    # AI 狀態
    summary = TextField(blank=True)             # AI 觀察筆記（逐漸累積）
    techs = JSONField(default=dict)             # 目前偵測到的所有技術棧
    knowledge = JSONField(default=dict)         # AI 對目標的認知快照（長期記憶）
    plan = JSONField(default=dict)              # 結構化攻擊計畫
    project_root = CharField(max_length=500, blank=True)  # Golang 專案路徑
    # 執行狀態
    status = CharField(
        max_length=20,
        choices=[
            (PLANNING, "規劃中"),
            (EXECUTING, "執行中"),
            (NEEDS_GUIDANCE, "需要指導"),
            (COMPLETED, "已完成"),
            (STALLED, "停滯"),
        ],
        default=PLANNING,
    )
    risk_score = PositiveSmallIntegerField(default=0)  # 0-100
    business_impact = CharField(max_length=20, default="Medium")
    # AI 對話追蹤
    thread_id = IntegerField(null=True)         # apps.ai_assistant Thread ID
    parent_thread_id = IntegerField(null=True)  # 上層 Caller Thread ID
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            Index(fields=["target", "status"]),
            Index(fields=["risk_score"]),
        ]
```

**設計要點**：

- `knowledge`（JSONB）= AI 長期記憶，儲存對目標當前認知快照（已發現資產、已測試向量、已排除路徑），避免 Context Window 溢出
- `plan`（JSONB）= 結構化攻擊計畫，如 `[{"step": 1, "action": "port_scan", "target": "1.2.3.4"}]`
- `thread_id` / `parent_thread_id` = AI 對話 Thread 雙向連結，支援階層式 Agent 溝通

#### Step — 執行步驟

```python
# apps/core/models/analyze/Step.py
class Step(models.Model):
    id = AutoField(primary_key=True)
    overview = ForeignKey(Overview, on_delete=CASCADE, related_name="steps")
    parent_step = ForeignKey("self", null=True, on_delete=CASCADE)  # 樹狀結構
    order = PositiveIntegerField()               # 自動遞增（同 Overview 下）
    name = CharField(max_length=500)
    prompt = TextField(blank=True)               # AI 的執行指令全文
    status = CharField(
        max_length=20,
        choices=[
            PENDING / RUNNING / COMPLETED / FAILED / WAITING_FOR_ASYNC / ENDED
        ],
        default=PENDING,
    )
    result_summary = TextField(blank=True)       # 執行結果摘要
    # 關聯資產（Polymorphic M2M）
    ips = ManyToManyField(IP, blank=True)
    subdomains = ManyToManyField(Subdomain, blank=True)
    url_results = ManyToManyField(URLResult, blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            Index(fields=["overview", "order"]),
            Index(fields=["status"]),
        ]
```

#### AttackVector — 攻擊向量

```python
# apps/core/models/analyze/AttackVector.py
class AttackVector(models.Model):
    id = AutoField(primary_key=True)
    overview = ForeignKey(Overview, on_delete=CASCADE, related_name="attack_vectors")
    name = CharField(max_length=500)        # "Reflected XSS on /api/user"
    vector_type = CharField(
        max_length=30,
        choices=[
            WEB_VULN / NETWORK_EXPOSURE / AUTH_BYPASS / INFO_LEAK / CONFIG_ISSUE / OTHER
        ],
    )
    status = CharField(
        max_length=20,
        choices=[
            IDENTIFIED / TESTING / EXPLOITABLE / EXHAUSTED / MITIGATED
        ],
        default=IDENTIFIED,
    )
    risk_score = PositiveSmallIntegerField(default=0)  # 0-100
    evidence = TextField(blank=True)         # 具體利用 PoC
    discovery_step = ForeignKey(Step, null=True, on_delete=SET_NULL)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

#### Verification — AI 驗證

```python
class Verification(models.Model):
    id = AutoField(primary_key=True)
    attack_vector = ForeignKey(AttackVector, on_delete=CASCADE, related_name="verifications")
    observation_prompt = TextField()          # 成功標準（如 "nmap output contains 80/tcp open"）
    execution_output = TextField()            # 實際執行輸出
    ai_response = JSONField(default=dict)     # AI 驗證完整回應
    verdict = CharField(
        max_length=20,
        choices=[PENDING / PASSED / FAILED / INCONCLUSIVE],
        default=PENDING,
    )
    confidence_score = PositiveSmallIntegerField(default=0)
    auto_create_vulnerability = BooleanField(default=False)
    created_vulnerability = ForeignKey(Vulnerability, null=True, on_delete=SET_NULL)
    created_at = DateTimeField(auto_now_add=True)
```

#### StepLog — AI 執行日誌

```python
# apps/core/models/analyze/StepLog.py
class StepLog(models.Model):
    id = AutoField(primary_key=True)
    step = ForeignKey(Step, on_delete=CASCADE, related_name="logs")
    level = CharField(max_length=20, choices=[INFO / DEBUG / WARN / ERROR / AI_THOUGHT / ACTION / RESULT])
    tag = CharField(max_length=30, choices=[SKILL_EXEC / COMMAND / API_CALL / SCAN / PARSE / DECISION / ERROR_HANDLING / STATE_UPDATE / CHECKPOINT])
    message = TextField()
    metadata = JSONField(default=dict)        # 可擴展的 metadata
    sequence = PositiveIntegerField()         # 自動遞增
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            Index(fields=["step", "sequence"]),
            Index(fields=["created_at"]),
        ]
        ordering = ["sequence"]
```

**設計要點**：

- `metadata`（JSONB）= 等級／標籤以外的所有擴展資料（`ai_model` / `token_used` / `duration_ms` / `command` / `exit_code` 等）
- `sequence`（PositiveIntegerField）替代 UUID 排序，數字型更快、可讀

#### ContentBlob — AI 長期記憶

```python
# apps/core/models/analyze/ContentBlob.py
class ContentBlob(models.Model):
    id = AutoField(primary_key=True)
    overview = ForeignKey(Overview, on_delete=CASCADE, related_name="content_blobs")
    source_step = ForeignKey(Step, null=True, on_delete=SET_NULL)
    title = CharField(max_length=500)
    blob_type = CharField(max_length=50, choices=[RECON_NOTE / AI_ANALYSIS / SCAN_RESULT / COMMAND_OUTPUT])
    content = TextField()
    ai_summary = TextField(blank=True)       # AI 摘要（壓縮用）
    tokens = PositiveIntegerField(default=0)  # Token 計數
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [Index(fields=["overview", "blob_type"])]
```

**設計要點**：

- `ai_summary` 搭配 `compress_long_threads()`：舊 ContentBlob 由 Mistral Small 壓縮為摘要，保留 `ai_summary` 後可刪除原始 `content`
- `tokens`（PositiveIntegerField）= Token 計數，供排程器決定何時需要壓縮

### 7.5 ai_assistant 模型

```python
# apps/ai_assistant/models.py
class Thread(models.Model):
    id = AutoField(primary_key=True)
    name = CharField(max_length=255)                    # 對話標題
    metadata = JSONField(default=dict)                  # 擴展屬性
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        indexes = [Index(fields=["created_at"])]

class Message(models.Model):
    id = AutoField(primary_key=True)
    thread = ForeignKey(Thread, on_delete=CASCADE, related_name="messages")
    role = CharField(max_length=20, choices=[USER / ASSISTANT / SYSTEM])
    content = TextField()
    metadata = JSONField(default=dict)                  # token 用量、ai_model 等
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            Index(fields=["thread", "created_at"]),
            Index(fields=["role"]),
        ]
        ordering = ["created_at"]
```

### 7.6 索引策略總結

| 索引類型                                 | 用途                      | 範例模型                                                                            |
| ---------------------------------------- | ------------------------- | ----------------------------------------------------------------------------------- |
| `unique_together`                        | 防止重複                  | Subdomain (target, subdomain) / Port (ip, port, protocol) / IP (target, ip_address) |
| `unique=True` + `db_index=True`          | 指紋去重                  | Vulnerability.hash / URLResult.raw_response_hash / JavaScriptFile.hash              |
| `Index(fields=["target", status_field])` | 按 Target 過濾 + 狀態篩選 | IP / Subdomain / URLResult / Vulnerability                                          |
| `Index(fields=["created_at"])`           | 時間排序                  | StepLog / Message                                                                   |
| `Index(fields=["overview", "order"])`    | 樹狀遍歷                  | Step                                                                                |
| `IntegerField(null=True)`（無 FK）       | 非同步寫入效能            | NucleiScan.subdomain_id                                                             |

### 7.7 關鍵設計模式

#### 模式 A：增量掃描狀態機

七個核心 Model 使用 `is_*` Boolean 標記做增量處理：

| 模型        | 標記                                                                      | 用途           |
| ----------- | ------------------------------------------------------------------------- | -------------- |
| `Subdomain` | `is_dns_resolved` / `is_tech_analyzed` / `is_vuln_scanned` / `is_crawled` | 子域名處理狀態 |
| `IP`        | `is_nmap_scanned` / `is_vuln_scanned`                                     | IP 處理狀態    |
| `URLResult` | `is_tech_analyzed` / `is_vuln_scanned` / `is_crawled` / `is_js_analyzed`  | URL 處理狀態   |

```python
# 範例：定時任務取下一批
to_scan = URLResult.objects.filter(
    target=target, is_tech_analyzed=False
)[:batch_size]
URLResult.objects.filter(id__in=[o.id for o in to_scan]).update(is_tech_analyzed=True)
```

#### 模式 B：SHA256 指紋去重

五個 Model 使用 SHA256 hash 做 Idempotent Dedup：

| 模型             | hash 來源                            |
| ---------------- | ------------------------------------ |
| `Vulnerability`  | `sha256(name + url + parameter)`     |
| `URLResult`      | `sha256(url + response_body[:1024])` |
| `JavaScriptFile` | `sha256(url)`                        |
| `ExtractedJS`    | `sha256(url + extracted_urls)`       |
| `URLParameter`   | `sha256(url + parameter)`            |

#### 模式 C：Polymorphic FK 三選一

`Vulnerability` / `InitialAIAnalysis` / `NucleiScan` / `TechStack` 同時關聯到 IP / Subdomain / URLResult 三者之一：

```
vulnerability
├── ip_id          → IP(id)          (可空)
├── subdomain_id   → Subdomain(id)   (可空)
└── url_result_id  → URLResult(id)   (可空)
```

**優點**：直接 JOIN（`SELECT * FROM vulnerability WHERE ip_id=123`），效能遠優於 GenericForeignKey 的 `(content_type_id, object_id)` 雙欄位查詢。

#### 模式 D：JSONB 去正規化

六個 JSONField（PostgreSQL JSONB）做快取層，減少 JOIN：

| 模型        | JSONB 欄位          | 快取內容                              |
| ----------- | ------------------- | ------------------------------------- |
| `Overview`  | `knowledge`         | AI 認知快照（已發現資產、已測試向量） |
| `Overview`  | `plan`              | 結構化攻擊計畫                        |
| `Overview`  | `techs`             | 技術棧聚合                            |
| `URLResult` | `response_headers`  | HTTP 回應標頭                         |
| `URLResult` | `extracted_results` | Forms/Endpoints/Inputs                |
| `URLResult` | `techs`             | Wappalyzer 風格技術偵測               |

#### 模式 E：訊號驅動 Target 自動同步

```python
# apps/core/models/signals.py
# M2M changed → 自動更新關聯資產的 target_id
@receiver(m2m_changed, sender=Overview.ips.through)
def sync_overview_ips_target(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        ips = IP.objects.filter(id__in=pk_set)
        for ip in ips:
            if ip.target_id != instance.target_id:
                ip.target_id = instance.target_id
                ip.save()
```

所有資產最終透過 signal 收斂到同一個 `target_id`，避免跨 Target 資料混淆。

#### 模式 F：Token 計量 & 智能壓縮

```python
# ContentBlob.tokens → compress_long_threads() 判斷基準
threshold = 40   # Message 數量 > 40 條
# 保留最近 30% 的 ContentBlob
# 舊的 70% 由 Mistral Small 壓縮為 ai_summary
# 壓縮後保留 ai_summary，刪除 content 釋放空間
```

#### 模式 G：LLM Provider 路由

```python
# apps/ai_assistant/helpers/assistants.py
# 根據 assistant_type 選擇 LLM Provider：
# HACKER → claude-sonnet-4-20250514（複雜推理）
# ORCHESTRATOR → claude-sonnet-4-20250514
# COMPRESSOR → mistral-small-latest（低成本壓縮）
```

#### 模式 H：Agent 獨立 LLM 配置（DB 化）

**問題背景：** 5 個 Agent（`initial_analyzer_agent`、`automation_agent`、`skill_creator_agent`、`skill_verifier_agent`、`skill_merger_evaluator_agent`）需要使用不同廠商的不同模型，但純 env var 方式無法透過 UI 動態管理。

**解決方案：** `AgentLLMConfig` 資料模型 + REST API + 前端管理頁面，實現 DB 化的 per-agent LLM 配置。

**資料模型（`apps/api_keys/models.py`）：**

| 欄位 | 類型 | 說明 |
|------|------|------|
| `agent_id` | `CharField(unique)` | Agent 識別碼，例如 `automation_agent` |
| `provider` | `CharField(nullable)` | LLM 廠商：openai / anthropic / mistral / deepseek / ollama |
| `model_name` | `CharField(nullable)` | 具體模型，例如 `gpt-4o`、`claude-3-5-sonnet-20241022` |
| `temperature` | `FloatField(nullable)` | 溫度參數 0.0–2.0；`None` 沿用全域默認 |
| `api_base_url` | `CharField(nullable)` | 自定義 API Base URL（代理 / 私有部署） |
| `api_key_ref` | `FK → core.APIKey(nullable)` | 指向特定 APIKey 記錄；`None` 則使用全域同廠商密鑰 |
| `is_active` | `BooleanField` | 是否啟用此配置 |

**配置解析優先級（每個欄位獨立計算）：**

```
DB (AgentLLMConfig) > env var (AGENT_<ID>_*) > 全域默認 (DEFAULT_LLM_PROVIDER)
```

實現位置：`apps/auto/settings.py` → `AutoAppConfig.get_agent_config(agent_id)`，在方法內優先查詢 DB，DB 無值則自動回退到 env var 或全域默認。

**REST API（`/api/api_keys/`）：**

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/agent-configs/` | 所有已知 agent 的有效配置（DB + env + 默認合并視圖） |
| GET | `/agent-configs/db/` | 僅 DB 中有記錄的 agent |
| PUT | `/agent-configs/{agent_id}` | Upsert（新建或更新） |
| DELETE | `/agent-configs/{agent_id}` | 刪除 DB 記錄，回退到 env/默認 |

**前端管理頁面：** 路由 `/agent-config`（Navbar → Agents），顯示每個 agent 的有效配置及狀態標籤（DB OVERRIDE / ENV VAR / DEFAULT），支援直接 EDIT 和 RESET。

**典型使用場景：**
```
automation_agent     → openai  / gpt-4o               （高精度漏洞分析）
skill_creator_agent  → anthropic / claude-3-5-sonnet  （長上下文程式碼生成）
skill_verifier_agent → mistral / mistral-small         （低成本快速驗證）
```

### 7.8 ER 關係圖（文字版）

```
Target (1) ──< Seed (N)                根節點
  │
  ├──< Subdomain (N) ──< URLResult (N)  域名層級
  │       │                 │
  │       │           ┌─────┼──────────┐
  │       │      TechStack Vuln  JSFile
  │       │
  ├──< IP (N) ──< Port (N)             網路層級
  │       │
  │       ├──< TechStack (N)
  │       ├──< Vulnerability (N)
  │       └──< URLResult (N)
  │
  ├──< Overview (1) ──< Step (N)       AI 分析層級
  │       │               │
  │       │         ┌─────┴──────┐
  │       │    AttackVector  StepLog (N)
  │       │         │
  │       │    Verification (N)
  │       │
  │       └──< ContentBlob (N)
  │
  ├──< NucleiScan (N)                  掃描記錄層級
  ├──< TechStack (N)
  └──< Vulnerability (N)
```

### 7.9 空間估算

| 模型          | 預期記錄數 | 單行大小          | 總空間  |
| ------------- | ---------- | ----------------- | ------- |
| Target        | 100        | ~0.5 KB           | ~50 KB  |
| Seed          | 500        | ~0.5 KB           | ~250 KB |
| Subdomain     | 50,000     | ~1 KB             | ~50 MB  |
| IP            | 10,000     | ~1 KB             | ~10 MB  |
| Port          | 50,000     | ~0.5 KB           | ~25 MB  |
| URLResult     | 200,000    | ~10 KB（含 body） | ~2 GB   |
| Vulnerability | 20,000     | ~2 KB             | ~40 MB  |
| StepLog       | 500,000    | ~2 KB             | ~1 GB   |
| Message       | 100,000    | ~4 KB             | ~400 MB |
| ContentBlob   | 50,000     | ~8 KB             | ~400 MB |

**合計預估**：約 **3.5-4 GB**（含索引），主要空間消耗在 `URLResult.response_body` 與 `StepLog.message`。

---

## 八、Hasura GraphQL 即時查詢層

### 8.1 架構定位

```
┌─────────────────────────────────────────────────────┐
│                  前端 React (Vite 7)                  │
│  ┌─────────────────────────────────────────────────┐ │
│  │  Apollo Client (@apollo/client ^4.1.9)          │ │
│  │  ├─ HTTP Link → 查詢/變更 (POST)                │ │
│  │  └─ WebSocket → 訂閱 (graphql-ws ^6.0.8)       │ │
│  └─────────────────────────────────────────────────┘ │
│              │                    ▲                    │
│         HTTP  │             WebSocket                  │
│         POST  │             Subscription               │
│              ▼                    │                    │
│  ┌─────────────────────────────────────────────────┐ │
│  │  Hasura GraphQL Engine (v2.36.0)                  │ │
│  │  :8085/v1/graphql                                 │ │
│  │  ┌─────────────────────────────────────────────┐ │ │
│  │  │  Auto-Generated GraphQL Schema              │ │ │
│  │  │  (自動追蹤 PostgreSQL 所有表格與關聯)         │ │ │
│  │  │  - 每個 Django Model → GraphQL Type          │ │ │
│  │  │  - 每個 ForeignKey → Nested Query            │ │ │
│  │  │  - M2M → Array Relationship                  │ │ │
│  │  └─────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────┘ │
│              │                                        │
│              ▼                                        │
│  ┌─────────────────────────────────────────────────┐ │
│  │  PostgreSQL 14 (同 Django 共用資料庫)             │ │
│  │  postgres://myuser:secret@postgres:5432/mydb     │ │
│  │  - Hasura 唯讀查詢 (不經由 Django ORM)            │ │
│  │  - 直接透過 PostgreSQL 權限系統存取                │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

Hasura 作為 **Django REST API 的補充查詢層**，不取代 Django 的寫入接口：

- **寫入操作** → Django Ninja/DRF REST API（POST/PUT/DELETE）
- **讀取操作** → Hasura GraphQL（GET/查詢）
- **即時更新** → Hasura GraphQL Subscription（WebSocket）

### 8.2 佈署配置

| 面向           | 值                                            | 來源檔案                                               |
| -------------- | --------------------------------------------- | ------------------------------------------------------ |
| Docker Image   | `hasura/graphql-engine:v2.36.0`               | `docker/docker-compose.yml`                            |
| 主機連接埠     | `127.0.0.1:8085 → 容器 :8080`                 | `docker/docker-compose.yml`                            |
| 資料庫連線     | `postgres://myuser:secret@postgres:5432/mydb` | `docker/docker-compose.yml`                            |
| GraphQL 端點   | `http://127.0.0.1:8085/v1/graphql`            | `frontend/src/config.ts`                               |
| WebSocket 端點 | `ws://127.0.0.1:8085/v1/graphql`              | `frontend/src/apolloClient.ts`（自動轉換）             |
| Admin Secret   | `YourSuperStrongAdminSecretHere`              | `docker/docker-compose.yml` + `frontend/src/config.ts` |
| 管理模式       | Hasura Console 啟用（`ENABLE_CONSOLE=true`）  | `docker/docker-compose.yml`                            |

### 8.3 前端 GraphQL 客戶端層

| 客戶端                  | 檔案                                          | 用途                                             | 傳輸層                                                                    |
| ----------------------- | --------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------- |
| Apollo Client           | `frontend/src/apolloClient.ts`                | 完整 GraphQL 客戶端，自動路由 query/subscription | HTTP Link + WebSocket Link（`graphql-ws`），透過 `split()` 依操作類型路由 |
| `useHasuraQuery`        | `frontend/src/hooks/useHasuraQuery.ts`        | 輕量單次 HTTP POST 查詢（頁面載入用）            | HTTP POST + `x-hasura-admin-secret` Header                                |
| `useHasuraSubscription` | `frontend/src/hooks/useHasuraSubscription.ts` | WebSocket 即時訂閱（監控頁面用）                 | WebSocket（`graphql-ws`），keepAlive 30s，Infinite Retry                  |

**Apollo Client 核心配置**：

- HTTP Link → `GLOBAL_CONFIG.HASURA_GRAPHQL_URL`（`http://127.0.0.1:8085/v1/graphql`）
- WebSocket Link → 自動將 `http` 替換為 `ws`，傳送 `x-hasura-admin-secret` Header
- Cache → `InMemoryCache`（標準正規化快取）

### 8.4 實際 GraphQL Query 列表

#### 前端頁面查詢一覽

| 頁面                           | Query / Subscription                    | 變數                     | 主要回傳欄位                                                                  | 來源檔案                        |
| ------------------------------ | --------------------------------------- | ------------------------ | ----------------------------------------------------------------------------- | ------------------------------- |
| 首頁                           | `GetTargets`                            | 無                       | `core_target { id name description created_at }`                              | `services/api.ts`               |
| TargetDashboard Seed 頁籤      | `GetTargetDetail`                       | `$id: bigint!`           | `core_target_by_pk { core_seeds(id,value,type,is_active) }`                   | `services/api.ts`               |
| TargetDashboard Subdomain 頁籤 | `GetTargetSubdomains`                   | `$targetId: bigint!`     | `core_subdomain { name,is_resolvable,core_subdomain_ips }` limit 200          | `services/api.ts`               |
| TargetDashboard IP 頁籤        | `GetTargetIPs`                          | `$targetId: bigint!`     | `core_ip { address,core_ports(port_number,service) }` limit 200               | `services/api.ts`               |
| TargetDashboard Overview 頁籤  | `GetTargetOverviews`                    | `$targetId: bigint!`     | `core_overview { status,risk_score,knowledge,plan }`                          | `services/api.ts`               |
| TargetDashboard URL 頁籤       | `GetTargetURLs`                         | `$targetId: bigint!`     | `core_urlresult { url,status_code,title }` limit 200                          | `services/api.ts`               |
| ExecutionMonitor               | `GetAllExecutionSteps` **Subscription** | 無                       | `core_overview → core_steps → core_stepnote + core_attackvectors`             | `queries.ts`                    |
| SkillLibraryPage               | `GetSkills`                             | `$search: String`        | `core_skill_template { name,tags,usage_count }` + aggregate count             | `queries.ts`                    |
| SubdomainDetailPage            | `GetSubdomainDetail`                    | `$subdomain_id: bigint!` | `core_subdomain_by_pk { core_subdomainaianalyses,core_urlresult }`            | `services/subdomains_detail.ts` |
| URLDetailPage                  | `GetURLDetail`                          | `$url_id: bigint!`       | `core_urlresult_by_pk { core_techstacks,core_vulnerabilities,headers,forms }` | `services/url_detail.ts`        |
| SeedReconPage                  | `GetSeedUltimateIntel`                  | `$seed_id: bigint!`      | `core_seed { core_nmapscan,core_subfinderscans,core_ip,core_subdomain }`      | `services/api_recon.ts`         |

#### 後端 Python GraphQL 查詢

| 位置                               | 用途                                      | 查詢內容                                                                                         |
| ---------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `apps/analyze_ai/tasks/common.py`  | 提供 Hasura `gql.Client` 基礎連線能力     | 目前初步 AI 分析主路徑以 Django ORM + `prefetch_related()` 組裝資產摘要，保留 GraphQL 擴充入口 |
| `apps/http_sender/tasks/fuzzer.py` | Fuzzer 讀取端點與 URL 關聯                | `core_endpoint { path,method,core_urlparameters,core_endpoint_discovered_by_urls }`             |
| 前端 Apollo / Hooks                | 監控頁面、Dashboard、詳細頁的複合關聯讀取 | 透過 Nested Query 一次取回 URL / Form / TechStack / Vulnerability / Step 等多層資料             |

```python
# 後端標準連線模式（gql 4.0.0）
transport = RequestsHTTPTransport(
    url=f"{Config.HASURA_URL}/v1/graphql",
    headers={"x-hasura-admin-secret": Config.HASURA_ADMIN_SECRET},
)
client = Client(transport=transport)
result = client.execute(query, variable_values={"id": endpoint_id})
```

**實務取捨**：

- 讀取圖狀關聯資料時，Hasura 適合前端與複雜聚合查詢
- 需要在任務內做摘要、裁剪欄位、控制 token 成本時，Django ORM 組裝 payload 更直接
- 因此目前 `InitialAIAnalysis` 採 ORM 摘要化策略，把 Forms、TechStack、Headers、DNS、`strategic_context` 等資訊整理後再送入 LLM

### 8.5 Hasura vs Django REST API 職責分界

| 面向            | Django Ninja / DRF          | Hasura GraphQL                              |
| --------------- | --------------------------- | ------------------------------------------- |
| **角色**        | 寫入層（CUD）               | 讀取層（R + Subscription）                  |
| **協議**        | HTTP REST (JSON)            | GraphQL (Query / Subscription)              |
| **連線方式**    | HTTP POST                   | HTTP POST + WebSocket                       |
| **資料過濾**    | Django ORM QuerySet         | Hasura `where` / `order_by` / `limit`       |
| **關聯查詢**    | N+1 需手動 `select_related` | 自動 Nested Query（Hasura 追蹤 FK）         |
| **即時更新**    | SSE（StepLog 專用）         | WebSocket Subscription                      |
| **身分驗證**    | Token / Session             | `x-hasura-admin-secret` Header              |
| **Schema 維護** | 手動寫 Serializer + Router  | 自動從 PostgreSQL 反射（Database Tracking） |

### 8.6 使用 Hasura 而非純 Django REST 的原因

| 問題                         | 純 Django REST                                     | Django + Hasura                                      |
| ---------------------------- | -------------------------------------------------- | ---------------------------------------------------- |
| 前端需多種不同組合的資產查詢 | 每種組合需寫一個 ViewSet/Serializer                | Hasura 自動產出所有組合，前端自由組合欄位與過濾      |
| N+1 關聯查詢                 | `select_related` / `prefetch_related` 需逐一優化   | Hasura 自動產生 SQL JOIN，無需手動優化               |
| 即時訂閱（WebSocket）        | 需手動實作 GraphQL Subscription 或 Django Channels | Hasura 原生支援 PostgreSQL LISTEN/NOTIFY + WebSocket |
| Schema 變更同步              | 需手動新增 Serializer/Router/URL                   | 一鍵 `track table` 自動更新 GraphQL Schema           |
| 前端迭代速度                 | 後端 API 常需跟著前端需求修改                      | 前端自訂查詢欄位與過濾，後端無需變動                 |

---

## 九、網站架構 vs CLI 工具

### 9.1 完整資產生命週期追蹤

| 維度       | CLI 工具                           | 網站架構                                                 |
| ---------- | ---------------------------------- | -------------------------------------------------------- |
| 資產數據   | 一次性文字輸出，關閉 terminal 消失 | PostgreSQL 永久儲存，隨時回溯查詢                        |
| 資產關聯   | 人腦手動關聯不同工具輸出           | Seed→Subdomain→IP→Port→URL→TechStack→Vuln 完整圖形化關聯 |
| 執行過程   | 只能看 terminal 即時輸出           | StepLog 7 等級 + 9 標籤 + SSE 即時串流 + 篩選搜尋        |
| AI 對話    | 關閉 terminal 遺失                 | Thread/Message 永久儲存 + SSE 串流 + Markdown 渲染       |
| 風險可視   | `Risk: 75` 純文字                  | 彩色進度條 + 狀態徽章 + 步驟統計 + 成功率 %              |
| 技能管理   | 腳本散落在檔案系統                 | SkillLibraryPage 完整 CRUD + 排序 + 標籤過濾             |
| 多用戶     | 無                                 | Django Admin + Token Auth + Hasura GraphQL               |
| 自動化排程 | 需手動寫 cron                      | DatabaseScheduler + Ninja API 動態管理                   |

### 9.2 TargetDashboard 五頁籤可視化

```typescript
// frontend/src/pages/TargetDashboard/TargetDashboard.tsx
// 頁面路由: /target/:targetId
// 使用 Hasura GraphQL 即時查詢

TABS = [
  { id: "seeds", label: "Seeds", count: seeds.length },
  { id: "subdomains", label: "Subdomains", count: subdomains.length },
  { id: "ips", label: "IPs / Ports", count: ips.length },
  { id: "urls", label: "URLs", count: urls.length },
  { id: "ai", label: "AI Overview", count: overviews.length },
];

// 每個 IP 可展開 Port 表格（port/protocol/state/service/version）
// 每個 Overview 顯示 Attack Plan 目標樹 + Risk Score 進度條
// 每個資產可點擊進入專屬詳細頁
```

### 9.3 ExecutionMonitor 即時監控

```typescript
// frontend/src/pages/ExecutionMonitorPage/ExecutionMonitorPage.tsx
// 使用 Hasura GraphQL Subscription 即時更新

// Overview 樹狀結構顯示：
// - 狀態徽章 + 風險分數 + 執行時間
// - Thread 來源追溯 + 一鍵複製
// - Step 統計（OK / RUN / FAIL / WAIT + 成功率 %）
// - 展開顯示 Step 明細 + Attack Vector 標籤
// - 點擊 → 右側 StepLog 面板

// 篩選功能：
// - TIME RANGE: All / 1h / 24h / 7d
// - SORT BY: Updated / Created / Duration / Success Rate
// - STATUS: 複選過濾
// - TARGET: 複選過濾
// - 全文搜尋（target name / step content / attack vector）
```

### 9.4 StepLogViewer 即時日誌

```typescript
// frontend/src/components/StepLogViewer.tsx
const { logs, isConnected, error, lastSequence } = useStepLogStream(stepId);
// SSE 即時串流，不需輪詢

// 7 種日誌等級各自有顏色 + 圖標：
//   ℹ️ INFO / 🐛 DEBUG / ⚠️ WARN / ❌ ERROR
//   💭 AI_THOUGHT / ▶️ ACTION / ✓ RESULT

// 9 種標籤各自有獨立色：
//   SKILL_EXEC / COMMAND / API_CALL / SCAN
//   PARSE / DECISION / ERROR_HANDLING / STATE_UPDATE / CHECKPOINT

// 功能：
// - 即時過濾等級
// - 全文搜尋
// - 點擊展開 metadata（ID / Sequence / Duration / Timestamp）
// - 一鍵複製 Log
// - 自動滾動
// - 🔴 LIVE / ⚫ OFFLINE 連線指示
```

### 9.5 AI Center 對話管理

```typescript
// frontend/src/pages/AICenterPage/AICenterPage.tsx
// 路由: /aicenter

// 所有對話持久化（自動過濾系統線程）
// SSE 串流逐字顯示 + Markdown 渲染
// 自動更名（取第一行作為對話標題）
// Target 綁定顯示
// 完整 CRUD（建立/刪除/切換對話）
```

---

## 十、AI 生成技能系統升級

### 10.1 核心問題

原始 Skill 系統存在的問題：

1. **臨時腳本遺失** - AI 生成的臨時腳本無法追蹤，只有手動 `create_or_update_skill` 時才被記錄
2. **類型驗證缺失** - 腳本輸入/輸出無驗證機制，容易導致格式不匹配
3. **執行歷史不完整** - 無法查詢「此腳本曾在哪些 Step 執行過」
4. **升級流程複雜** - 臨時腳本升級為持久技能需要 AI 手動決定和操作

### 10.2 解決方案架構

```
SkillTemplate（已驗證的持久技能）
    ↑
    │ promote_successful_script()
    │
ScriptExecution（所有腳本執行記錄）
    ↑
    ├── 臨時腳本：無需立即存入庫
    ├── 已驗證腳本：可自動升級為技能
    ├── 失敗腳本：記錄失敗原因供診斷
    └── 關聯 Step & StepLog：完整審計鏈
```

### 10.3 四層改進

#### 層級 1：SkillTemplate 增強版

**新增欄位：**

| 欄位 | 類型 | 說明 |
|------|------|------|
| `input_schema` | JSONField | 輸入參數的 JSON Schema |
| `output_schema` | JSONField | 輸出的預期結構 JSON Schema |
| `is_robust` | BooleanField | 是否為已驗證的「健壯」技能 |
| `last_verified_at` | DateTimeField | 最後驗證通過的時間 |
| `last_failure_reason` | TextField | 最近失敗原因（用於診斷） |
| `version` | PositiveIntegerField | 技能版本號（修改自動遞增） |

**模型驗證：**

```python
def clean(self):
    # 驗證 JSON Schema 有效性
    # 驗證 name 必須是 kebab-case（如 django-csrf-bypass）
    # 驗證 tags 必須是列表
    
def save(self):
    # 如果修改已驗證的技能，自動遞增版本
    # 新版本重置 is_robust = False
```

**排序優先級：**

```
-is_robust, -usage_count, -updated_at
```

ROBUST 技能優先排序，表示已多次驗證、可信度最高。

#### 層級 2：ScriptExecution 模型

**目的：** 追蹤所有臨時腳本的執行歷史，無論是否存入 SkillTemplate。

**核心欄位：**

```python
class ScriptExecution(models.Model):
    # 關聯
    skill = ForeignKey(SkillTemplate, null=True)  # 可選，臨時腳本為 null
    step = ForeignKey(Step)                        # 必須，用於審計
    attack_vector = ForeignKey(AttackVector, null=True)  # 用於導出
    
    # 腳本內容
    script_content = TextField()
    script_language = CharField(choices=[("python", "Python"), ("bash", "Bash")])
    
    # 執行參數
    args_string = TextField(blank=True)
    input_json = JSONField(null=True)  # 結構化輸入
    
    # 執行狀態
    status = CharField(choices=[PENDING, RUNNING, SUCCESS, FAILED, TIMEOUT])
    exit_code = IntegerField(null=True)
    raw_output = TextField(blank=True)
    output_json = JSONField(null=True)  # 結構化輸出
    error_message = TextField(blank=True)
    
    # 驗證狀態
    validation_status = CharField(choices=[
        NOT_VALIDATED,      # 未驗證
        INPUT_INVALID,      # 輸入驗證失敗
        OUTPUT_INVALID,     # 輸出驗證失敗
        VALIDATED,          # 驗證通過
        VALIDATION_ERROR    # 驗證過程出錯
    ])
    validation_error = TextField(blank=True)
    
    # 時間戳
    started_at = DateTimeField(auto_now_add=True)
    completed_at = DateTimeField(null=True)
    execution_duration_ms = IntegerField(null=True)
```

**數據庫索引（用於快速查詢）：**

```python
Index(fields=["step", "-started_at"])
Index(fields=["attack_vector", "-started_at"])
Index(fields=["skill", "-started_at"])
Index(fields=["status"])
```

**典型查詢：**

```sql
-- 查詢特定攻擊向量的所有腳本執行
SELECT * FROM ScriptExecution 
WHERE attack_vector_id = 123 
ORDER BY started_at DESC;

-- 查詢失敗的執行
SELECT * FROM ScriptExecution 
WHERE status = 'FAILED' 
ORDER BY started_at DESC;

-- 查詢可升級為技能的腳本
SELECT * FROM ScriptExecution 
WHERE status = 'SUCCESS' 
AND validation_status = 'VALIDATED' 
AND skill_id IS NULL;
```

#### 層級 3：JSON Schema 驗證庫

**位置：** `apps/core/validators/schema_validators.py`

**支持的驗證類型：**

| 類型 | 驗證規則 | 例子 |
|------|--------|------|
| string | minLength, maxLength, pattern (正則), enum | `{"type": "string", "pattern": "^https?://.*", "minLength": 5}` |
| integer | minimum, maximum, enum | `{"type": "integer", "minimum": 1, "maximum": 65535}` |
| number | minimum, maximum | `{"type": "number", "minimum": 0.0, "maximum": 1.0}` |
| boolean | 無額外規則 | `{"type": "boolean"}` |
| array | items, minItems, maxItems | `{"type": "array", "items": {"type": "string"}, "minItems": 1}` |
| object | properties, required | `{"type": "object", "properties": {...}, "required": [...]}` |
| null | 無額外規則 | `{"type": "null"}` |

**核心類：**

```python
# 驗證輸入
InputValidator.validate(input_data, input_schema) → (bool, error_msg)

# 驗證輸出（自動從文本中提取 JSON）
OutputValidator.validate(output_text, output_schema) → (bool, error_msg, parsed_json)

# 快速構建 schema
SchemaBuilder.string(pattern="^https?://.*")
SchemaBuilder.integer(minimum=1, maximum=100)
SchemaBuilder.object(
    properties={"url": ..., "timeout": ...},
    required=["url"]
)
```

#### 層級 4：自動執行追蹤與升級機制

**execute_skill_script 工作流：**

```
1. 驗證輸入參數（如果定義了 input_schema）
   └─ 失敗 → 拒絕執行，回傳錯誤
   
2. 在 Docker 中執行腳本
   └─ 捕獲 exit_code 和 raw_output
   
3. 驗證輸出（如果定義了 output_schema）
   └─ 嘗試從 raw_output 解析 JSON
   └─ 驗證 JSON 是否符合 output_schema
   
4. 自動記錄到 ScriptExecution
   └─ 保存所有參數和結果
   └─ 記錄驗證狀態
   
5. 建立 StepLog 記錄
   └─ 關聯到當前 Step
   └─ 便於前端完整顯示執行鏈
   
6. 更新 SkillTemplate 的驗證狀態
   └─ 成功 → 更新 last_verified_at
   └─ 失敗 → 記錄 last_failure_reason
```

**新增方法簽名：**

```python
@method_tool
def execute_skill_script(
    self, 
    name: str,
    args_string: str = "",
    attack_vector_id: int = None,  # 關聯到攻擊向量
    input_json: dict = None         # 結構化輸入
) -> str
```

**臨時腳本升級流程：**

```python
# 步驟 1：AI 執行臨時腳本，無需立即存入庫
output = execute_skill_script("temp-csrf-extractor", args_string="--url https://target.com")
# 系統自動在 ScriptExecution 中記錄所有細節

# 步驟 2：驗證成功後，查看可升級的腳本
candidates = list_ready_for_promotion()

# 步驟 3：升級為持久技能
promote_successful_script(
    script_execution_id=123,
    skill_name="csrf-token-extractor",
    tags=["csrf", "django", "token-extraction"],
    description="Extract CSRF token from Django login form"
)
# 系統自動：
# - 生成 instructions（基於執行上下文）
# - 提取 input_schema 和 output_schema
# - 創建 SkillTemplate（版本 1，is_robust=False）

# 步驟 4：驗證充分後，標記為可信賴
mark_skill_as_robust("csrf-token-extractor", verified=True)
```

### 10.4 AI 提示詞增強

在 `planning_agent.py` 中的新規則：

```
=== 新增：類型驗證與執行追蹤 ===

所有腳本（臨時或持久）執行都會自動被記錄到 ScriptExecution，
前端可查看執行歷史與關聯 StepLog。

**輸入參數驗證（Input Schema）**：
When saving to SkillTemplate, ALWAYS define input_schema for parameters. Example:
{
  "type": "object",
  "properties": {"url": {"type": "string", "pattern": "^https?://.*"}},
  "required": ["url"]
}

When calling execute_skill_script(name, input_json={"url": "https://..."}),
the system will validate input BEFORE execution.

**輸出驗證（Output Schema）**：
Define output_schema for expected script output format. Your script MUST output valid JSON.
Example:
{
  "type": "object",
  "properties": {"token": {"type": "string"}, "success": {"type": "boolean"}},
  "required": ["token", "success"]
}

If output fails validation, execution is marked VALIDATION_ERROR 
and last_failure_reason is recorded for diagnosis.

**臨時腳本執行追蹤**：
Even if you write a one-off temporary script (不存到 SkillTemplate)，
the system STILL records it in ScriptExecution:
- 完整的腳本內容（script_content）
- 輸入參數（input_json）與輸出（output_json）
- 執行狀態（SUCCESS/FAILED/TIMEOUT）
- 驗證狀態（VALIDATED / OUTPUT_INVALID / ...）
- 關聯的 Step 與 StepLog（便於前端顯示）

This means you can always query to see all scripts run against a vector.
```

### 10.5 前端集成

**查詢腳本執行歷史：**

```graphql
query {
  scriptExecutions(stepId: 123, orderBy: "-started_at") {
    id
    skill { name version }
    status
    validationStatus
    executionDurationMs
    startedAt
  }
}
```

**攻擊向量的完整腳本清單（導出）：**

```python
from apps.core.models.analyze.AttackVector import ScriptExecution
import json

scripts = ScriptExecution.objects.filter(attack_vector_id=456)

export = {
    "attack_vector_id": 456,
    "scripts": [
        {
            "id": s.id,
            "skill": s.skill.name if s.skill else "temporary",
            "language": s.script_language,
            "content": s.script_content,
            "input": s.input_json,
            "output": s.output_json,
            "status": s.status,
            "validation": s.validation_status,
            "executed_at": s.started_at.isoformat()
        }
        for s in scripts
    ]
}

with open("attack_vector_scripts.json", "w") as f:
    json.dump(export, f, indent=2, ensure_ascii=False)
```

### 10.6 使用範例

**範例 1：簡單臨時腳本**

```python
# AI 執行臨時腳本，無需手動存儲
result = execute_skill_script(
    "my-header-extractor",
    args_string="--target https://example.com"
)
# 系統自動記錄到 ScriptExecution
# 前端可查詢：ScriptExecution.objects.filter(step_id=123)
```

**範例 2：帶驗證的技能**

```python
# 建立帶 schema 的技能
create_or_update_skill(
    name="csrf-bypass-django",
    description="Django CSRF token extraction and bypass",
    instructions="...",
    script_content="...",
    input_schema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "pattern": "^https?://.*"}
        },
        "required": ["url"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "csrf_token": {"type": "string"},
            "session_key": {"type": "string"}
        },
        "required": ["csrf_token"]
    }
)

# 執行時自動驗證
result = execute_skill_script(
    "csrf-bypass-django",
    input_json={"url": "https://target.com/login"},
    attack_vector_id=789
)
# ScriptExecution 記錄輸入/輸出驗證狀態
```

**範例 3：升級流程**

```python
# 執行多次成功驗證
for i in range(3):
    execute_skill_script("temp-recon", args_string=f"--target {targets[i]}")

# 查看可升級的腳本
ready = list_ready_for_promotion()

# 升級為持久技能
promote_successful_script(
    script_execution_id=999,
    skill_name="http-header-extraction",
    tags=["reconnaissance", "http", "headers"],
    description="Extract HTTP headers from target URL"
)

# 進一步驗證後標記為 ROBUST
mark_skill_as_robust("http-header-extraction", verified=True)
```

### 10.7 相關文件位置

| 組件 | 位置 |
|------|------|
| SkillTemplate 增強版 | `apps/core/models/analyze/SkillTemplate.py` |
| ScriptExecution 模型 | `apps/core/models/analyze/AttackVector.py` |
| JSON Schema 驗證庫 | `apps/core/validators/schema_validators.py` |
| 升級工具函數 | `apps/core/script_upgrader.py` |
| SkillMixin 工具集 | `apps/auto/tools/skill_tools.py` |
| AI 提示詞 | `apps/auto/assistants/planning_agent.py:58-70` |
| Django 遷移 | `apps/core/migrations/0004_scriptexecution_*.py` |

### 10.8 數據庫遷移

遷移文件 `0004_scriptexecution_alter_skilltemplate_options_and_more.py` 包含：

```python
# 新增 ScriptExecution 表
+ Create model ScriptExecution

# SkillTemplate 修改
+ Add field input_schema
+ Add field output_schema
+ Add field is_robust
+ Add field last_verified_at
+ Add field last_failure_reason
+ Add field version
+ Create constraint unique_skill_version

# 索引
+ Create index core_script_step_id_*_idx on (step, -started_at)
+ Create index core_script_attack__*_idx on (attack_vector, -started_at)
+ Create index core_script_skill_*_idx on (skill, -started_at)
+ Create index core_script_status_*_idx on (status)
```

執行遷移：

```bash
python manage.py migrate core
```

### 10.9 前端整合：ScriptExecutionViewer

#### 10.9.1 概述

前端通過 React 組件 `ScriptExecutionViewer` 完整展示腳本執行歷史，用戶可以：
- 檢查執行狀態（SUCCESS/FAILED/TIMEOUT/PENDING/RUNNING）
- 查看輸入輸出驗證結果
- 檢查執行耗時和錯誤信息
- 識別可升級為持久技能的成功腳本

#### 10.9.2 前端組件架構

**主要文件**：

```
frontend/src/
├── components/
│   ├── ScriptExecutionViewer.tsx      (主要組件，~230 行)
│   └── ScriptExecutionViewer.css      (樣式，~400 行)
├── pages/
│   └── ExecutionMonitorPage/
│       └── ExecutionMonitorPage.tsx   (集成點)
└── queries.ts                          (GraphQL 查詢)
```

#### 10.9.3 ScriptExecutionViewer 功能細節

**組件簽名**：

```typescript
interface ScriptExecutionViewerProps {
  stepId: number | null;                // Step ID（可能為 null）
  onExecutionsLoaded?: (executions: ScriptExecution[]) => void;
  compact?: boolean;                    // 緊湊視圖模式
}
```

**核心功能**：

1. **條件性查詢**：只在 `stepId` 非 null 時啟動 GraphQL 查詢
   ```typescript
   const { data, loading, error } = useHasuraQuery(
     GET_SCRIPT_EXECUTIONS,
     stepId ? { stepId } : {}
   );
   ```

2. **狀態可視化**：使用顏色編碼的徽章
   - SUCCESS: 綠色 (#dcfce7)
   - FAILED: 紅色 (#fee2e2)
   - RUNNING: 藍色 (#dbeafe)
   - PENDING: 灰色 (#f3f4f6)
   - TIMEOUT: 橙色 (#fed7aa)

3. **驗證狀態指示器**：
   - VALIDATED: 綠色背景，表示輸入輸出均已驗證
   - INPUT_INVALID / OUTPUT_INVALID: 紅色背景
   - VALIDATION_ERROR: 橙色背景
   - NOT_VALIDATED: 灰色背景

4. **展開式細節檢視**：點擊執行項可展開查看
   - Arguments（命令行參數）
   - Language（腳本語言）
   - Exit Code（退出碼）
   - Input JSON（結構化輸入）
   - Output JSON（結構化輸出）
   - Raw Output（原始輸出）
   - Error Message（錯誤消息）
   - Validation Error（驗證錯誤）

5. **升級建議**：成功且通過驗證的臨時腳本自動提示
   ```typescript
   {exec.status === 'SUCCESS' && 
    exec.validation_status === 'VALIDATED' && 
    !exec.skill && (
     <div className="detail-section suggestion">
       <h4>💡 Ready for Promotion</h4>
       <p>此腳本可升級為持久技能</p>
       <code>promote_successful_script(...)</code>
     </div>
   )}
   ```

#### 10.9.4 GraphQL 查詢集成

**查詢定義** (`frontend/src/queries.ts`)：

```graphql
query GET_SCRIPT_EXECUTIONS($stepId: Int!) {
  core_script_execution(where: { step_id: { _eq: $stepId } }, order_by: { started_at: desc }) {
    id
    status
    validation_status
    script_language
    args_string
    input_json
    output_json
    raw_output
    exit_code
    error_message
    validation_error
    execution_duration_ms
    started_at
    completed_at
    skill {
      id
      name
      version
      is_robust
    }
    attack_vector {
      id
      name
    }
  }
}
```

此查詢由 Hasura GraphQL Engine 自動生成，映射到 `ScriptExecution` 模型。

#### 10.9.5 集成到 ExecutionMonitorPage

**標籤頁結構**：

右側面板現支持兩個標籤：

1. **Logs 標籤** (`rightPanelTab === 'logs'`)
   - StepNote（人類可讀摘要）
   - AI Thoughts（AI 推理記錄）
   - StepLogViewer（完整執行跟蹤）

2. **Scripts 標籤** (`rightPanelTab === 'scripts'`)
   - ScriptExecutionViewer（腳本執行歷史）

**實現代碼**：

```typescript
{/* Logs Tab Content */}
{rightPanelTab === 'logs' && (
  <>
    {/* StepNote section */}
    {/* StepLogViewer section */}
  </>
)}

{/* Scripts Tab Content */}
{rightPanelTab === 'scripts' && (
  <div style={{ flex: 1, overflow: 'hidden', minHeight: 0, padding: '12px 16px' }}>
    <ScriptExecutionViewer stepId={selectedStepId} compact={false} />
  </div>
)}
```

#### 10.9.6 數據流程

```
User selects Step
    ↓
selectedStepId 設置
    ↓
ExecutionMonitorPage 渲染右側面板
    ↓
標籤頁選擇 (logs/scripts)
    ↓
若選擇 scripts 標籤：
    ↓
ScriptExecutionViewer 掛載，stepId 不為 null
    ↓
useHasuraQuery 調用 GET_SCRIPT_EXECUTIONS
    ↓
Hasura GraphQL 查詢 ScriptExecution 表（過濾 step_id）
    ↓
數據返回，渲染執行列表
    ↓
用戶可點擊展開查看細節或升級建議
```

#### 10.9.7 前端測試清單

| 項目 | 預期行為 | 狀態 |
|------|---------|------|
| 頁面加載無 Step 選中時 | 顯示 "Select a step..." | ✅ |
| 選中 Step 後加載 Scripts 標籤 | 加載動畫出現，自動查詢 | 待測試 |
| 執行記錄列表 | 按 started_at 降序排列 | 待測試 |
| 點擊執行項 | 展開細節視圖 | 待測試 |
| 狀態徽章顏色 | 根據 status 字段正確顯示顏色 | 待測試 |
| 驗證狀態徽章 | 根據 validation_status 正確顯示 | 待測試 |
| 升級建議 | SUCCESS + VALIDATED + !skill 時出現 | 待測試 |
| 錯誤訊息顯示 | Hasura 查詢失敗時顯示紅色錯誤 | 待測試 |
| JSON 格式化 | Input/Output JSON 正確縮進顯示 | 待測試 |
| 響應式設計 | 右側面板縮小時內容仍可用 | 待測試 |

#### 10.9.8 相關前端文件位置

| 文件 | 行數 | 說明 |
|------|------|------|
| `ScriptExecutionViewer.tsx` | 230 | 主要元件，狀態視覺化，細節檢視 |
| `ScriptExecutionViewer.css` | 400 | 色彩編碼、徽章、展開式動畫 |
| `ExecutionMonitorPage.tsx` | 1128 | 標籤頁集成點，line 895-928 |
| `queries.ts` | - | GET_SCRIPT_EXECUTIONS GraphQL 查詢 |

#### 10.9.9 性能考慮

- **延遲查詢**：只在 `stepId` 非 null 且用戶選中 Scripts 標籤時執行查詢
- **索引優化**：`ScriptExecution` 表在 `(step_id, -started_at)` 上建立複合索引，加快查詢
- **分頁**：當執行記錄超過 100 條時，建議實現虛擬滾動或分頁加載
- **緩存**：useHasuraQuery 通過 Apollo Client 自動快取結果

### 10.10 Target 級別實時 AI 活動監控

#### 10.10.1 概述

用戶現在可以從 **Target Dashboard** 直接監控 AI 活動，無需等待 Overview 建立。新增 "🤖 AI Activity" 標籤頁，顯示目標相關的所有 Step 執行進度。

**核心價值**：
- 即時看到 AI 正在做什麼
- 不依賴 Overview 的建立
- 支持無 Overview 的臨時執行追蹤

#### 10.10.2 前端實現

**新增組件**：

```
frontend/src/
├── components/
│   ├── TargetActivityMonitor.tsx      (200 行)
│   └── TargetActivityMonitor.css      (500 行)
└── pages/TargetDashboard/
    └── TargetDashboard.tsx             (修改：+20 行)
```

**TargetDashboard 標籤頁結構**：

```
[Seeds] [🤖 AI Activity] [Subdomains] [IPs/Ports] [URLs] [AI Overview]
         ^^^^^^^^^^^^^^^^ 新增
```

#### 10.10.3 GraphQL 查詢策略

**查詢設計**：採用「反向查詢」策略規避 Hasura 的嵌套過濾限制；日誌通過 SSE 實時推送

**問題**（舊方案）：
```graphql
core_step(where: {
  _or: [
    { overview: { target_id: { _eq: $targetId } } }  # ❌ 不支持
  ]
})
```

**解決方案**（新方案）：
```graphql
query GetTargetActiveSteps($targetId: bigint!) {
  # 方案 1：通過 Overview 獲取相關 Steps（推薦：高效、支持完整數據）
  core_overview(where: { target_id: { _eq: $targetId } }) {
    id
    status
    summary
    risk_score
    created_at
    updated_at
    core_steps(order_by: { created_at: desc }) {
      id
      status
      operation_type
      created_at
      completed_at
      core_stepnote { 
        content
        ai_thoughts
      }
      script_executions(order_by: { started_at: desc }, limit: 5) { 
        id
        status 
        validation_status 
        script_language
        started_at
      }
    }
  }
  
  # 方案 2：獲取孤立 Steps（無 Overview，預留支持）
  core_step(where: { overview_id: { _is_null: true } }, limit: 50) {
    id
    status
    operation_type
    created_at
    completed_at
    core_stepnote { content }
    script_executions(limit: 5) { 
      id
      status 
      validation_status 
    }
  }
}
```

**GraphQL 字段映射**：

| Django 模型 | 字段名 | GraphQL 名稱 | 類型 | 說明 |
|------------|--------|-------------|------|------|
| Step | status | status | VARCHAR | PENDING/RUNNING/COMPLETED/FAILED 等 |
| Step | operation_type | operation_type | VARCHAR | 操作類型 |
| Step | created_at | created_at | TIMESTAMP | 步驟建立時間 |
| Step | completed_at | completed_at | TIMESTAMP | 完成時間 |
| Step | notes → StepNote | core_stepnote | OBJECT | 步驟注記和 AI 思考 |
| StepNote | content | content | TEXT | 步驟摘要 |
| StepNote | ai_thoughts | ai_thoughts | TEXT | AI 思考過程 |
| ScriptExecution | status | status | VARCHAR | 腳本執行狀態 |
| ScriptExecution | validation_status | validation_status | VARCHAR | 輸入/輸出驗證狀態 |
| ScriptExecution | script_language | script_language | VARCHAR | 腳本語言（python/bash） |
| ScriptExecution | started_at | started_at | TIMESTAMP | 開始時間 |

**Hasura 關係映射**：
- `Overview.target` → Hasura: `core_overview(where: {target_id})`
- `Overview.steps` → Hasura: `core_steps()` (ForeignKey reverse)
- `Step.overview` → Hasura: reverse query from Overview
- `Step.note_detail` → Hasura: `core_stepnote` (OneToOne)
- `Step.script_executions` → Hasura: `script_executions()` (ForeignKey reverse)

**日誌獲取策略**：
- **GraphQL 層**：不查詢 StepLog（Hasura 未完全支援反向關係）
- **SSE 實時推送**：日誌通過 useStepLogStream hook 從後端流式推送
- **優勢**：前端減少初始加載時間；用戶點擊展開時才獲取詳細日誌

**關鍵技術點**：
1. 先查 Overview（直接過濾 target_id）
2. 通過 Overview 的 `core_steps` 關聯取得所有步驟
3. 額外查詢孤立 Steps（future 支持臨時執行）
4. 日誌通過 SSE 實時推送（無需 GraphQL）
5. 前端 flatMap + sort 展平并合並數據
6. 支持實時更新：subscription 自動推送新 Steps 和 Overview 變化

#### 10.10.4 前端數據處理

前端使用三步法展平和合並數據：

```typescript
// TargetActivityMonitor.tsx 中的數據提取邏輯
const steps: TargetStep[] = targetId && data?.core_overview ? 
  // 步驟 1：flatMap 展平所有 Overview 的 Steps
  data.core_overview
    .flatMap((overview: any) => 
      (overview.core_steps || []).map((step: any) => ({
        ...step,
        overview: {
          id: overview.id,
          status: overview.status,
          summary: overview.summary,
          risk_score: overview.risk_score,
          created_at: overview.created_at,
          updated_at: overview.updated_at
        }
      }))
    )
    // 步驟 2：按 created_at 降序排列（最新優先）
    .sort((a: TargetStep, b: TargetStep) => {
      const aTime = new Date(a.created_at).getTime();
      const bTime = new Date(b.created_at).getTime();
      return bTime - aTime;  // DESC by created_at
    })
    // 步驟 3：限制最多 maxSteps 個（預設 20）
    .slice(0, maxSteps)
  : [];
```

**數據流向**：

```
Hasura (GraphQL)
  ↓
SUBSCRIBE_TARGET_STEPS 返回結構化數據
  ├─ core_overview[0]
  │  ├─ id: 42
  │  ├─ status: "EXECUTING"
  │  ├─ core_steps[0..N]
  │  │  ├─ id, status, operation_type
  │  │  ├─ created_at, completed_at
  │  │  ├─ core_stepnote { content, ai_thoughts }
  │  │  └─ script_executions[0..5]
  │  └─ (更多字段...)
  └─ core_overview[1]
     └─ (同上結構)
  ↓
前端 flatMap 展平
  ↓
[
  { id: 542, status: "RUNNING", overview: {...}, created_at: "2026-05-19T10:45:22Z" },
  { id: 541, status: "COMPLETED", overview: {...}, created_at: "2026-05-19T10:44:15Z" },
  ...
]
  ↓
排序 + 切片
  ↓
最多 20 個最新的 Steps
  ↓
前端渲染時間線
```

**SSE 日誌補充**：

用戶點擊展開 Step 時，組件觸發 `useStepLogStream` hook：

```typescript
// 在 ExecutionMonitorPage 中
const { logs, isConnected } = useStepLogStream(selectedStepId);

// 訂閱方式：Server-Sent Events (SSE)
// 後端流式推送日誌，無需輪詢
// 支援實時進度顯示和錯誤捕捉
```

**優化策略**：

1. **延遲加載日誌**：只在用戶點擊展開時獲取詳細日誌（SSE）
2. **限制 Steps 數量**：預設 maxSteps=20 避免一次加載過多數據
3. **subscription 實時更新**：新 Steps 建立時自動推送，無需輪詢
4. **前端緩存**：Apollo Client 自動緩存 Overview 和 Step 數據
5. **虛擬化（未實現）**：>100 Steps 時可實現虛擬滾動優化性能
    .slice(0, maxSteps)  // 限制為 maxSteps（預設 50）
  : [];
```

**為什麼需要 flatMap？**
- 一個 Target 可能有多個 Overview
- 每個 Overview 有多個 Steps
- 需要展平後按時間統一排序

#### 10.10.5 UI 組件功能

**TargetActivityMonitor** 特性：

| 特性 | 描述 |
|------|------|
| 時間線可視化 | 彩色編碼的 Step 流程展示 |
| 活動統計 | Running / Completed / Failed 計數 |
| 狀態徽章 | 5 色方案：PENDING/RUNNING/COMPLETED/FAILED/WAITING_FOR_ASYNC |
| 操作標籤 | 🤖 AI 自動化 / 👤 手動測試 / 🔍 掃描操作等 |
| 展開式詳情 | 點擊 Step 查看完整摘要、日誌、Overview 上下文 |
| 快速導航 | 直接鏈接到 Overview 和完整執行監控頁面 |
| 持續時間 | 顯示 Step 執行耗時（秒） |
| 實時更新 | GraphQL subscription 自動推送新 Steps |

#### 10.10.6 SUBSCRIBE_TARGET_STEPS 訂閱

```graphql
subscription SubscribeTargetSteps($targetId: bigint!) {
  core_overview(
    where: { target_id: { _eq: $targetId } }
    order_by: { updated_at: desc }
  ) {
    id
    status
    created_at
    updated_at
    core_steps(order_by: { created_at: desc }, limit: 50) {
      id
      status
      operation_type
      created_at
      completed_at
      overview_id
      core_stepnote { 
        content
      }
    }
  }
}
```

**訂閱特性**：

| 特性 | 說明 |
|------|------|
| 觸發事件 | Overview 狀態變更、新 Step 建立、Step 狀態轉移 |
| 推送延遲 | <100ms（WebSocket） |
| 更新頻率 | 無節流，每個更改推送一次 |
| 數據量 | 平均 5-15KB（取決於 Step 數量） |
| 日誌 | **不包含**（通過 SSE useStepLogStream 獲取） |

**訂閱會在以下事件自動觸發更新**：
- Overview 狀態變更（PLANNING → EXECUTING → COMPLETED）
- 新 Step 建立
- Step 狀態轉移（PENDING → RUNNING → COMPLETED 等）
- Step completed_at 更新（步驟完成）

#### 10.10.7 數據流程圖

```
Target Dashboard (targetId=37)
    ↓
用戶點擊 "🤖 AI Activity" 標籤
    ↓
TargetActivityMonitor 組件掛載
    ↓
調用 SUBSCRIBE_TARGET_STEPS(targetId=37)
    ↓
Hasura GraphQL 執行訂閱 (WebSocket)
    ↓
查詢所有 core_overview 其中 target_id=37
    ↓
對每個 Overview，獲取其關聯的 core_steps（最多 50 個）
    ↓
返回嵌套結構：
{
  core_overview: [
    {
      id: 42,
      status: "EXECUTING",
      created_at: "2026-05-19T10:30:00Z",
      updated_at: "2026-05-19T10:45:22Z",
      core_steps: [
        { 
          id: 542, 
          status: "RUNNING", 
          operation_type: "AI_AUTOMATION_EXECUTION",
          created_at: "2026-05-19T10:45:00Z",
          completed_at: null,
          core_stepnote: { content: "Executing scan on target..." }
        },
        { 
          id: 541, 
          status: "COMPLETED", 
          operation_type: "SCAN_OPERATION",
          created_at: "2026-05-19T10:44:00Z",
          completed_at: "2026-05-19T10:44:45Z",
          core_stepnote: { content: "Port scan completed" }
        },
        ...
      ]
    }
  ]
}
    ↓
前端接收更新
    ↓
TargetActivityMonitor 重新計算 steps 列表（flatMap + sort）
    ↓
根據新 Step 的狀態著色時間線
    ↓
跑動畫效果（RUNNING 脈衝、動作轉換）
    ↓
如果用戶點擊展開 Step，調用 useStepLogStream 獲取詳細日誌（SSE）
    ↓
顯示完整的執行跟蹤和 AI 思考過程
```
      ]
    },
    ...
  ]
}
    ↓
前端 flatMap 展平為單層 Steps 數組
    ↓
按 created_at DESC 排序
    ↓
渲染時間線 UI，顯示：
  ⟳ RUNNING Step #542 (2026-05-19 14:23:15)
  ✓ COMPLETED Step #541 (2026-05-19 14:22:30)
  ...
    ↓
用戶可點擊展開查看詳情或導航到其他頁面
```

#### 10.10.8 三層監控體系完成

結合 **ScriptExecutionViewer** 和 **TargetActivityMonitor**，用戶現在擁有三層監控：

| 層級 | 組件 | 位置 | 用途 |
|------|------|------|------|
| **Macro** | TargetActivityMonitor | Target Dashboard | 看 AI 在做什麼（高層概覽） |
| **Meso** | ExecutionMonitorPage | 點擊 Step 後 | 看每個 Step 的詳細執行流 |
| **Micro** | ScriptExecutionViewer | ExecutionMonitor 的 Scripts 標籤 | 看具體的腳本執行和驗證狀態 |

**使用流程**：
```
Target Dashboard 🤖 Activity 標籤
    ↓ 發現 Step #542 RUNNING
    ↓
點擊進入 ExecutionMonitorPage
    ↓ 查看 StepLog 和詳細信息
    ↓
切換到 Scripts 標籤
    ↓ 查看腳本執行歷史和驗證結果
```

#### 10.10.9 性能與優化

**查詢優化**：
- 利用 PostgreSQL 的外鍵索引加快 Overview → Steps 的導航
- GraphQL subscription 只返回最近 50 個 Steps（可配置）
- 前端限制渲染 maxSteps=50，超過部分使用虛擬滾動（future）

**數據量估算**：
- Target 通常有 1-5 個 Overview
- 每個 Overview 通常有 10-50 個 Steps
- 單次查詢返回數據量：~5KB - 50KB（取決於 stepnote 和 log 長度）

**實時性**：
- GraphQL subscription 使用 WebSocket
- 新 Step 創建後 <100ms 推送到前端
- 用戶無需手動刷新

#### 10.10.10 相關文件位置

| 文件 | 類型 | 行數 | 說明 |
|------|------|------|------|
| `TargetActivityMonitor.tsx` | 新建 | 200 | 主要 React 組件 |
| `TargetActivityMonitor.css` | 新建 | 500 | 時間線樣式、動畫、響應式 |
| `TargetDashboard.tsx` | 修改 | +20 | 新增 activity 標籤，導入組件 |
| `queries.ts` | 修改 | +60 | 新增 GET_TARGET_ACTIVE_STEPS、SUBSCRIBE_TARGET_STEPS |

#### 10.10.11 已知限制與未來改進

**已知限制**：
1. 孤立 Steps（無 Overview）的支持尚在 future 計劃中
2. 大量 Steps（>500）的虛擬滾動尚未實現
3. 步驟搜索/過濾功能尚未添加

**未來改進方向**：
1. ✅ 孤立 Steps 支持（代碼已預留）
2. 📊 Steps 統計圖表（按操作類型、狀態分布）
3. 🔍 高級過濾器（狀態、時間範圍、操作類型）
4. 📤 執行歷史導出（CSV/JSON）
5. 🔔 Step 狀態變更通知（郵件、Slack）
6. 📈 性能分析面板（平均執行時間、成功率趨勢）

---

## 十二、附錄：完整 API 路由映射

```
/api/admin/                           — Django Admin 管理後台
/api/assistant/                       — apps.ai_assistant 原生接口

/api/targets                          — Targets 目標管理
/api/scanners/nmap                    — Nmap 掃描
/api/scanners/subdomain               — Subfinder 子域名
/api/scanners/vuln                    — Nuclei 漏洞/技術掃描
/api/scanners/crawler                 — URL 發現（GAU + Crawler）
/api/scanners/cve                     — CVE Intelligence 情報查詢
/api/flaresolverr                     — FlareSolverr 反機器人繞過
/api/core                             — Core 模型層對外 API（目前主要為 Steps / Overviews）
/api/core/steps                       — Steps 執行步驟
/api/core/overviews                   — Overviews 戰略概覽
/api/analyze_ai                       — Initial AI 分析入口
/api/scheduler                        — 定時任務管理 CRUD
/api/http_sender                      — Endpoint fuzzing 入口
/api/api_keys                         — 外部 API Key 管理
/api/auto                             — 已廢棄的舊公開 API（內部自動化仍由 apps.auto 執行）
```

---

## 十三、CVE Intelligence 情報系統

### 13.1 系統概述

CVE Intelligence 是 SKRpyASM 的漏洞情報查詢與關聯系統，整合 NVD、CISA KEV、EPSS 等多個權威資料來源，為發現的漏洞提供詳細的 CVE 情報，並自動對應技術棧到已知漏洞。

**核心功能**：
- 三層快取策略（PostgreSQL → Redis → External API）
- 自動豐富化 Nuclei 掃描結果
- 技術棧 CVE 風險評估
- CISA KEV（已被利用漏洞）監控
- AI Agent 工具整合
- REST API 端點

### 13.2 資料模型

#### CVEIntelligence 模型

```python
# apps/core/models/cve_intelligence.py
class CVEIntelligence(models.Model):
    """CVE 情報記錄，整合多個資料來源"""
    # 核心識別
    cve_id = CharField(max_length=20, unique=True, db_index=True)
    
    # 漏洞詳情
    description = TextField()
    severity = CharField(max_length=20)  # CRITICAL, HIGH, MEDIUM, LOW
    cvss_score = FloatField(null=True)
    cvss_vector = CharField(max_length=200, null=True)
    
    # 受影響產品
    affected_products = JSONField(default=list)
    
    # 威脅情報
    exploit_available = BooleanField(default=False)
    exploited_in_wild = BooleanField(default=False)
    cisa_kev = BooleanField(default=False)  # CISA Known Exploited Vulnerability
    epss_score = FloatField(null=True)  # Exploit Prediction Scoring System
    
    # 參考資料
    references = JSONField(default=list)
    published_date = DateTimeField(null=True)
    last_modified_date = DateTimeField(null=True)
    
    # 資料來源追蹤
    data_sources = JSONField(default=dict)
    
    # 本地追蹤
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    @property
    def risk_score(self):
        """計算風險分數（0-100）"""
        score = 0
        if self.cvss_score:
            score += self.cvss_score * 10
        if self.cisa_kev:
            score += 20
        if self.exploit_available:
            score += 15
        if self.epss_score:
            score += self.epss_score * 10
        return min(score, 100)
```

#### TechStackCVEMapping 模型

```python
class TechStackCVEMapping(models.Model):
    """將發現的 TechStack 對應到相關 CVE"""
    techstack = ForeignKey("core.TechStack", related_name="cve_mappings")
    cve_intelligence = ForeignKey("core.CVEIntelligence", related_name="techstack_mappings")
    version_match = CharField(max_length=20)  # exact, range, unknown
    confidence = FloatField(default=1.0)
    discovered_at = DateTimeField(auto_now_add=True)
    notified = BooleanField(default=False)
```

#### Vulnerability 模型擴充

```python
# apps/core/models/Vulnerability.py
class Vulnerability(models.Model):
    # ... 原有欄位
    
    # CVE 豐富化欄位
    cve_intelligence = ForeignKey("core.CVEIntelligence", null=True, related_name="discovered_instances")
    enrichment_status = CharField(default="pending")  # pending, enriched, no_cve, failed
    enrichment_attempted_at = DateTimeField(null=True)
```

### 13.3 三層快取策略

CVE Intelligence 使用三層快取策略，優先使用本地資料，減少 70% 的外部 API 請求：

```
Layer 1: PostgreSQL (CVEIntelligence 模型)
  ↓ 未找到
Layer 2: Redis (24h TTL)
  ↓ 未找到
Layer 3: External APIs (NVD, CISA KEV, EPSS)
  ↓ 查詢成功
  儲存到 Layer 1 & Layer 2
```

**批次查詢優化**：
```python
# 智慧批次處理範例
cve_ids = ["CVE-2021-44228", "CVE-2021-45046", ...]  # 10 個 CVE

# 1. 優先查詢本地資料庫
existing = CVEIntelligence.objects.filter(cve_id__in=cve_ids)
# 找到 7 個已存在的 CVE

# 2. 僅對 3 個缺失的 CVE 發起外部 API 請求
missing_cve_ids = [cve for cve in cve_ids if cve not in existing]
# 只需 3 次 API 請求，而非 10 次

# 效能提升：70% 減少 API 請求
```

### 13.4 資料來源整合

#### NVD API 2.0

```python
# apps/scanners/cve_intelligence/clients/nvd_client.py
class NVDClient(BaseCVEClient):
    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    # 速率限制
    # 無 API key: 5 req/30s
    # 有 API key: 50 req/30s (建議申請)
    
    async def query_cve(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """查詢特定 CVE 的詳細資訊"""
```

#### CISA KEV Client

```python
# apps/scanners/cve_intelligence/clients/cisa_kev_client.py
class CISAKEVClient(BaseCVEClient):
    KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    
    async def fetch_kev_catalog(self) -> Dict[str, Dict]:
        """抓取 CISA KEV 目錄（已被利用的漏洞）"""
```

#### EPSS Client

```python
# apps/scanners/cve_intelligence/clients/epss_client.py
class EPSSClient(BaseCVEClient):
    BASE_URL = "https://api.first.org/data/v1/epss"
    
    async def query_cve(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """查詢 EPSS 分數（30 天內被利用的機率預測）"""
```

### 13.5 自動豐富化流程

#### Nuclei 掃描後自動觸發

```python
# apps/scanners/nuclei_scanner/tasks/executor.py
# Nuclei 掃描完成後
if callback_step_id:
    from apps.scanners.cve_intelligence.tasks.enrichment_tasks import enrich_vulnerabilities_batch
    
    vuln_ids = Vulnerability.objects.filter(
        tool_source="nuclei",
        enrichment_status="pending"
    ).values_list("id", flat=True)[:50]
    
    if vuln_ids:
        enrich_vulnerabilities_batch.delay(list(vuln_ids), callback_step_id)
```

#### 技術棧偵測後自動對應

```python
# apps/scanners/nuclei_scanner/tasks/url_tech.py
# TechStack 記錄建立後
from apps.scanners.cve_intelligence.tasks.enrichment_tasks import sync_techstack_cves

sync_techstack_cves.delay(target_id, callback_step_id)
```

#### 排程式 CISA KEV 同步

```python
# apps/scanners/cve_intelligence/tasks/scheduled_sync.py
@shared_task(bind=True)
def sync_cisa_kev_database(self, callback_step_id: Optional[int] = None):
    """
    每日同步 CISA KEV 目錄
    
    工作流程：
    1. 抓取 CISA KEV 目錄
    2. 更新本地 CVEIntelligence 記錄的 KEV 狀態
    3. 對於本地不存在的 KEV CVE，觸發 NVD 查詢補充詳情
    4. 檢查是否有新的 KEV CVE 影響現有的 TechStack
    """
```

### 13.6 AI Agent 工具整合

#### CVEIntelligenceMixin 工具

```python
# apps/auto/tools/cve_intelligence_tools.py
class CVEIntelligenceMixin:
    """CVE Intelligence Tools Mixin"""
    
    @method_tool
    def query_cve_by_id(self, cve_id: str) -> str:
        """查詢特定 CVE 的詳細情報"""
    
    @method_tool
    def search_cves_for_technology(
        self, tech_name: str, version: str = None,
        severity_min: str = "MEDIUM", exploited_only: bool = False
    ) -> str:
        """根據技術名稱和版本搜尋相關 CVE"""
    
    @method_tool
    def enrich_vulnerability_with_cve(self, vulnerability_id: int) -> str:
        """為 Vulnerability 記錄豐富化 CVE 情報"""
    
    @method_tool
    def get_techstack_cve_report(self, target_id: int, overview_id: int) -> str:
        """生成目標的技術棧 CVE 風險報告"""
```

#### 整合到 AutomationAgent

```python
# apps/auto/tools/db_tools.py
class DBToolsMixin(
    ReconnaissanceMixin,
    AssetCreationMixin,
    EndpointMixin,
    MemoryMixin,
    SkillMixin,
    SandboxMixin,
    StepManagementMixin,
    CVEIntelligenceMixin,  # CVE 情報工具
):
    """統一的資料庫工具 Mixin"""
```

### 13.7 REST API 端點

#### 端點總覽

| 端點                                          | 方法   | 類型   | 說明                       |
| --------------------------------------------- | ------ | ------ | -------------------------- |
| `/api/scanners/cve/query`                     | POST   | 同步   | 查詢特定 CVE               |
| `/api/scanners/cve/search`                    | POST   | 同步   | 根據技術名稱搜尋 CVE       |
| `/api/scanners/cve/search_by_tags`            | POST   | 同步   | 根據 tags 搜尋 CVE（新功能）|
| `/api/scanners/cve/techstack_report/{id}`     | GET    | 同步   | 技術棧 CVE 報告            |
| `/api/scanners/cve/enrich_vulnerabilities`    | POST   | 異步   | 批次豐富化 Vulnerability   |
| `/api/scanners/cve/sync_techstack`            | POST   | 異步   | 同步 TechStack CVE         |
| `/api/scanners/cve/sync_kev`                  | POST   | 異步   | 手動同步 CISA KEV          |

#### Tags 搜尋功能（新功能）

支援多標籤 OR 查詢，靈活搜尋相關技術的 CVE：

```bash
# 搜索 Apache RCE 漏洞
curl -X POST http://localhost:8000/api/scanners/cve/search_by_tags \
  -H "Content-Type: application/json" \
  -d '{
    "tags": ["apache", "rce"],
    "severity_min": "HIGH",
    "exploited_only": false,
    "limit": 10
  }'

# 搜索已被利用的認證繞過漏洞
curl -X POST http://localhost:8000/api/scanners/cve/search_by_tags \
  -H "Content-Type: application/json" \
  -d '{
    "tags": ["authentication", "bypass"],
    "severity_min": "CRITICAL",
    "exploited_only": true,
    "limit": 20
  }'
```

**排序規則**：
1. 優先顯示 CISA KEV（已被利用的 CVE）
2. 按 CVSS 分數降序
3. 按 EPSS 分數降序

### 13.8 使用場景

#### 場景 1：發現新技術後立即查詢 CVE

```
1. Nuclei 技術掃描發現 Apache Struts 2.5.30
2. AutomationAgent 自動呼叫：
   search_cves_for_technology("Apache Struts", "2.5.30", severity_min="HIGH")
3. 返回相關 CVE 列表，包含 CVSS、EPSS、KEV 狀態
4. Agent 根據風險評分決定下一步攻擊策略
```

#### 場景 2：Nuclei 掃描後自動豐富化

```
1. Nuclei 掃描發現 10 個漏洞（template_id 包含 CVE ID）
2. 掃描完成後自動觸發 enrich_vulnerabilities_batch
3. 系統從 template_id 提取 CVE ID
4. 優先查詢本地資料庫（找到 7 個）
5. 僅對 3 個缺失的 CVE 發起外部 API 請求
6. 自動關聯 Vulnerability.cve_intelligence
7. 更新 enrichment_status = "enriched"
```

#### 場景 3：CISA KEV 主動監控

```
1. Celery Beat 每日 02:00 UTC 觸發 sync_cisa_kev_database
2. 抓取最新 CISA KEV 目錄
3. 發現新條目：CVE-2024-99999 (Apache Struts 2.5.30)
4. 查詢本地 TechStack，找到 3 個目標使用該版本
5. 建立 TechStackCVEMapping 記錄
6. 發送通知到 HackerAssistant：
   "🚨 CISA KEV Alert: 3 targets vulnerable to CVE-2024-99999"
```

#### 場景 4：技術棧風險報告

```
1. 前端請求：GET /api/scanners/cve/techstack_report/1
2. 系統查詢 Target 1 的所有 TechStack
3. 查詢所有 TechStackCVEMapping
4. 統計：總 CVE 數、CRITICAL 數、HIGH 數、KEV 數
5. 返回前 10 個高危 CVE（按 CVSS 排序）
6. 前端展示風險儀表板
```

### 13.9 效能優化

#### 批次查詢優化

```
範例：批次查詢 10 個 CVE

無快取：10 次 API 請求
有快取（7 個已存在）：3 次 API 請求
效能提升：70% 減少 API 請求
```

#### 速率限制處理

| API 來源  | 無 API Key    | 有 API Key     | 建議           |
| --------- | ------------- | -------------- | -------------- |
| NVD       | 5 req/30s     | 50 req/30s     | 強烈建議申請   |
| CISA KEV  | 無限制        | 無限制         | 無需 API Key   |
| EPSS      | 無限制        | 無限制         | 無需 API Key   |

#### API Key 管理

```bash
# 申請 NVD API Key
# https://nvd.nist.gov/developers/request-an-api-key

# 添加到系統
curl -X POST http://localhost:8000/api/api_keys/ \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "nvd",
    "key_value": "your-nvd-api-key",
    "is_active": true,
    "description": "NVD API Key for CVE queries"
  }'
```

### 13.10 架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                     AutomationAgent                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           CVEIntelligenceMixin (4 tools)             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              CVEEnrichmentService                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  三層快取策略：PostgreSQL → Redis → External API    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  NVDClient   │   │ CISAKEVClient│   │  EPSSClient  │
│  (API 2.0)   │   │   (KEV)      │   │   (EPSS)     │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    CVEIntelligence                           │
│                  TechStackCVEMapping                         │
│                    Vulnerability                             │
└─────────────────────────────────────────────────────────────┘
```

### 13.11 關鍵檔案清單

**新增檔案（18 個）**：
- `apps/core/models/cve_intelligence.py` - CVE 資料模型
- `apps/scanners/cve_intelligence/clients/base.py` - 抽象基礎客戶端
- `apps/scanners/cve_intelligence/clients/nvd_client.py` - NVD API 2.0 客戶端
- `apps/scanners/cve_intelligence/clients/cisa_kev_client.py` - CISA KEV 客戶端
- `apps/scanners/cve_intelligence/clients/epss_client.py` - EPSS 客戶端
- `apps/scanners/cve_intelligence/services/cve_enrichment.py` - CVE 豐富化服務
- `apps/scanners/cve_intelligence/services/version_matcher.py` - 版本匹配邏輯
- `apps/scanners/cve_intelligence/tasks/enrichment_tasks.py` - Celery 豐富化任務
- `apps/scanners/cve_intelligence/tasks/scheduled_sync.py` - CISA KEV 排程同步
- `apps/scanners/cve_intelligence/schemas.py` - Pydantic request/response schemas
- `apps/scanners/cve_intelligence/api.py` - Django Ninja API 端點
- `apps/auto/tools/cve_intelligence_tools.py` - AI Agent 工具（4 個核心工具）
- `test_cve_intelligence.py` - 測試腳本
- `test_cve_api.sh` - API 測試腳本
- `CVE_IMPLEMENTATION_SUMMARY.md` - 實作總結文件
- `CVE_API_GUIDE.md` - API 使用指南

**修改檔案（7 個）**：
- `apps/core/models/Vulnerability.py` - 新增 enrichment 欄位
- `apps/core/models/__init__.py` - 匯出 CVEIntelligence 和 TechStackCVEMapping
- `apps/auto/tools/db_tools.py` - 整合 CVEIntelligenceMixin
- `apps/scanners/nuclei_scanner/tasks/executor.py` - 新增掃描後 hook
- `apps/scanners/nuclei_scanner/tasks/url_tech.py` - 新增技術棧 CVE 對應
- `apps/scanners/api.py` - 掛載 CVE router
- `apps/api_keys/api.py` - 新增 "nvd" 到 SUPPORTED_SERVICES
- `c2_core/settings.py` - 新增 Celery imports
- `.env.example` - 新增 CVE 設定

### 13.12 環境變數設定

```bash
# === CVE Intelligence Configuration ===
NVD_API_KEY=your_nvd_api_key_here
VULNCHECK_API_KEY=your_vulncheck_api_key_here
CVE_CACHE_TTL=86400
CVE_ENRICHMENT_BATCH_SIZE=50
CVE_SYNC_ENABLED=true
CISA_KEV_SYNC_SCHEDULE=0 2 * * *
CVE_LOCAL_DB_PRIORITY=true
```

---

## 十四、附錄：構建與部署指南

### 14.1 系統需求

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+
- Docker & Docker Compose

### 14.2 快速啟動

```bash
# 1. 克隆專案
git clone <repository-url>
cd C2_Django_AI_git

# 2. 複製環境變數
cp .env.example .env
# 編輯 .env 填入必要的 API Keys

# 3. 啟動服務
docker-compose up -d

# 4. 初始化資料庫
python manage.py migrate

# 5. 建立超級使用者
python manage.py createsuperuser

# 6. 啟動 Celery Worker
celery -A c2_core worker -P prefork -c 8 -l info

# 7. 啟動 Celery Beat
celery -A c2_core beat -l info

# 8. 啟動 Django 開發伺服器
python manage.py runserver

# 9. 啟動前端開發伺服器
cd frontend
npm install
npm run dev
```

### 14.3 生產環境部署

詳細部署指南請參考 `docs/BUILD_GUIDE.md`。

### 14.4 Docker 全棧部署模式

除 conda 混合模式外（Django 在 host 執行、基礎設施在 Docker），項目亦支援完整的容器化全棧部署。

**架構設計：**
- 單一 `Dockerfile`（`python:3.10-slim`）同時服務於 Django、Celery Worker、Celery Beat，以不同 `command` 啟動
- 安全工具直接嵌入鏡像：`nmap`（apt）、`subfinder v2.6.6`（Go binary）、`nuclei v3.1.0`（Go binary）
- 雙文件 env 注入：`.env`（密鑰，不進鏡像）+ `.env.docker`（Docker 內服務名覆蓋）

**完整服務清單（`docker/docker-compose.yml`）：**

| 服務名 | 鏡像 / 來源 | 用途 |
|--------|------------|------|
| `postgres` | `postgres:14-bullseye` | PostgreSQL 資料庫 |
| `redis` | `redis:8.0` | Celery broker / result backend |
| `hasura` | `hasura/graphql-engine:v2.36.0` | GraphQL 即時查詢層 |
| `nocodb` | `nocodb/nocodb:latest` | 無代碼資料庫管理後台 |
| `flaresolverr` | `ghcr.io/flaresolverr/flaresolverr` | Cloudflare WAF 繞過 |
| `flareproxygo` | `ghcr.io/kljensen/flareproxygo` | FlareSolverr 代理 |
| `c2_kali_sandbox` | `./kali_sandbox`（本地 build） | AI Skill 沙盒執行環境（`network_mode: host`） |
| `django` | `Dockerfile`（本地 build） | Django ASGI Web 服務（uvicorn × 4 workers） |
| `celery_worker` | `Dockerfile`（本地 build） | Celery 任務執行（prefork × 8） |
| `celery_beat` | `Dockerfile`（本地 build） | Celery Beat 定時排程 |

**環境配置機制：**

```ini
# .env.docker（僅覆蓋 Docker 容器內差異值，不含密鑰）
POSTGRES_HOST=postgres           # 容器服務名取代 localhost
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
API_BASE_URL=http://django:8000
DJANGO_ALLOWED_HOSTS=django,localhost,127.0.0.1
```

**全棧啟動命令：**

```bash
# 1. 填寫密鑰
cp .env.example .env

# 2. 全棧啟動（自動執行 migrate）
cd docker
docker compose up --build -d

# 3. 確認服務狀態
docker logs c2_django --tail 30     # 看到 "Started server process"
docker logs c2_celery_worker --tail 10  # 看到 "celery@... ready"
```

**Conda 混合模式相容性：** `c2_core/settings.py` 所有 Redis / Postgres 連線設定均採用 `os.environ.get(key, localhost_default)` 模式，conda 本地開發模式完全不受影響。

---

_本白皮書基於 SKRpyASM 原始碼分析生成，反映截至 2026-06-02 的系統架構與設計。_
