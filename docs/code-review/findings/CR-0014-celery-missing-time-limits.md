# CR-0014：Celery 任務缺乏 time_limit/soft_time_limit

- Status: **Open**
- Severity: P2
- Domain: Celery
- Confidence: High
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Review cycle: 4
- Fingerprint: celery/missing-time-limits/tasks/*.py/@shared_task

## Summary

專案中 79 個 `@shared_task` 定義，**完全沒有**設定 `time_limit` 或 `soft_time_limit`。這包含多個長跑任務（Nmap 掃描、Nuclei 掃描、FlareSolverr JS 分析、Auto Agent 執行），若任務卡死或陷入無限循環，會永久佔用 worker process，導致 worker 耗盡無法處理新任務。

## Evidence

- Files: 所有 `apps/*/tasks/` 下的任務模組
- Symbol: `@shared_task` decorator (無 `time_limit` / `soft_time_limit` 參數)

### 高風險長跑任務 (無時間限制):

| 任務 | 模組 | 預估執行時間 | 風險 |
|------|------|--------------|------|
| `perform_nmap_scan` | apps.scanners.nmap_scanner.tasks | 60-300s | 系統呼叫阻塞、掃描卡死 |
| `perform_nuclei_scans_for_*_batch` (7 tasks) | apps.scanners.nuclei_scanner.tasks | 30-600s | 外部工具無回應、模板過多 |
| `perform_js_scan` + 子任務 | apps.flaresolverr.tasks.js_trigger | 30-180s | AI 模型推理、瀏覽器自動化 |
| `run_automation_agent_async` | apps.auto.tasks | 60-300s+ | LLM 多輪對話、工具調用鏈 |
| `run_recon_agent_async` 等 | apps.auto.tasks | 60-600s | 多工具串聯執行 |
| `scan_katana` | apps.scanners.katana_scanner.tasks | 30-300s | 爬蟲深度不可控 |
| `start_subfinder` / `start_amass_scan` | apps.scanners.subfinder.tasks | 60-300s | 被動/主動枚舉時間不可預期 |

### Celery 配置確認:
```python
# c2_core/celery.py - 無全域 time_limit 設定
app.conf.task_time_limit = ?  # 未設定
app.conf.task_soft_time_limit = ?  # 未設定
app.conf.worker_cancel_long_running_tasks = ?  # 未設定
```

## Trigger

Cycle 4 (Celery Rotation) - 審查所有任務定義與 Celery 配置。

## Impact

1. **Worker 耗盡**: 一個卡死任務永久佔用 1 個 prefork process (共 8 個)，8 個卡死任務即癱瘓整個 worker
2. **無法優雅降級**: 無 `soft_time_limit` 意味著任務無法在硬限制前釋放資源、記錄狀態、通知上游
3. **監控盲區**: 無法透過 `worker_cancel_long_running_tasks` 自動終止異常任務
4. **連鎖效應**: 卡死的掃描任務會阻塞後續依賴其結果的任務 (如 AI 分析、自動化規劃)

## Why this matters

Celery 最佳實踐強烈建議所有任務設定合理的時間上限。對於呼叫外部工具 (nmap, nuclei, flaresolverr) 或 LLM 的任務，**必須**設定 `soft_time_limit` (優雅終止) 和 `time_limit` (強制殺掉)。

## Recommended change

1. **全域預設** (celery.py):
```python
app.conf.task_soft_time_limit = 300   # 5 分鐘軟限制
app.conf.task_time_limit = 360        # 6 分鐘硬限制 (soft + 60s 緩衝)
app.conf.worker_cancel_long_running_tasks = True  # 自動取消超時任務
```

2. **任務級覆蓋** (視任務特性調整):
```python
# 掃描類任務 - 較長限制
@shared_task(soft_time_limit=600, time_limit=660)
def perform_nmap_scan(...):

# AI/LLM 任務 - 中等限制  
@shared_task(soft_time_limit=180, time_limit=240)
def run_automation_agent_async(...):

# 快速任務 - 短限制
@shared_task(soft_time_limit=30, time_limit=45)
def enrich_vulnerabilities_batch(...):
```

3. **在任務中處理 SoftTimeLimitExceeded**:
```python
from celery.exceptions import SoftTimeLimitExceeded

@shared_task(soft_time_limit=300, time_limit=360)
def long_task(...):
    try:
        # 執行邏輯
        return result
    except SoftTimeLimitExceeded:
        logger.warning("Task approaching time limit, cleaning up...")
        # 釋放資源、更新狀態、通知上游
        raise  # 重拋讓 Celery 執行硬限制終止
```

## Verification

1. 部署配置後啟動 worker
2. `celery -A c2_core inspect conf | grep -E "time_limit|worker_cancel_long_running"`
3. 人為製造卡死任務驗證自動終止機制
4. 確認 worker process 在超時後被回收並重新 fork

## Resolution criteria

- 所有 79 個任務皆有合理的 `time_limit` / `soft_time_limit` 設定
- 全域 `worker_cancel_long_running_tasks = True` 生效
- 長跑任務超時時能優雅清理並釋放 worker slot

## Notes

- `soft_time_limit` 拋出 `SoftTimeLimitExceeded` 異常，任務可捕捉並清理
- `time_limit` 會發送 `SIGKILL` 強制終止 process，無法捕捉
- 建議 `time_limit = soft_time_limit + 60s` 給清理緩衝
- 需配合監控告警 (Flower / Prometheus) 追蹤超時頻率