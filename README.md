# SKRpyASM

**Authorized attack-surface management and AI-assisted security workflow platform.**

SKRpyASM 是一套面向開發者與安全研究人員的資產偵察、安全掃描、AI 分析與自動化工作流平台。系統以 Django 後端、React 前端、Celery 任務隊列與 PostgreSQL 資料庫為核心，整合 Nmap、Subfinder、Nuclei、FlareSolverr 等工具，用於授權環境中的攻擊面管理與安全測試。

---

## Legal Notice / 合法授權使用聲明

**For educational, research, and authorized security testing only.**

Use this project only against systems that you own or where you have explicit written permission to test. Unauthorized scanning, exploitation, or intrusion attempts may violate applicable laws. You are solely responsible for how you deploy and operate this software.

**本工具僅限教育研究、受控環境測試，以及已取得明確授權的安全測試。**

請勿對未授權目標進行掃描、滲透或自動化測試。未經授權的網路行為可能違反相關法律。使用者必須自行承擔部署與操作本工具所產生的所有責任。

The software is provided "as is", without warranty of any kind, express or implied.

---

## What It Does / 功能概覽

SKRpyASM provides a developer-oriented workflow for collecting assets, enriching scan data, and feeding findings into AI-assisted analysis and planning loops.

SKRpyASM 提供一套從資產建立、偵察掃描、資料入庫，到 AI 輔助分析與自動化任務編排的完整流程。

- **Target and seed management / 目標與種子管理**: manage targets and seed assets such as domains, IP ranges, and URLs.
- **Subdomain discovery / 子域名枚舉**: run Subfinder and Amass workflows, then resolve and enrich discovered subdomains.
- **Network scanning / 網路掃描**: run Nmap scans for IP assets and store discovered ports, services, and versions.
- **URL discovery and crawling / URL 發現與爬取**: collect URLs and page assets for deeper analysis.
- **Vulnerability and technology scanning / 漏洞與技術棧掃描**: use Nuclei templates for vulnerability checks and technology detection.
- **Protected page handling / 受保護頁面處理**: integrate FlareSolverr and FlareProxyGo for anti-bot protected content retrieval.
- **AI-assisted analysis / AI 輔助分析**: triage assets, summarize risks, generate next-step plans, and maintain analysis context.
- **Scheduler and automation / 排程與自動化**: orchestrate recurring scan and analysis jobs through Celery and django-celery-beat.
- **Developer data access / 開發者資料存取**: use Django Ninja APIs, Django Admin, Hasura GraphQL, and NocoDB for inspection and integration.

---

## Architecture / 技術架構

| Layer | Stack |
| --- | --- |
| Backend / 後端 | Django 5.2.4, Django Ninja 1.4.5, Django REST Framework 3.16.0 |
| Async tasks / 非同步任務 | Celery 5.5.3, django-celery-beat 2.8.1, Redis |
| Database / 資料庫 | PostgreSQL 14 |
| Frontend / 前端 | React 19.1, TypeScript 5.8, Vite 7 |
| Data/API tools / 資料與 API 工具 | Hasura GraphQL, NocoDB, Django Admin |
| Security tooling / 安全工具 | Nmap, Subfinder, Amass, dnsx, httpx, naabu, Nuclei, wafw00f, GAU |
| Protected content / 受保護內容 | FlareSolverr, FlareProxyGo |
| AI / LLM | OpenAI, Anthropic, LiteLLM, LangChain, LangGraph |

### Main Runtime Flow / 主要執行流程

```text
React frontend
    -> Django Ninja API / Django Admin
        -> PostgreSQL
        -> Celery workers
            -> Nmap / Subfinder / Amass / Nuclei / FlareSolverr / AI providers
        -> Hasura GraphQL / NocoDB
```

---

## Repository Layout / 目錄結構

```text
.
├── apps/
│   ├── core/             # Shared asset, scan, URL, vulnerability, and analysis models
│   ├── targets/          # Target and seed management APIs
│   ├── scanners/         # Nmap, Subfinder, Amass, Nuclei, and URL discovery workflows
│   ├── flaresolverr/     # Protected page fetching, parsing, JS/security analysis helpers
│   ├── analyze_ai/       # AI analysis dispatch and readiness checks
│   ├── scheduler/        # Celery Beat schedules and recurring scan triggers
│   ├── auto/             # AI-assisted automation and step execution helpers
│   ├── api_keys/         # External service API key management
│   └── http_sender/      # HTTP request, fuzzing, and URL ingestion helpers
├── c2_core/              # Django project settings, ASGI app, URL routing, Celery app
├── django_ai_assistant/  # Assistant/thread/message APIs and LangChain helper tooling
├── frontend/             # React + TypeScript + Vite frontend
├── docker/               # Docker Compose infrastructure
├── docs/                 # Module-level documentation
├── scripts/              # Operational helper scripts
├── requirements.txt      # Minimal backend dependency set
├── environment.yml       # Conda environment snapshot
└── BUILD_GUIDE.md        # Extended build and deployment guide
```

---

## Prerequisites / 前置需求

- Python 3.10
- Conda, Miniconda, or another Python virtual environment manager
- Docker and Docker Compose plugin
- Node.js and npm for frontend development
- PostgreSQL and Redis through the provided Docker Compose stack
- Nmap installed locally if running local Nmap scans
- Optional external tools for full scan coverage: Subfinder, Amass, dnsx, httpx, naabu, Nuclei, wafw00f, GAU
- Optional AI provider API keys for AI-assisted analysis

Ubuntu/Debian system dependencies commonly needed by this project:

```bash
sudo apt update
sudo apt install -y build-essential python3-dev libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev libjpeg-dev libpng-dev libmagic1 libmagic-dev nmap git curl wget golang-go
```

---

## Quick Start / 快速啟動

### 1. Clone and enter the repository / 下載專案

```bash
git clone <your-skrpyasm-repository-url> SKRpyASM
cd SKRpyASM
```

If you are already inside this repository, start from the next step.

### 2. Configure environment / 設定環境變數

```bash
cp .env.example .env
```

Update `.env` before production use. At minimum, review database credentials, `DJANGO_SECRET_KEY`, `HASURA_GRAPHQL_ADMIN_SECRET`, Redis URLs, and AI provider keys.

### 3. Start infrastructure services / 啟動基礎設施

```bash
cd docker
docker compose up -d
cd ..
```

The compose stack currently starts PostgreSQL, Redis, Hasura, NocoDB, FlareSolverr, and FlareProxyGo.

### 4. Create Python environment / 建立 Python 環境

```bash
conda create -n mtc_env python=3.10 -y
conda activate mtc_env
pip install -r requirements.txt
```

For a fuller pinned environment, you may also inspect `environment.yml` or `requirements/requirements.txt`.

### 5. Initialize database / 初始化資料庫

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Run backend API / 啟動後端 API

```bash
uvicorn c2_core.asgi:application --host 0.0.0.0 --port 8000 --reload
```

### 7. Run Celery worker / 啟動 Celery Worker

Open another terminal from the repository root:

```bash
conda activate mtc_env
python scripts/celery_worker_eventlet.py -A c2_core.celery:app worker -P eventlet -c 100 -l info
```

### 8. Run Celery Beat / 啟動 Celery Beat

Open another terminal from the repository root:

```bash
conda activate mtc_env
celery -A c2_core beat -l info
```

### 9. Run frontend / 啟動前端

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

---

## Service URLs / 服務入口

| Service | URL |
| --- | --- |
| Frontend / 前端 | `http://127.0.0.1:5173` |
| Django API / 後端 API | `http://127.0.0.1:8000/api/` |
| Django Admin / 管理後台 | `http://127.0.0.1:8000/admin/` |
| Hasura Console | `http://127.0.0.1:8085` |
| NocoDB | `http://127.0.0.1:8081` |
| FlareSolverr | `http://127.0.0.1:8191` |
| Redis | `127.0.0.1:6379` |
| PostgreSQL | `127.0.0.1:5432` |

---

## Development Commands / 開發常用指令

### Backend / 後端

```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py test
python manage.py shell
```

### ASGI server / ASGI 服務

```bash
uvicorn c2_core.asgi:application --host 0.0.0.0 --port 8000 --reload
```

Production-style local command:

```bash
uvicorn c2_core.asgi:application --host 0.0.0.0 --port 8000 --workers 9 --loop uvloop --http httptools --backlog 2048 --limit-concurrency 1000
```

### Celery / 任務隊列

```bash
python scripts/celery_worker_eventlet.py -A c2_core.celery:app worker -P eventlet -c 100 -l info
celery -A c2_core beat -l info
celery -A c2_core inspect active
celery -A c2_core inspect stats
```

### Frontend / 前端

```bash
cd frontend
npm run dev
npm run build
npm run lint
npm run preview
```

### Docker / 基礎設施

```bash
cd docker
docker compose ps
docker compose logs -f
docker compose down
```

---

## API and Module Map / API 與模組對照

The central API is mounted under `/api/` in `c2_core/urls.py`.

| API prefix | Module | Responsibility |
| --- | --- | --- |
| `/api/targets` | `apps.targets` | Target and seed CRUD |
| `/api/scanners/nmap` | `apps.scanners.nmap_scanner` | Nmap scan dispatch and results |
| `/api/scanners/subdomain` | `apps.scanners.subfinder` | Subfinder and Amass workflows |
| `/api/scanners/vuln` | `apps.scanners.nuclei_scanner` | Nuclei vulnerability and technology scans |
| `/api/scanners/crawler` | `apps.scanners.get_all_url` | URL discovery and ingestion |
| `/api/flaresolverr` | `apps.flaresolverr` | Protected page retrieval and parsing |
| `/api/analyze_ai` | `apps.analyze_ai` | AI analysis dispatch |
| `/api/scheduler` | `apps.scheduler` | Schedule and trigger management |
| `/api/http_sender` | `apps.http_sender` | HTTP sender and fuzzing helpers |
| `/api/api_keys` | `apps.api_keys` | External API key management |
| `/api/auto` | `apps.auto` | AI-assisted automation step execution |
| `/api/assistant` | `django_ai_assistant` | Assistant and thread APIs |

---

## Configuration / 設定說明

Start from `.env.example`:

```bash
cp .env.example .env
```

Important configuration groups:

- **Database / 資料庫**: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- **Django / 後端**: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_SETTINGS_MODULE`
- **Redis and Celery / 任務隊列**: `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- **Hasura / GraphQL**: `HASURA_GRAPHQL_ADMIN_SECRET`, `HASURA_GRAPHQL_DATABASE_URL`
- **AI providers / AI 服務**: `GEMINI_API_KEY`, `MISTRAL_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- **LangChain and automation / 自動化功能**: `AUTO_USE_LANGCHAIN`, `AUTO_USE_LANGSMITH_TRACING`, `AUTO_DEFAULT_LLM_PROVIDER`
- **Scanner tuning / 掃描設定**: `NMAP_OPTIONS`, `NMAP_TIMEOUT`, `SUBFINDER_TIMEOUT`, `NUCLEI_TEMPLATES_PATH`

Development caveat: some credentials and local defaults are still hardcoded in `docker/docker-compose.yml` and Django settings. Treat the provided values as development defaults only and review them before deploying to shared or production environments.

---

## Testing / 測試

The basic backend verification flow is:

```bash
cd docker
docker compose up -d
cd ..
python manage.py check
python manage.py migrate
python manage.py test
```

If your environment includes pytest dependencies, you can also run:

```bash
pytest
pytest -v
```

Frontend checks:

```bash
cd frontend
npm run build
npm run lint
```

---

## Documentation / 文件索引

- [Build Guide](BUILD_GUIDE.md): extended installation, deployment, and operations notes.
- [Documentation Center](docs/README.md): module-level documentation index.
- [Internal Workflow](docs/internal_workflow.md): asset discovery, AI triage, planning, and execution loop.
- [Core Models](docs/core.md): shared model layer and asset structures.
- [Targets](docs/targets.md): target and seed management.
- [Subfinder](docs/subfinder.md): subdomain discovery workflows.
- [Nmap Scanner](docs/nmap_scanner.md): network scan workflows.
- [Get All URL](docs/get_all_url.md): URL discovery and endpoint mapping.
- [FlareSolverr](docs/flaresolverr.md): protected content retrieval and parsing.
- [Nuclei Scanner](docs/nuclei_scanner.md): vulnerability and technology scanning.
- [Analyze AI](docs/analyze_ai.md): AI analysis pipeline.
- [Scheduler](docs/scheduler.md): periodic task orchestration.
- [Auto Tasks](docs/auto_tasks.md): automation and AI planning tasks.
- [API Keys](docs/api_keys.md): external service key management.
- [HTTP Sender Payload Mapping](apps/http_sender/PayloadMapping.md): HTTP/fuzzing payload reference.

Developer guidance:

- [AGENTS.md](AGENTS.md): English development guide and repository conventions.
- [AGENTS_ZH.md](AGENTS_ZH.md): Chinese development guide.

---

## Known Limitations / 已知限制

- The repository is under active development, and some documentation may reference older app paths or route names.
- `.env.example`, Django settings, and `docker/docker-compose.yml` are not fully unified yet; review hardcoded development values before deployment.
- The Docker Compose stack does not currently include every tool mentioned in extended architecture docs.
- Some advanced automation and AI planning concepts are still evolving across `apps.auto`, `apps.analyze_ai`, and `apps.core`.
- External security tools must be installed and configured separately unless a workflow explicitly runs them through Docker.
- Only run scanners against authorized targets.

---

## FAQ / 常見問題

### Where should I run Docker Compose? / Docker Compose 要在哪裡執行？

Run it from the `docker/` directory:

```bash
cd docker
docker compose up -d
```

Or from the repository root:

```bash
docker compose -f docker/docker-compose.yml up -d
```

### Which frontend port should I use? / 前端使用哪個 port？

Vite defaults to `http://127.0.0.1:5173`. Use that unless you explicitly configure another port.

### Are AI API keys required? / AI API keys 是必填嗎？

They are required for AI-assisted analysis features, but non-AI workflows such as target management and some scanner flows can be developed without them.

### Can I scan third-party targets? / 可以掃描第三方目標嗎？

Only if you have explicit authorization. Do not scan systems you do not own or administer without written permission.

### Why do some docs mention different paths? / 為什麼部分文件提到不同路徑？

Some docs predate the current `apps/scanners/` layout. Prefer the route map in this README and the current source code when behavior differs.

---

## Contributing / 開發規範

- Keep changes small and focused.
- Preserve existing bilingual comments where present.
- Prefer Django transactions for bulk database writes.
- Add `related_name` and `help_text` for Django relationships and fields when adding models.
- Use Celery for long-running scanning, crawling, and AI analysis tasks.
- Keep API schemas explicit and validate request/response payloads.
- Review [AGENTS.md](AGENTS.md) and [AGENTS_ZH.md](AGENTS_ZH.md) before making larger changes.

---

## License / 授權

See [LICENSE](LICENSE). Contact the repository owner before redistribution or production use if you need additional licensing clarification.

