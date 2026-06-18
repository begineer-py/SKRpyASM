# SKRpyASM

**AI-native attack-surface management platform — where autonomous agents orchestrate reconnaissance, exploit validation, and strategic reporting.**

SKRpyASM 是一套以 AI Agent 為核心的攻擊面管理與授權安全測試平台。不同於傳統資產掃描工具的被動輸出，它讓 LLM Agent 自主編排偵察、分析漏洞、執行利用驗證，並生成結構化報告——整個流程可追溯、可干預、可重現。

[![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev/)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python)](https://www.python.org/)
[![Celery](https://img.shields.io/badge/Celery-5.5-37814A?logo=celery)](https://docs.celeryq.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-4169E1?logo=postgresql)](https://www.postgresql.org/)
[![LangChain](https://img.shields.io/badge/LangChain-LangGraph-1C3C3C?logo=langchain)](https://www.langchain.com/)
[![License](https://img.shields.io/badge/License-Custom-red)](LICENSE)

---

## Why SKRpyASM? / 為什麼選擇 SKRpyASM

Security testing today is fragmented: recon tools dump raw lists, scanners flood with noise, and findings live in disconnected spreadsheets. SKRpyASM bridges the gap with an **AI-native architecture** that combines traditional security tooling with autonomous LLM agents.

| Pain Point | SKRpyASM Approach |
|------------|-------------------|
| Tool outputs are siloed | 10+ tools unified under one data model — Nmap ports, Subfinder subdomains, Nuclei vulns, and FlareSolverr pages all link back to the same Target |
| AI analysis is bolted on | AI is **first-class** — agents own the orchestration loop, not a post-scan afterthought |
| Context gets lost | Agent-driven memory compression (`review_chunks → decide_chunk → apply_compression`) preserves strategic awareness across sessions |
| No traceability | `ExecutionGraph → Node → Event → Artifact` 4-level hierarchy captures every tool call, LLM token, and state transition |
| Vulnerabilities lack intelligence | CVE Intelligence auto-enriches findings with NVD/CISA KEV/EPSS scoring — know what matters before you triage |

---

## Core Highlights / 核心亮點

### 1. Three-Tier AI Agent Architecture / 三層 AI Agent

Agents aren't chatbots bolted onto a scanner. They are **native LangGraph state machines** that own the security workflow.

```
┌─────────────────────────────────────────────────────┐
│  AutomationAgent (Layer 3 Orchestrator)              │
│  ── plans, delegates, synthesizes                    │
│  ── decides: self-execute or spawn sub-agent         │
├─────────────────────────────────────────────────────┤
│  ReconAgent         PostExploitAgent  ReportingAgent │
│  ── subdomain enum  ── lateral move   ── structured  │
│  ── port scan       ── credential      report gen    │
│  ── tech detect     harvesting        mark COMPLETED │
│  ── URL discovery                                    │
└─────────────────────────────────────────────────────┘
```

- **Orchestrator** (`apps/auto/assistants/planning_agent.py`): Uses LangGraph `StateGraph` with nodes: `setup → history → context_check → retriever → agent → (tool_selector → execute_tools → compress_tool_outputs → loop) | respond → END`
- **Sub-agents** (`apps/auto/agents/`): Spawned via Celery, report back via `notify_caller_agent()`
- **Dynamic tool loading**: CAI system (`apps/auto/cai/`) auto-discovers Django Ninja API endpoints and exposes them as LangChain `StructuredTool`s

### 2. Agent-Driven Memory Compression / 記憶壓縮

LLM context windows fill fast during long-running pentests. SKRpyASM's agents **self-manage** their own context using a 3-tool protocol:

```
Message threshold (40+) → review_chunks() → decide_chunk() → apply_compression()
                              │                    │
                   LLM generates           Agent chooses per chunk:
                   GlobalContextOverview    RETAIN / TEXTUALIZE / DISCARD
                   + THINK→ACT→RESULT
                   chunk division
```

- **Never deletes data**: `Message.compressed_content` is set, original is preserved
- **GlobalContextOverview** is auto-injected into the system prompt on next conversation via the `setup` LangGraph node
- Compression uses a **cheap LLM** (`mistral-small` recommended), keeping the main agent budget for strategy
- Auto-compression: tool outputs >2500 chars are transparently saved to `ContentBlob` with LLM-generated summary

### 3. ExecutionGraph — Full-Stack Traceability / 全鏈路追蹤

Every action—an LLM token stream, a tool execution, a scanner dispatch, a Celery task—is captured in a 4-level hierarchical event model:

```
ExecutionGraph         (run container, FK to Thread)
  └── ExecutionNode    (a step: LLM call, tool exec, scanner task)
       └── ExecutionEvent   (immutable, append-only event log)
            └── ExecutionArtifact  (output data: scan results, HTTP traces, notes)
```

- **Monotonically increasing sequences** per graph — enables exact-resume SSE streaming
- **Reconciliation**: `ExecutionService.reconcile_graph_status()` auto-derives graph status from child node states
- **Frontend**: `ExecutionTimelineViewer` with real-time SSE, auto-reconnect with exponential backoff, event deduplication
- **API**: `GET /api/core/executions/` with `target_id`/`thread_id`/`status` filters

### 4. CVE Intelligence System / CVE 情報系統

Multi-source vulnerability enrichment that **closes the gap** between scanner output and actionable intelligence:

```
NVD API 2.0 ─┐
CISA KEV   ──┼── CVEEnrichmentService (3-layer cache: DB → Redis → API) → CVEIntelligence
EPSS API   ──┘
                     │
                     ├── TechStackCVEMapping (version-aware CPE matching)
                     ├── Composite Risk Score (CVSS 0-50 + EPSS 0-20 + KEV +20 + exploit +10)
                     └── Auto-triggered after Nuclei scans + URL TechStack discovery
```

- 7 API endpoints at `/api/scanners/cve/`: query, search, tech-stack report, batch enrichment, KEV sync
- AI agents can query CVE intelligence via `CVEIntelligenceMixin` tools
- Scheduled daily CISA KEV sync with auto-TechStack impact check

### 5. Unified Scanner Workflow / 統一掃描調度

```text
Target
  ├── Subfinder / Amass ──→ Subdomains → dnsx/httpx resolution
  ├── Nmap ────────────────→ Ports + Services + Versions
  ├── Nuclei ──────────────→ Vulnerabilities + TechStack + CVE enrichment
  ├── GAU / Katana ────────→ URLs + Page assets
  └── FlareSolverr ────────→ Anti-bot protected page content
```

All routed through a unified `Scenario` framework (`apps/scanners/base_task.py`) with `ScannerLifecycle` context manager for PENDING→RUNNING→COMPLETED/FAILED state management.

### 6. SSE Real-Time Streaming / 即時串流

Three SSE streaming endpoints, all resumable:

| Endpoint | Streams | Resume |
|----------|---------|--------|
| `/api/assistant/threads/{id}/messages/stream/` | LLM tokens | — |
| `/api/assistant/threads/{id}/events/stream/` | Thread-level events | `last_sequence` |
| `/api/core/executions/{id}/events/stream/` | Execution events | `last_sequence` + `Last-Event-ID` |

---

## Architecture / 技術架構

```text
┌──────────────────────────────────────────────────────────────────┐
│                       Frontend (React 19 + Vite 7)                │
│  Hasura GraphQL (subscriptions)   Axios (REST)   SSE (events)    │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                   Django Ninja API (/api/)                        │
│  targets │ scanners │ flaresolverr │ core │ analyze_ai            │
│  scheduler │ http_sender │ api_keys │ assistant                  │
└────┬──────────────────────────────────────────────────┬──────────┘
     │                                                  │
┌────▼──────────┐                            ┌──────────▼──────────┐
│  PostgreSQL   │                            │   Celery Workers     │
│  Core Models  │                            │  ┌─────────────────┐ │
│  ScanRecords  │                            │  │ LangGraph Agents│ │
│  CVEIntell.   │◄──────────── Redis ────────►  │ Nmap/Sbf/Nuclei│ │
│  Execution    │                            │  │ CVE Enrichment  │ │
│  Messages     │                            │  │ Scheduler/Watch │ │
└───────────────┘                            └──────────────────────┘
```

| Layer | Stack |
|-------|-------|
| Backend | Django 5.2, Django Ninja 1.4, DRF 3.16 |
| AI / Agent | LangChain, LangGraph, OpenAI, Anthropic, Mistral, LiteLLM |
| Async / Queue | Celery 5.5, django-celery-beat 2.8, Redis |
| Database | PostgreSQL 14 |
| Frontend | React 19.1, TypeScript 5.8, Vite 7 |
| Data / API Tools | Hasura GraphQL, NocoDB, Django Admin |
| Security Tools | Nmap, Subfinder, Amass, dnsx, httpx, naabu, Nuclei, wafw00f, GAU, Katana, ffuf |
| Anti-Bot | FlareSolverr, FlareProxyGo |

---

## Quick Start / 快速啟動

**Prerequisites**: Python 3.10, Docker + Compose, Node.js 18+

```bash
# 1. Infrastructure (PostgreSQL, Redis, Hasura, FlareSolverr...)
cd docker && docker compose up -d && cd ..

# 2. Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # review DB credentials + AI provider keys
python manage.py migrate
uvicorn c2_core.asgi:application --host 0.0.0.0 --port 8000 --reload

# 3. In separate terminals:
celery -A c2_core worker -P prefork -c 8 -l info
celery -A c2_core beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# 4. Frontend
cd frontend && npm install && npm run dev
```

Full deployment guide: [docs/BUILD_GUIDE.md](docs/BUILD_GUIDE.md)

---

## API Map / API 路由

| Prefix | Module | Purpose |
|--------|--------|---------|
| `/api/targets/` | `apps.targets` | Target & seed CRUD |
| `/api/scanners/nmap` | `apps.scanners.nmap_scanner` | Nmap dispatch & results |
| `/api/scanners/subdomain` | `apps.scanners.subfinder` | Subfinder / Amass workflows |
| `/api/scanners/vuln` | `apps.scanners.nuclei_scanner` | Nuclei vuln & tech scans |
| `/api/scanners/crawler` | `apps.scanners.get_all_url` | URL discovery |
| `/api/scanners/cve` | `apps.scanners.cve_intelligence` | CVE intelligence query & enrichment |
| `/api/flaresolverr/` | `apps.flaresolverr` | Anti-bot page crawling |
| `/api/core/` | `apps.core` | Overviews, executions, events |
| `/api/analyze_ai/` | `apps.analyze_ai` | AI triage entrypoint |
| `/api/scheduler/` | `apps.scheduler` | Periodic schedule management |
| `/api/http_sender/` | `apps.http_sender` | Endpoint fuzzing |
| `/api/api_keys/` | `apps.api_keys` | API key & agent LLM config |
| `/api/assistant/` | `apps.ai_assistant` | Threads / messages / SSE streaming |

---

## Service Ports / 服務入口

| Service | URL |
|---------|-----|
| Frontend | `http://127.0.0.1:5173` |
| Django API | `http://127.0.0.1:8000/api/` |
| Django Admin | `http://127.0.0.1:8000/admin/` |
| Hasura Console | `http://127.0.0.1:8085` |
| NocoDB | `http://127.0.0.1:8081` |
| FlareSolverr | `http://127.0.0.1:8191` |

---

## Documentation / 文檔

| Document | Content |
|----------|---------|
| [SKRpyASM_技術白皮書.md](SKRpyASM_技術白皮書.md) | 完整技術白皮書（4000+ 行）：架構、Agent 設計、API 映射 |
| [docs/BUILD_GUIDE.md](docs/BUILD_GUIDE.md) | 環境配置與部署 |
| [docs/CVE_API_GUIDE.md](docs/CVE_API_GUIDE.md) | CVE Intelligence REST API |
| [docs/ai_assistant.md](docs/ai_assistant.md) | Assistant/SSE 介面 |
| [docs/auto.md](docs/auto.md) | 自動化框架 |
| [docs/README.md](docs/README.md) | 完整文檔索引 |

---

## Legal Notice / 合法授權使用聲明

**For educational, research, and authorized security testing only.**

本工具僅限教育研究、受控環境測試，以及已取得明確授權的安全測試。使用者必須自行承擔部署與操作本工具所產生的所有責任。The software is provided "as is", without warranty of any kind.

---

## License

See [LICENSE](LICENSE). Contact the repository owner before redistribution or production use.

---

## Contributing / 開發規範

- Keep changes small and focused. Preserve bilingual patterns.
- Use Celery for long-running tasks. Use Django transactions for bulk DB writes.
- Review [CLAUDE.md](CLAUDE.md) before larger changes — it contains the full architecture reference.
- New Celery tasks must be added to `CELERY_IMPORTS` in `c2_core/settings.py`.
- API schemas use Pydantic v2 (`.model_dump()`, never `.dict()`).
