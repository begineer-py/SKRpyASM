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
| `/api/core/` | `apps.core.api`, `step_api`, `overview_api` | Core models, steps, overviews |
| `/api/analyze_ai/` | `apps.analyze_ai.api` | AI analysis dispatch |
| `/api/scheduler/` | `apps.scheduler.api` | Celery Beat schedules |
| `/api/http_sender/` | `apps.http_sender.api` | HTTP requests and fuzzing |
| `/api/api_keys/` | `apps.api_keys.api` | API key management |
| `/api/auto/` | `apps.auto.api` | AI agent orchestration |
| `/api/assistant/` | `apps.ai_assistant.urls` (Django URLconf, not Ninja) | Threads/messages + SSE streaming |

Each app's router is defined in its `api.py` using Django Ninja's `Router` class. Exception: `ai_assistant` uses its own Django URLconf with both Ninja REST and SSE streaming endpoints.

### App Responsibilities

- **core**: Central models (Target, Seed, Subdomain, Port, Vulnerability, URLResult, NmapScan, SubfinderScan, NucleiScan, Overview, Step, AttackVector, SkillTemplate). Heavily interconnected — check `apps/core/models/__init__.py` for exports.
- **targets**: Target/Seed CRUD APIs.
- **scanners**: Unified scanner interface. Sub-apps: `nmap_scanner`, `subfinder`, `nuclei_scanner`, `get_all_url` — each has its own `tasks/` directory with Celery tasks.
- **flaresolverr**: FlareSolverr/FlareProxyGo integration for anti-bot protected pages. Includes JS/security analysis parsers.
- **analyze_ai**: AI triage and analysis dispatch to LLM providers via LangChain.
- **auto**: 3-tier AI agent orchestration (ReconAgent, ExploitAgent, StrategyAgent). Uses LangChain or custom CAI depending on feature flags. See `apps/auto/cai_tool_implementation_guide.md`.
- **scheduler**: Celery Beat periodic task management (ScheduleDefinition, ScheduleLog).
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

Note: `c2_core/settings.py` has hardcoded fallback values for database credentials (`mydb`/`myuser`/`secret`) used in development.

## Key Patterns

- **API schemas**: Django Ninja uses Pydantic-based schemas for request/response validation (defined in each app's `schemas.py`).
- **Authentication**: DRF TokenAuthentication is the default (`REST_FRAMEWORK` in settings). CSRF middleware is disabled for dev (commented out in MIDDLEWARE).
- **Model primary keys**: `BigAutoField` as default.
- **Docker infrastructure**: `docker/docker-compose.yml` runs PostgreSQL, Redis, Hasura, NocoDB, FlareSolverr, FlareProxyGo.
