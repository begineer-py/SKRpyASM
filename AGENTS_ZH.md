# AGENTS.md - C2 Django AI 開發指南（中文版）

## 專案概述

**C2 Django AI** 是一個全方位的網路安全掃描和滲透測試平台，具備 AI 驅動的分析能力。系統使用 Django 5.2.4 後端配合 Django Ninja REST API 框架、Celery 任務隊列與 Redis、PostgreSQL 資料庫，並整合多種安全工具（Nmap、Subfinder、Nuclei、FlareSolverr）。

**技術棧**: Django 5.2.4, Django Ninja, Django REST Framework, Celery 5.5.3, Redis, PostgreSQL, React (前端), Docker, Uvicorn, pytest

**核心功能**: 資產發現、子域名枚舉、端口掃描、漏洞掃描、AI 驅動的攻擊規劃、持續監控

---

## 建置、測試與執行命令

### 環境設置

```bash
# 創建 conda 環境
conda create -n mtc_env python=3.10 -y
conda activate mtc_env

# 安裝依賴
pip install -r requirements.txt

# 啟動基礎設施服務（PostgreSQL、Redis、Hasura 等）
cd docker && docker compose up -d && cd ..
```

### 資料庫操作

```bash
# 執行所有遷移
python manage.py migrate

# 創建超級用戶
python manage.py createsuperuser

# 在模型變更後生成新的遷移
python manage.py makemigrations

# 檢查遷移狀態
python manage.py showmigrations

# 進入 Django shell
python manage.py shell
```

### 執行服務

```bash
# 執行 Django 開發伺服器（Uvicorn）
uvicorn c2_core.asgi:application --host 0.0.0.0 --port 8000 --reload

# 生產級 Uvicorn 配置（優化版）
uvicorn c2_core.asgi:application --host 0.0.0.0 --port 8000 --workers 9 --loop uvloop --http httptools --backlog 2048 --limit-concurrency 1000

# 執行 Celery worker 使用 eventlet（用於異步任務）
python scripts/celery_worker_eventlet.py -A c2_core.celery:app worker -P eventlet -c 100 -l info

# 執行 Celery beat 調度器（用於定期任務）
celery -A c2_core beat -l info

# 監控 Celery 任務
celery -A c2_core inspect active
celery -A c2_core inspect stats
```

### 測試

```bash
# 執行所有測試
python manage.py test

# 執行特定應用程式的測試
python manage.py test apps.core

# 使用 pytest 執行（如已配置）
pytest

# 執行特定測試檔案
pytest apps/subfinder/tests/test_performance.py

# 執行特定測試類別
pytest apps/subfinder/tests/test_performance.py::SubfinderUtilsTest

# 執行特定測試方法
pytest apps/subfinder/tests/test_performance.py::SubfinderUtilsTest::test_performance_10000_subdomains

# 執行測試並顯示詳細輸出
pytest -v

# 執行測試並生成覆蓋率報告
pytest --cov=apps --cov-report=html
```

### 程式碼檢查與品質

```bash
# 檢查 Python 程式碼風格（如已配置）
# 注意：此專案尚未配置明確的 linter
# 建議添加：black、flake8、ruff、isort

# 手動檢查
python manage.py check
python manage.py check --deploy  # 生產就緒檢查
```

---

## 程式碼風格指南

### Import 組織

**順序**: 標準庫 → Django → 第三方 → 本地應用

```python
# 標準庫
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

# 第三方
from celery import shared_task
import requests
from pydantic import BaseModel

# 本地 imports
from c2_core.config.logging import log_function_call
from apps.core.models import Target, Seed, Subdomain
```

**特殊 Import 模式**: 需要時使用 `from __future__ import annotations` 以支援現代類型提示。

### 格式化標準

- **縮排**: 4 個空格（不使用 Tab）
- **行長度**: 約 120 字元（彈性，但保持可讀性）
- **註解**: 雙語 - 中文註解是標準且應保留
- **字串**: 優先使用雙引號以保持一致性
- **文檔字串**: 使用三重雙引號，包含中英文描述

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

### 類型提示與註解

一致地使用類型提示，特別是在函數簽名中：

```python
from typing import Optional, List, Dict, Any

def update_subdomain_assets(
    seed: Seed, 
    subdomain_map: Dict[str, set], 
    scan: SubfinderScan
) -> Dict[str, int]:
    """處理子域名發現結果。"""
    pass

async def fetch_data(url: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
    """異步數據抓取，帶超時設定。"""
    pass
```

使用 Pydantic 進行 schema 驗證：

```python
from pydantic import BaseModel

class TargetSchema(BaseModel):
    name: str
    description: Optional[str] = None
```

### 命名慣例

- **模型**: PascalCase - `Target`、`Seed`、`Subdomain`、`SubfinderScan`
- **函數/方法**: snake_case - `update_subdomain_assets`、`run_nmap_scan`、`create_or_update_ip_objects`
- **變數**: snake_case - `target_name`、`scan_results`、`subdomain_map`
- **常數**: UPPERCASE - `SEED_TYPE_CHOICES`、`CELERY_BROKER_URL`、`MAX_RETRIES`
- **私有方法**: 前綴下劃線 - `_internal_helper`、`_parse_results`
- **Django related_name**: snake_case 複數形 - `related_name="seeds"`、`related_name="scan_results"`

### Django 模型模式

**必須包含** 在 Model Meta 中：
- `app_label` - 明確設定所有模型
- `verbose_name` 和 `verbose_name_plural` - 優先使用雙語
- `unique_together` 或 `constraints` - 用於複合唯一性

```python
class Seed(models.Model):
    target = models.ForeignKey(
        Target, 
        on_delete=models.CASCADE, 
        related_name="seeds",  # 始終提供 related_name
        help_text="所屬的目標專案"  # 始終提供 help_text
    )
    value = models.CharField(max_length=512)
    type = models.CharField(max_length=20, choices=SEED_TYPE_CHOICES)
    
    class Meta:
        app_label = "core"  # apps/core/models/* 結構必需
        unique_together = ("target", "value")
        verbose_name = "掃描種子"
        verbose_name_plural = "掃描種子"
```

### 使用 Django Ninja 開發 API

```python
from ninja import Router
from ninja.errors import HttpError
from typing import List

router = Router()

@router.get("/targets", response=List[TargetSchema])
def list_targets(request):
    """列出所有目標。"""
    return Target.objects.all()

@router.post("/targets")
def create_target(request, payload: TargetSchema):
    """創建新目標。"""
    target = Target.objects.create(**payload.dict())
    return {"id": target.id, "name": target.name}
```

### Celery 任務模式

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
        # 任務邏輯
    except Exception as exc:
        # 指數退避重試
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

### 錯誤處理

```python
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from ninja.errors import HttpError
import logging

logger = logging.getLogger(__name__)

def get_target_by_name(name: str) -> Target:
    """通過名稱獲取目標，包含適當的錯誤處理。"""
    try:
        return Target.objects.get(name=name)
    except ObjectDoesNotExist:
        logger.error(f"找不到目標: {name}")
        raise HttpError(404, f"找不到目標 '{name}'")
    except Exception as e:
        logger.exception(f"意外錯誤: {e}")
        raise HttpError(500, "內部伺服器錯誤")
```

### 資料庫事務

對於批量操作，始終使用事務：

```python
from django.db import transaction

@transaction.atomic
def bulk_create_subdomains(subdomain_list: List[str], seed: Seed):
    """批量創建子域名，具有事務保護。"""
    subdomains = [
        Subdomain(name=name, seed=seed)
        for name in subdomain_list
    ]
    Subdomain.objects.bulk_create(subdomains, ignore_conflicts=True)
```

### 日誌記錄

使用專案的自定義日誌裝飾器和標準 Python 日誌模組：

```python
from c2_core.config.logging import log_function_call
import logging

logger = logging.getLogger(__name__)

@log_function_call
def important_function(param: str) -> dict:
    """具有自動日誌記錄的函數。"""
    logger.info(f"處理中: {param}")
    return {"status": "success"}
```

---

## 專案結構與組織

```
/
├── apps/                      # Django 應用程式
│   ├── core/                 # 核心模型（Target、Seed、Subdomain 等）
│   ├── targets/              # 目標管理
│   ├── nmap_scanner/         # Nmap 整合
│   ├── subfinder/            # 子域名枚舉
│   ├── nuclei_scanner/       # 漏洞掃描
│   ├── analyze_ai/           # AI 分析引擎
│   ├── flaresolverr/         # 反爬蟲繞過
│   └── scheduler/            # 任務調度
├── c2_core/                  # Django 專案核心
│   ├── settings.py           # Django 設置
│   ├── urls.py               # URL 路由
│   ├── celery.py             # Celery 配置
│   └── logs/                 # 應用日誌
├── scripts/                  # 工具腳本
│   ├── celery_worker_eventlet.py
│   └── init_auto_pentest.py
├── docker/                   # Docker compose 與配置
├── docs/                     # 文檔
├── requirements.txt          # Python 依賴
└── manage.py                 # Django 管理
```

**模型組織**: 模型放在子目錄中，使用 `__init__.py` 匯入：
```
apps/core/models/
├── __init__.py              # 匯出所有模型
├── base.py                  # Target、Seed
├── domain.py                # Subdomain、SubdomainSeed
├── network.py               # IP、Port
└── scans_record_models.py   # 掃描記錄
```

---

## 關鍵開發實踐

1. **始終設定 `app_label`** - 當模型位於子目錄時，在 Model Meta 類中設定
2. **始終提供 `related_name`** - 用於 ForeignKey 和 ManyToMany 關係
3. **始終添加 `help_text`** - 為模型欄位添加，以改善文檔
4. **使用事務** - 用於批量資料庫操作
5. **保留中文註解** - 它們是程式碼庫標準的一部分
6. **使用 Celery 處理長時間運行的任務** - 掃描、枚舉、AI 分析
7. **記錄重要操作** - 使用自定義裝飾器和日誌記錄器
8. **優雅地處理例外** - 使用 Django 例外和適當的 HTTP 錯誤
9. **使用 Pydantic schemas** - 用於 API 請求/響應驗證
10. **測試性能關鍵操作** - 參見 `apps/subfinder/tests/test_performance.py`

---

## 環境變數

關鍵環境變數（參見 `.env.example`）：

```bash
# 資料庫
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

# AI 服務
GEMINI_API_KEY=your_key
MISTRAL_API_KEY=your_key
```

---

## 額外資源

- **詳細建置指南**: 參見 `BUILD_GUIDE.md` 以獲取全面的設置說明
- **內部工作流**: 參見 `docs/internal_workflow.md` 以了解系統架構
- **Django 文檔**: https://docs.djangoproject.com/en/5.2/
- **Django Ninja**: https://django-ninja.rest-framework.com/
- **Celery 文檔**: https://docs.celeryproject.org/

---

**法律聲明**: 本工具僅用於教育和授權的安全測試。未經授權的掃描是非法的。
