# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SKRpyASM is an authorized attack-surface management and AI-assisted security workflow platform. Django 5.2 backend + React 19 frontend + Celery task queue + PostgreSQL + Redis. Integrates security tools (Nmap, Subfinder, Nuclei, FlareSolverr) and AI providers (OpenAI, Anthropic, Mistral) via LangChain.

Code comments throughout the codebase are in Chinese (Traditional/Simplified).

## Development Commands

### Docker-first Development

This project follows a **Docker-first development workflow**.

Docker Compose is the primary environment for running application services.

The Makefile is the canonical interface for:

- starting/stopping services
- rebuilding containers
- migrations
- backend checks
- tests
- logs
- environment management

Available commands:

```bash
make up
make down
make logs
make ps
make rebuild
make migrate
make shell
make check
make test
make smoke
make clean
Backend

Backend runtime services must run through Docker Compose.

Use Makefile commands:

make up
make migrate
make check
make test

Do not start backend services directly on the host machine:

uvicorn
celery
python manage.py runserver

unless explicitly debugging the local environment.

Frontend

Frontend runtime is Docker-based.

The frontend application should normally run through Docker Compose.

However, lightweight local developer tools are allowed when they do not replace the container runtime.

Examples:

Allowed:

npx tsc --noEmit
npm run lint

or other static checks.

Not preferred:

npm run dev
npm run start

because the development runtime should remain consistent with Docker.

Local Tools vs Runtime

Rule:

Application services → Docker Compose
Infrastructure → Docker Compose
Database / Redis / Celery → Docker Compose
Static analysis tools → local execution allowed

Examples:

Task	Preferred
Start Django	make up
Run Celery	Docker Compose
Database migration	make migrate
Backend tests	make test
API smoke test	make smoke
TypeScript check	npx tsc --noEmit
ESLint	npm run lint


### Testing Workflow (API-First)

When debugging, testing, or verifying behavior, **always prefer the REST API over `docker exec` + Django shell**. It is simpler, faster, and double-tests the API layer.

```bash
# Check state via API (no auth required)
curl -s http://localhost:8000/api/core/overviews/                # list all overviews
curl -s "http://localhost:8000/api/core/overviews?target_id=62"  # filter by target
curl -s "http://localhost:8000/api/core/attack-plans?target_id=62"  # attack plans for target
curl -s http://localhost:8000/api/assistant/threads/             # thread history
curl -s "http://localhost:8000/api/core/executions?target_id=62" # execution graphs
curl -s http://localhost:8000/api/scheduler/                     # periodic tasks

# Trigger automation forward progress (when stalled)
curl -s -X PATCH http://localhost:8000/api/core/overviews/{id} \
  -H 'Content-Type: application/json' \
  -d '{"status": "PLANNING"}'   # resets to PLANNING so auto_execute_plan picks it up

# Trigger directly via Django shell only as absolute last resort
docker exec c2_django python manage.py shell -c "from apps.auto.tasks import auto_execute_plan; auto_execute_plan()"
```

**Anti-pattern**: Do NOT `docker exec` + Django shell for routine state checks or testing. Use curl + API first.

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
| `/api/assistant/` | `apps.ai_assistant.urls` (Django URLconf, not Ninja) | Threads/messages + SSE streaming |

Each app's router is defined in its `api.py` using Django Ninja's `Router` class. Exception: `ai_assistant` uses its own Django URLconf with both Ninja REST and SSE streaming endpoints.

### App Responsibilities

- **core**: Central models (Target, Seed, Subdomain, Port, Vulnerability, URLResult, NmapScan, SubfinderScan, NucleiScan, Overview, AttackVector, SkillTemplate, Verification, ExecutionGraph, ExecutionNode, ExecutionEvent, ExecutionArtifact). Heavily interconnected — check `apps/core/models/__init__.py` for exports. All scan record models (`NmapScan`, `SubfinderScan`, `NucleiScan`, `URLScan`, `AmassScan`, `SubBrute`) inherit from `ScanRecord` abstract base (`apps/core/models/scans_record_models.py`), which provides `status`, `started_at`, `completed_at`, `error_message`, `created_at`. Canonical `ErrorSchema` (field: `detail`) lives in `apps/core/schemas.py` — do not redeclare it in other apps.
- **targets**: Target/Seed CRUD APIs.
- **scanners**: Unified scanner interface. Sub-apps: `nmap_scanner`, `subfinder`, `nuclei_scanner`, `get_all_url`, `katana_scanner` — each has its own `tasks/` directory with Celery tasks.
- **flaresolverr**: FlareSolverr integration for anti-bot protected pages. Includes JS/security analysis parsers.
- **analyze_ai**: AI triage and analysis dispatch to LLM providers via LangChain.
- **auto**: 3-tier AI agent orchestration (ReconAgent, PostExploitAgent, ReportingAgent, AutomationAgent). Internal automation framework — no public REST API (legacy `apps/auto/api.py` and `/api/auto/` route fully removed). Uses LangChain or custom CAI depending on feature flags. See `apps/auto/cai_tool_implementation_guide.md`. Agent-driven memory compression via `review_chunks → decide_chunk → apply_compression` tools in `apps/auto/tools/memory_tools.py` (MemoryMixin). Configure compression LLM via `compression_agent` in AgentLLMConfig (recommend a cheap model like `mistral-small`). Default Anthropic model: `claude-sonnet-4-6` (env: `AUTO_ANTHROPIC_MODEL`).
- **scheduler**: Celery Beat periodic task management (uses `django_celery_beat` PeriodicTask/IntervalSchedule/CrontabSchedule), watchdog, cleanup). `apps/scheduler/tasks/watchdog.py` recovers stalled Overviews; `apps/scheduler/tasks/cleanup.py` removes orphaned assets. Shared `async_post_batch(url, payloads, timeout)` helper in `apps/scheduler/tasks/utils.py` — use this for all concurrent HTTP fan-out in scheduler tasks instead of local `_post_all` copies.
- **api_keys**: Encrypted storage for external service API keys.
- **http_sender**: HTTP request helpers and payload fuzzing. See `apps/http_sender/PayloadMapping.md`.
- **ai_assistant**: Assistant/Thread/Message APIs with LangChain integration. SSE streaming for real-time responses.

### Celery Task Queue

- Broker and result backend: Redis (`redis://localhost:6379/0`)
- Beat scheduler: `django_celery_beat.schedulers:DatabaseScheduler` (persistent, survives restart)
- Autodiscovery via `app.autodiscover_tasks()` plus explicit `CELERY_IMPORTS` in `c2_core/settings.py`
- Task modules that must be in `CELERY_IMPORTS`: `apps.scanners.nmap_scanner.tasks`, `apps.flaresolverr.tasks.spider`, `apps.scanners.get_all_url.tasks`, `apps.scanners.subfinder.tasks`, `apps.analyze_ai.tasks`, `apps.scanners.nuclei_scanner.tasks`, `apps.scheduler.tasks`, `apps.auto.tasks`, `apps.scanners.cve_intelligence.tasks.enrichment_tasks`, `apps.scanners.cve_intelligence.tasks.scheduled_sync`, `apps.scanners.katana_scanner.tasks`

When adding new Celery tasks, add the module path to `CELERY_IMPORTS` in `c2_core/settings.py` or they won't be discovered.

### Frontend

React 19 + TypeScript 5.8 + Vite 7. **Hasura GraphQL as the primary data layer** — custom `useHasuraQuery`/`useHasuraSubscription` hooks (via `graphql-ws`) replace Axios calls to Django CRUD endpoints for all simple database operations. Axios is reserved for Django Ninja REST endpoints that involve non-CRUD actions (scan triggers, AI analysis, SSE streaming). Key dependencies: `react-router-dom`, `react-markdown`, `graphql-ws`.

#### Frontend Copy

Do not add decorative copy that only repeats a page name, route, or information already visible in the interface. Every label, heading, and description must communicate actionable context, distinct state, or information the user cannot otherwise infer.


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

## Git Workflow

Autonomous commits are expected behavior in this repo — do not pause to ask "should I commit?" when a unit of work is complete and verified.

- **Trigger**: When a logical unit (plan checkbox, bug fix, feature) is complete and tests/checks pass.
- **Atomicity**: One commit per logical change. Never bundle unrelated changes into a single commit.
- **Style**: Conventional Commits prefixes (`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`) with Chinese descriptions — see `git log --oneline` for established patterns.
- **Scope**: Stage only files relevant to the current change. Never use `git add -A` / `git add .` in a dirty worktree — always stage explicit paths.
- **No push**: Local commits only unless explicitly asked to push to remote.
- **Hooks**: Never skip git hooks (`--no-verify`) unless explicitly requested.

## Key Patterns

- **API schemas**: Django Ninja uses Pydantic-based schemas for request/response validation (defined in each app's `schemas.py`). Always use `.model_dump()` / `.model_dump(exclude_unset=True)` (Pydantic v2) — never `.dict()`.
- **ErrorSchema**: Canonical definition is `apps/core/schemas.py` (`detail: str`). Import from there; do not redeclare in sub-apps.
- **ScanRecord base model**: All scan record models inherit from `ScanRecord` (abstract, `apps/core/models/scans_record_models.py`). It provides `status` (PENDING/RUNNING/COMPLETED/FAILED with `db_index=True`), `started_at`, `completed_at`, `error_message`, `created_at`. `URLScan` overrides `status` with English labels. `ScannerLifecycle` context manager (`apps/scanners/base_task.py`) uses these fields for the PENDING→RUNNING→COMPLETED/FAILED state machine.
- **Authentication**: DRF TokenAuthentication is the default (`REST_FRAMEWORK` in settings). CSRF middleware is disabled for dev (commented out in MIDDLEWARE).
- **Model primary keys**: `BigAutoField` as default.
- **Docker infrastructure**: `docker/docker-compose.yml` runs PostgreSQL, Redis, Hasura, NocoDB, FlareSolverr.
- **ExecutionGraph-first monitoring**: The legacy `Step`/`StepLog`/`ScriptExecution` models and `callback_step_id` parameter have been fully removed. All scan and agent execution monitoring now uses `ExecutionGraph` → `ExecutionNode` → `ExecutionEvent` → `ExecutionArtifact` (defined in `apps/core/models/execution.py`). Backend API: `/api/core/executions` (list with `target_id`/`thread_id`/`status` filters), `/api/core/executions/{id}` (detail with nodes/events/artifacts). Frontend uses `executionApi` service + `ExecutionTimelineViewer` component + `useExecutionEventStream` SSE hook. Hasura GraphQL subscriptions are limited to a single top-level field per subscription (Hasura constraint).
- **Agent-Driven Memory Compression**: The agent self-manages context via three tools in `MemoryMixin` (`apps/auto/tools/memory_tools.py`):
  1. `review_chunks()` — reads all messages, generates GlobalContextOverview via LLM, divides into THINK→ACT→RESULT chunks
  2. `decide_chunk(chunk_index, strategy)` — agent chooses RETAIN/TEXTUALIZE/DISCARD per chunk (uses `compressed_content` + `compression_applied` on Message, never deletes)
  3. `apply_compression()` — finalizes decisions, updates ThreadCompressionState
  - `compression_middleware.py` flags `requires_compression=True` when 40+ new messages since last compress
  - `assistants.py` `context_check` node warns the agent; `setup` node auto-injects GlobalContextOverview into system prompt
   - LLM configured via AgentLLMConfig `compression_agent` (recommend cheap model for summarization)

Simple database CRUD operations MUST be implemented through Hasura GraphQL, not Django backend APIs.

**Do NOT create Django Ninja CRUD endpoints** for basic data operations (list, create, update, delete, filter, paginate). Hasura auto-generates these from the database schema — adding a Ninja CRUD endpoint duplicates work and bypasses the GraphQL layer that the frontend already uses.

Use Hasura for:

- list/query records
- filtering
- pagination
- sorting
- simple create operations
- simple update operations
- simple delete operations
- relational data fetching
- frontend data synchronization

Reserve Django Ninja REST endpoints exclusively for non-CRUD actions: scan triggers, AI analysis dispatch, SSE streaming, Celery task control, and other operations with side effects beyond simple data manipulation.
