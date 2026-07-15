# CR-0019：錯誤處理與可觀測性不足

- Status: **Open**
- Severity: P2
- Domain: Cross-cutting (Observability)
- Confidence: High
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Review cycle: 4
- Fingerprint: cross-cutting/error-handling/observability/gaps

## Summary

專案雖有基本的 try/except 和 logging，但缺乏統一的錯誤處理策略、結構化日誌、分散式追蹤、指標收集與告警機制。Sentry SDK 已安裝但未初始化，Prometheus client 已安裝但未整合。

## Evidence

### 1. 錯誤處理模式不一致

**良好範例** (使用 `logger.exception` 記錄完整堆疊):
```python
# apps/scanners/nmap_scanner/tasks/__init__.py
logger.exception(f"解析 XML 或存儲數據時出錯: {e}")

# apps/flaresolverr/tasks/spider.py
logger.exception(f"任務執行發生未預期錯誤 {url}: {e}")
```

**問題範例** (吞沒異常、缺乏上下文):
```python
# apps/scanners/get_all_url/tasks/__init__.py
except Exception:
    pass  # 完全吞沒，無日誌、無重試、無錯誤傳播

# 多處 catch Exception as e 但僅記錄 str(e)，缺 exc_info=True
logger.error(f"錯誤: {e}")  # 無堆疊追蹤
```

### 2. 無統一錯誤回應格式 (Ninja API)

- `apps/core/schemas.py` 定義了 `ErrorSchema(detail: str)` 但**未強制使用**
- 不同 app 回傳格式不一:
  - 有些回傳 `{"detail": "..."}`
  - 有些回傳 `{"error": "..."}`
  - 有些直接 raise `HttpError` (Ninja 自動轉換)
  - 有些回傳字串而非結構化物件

### 3. Sentry SDK 已安裝但未初始化

`environment.yml` 包含 `sentry-sdk==2.33.2`，但 `c2_core/settings.py` 或 `c2_core/wsgi.py` / `asgi.py` **完全沒有初始化代碼**。

```python
# 缺失:
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
        RedisIntegration(),
    ],
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
    environment=os.environ.get("SENTRY_ENVIRONMENT", "development"),
)
```

### 4. Prometheus Client 已安裝但未暴露指標

`prometheus-client==0.17.1` 已安裝，但：
- 無 `/metrics` 端點
- 無自定義指標 (任務佇列長度、執行時間、錯誤率、掃描進度等)
- 無 `django-prometheus` 整合

### 5. 缺乏分散式追蹤

- Celery 任務鏈 (scan → analyze → auto) 無 trace context 傳遞
- 跨服務調用 (Django → FlareSolverr → FlareProxyGo) 無 trace header 傳遞
- LangChain/LangGraph 內部有 tracing 但未連接到中央系統

### 6. 日誌結構化不足

當前 logging 使用 `verbose` formatter (人類可讀)，但：
- 無 JSON 格式化輸出 (難以被 log aggregation 系統解析)
- 無關聯 ID (request_id, trace_id, task_id) 貫穿調用鏈
- Celery worker 日誌與 Django 日誌分離但無關聯

### 7. 健康檢查不完整

Docker Compose 有基本 healthcheck，但應用層面缺乏:
- `/health/` 或 `/ready/` 端點檢查 DB、Redis、Celery、外部服務連線
- Kubernetes liveness/readiness probe 就緒

### 8. 告警機制缺失

- 無錯誤率告警 (Sentry alerts / Prometheus alerts)
- 無任務積壓告警 (Celery queue length)
- 無資源耗盡告警 (Disk, Memory, CPU, DB connections)
- 無業務指標告警 (掃描失敗率、AI 分析異常)

## Trigger

Cycle 4 (Cross-cutting Rotation) - 可觀測性成熟度審查。

## Impact

1. **MTTR (平均修復時間) 延長**: 無集中錯誤追蹤，需登入多台機器查日誌
2. **無法主動發現問題**: 依賴用戶回報或人工巡檢，而非告警推送
3. **效能調優盲區**: 無指標數據，無法識別瓶頸 (慢查詢、任務堆積、記憶體洩漏)
4. **跨服務除錯困難**: 請求流經 Django → Celery → FlareSolverr → 外部 API，無 trace 串聯
5. **合規風險**: 安全事件無審計軌跡，錯誤日誌可能遺漏關鍵上下文

## Why this matters

現代雲原生應用**必須**具備三大支柱: **Logs, Metrics, Traces**。專案已安裝工具但未整合，屬「買了健身卡不去健身」狀態。

## Recommended Change

### 階段 1: 統一錯誤處理 (1-2 天)

1. **建立共用例外處理模組** (`c2_core/exceptions.py`):
```python
class C2Exception(Exception):
    """基礎業務例外，攜帶錯誤碼、用戶訊息、內部詳情"""
    def __init__(self, code: str, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

class ValidationError(C2Exception): pass
class ExternalServiceError(C2Exception): pass
class TaskExecutionError(C2Exception): pass
```

2. **Ninja 全域例外處理器** (自動轉換為統一格式):
```python
# c2_core/urls.py
@api.exception_handler(C2Exception)
def c2_exception_handler(request, exc: C2Exception):
    return api.create_response(request, {
        "error": {"code": exc.code, "message": exc.message, "details": exc.details}
    }, status=400)

@api.exception_handler(Exception)
def generic_exception_handler(request, exc: Exception):
    logger.exception("Unhandled exception", exc_info=exc)
    return api.create_response(request, {
        "error": {"code": "INTERNAL_ERROR", "message": "內部伺服器錯誤"}
    }, status=500)
```

3. **強制使用 `ErrorSchema`** 於所有 API 回應。

### 階段 2: 初始化 Sentry (半天)

```python
# c2_core/settings.py 或專用 sentry.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_logging = LoggingIntegration(
    level=logging.INFO,        # 捕捉 INFO 以上為 breadcrumbs
    event_level=logging.ERROR  # 發送 ERROR 以上為 events
)

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
        RedisIntegration(),
        sentry_logging,
    ],
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
    environment=os.environ.get("DEPLOY_ENV", "development"),
    release=os.environ.get("APP_VERSION", "unknown"),
    # 機密資料過濾
    before_send=lambda event, hint: _scrub_sensitive_data(event),
)
```

### 階段 3: Prometheus Metrics 整合 (1 天)

1. **安裝 `django-prometheus`** (已有 `prometheus-client`)
2. **暴露 `/metrics` 端點**:
```python
# urls.py
from django_prometheus import exports
urlpatterns = [
    ...
    path("metrics/", exports.ExportToDjangoView),  # 或自定義 view
]
```
3. **自定義業務指標**:
```python
# c2_core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

TASK_DURATION = Histogram("c2_task_duration_seconds", "Task execution time", ["task_name", "status"])
TASK_QUEUE_LENGTH = Gauge("c2_celery_queue_length", "Pending tasks per queue", ["queue"])
SCAN_TOTAL = Counter("c2_scans_total", "Total scans", ["scanner", "status"])
VULN_FOUND = Counter("c2_vulnerabilities_found_total", "Vulnerabilities found", ["severity", "scanner"])
AI_TOKEN_USAGE = Counter("c2_ai_tokens_total", "LLM token usage", ["model", "type"])
```

4. **在關鍵路徑埋點** (Celery tasks, API views, scanner executors)。

### 階段 4: 分散式追蹤 (1-2 天)

1. **OpenTelemetry 整合** (Sentry 支援 OTLP export):
```python
# 設定 OTLP exporter 送到 Sentry/Jaeger/Collector
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")))
)
```

2. **Celery 任務傳遞 trace context**:
```python
# celery.py 或 task 基類
from opentelemetry.propagate import inject, extract

class TracedTask(Task):
    def apply_async(self, args, kwargs, **options):
        headers = {}
        inject(headers)  # 注入當前 trace context
        options.setdefault("headers", {}).update(headers)
        return super().apply_async(args, kwargs, **options)

    def __call__(self, *args, **kwargs):
        # 從 headers 提取 trace context
        headers = getattr(self.request, "headers", {})
        ctx = extract(headers)
        with trace.use_span(ctx):
            return super().__call__(*args, **kwargs)
```

3. **HTTP 呼叫傳遞 trace header** (httpx, requests 攔截器)。

### 階段 5: 結構化日誌 (JSON) (半天)

```python
# settings.py LOGGING 格式化器
import json
import logging

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        # 加入額外欄位
        for key in ["request_id", "trace_id", "task_id", "target_id", "user_id"]:
            if hasattr(record, key):
                log_obj[key] = getattr(record, key)
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)

LOGGING = {
    "formatters": {
        "json": {"()": JsonFormatter},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "json"},
        ...
    }
}
```

### 階段 6: 健康檢查端點與告警 (1 天)

```python
# apps/core/health.py
from ninja import Router
from django.db import connection
from redis import Redis
from celery import Celery

router = Router(tags=["Health"])

@router.get("/health/")
def health_check(request):
    checks = {}
    # DB
    try:
        with connection.cursor() as c: c.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"
    # Redis
    try:
        Redis.from_url(settings.REDIS_URL).ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"
    # Celery
    try:
        Celery("c2_core").control.ping(timeout=2)
        checks["celery"] = "ok"
    except Exception as e:
        checks["celery"] = f"error: {e}"
    
    status = 200 if all(v == "ok" for v in checks.values()) else 503
    return JsonResponse({"status": "healthy" if status == 200 else "unhealthy", "checks": checks}, status=status)
```

**告警規則範例** (Prometheus AlertManager / Sentry):
- `rate(c2_task_errors_total[5m]) > 0.1` → Critical
- `c2_celery_queue_length{queue="default"} > 100` → Warning
- `histogram_quantile(0.95, c2_task_duration_seconds) > 300` → Warning

## Verification

1. `python manage.py check --deploy` 通過
2. 觸發測試錯誤 → Sentry 儀表板收到事件、包含完整堆疊、請求上下文
3. `curl /metrics` → 回傳 Prometheus 格式指標、包含自定義業務指標
4. 發起掃描請求 → Jaeger/Sentry Trace 顯示完整鏈路 (Django → Celery → Scanner)
5. 日誌輸出為 JSON、包含 `trace_id`、`request_id` 可關聯
6. `/health/` 端點正確反映依賴服務狀態

## Resolution Criteria

- 統一錯誤回應格式 (ErrorSchema) 覆蓋所有 Ninja API
- Sentry 初始化並接收 Django/Celery/Redis 錯誤
- Prometheus `/metrics` 端點暴露核心業務指標
- 關鍵路徑具備分散式追蹤 (trace context 傳遞)
- 結構化 JSON 日誌輸出，含關聯 ID
- 健康檢查端點涵蓋所有關鍵依賴
- 基本告警規則配置 (錯誤率、佇列積壓、延遲)

## Notes

- 開發環境可關閉 Sentry 送樣 (`traces_sample_rate=0`) 或用本地 Sentry (self-hosted)
- OpenTelemetry 可選擇只 export 到 Sentry (省去 Jaeger/Collector 部署)
- 參考: Sentry Python docs, OpenTelemetry Python, Prometheus Client Python, Django Prometheus