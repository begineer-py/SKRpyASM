# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SKRpyASM is an authorized attack-surface management and AI-assisted security workflow platform. Django 5.2 backend + React 19 frontend + Celery task queue + PostgreSQL + Redis. Integrates security tools (Nmap, Subfinder, Nuclei, FlareSolverr) and AI providers (OpenAI, Anthropic, Mistral) via LangChain.

Code comments throughout the codebase are in Chinese (Traditional/Simplified).

## Development Commands

### Backend
```bash
# Start infrastructure
cd docker && docker compose up -d && cd ..

# Django server (ASGI)
uvicorn c2_core.asgi:application --host 0.0.0.0 --port 8000 --reload

# Celery worker
celery -A c2_core worker -P prefork -c 8 -l info

# Celery Beat scheduler
celery -A c2_core beat -l info

# Migrations
python manage.py makemigrations
python manage.py migrate

# Tests
python manage.py test
pytest
pytest apps/scanners/nmap_scanner/tests.py -v   # single app tests

# Project check
python manage.py check
```

### Frontend
```bash
cd frontend
npm install
npm run dev       # Vite dev server on port 5173
npm run build     # tsc + vite build
npm run lint      # ESLint
```

### CI
GitHub Actions (`.github/workflows/ci.yml`): starts Docker Compose, runs `manage.py check`, `migrate`, and `test`.

## Architecture

### API Routing (Django Ninja)

All API routes registered in `c2_core/urls.py` via a single `NinjaAPI` instance at `/api/`:

| Prefix | Router source | Purpose |
|--------|--------------|---------|
| `/api/targets/` | `apps.targets.api` | Target and seed CRUD |
| `/api/scanners/` | `apps.scanners.api` | Unified scan dispatch |
| `/api/flaresolverr/` | `apps.flaresolverr.api` | Anti-bot bypass |
| `/api/core/` | `apps.core.api`, `overview_api` | Core models, executions, overviews |
| `/api/analyze_ai/` | `apps.analyze_ai.api` | AI analysis dispatch |
| `/api/scheduler/` | `apps.scheduler.api` | Celery Beat schedules |
| `/api/http_sender/` | `apps.http_sender.api` | HTTP requests and fuzzing |
| `/api/api_keys/` | `apps.api_keys.api` | API key management |
| `/api/auto/` | `apps.auto.api` | AI agent orchestration |
| `/api/assistant/` | `apps.ai_assistant.urls` (Django URLconf, not Ninja) | Threads/messages + SSE streaming |

Each app's router is defined in its `api.py` using Django Ninja's `Router` class. Exception: `ai_assistant` uses its own Django URLconf with both Ninja REST and SSE streaming endpoints.

### App Responsibilities

- **core**: Central models (Target, Seed, Subdomain, Port, Vulnerability, URLResult, NmapScan, SubfinderScan, NucleiScan, Overview, AttackVector, SkillTemplate, Verification, ExecutionGraph, ExecutionNode, ExecutionEvent, ExecutionArtifact). Heavily interconnected — check `apps/core/models/__init__.py` for exports. All scan record models (`NmapScan`, `SubfinderScan`, `NucleiScan`, `URLScan`, `AmassScan`, `SubBrute`) inherit from `ScanRecord` abstract base (`apps/core/models/scans_record_models.py`), which provides `status`, `started_at`, `completed_at`, `error_message`, `created_at`. Canonical `ErrorSchema` (field: `detail`) lives in `apps/core/schemas.py` — do not redeclare it in other apps.
- **targets**: Target/Seed CRUD APIs.
- **scanners**: Unified scanner interface. Sub-apps: `nmap_scanner`, `subfinder`, `nuclei_scanner`, `get_all_url` — each has its own `tasks/` directory with Celery tasks.
- **flaresolverr**: FlareSolverr/FlareProxyGo integration for anti-bot protected pages. Includes JS/security analysis parsers.
- **analyze_ai**: AI triage and analysis dispatch to LLM providers via LangChain.
- **auto**: 3-tier AI agent orchestration (ReconAgent, ExploitAgent, StrategyAgent). Uses LangChain or custom CAI depending on feature flags. See `apps/auto/cai_tool_implementation_guide.md`. Agent-driven memory compression via `review_chunks → decide_chunk → apply_compression` tools in `apps/auto/tools/memory_tools.py` (MemoryMixin). Configure compression LLM via `compression_agent` in AgentLLMConfig (recommend a cheap model like `mistral-small`). Default Anthropic model: `claude-sonnet-4-6` (env: `AUTO_ANTHROPIC_MODEL`).
- **scheduler**: Celery Beat periodic task management (ScheduleDefinition, ScheduleLog, watchdog, cleanup). `apps/scheduler/tasks/watchdog.py` recovers stalled Overviews; `apps/scheduler/tasks/cleanup.py` removes orphaned assets. Shared `async_post_batch(url, payloads, timeout)` helper in `apps/scheduler/tasks/utils.py` — use this for all concurrent HTTP fan-out in scheduler tasks instead of local `_post_all` copies.
- **api_keys**: Encrypted storage for external service API keys.
- **http_sender**: HTTP request helpers and payload fuzzing. See `apps/http_sender/PayloadMapping.md`.
- **ai_assistant**: Assistant/Thread/Message APIs with LangChain integration. SSE streaming for real-time responses.

### Celery Task Queue

- Broker and result backend: Redis (`redis://localhost:6379/0`)
- Beat scheduler: `django_celery_beat.schedulers:DatabaseScheduler` (persistent, survives restart)
- Autodiscovery via `app.autodiscover_tasks()` plus explicit `CELERY_IMPORTS` in `c2_core/settings.py`
- Task modules that must be in `CELERY_IMPORTS`: `apps.scanners.nmap_scanner.tasks`, `apps.flaresolverr.tasks.spider`, `apps.scanners.get_all_url.tasks`, `apps.scanners.subfinder.tasks`, `apps.analyze_ai.tasks`, `apps.scanners.nuclei_scanner.tasks`, `apps.scheduler.tasks`, `apps.auto.tasks`

When adding new Celery tasks, add the module path to `CELERY_IMPORTS` in `c2_core/settings.py` or they won't be discovered.

### Frontend

React 19 + TypeScript 5.8 + Vite 7. Apollo Client for Hasura GraphQL, Axios for Django Ninja REST. Key dependencies: `react-router-dom`, `react-markdown`, `graphql-ws`.

### Logging

Rich console handler + RotatingFileHandler. Logs to `c2_core/logs/` (app.log, error.log). Per-app loggers configured in `c2_core/settings.py` LOGGING dict. `analyze_ai`, `nuclei_scanner`, and `auto` loggers are at DEBUG level; others at INFO.

## Environment

Copy `.env.example` to `.env`. Key variable groups:
- Database: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- Django: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`
- Redis/Celery: `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- AI providers: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `MISTRAL_API_KEY`
- LangChain tracing: `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT` (optional LangSmith)
- Auto app flags: `AUTO_USE_LANGCHAIN`, `AUTO_DEFAULT_LLM_PROVIDER`, `AUTO_*_MODEL`
- Memory compression: configure `compression_agent` via AgentLLMConfig DB (cheap model recommended for summarization)

Note: `c2_core/settings.py` has hardcoded fallback values for database credentials (`mydb`/`myuser`/`secret`) used in development.

## Key Patterns

- **API schemas**: Django Ninja uses Pydantic-based schemas for request/response validation (defined in each app's `schemas.py`). Always use `.model_dump()` / `.model_dump(exclude_unset=True)` (Pydantic v2) — never `.dict()`.
- **ErrorSchema**: Canonical definition is `apps/core/schemas.py` (`detail: str`). Import from there; do not redeclare in sub-apps.
- **ScanRecord base model**: All scan record models inherit from `ScanRecord` (abstract, `apps/core/models/scans_record_models.py`). It provides `status` (PENDING/RUNNING/COMPLETED/FAILED with `db_index=True`), `started_at`, `completed_at`, `error_message`, `created_at`. `URLScan` overrides `status` with English labels. `ScannerLifecycle` context manager (`apps/scanners/base_task.py`) uses these fields for the PENDING→RUNNING→COMPLETED/FAILED state machine.
- **Authentication**: DRF TokenAuthentication is the default (`REST_FRAMEWORK` in settings). CSRF middleware is disabled for dev (commented out in MIDDLEWARE).
- **Model primary keys**: `BigAutoField` as default.
- **Docker infrastructure**: `docker/docker-compose.yml` runs PostgreSQL, Redis, Hasura, NocoDB, FlareSolverr, FlareProxyGo.
- **ExecutionGraph-first monitoring**: The legacy `Step`/`StepLog`/`ScriptExecution` models and `callback_step_id` parameter have been fully removed. All scan and agent execution monitoring now uses `ExecutionGraph` → `ExecutionNode` → `ExecutionEvent` → `ExecutionArtifact` (defined in `apps/core/models/execution.py`). Backend API: `/api/core/executions` (list with `target_id`/`thread_id`/`status` filters), `/api/core/executions/{id}` (detail with nodes/events/artifacts). Frontend uses `executionApi` service + `ExecutionTimelineViewer` component + `useExecutionEventStream` SSE hook. Hasura GraphQL subscriptions are limited to a single top-level field per subscription (Hasura constraint).
- **Agent-Driven Memory Compression**: The agent self-manages context via three tools in `MemoryMixin` (`apps/auto/tools/memory_tools.py`):
  1. `review_chunks()` — reads all messages, generates GlobalContextOverview via LLM, divides into THINK→ACT→RESULT chunks
  2. `decide_chunk(chunk_index, strategy)` — agent chooses RETAIN/TEXTUALIZE/DISCARD per chunk (uses `compressed_content` + `compression_applied` on Message, never deletes)
  3. `apply_compression()` — finalizes decisions, updates ThreadCompressionState
  - `compression_middleware.py` flags `requires_compression=True` when 40+ new messages since last compress
  - `assistants.py` `context_check` node warns the agent; `setup` node auto-injects GlobalContextOverview into system prompt
  - LLM configured via AgentLLMConfig `compression_agent` (recommend cheap model for summarization)
