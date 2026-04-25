# AGENTS.md - C2 Django AI Development Guide

## Project Overview

**C2 Django AI** is a comprehensive cybersecurity scanning and penetration testing platform with AI-driven analysis capabilities. The system uses Django 5.2.4 backend with Django Ninja REST API framework, Celery task queue with Redis, PostgreSQL database, and integrates multiple security tools (Nmap, Subfinder, Nuclei, FlareSolverr).

**Tech Stack**: Django 5.2.4, Django Ninja, Django REST Framework, Celery 5.5.3, Redis, PostgreSQL, React (frontend), Docker, Uvicorn, pytest

**Key Features**: Asset discovery, subdomain enumeration, port scanning, vulnerability scanning, AI-powered attack planning, continuous monitoring

---

## Build, Test & Run Commands

### Environment Setup

```bash
# Create conda environment
conda create -n mtc_env python=3.10 -y
conda activate mtc_env

# Install dependencies
pip install -r requirements.txt

# Start infrastructure services (PostgreSQL, Redis, Hasura, etc.)
cd docker && docker compose up -d && cd ..
```

### Database Operations

```bash
# Run all migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Generate new migration after model changes
python manage.py makemigrations

# Check migration status
python manage.py showmigrations

# Access Django shell
python manage.py shell
```

### Running Services

```bash
# Run Django development server (Uvicorn)
uvicorn c2_core.asgi:application --host 0.0.0.0 --port 8000 --reload

# Production-grade Uvicorn with optimizations
uvicorn c2_core.asgi:application --host 0.0.0.0 --port 8000 --workers 9 --loop uvloop --http httptools --backlog 2048 --limit-concurrency 1000

# Run Celery worker with eventlet (for async tasks)
python scripts/celery_worker_eventlet.py -A c2_core.celery:app worker -P eventlet -c 100 -l info

# Run Celery beat scheduler (for periodic tasks)
celery -A c2_core beat -l info

# Monitor Celery tasks
celery -A c2_core inspect active
celery -A c2_core inspect stats
```

### Testing

```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test apps.core

# Run with pytest (if configured)
pytest

# Run specific test file
pytest apps/subfinder/tests/test_performance.py

# Run specific test class
pytest apps/subfinder/tests/test_performance.py::SubfinderUtilsTest

# Run specific test method
pytest apps/subfinder/tests/test_performance.py::SubfinderUtilsTest::test_performance_10000_subdomains

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=apps --cov-report=html
```

### Linting & Code Quality

```bash
# Check Python code style (if configured)
# Note: This project doesn't have explicit linters configured yet
# Consider adding: black, flake8, ruff, isort

# Manual code checks
python manage.py check
python manage.py check --deploy  # Production readiness checks
```

---

## Code Style Guidelines

### Import Organization

**Order**: Standard library → Django → Third-party → Local apps

```python
# Standard library
import os
import sys
import json
import logging
from typing import Optional, List, Dict
from datetime import datetime

# Django imports
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

# Third-party
from celery import shared_task
import requests
from pydantic import BaseModel

# Local imports
from c2_core.config.logging import log_function_call
from apps.core.models import Target, Seed, Subdomain
```

**Special Import Pattern**: Use `from __future__ import annotations` for modern type hints when needed.

### Formatting Standards

- **Indentation**: 4 spaces (no tabs)
- **Line Length**: ~120 characters (flexible, but keep readable)
- **Comments**: Bilingual - Chinese comments are standard and should be preserved
- **Strings**: Double quotes preferred for consistency
- **Docstrings**: Triple double-quotes with descriptive Chinese/English

```python
class Target(models.Model):
    """
    目標（Target）項目，代表一個正在監控或掃描的專案、組織或客戶。
    Target project representing a monitored organization or customer.
    """
    
    name = models.CharField(
        max_length=255, 
        unique=True, 
        help_text="專案或組織的顯示名稱，如 'Google'"
    )
```

### Type Hints & Annotations

Use type hints consistently, especially for function signatures:

```python
from typing import Optional, List, Dict, Any

def update_subdomain_assets(
    seed: Seed, 
    subdomain_map: Dict[str, set], 
    scan: SubfinderScan
) -> Dict[str, int]:
    """Process subdomain discovery results."""
    pass

async def fetch_data(url: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
    """Async data fetching with timeout."""
    pass
```

Use Pydantic for schema validation:

```python
from pydantic import BaseModel

class TargetSchema(BaseModel):
    name: str
    description: Optional[str] = None
```

### Naming Conventions

- **Models**: PascalCase - `Target`, `Seed`, `Subdomain`, `SubfinderScan`
- **Functions/Methods**: snake_case - `update_subdomain_assets`, `run_nmap_scan`, `create_or_update_ip_objects`
- **Variables**: snake_case - `target_name`, `scan_results`, `subdomain_map`
- **Constants**: UPPERCASE - `SEED_TYPE_CHOICES`, `CELERY_BROKER_URL`, `MAX_RETRIES`
- **Private methods**: Leading underscore - `_internal_helper`, `_parse_results`
- **Django related_name**: snake_case plural - `related_name="seeds"`, `related_name="scan_results"`

### Django Model Patterns

**Always include** in Model Meta:
- `app_label` - explicitly set for all models
- `verbose_name` and `verbose_name_plural` - bilingual preferred
- `unique_together` or `constraints` - for composite uniqueness

```python
class Seed(models.Model):
    target = models.ForeignKey(
        Target, 
        on_delete=models.CASCADE, 
        related_name="seeds",  # Always provide related_name
        help_text="所屬的目標專案"  # Always provide help_text
    )
    value = models.CharField(max_length=512)
    type = models.CharField(max_length=20, choices=SEED_TYPE_CHOICES)
    
    class Meta:
        app_label = "core"  # Required for apps/core/models/* structure
        unique_together = ("target", "value")
        verbose_name = "掃描種子"
        verbose_name_plural = "掃描種子"
```

### API Development with Django Ninja

```python
from ninja import Router
from ninja.errors import HttpError
from typing import List

router = Router()

@router.get("/targets", response=List[TargetSchema])
def list_targets(request):
    """List all targets."""
    return Target.objects.all()

@router.post("/targets")
def create_target(request, payload: TargetSchema):
    """Create new target."""
    target = Target.objects.create(**payload.dict())
    return {"id": target.id, "name": target.name}
```

### Celery Task Patterns

```python
from celery import shared_task
from django.db import transaction

@shared_task(bind=True, max_retries=3)
def run_subfinder_scan(self, seed_id: int):
    """
    執行 Subfinder 子域名掃描任務
    Execute Subfinder subdomain enumeration task.
    """
    try:
        seed = Seed.objects.get(id=seed_id)
        # Task logic here
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

### Error Handling

```python
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from ninja.errors import HttpError
import logging

logger = logging.getLogger(__name__)

def get_target_by_name(name: str) -> Target:
    """Get target with proper error handling."""
    try:
        return Target.objects.get(name=name)
    except ObjectDoesNotExist:
        logger.error(f"Target not found: {name}")
        raise HttpError(404, f"Target '{name}' not found")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HttpError(500, "Internal server error")
```

### Database Transactions

For bulk operations, always use transactions:

```python
from django.db import transaction

@transaction.atomic
def bulk_create_subdomains(subdomain_list: List[str], seed: Seed):
    """Bulk create subdomains with transaction protection."""
    subdomains = [
        Subdomain(name=name, seed=seed)
        for name in subdomain_list
    ]
    Subdomain.objects.bulk_create(subdomains, ignore_conflicts=True)
```

### Logging

Use the project's custom logging decorator and standard Python logging:

```python
from c2_core.config.logging import log_function_call
import logging

logger = logging.getLogger(__name__)

@log_function_call
def important_function(param: str) -> dict:
    """Function with automatic logging."""
    logger.info(f"Processing: {param}")
    return {"status": "success"}
```

---

## Project Structure & Organization

```
/
├── apps/                      # Django applications
│   ├── core/                 # Core models (Target, Seed, Subdomain, etc.)
│   ├── targets/              # Target management
│   ├── nmap_scanner/         # Nmap integration
│   ├── subfinder/            # Subdomain enumeration
│   ├── nuclei_scanner/       # Vulnerability scanning
│   ├── analyze_ai/           # AI analysis engine
│   ├── flaresolverr/         # Anti-bot bypass
│   └── scheduler/            # Task scheduling
├── c2_core/                  # Django project core
│   ├── settings.py           # Django settings
│   ├── urls.py               # URL routing
│   ├── celery.py             # Celery configuration
│   └── logs/                 # Application logs
├── scripts/                  # Utility scripts
│   ├── celery_worker_eventlet.py
│   └── init_auto_pentest.py
├── docker/                   # Docker compose & configs
├── docs/                     # Documentation
├── requirements.txt          # Python dependencies
└── manage.py                 # Django management
```

**Model Organization**: Models in subdirectories with `__init__.py` for imports:
```
apps/core/models/
├── __init__.py              # Exports all models
├── base.py                  # Target, Seed
├── domain.py                # Subdomain, SubdomainSeed
├── network.py               # IP, Port
└── scans_record_models.py   # Scan records
```

---

## Key Development Practices

1. **Always set `app_label`** in Model Meta class when models are in subdirectories
2. **Always provide `related_name`** for ForeignKey and ManyToMany relationships
3. **Always add `help_text`** to model fields for better documentation
4. **Use transactions** for bulk database operations
5. **Preserve Chinese comments** - they are part of the codebase standard
6. **Use Celery for long-running tasks** - scanning, enumeration, AI analysis
7. **Log important operations** with the custom decorator and logger
8. **Handle exceptions gracefully** - use Django exceptions and proper HTTP errors
9. **Use Pydantic schemas** for API request/response validation
10. **Test performance-critical operations** - see `apps/subfinder/tests/test_performance.py`

---

## Environment Variables

Key environment variables (see `.env.example`):

```bash
# Database
POSTGRES_DB=mydb
POSTGRES_USER=myuser
POSTGRES_PASSWORD=secret
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Django
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=true
DJANGO_SETTINGS_MODULE=c2_core.settings

# Redis/Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# AI Services
GEMINI_API_KEY=your_key
MISTRAL_API_KEY=your_key
```

---

## Additional Resources

- **Detailed Build Guide**: See `BUILD_GUIDE.md` for comprehensive setup instructions
- **Internal Workflow**: See `docs/internal_workflow.md` for system architecture
- **Django Documentation**: https://docs.djangoproject.com/en/5.2/
- **Django Ninja**: https://django-ninja.rest-framework.com/
- **Celery Documentation**: https://docs.celeryproject.org/

---

**Legal Notice**: This tool is for educational and authorized security testing only. Unauthorized scanning is illegal.
