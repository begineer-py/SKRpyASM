# CR-0016：Celery 佇列隔離不足 (僅 default/ai_queue)

- Status: **Open**
- Severity: P3
- Domain: Celery
- Confidence: Medium
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Review cycle: 4
- Fingerprint: celery/queue-isolation/celery.py/task_routes

## Summary

專案目前僅定義 2 個佇列 (`default`, `ai_queue`)，所有 79 個任務集中在這兩隊列，缺乏針對任務特性 (CPU 密集、IO 密集、長跑、優先級) 的佇列隔離與專用 worker。導致資源爭用、優先級反轉、故障擴散風險。

## Evidence

- File: `c2_core/celery.py` (無 `task_routes`, `task_queues` 配置)
- File: `docker/docker-compose.yml` (單一 `celery_worker` 服務)
- Symbol: `@shared_task(queue=...)`

### 現狀佇列分佈:

| 佇列 | 任務數 | 任務類型 | 風險 |
|------|--------|----------|------|
| `default` | ~75 | 掃描、同步、清理、Agent 執行、排程觸發 | 混雜所有負載 |
| `ai_queue` | 4 | `ai_scan` (FlareSolverr AI 分析) | 僅隔離 AI 推理 |

### 任務特性分類 (建議佇列):

| 任務類別 | 代表任務 | 特性 | 建議佇列 | 建議 Worker |
|----------|----------|------|----------|-------------|
| **重掃描/外部工具** | nmap, nuclei, katana, subfinder, gau | CPU/IO 密集、長跑、不可控 | `scans_heavy` | 專用 worker (concurrency=2-4) |
| **輕量掃描/同步** | get_all_url, cve_sync, enrichment | 短跑、網路 IO | `scans_light` | 共用 worker |
| **AI/LLM 推理** | ai_scan, auto agents | GPU/記憶體密集、模型載入 | `ai_queue` | 專用 GPU worker (concurrency=1-2) |
| **排程/觸發/清理** | watchdog, bootstrapper, triggers | 極短、高頻、低延遲要求 | `control` | 專用/共用 worker |
| **HTTP Fuzzing** | fuzz_endpoint | 網路 IO、高併發 | `fuzzing` | 專用 worker (高 concurrency) |
| **優先/即時** | 用戶觸發掃描、即時分析 | 低延遲要求 | `priority` | 專用 worker |

### 現有配置缺失:
```python
# c2_core/celery.py - 完全缺少佇列路由配置
# app.conf.task_queues = [...]
# app.conf.task_routes = {...}
# app.conf.task_default_queue = 'default'
```

### Docker Compose 僅有單一 worker:
```yaml
celery_worker:
  command: celery -A c2_core worker -P prefork -c 8 -l info
  # 無 -Q 參數指定佇列，消費所有佇列
```

## Trigger

Cycle 4 (Celery Rotation) - 審查佇列架構與資源隔離。

## Impact

1. **資源爭用**: 重掃描任務佔用 CPU/記憶體，導致輕量任務 (如 watchdog、同步任務) 排隊延遲
2. **優先級反轉**: 低優先級批次掃描擋住高優先級用戶觸發任務
3. **故障擴散**: AI 模型 OOM 或掃描工具崩潰影響同一 worker 上所有任務類型
4. **無法水平擴展**: 無法針對瓶頸佇列單獨擴充 worker (如只擴充 scans_heavy)
5. **監控模糊**: 無法針對佇列維度監控積壓、延遲、吞吐

## Why this matters

Celery 設計支援多佇列、多 worker 專業化部署。生產環境**必須**將不同特性任務隔離，避免單點故障癱瘓整個任務系統。

## Recommended change

1. **定義佇列** (celery.py):
```python
from kombu import Queue

app.conf.task_queues = (
    Queue('control', routing_key='control.#'),      # 排程/控制 - 高優先級
    Queue('priority', routing_key='priority.#'),    # 用戶觸發 - 高優先級
    Queue('scans_heavy', routing_key='scans.heavy'), # 重掃描 - 低優先級
    Queue('scans_light', routing_key='scans.light'), # 輕掃描 - 中優先級
    Queue('ai_queue', routing_key='ai.#'),          # AI 推理 - 專用
    Queue('fuzzing', routing_key='fuzzing.#'),      # Fuzzing - 高併發
    Queue('default', routing_key='default'),        # 兜底
)

app.conf.task_default_queue = 'default'
app.conf.task_default_exchange = 'default'
app.conf.task_default_routing_key = 'default'
```

2. **配置路由** (celery.py):
```python
app.conf.task_routes = {
    # 控制/排程任務 - 高優先級
    'scheduler.tasks.watchdog_stalled_overviews': {'queue': 'control'},
    'scheduler.tasks.trigger_scan_*': {'queue': 'control'},
    'analyze_ai.tasks.periodic_initial_analysis_bootstrapper': {'queue': 'control'},
    
    # 用戶觸發即時任務 - 高優先級
    'apps.scanners.nmap_scanner.tasks.perform_nmap_scan': {'queue': 'priority'},
    'apps.scanners.nuclei_scanner.tasks.*': {'queue': 'priority'},
    
    # 重掃描批次任務 - 低優先級
    'apps.scanners.subfinder.tasks.start_subfinder': {'queue': 'scans_heavy'},
    'apps.scanners.katana_scanner.tasks.scan_katana': {'queue': 'scans_heavy'},
    'apps.scanners.cve_intelligence.tasks.*': {'queue': 'scans_light'},
    
    # AI 任務 - 專用佇列
    'apps.flaresolverr.tasks.js_trigger.ai_scan': {'queue': 'ai_queue'},
    'apps.auto.tasks.run_*_agent_async': {'queue': 'ai_queue'},
    
    # Fuzzing - 專用佇列
    'apps.http_sender.tasks.fuzz_endpoint': {'queue': 'fuzzing'},
}
```

3. **部署專用 Worker** (docker-compose.yml):
```yaml
celery_worker_control:
  command: celery -A c2_core worker -Q control -c 2 -l info

celery_worker_priority:
  command: celery -A c2_core worker -Q priority -c 4 -l info

celery_worker_scans_heavy:
  command: celery -A c2_core worker -Q scans_heavy -c 2 -l info
  deploy:
    resources:
      limits:
        cpus: '4.0'
        memory: 4096M

celery_worker_ai:
  command: celery -A c2_core worker -Q ai_queue -c 1 -l info
  deploy:
    resources:
      limits:
        cpus: '8.0'
        memory: 8192M
  # 可掛載 GPU

celery_worker_fuzzing:
  command: celery -A c2_core worker -Q fuzzing -c 16 -l info
  # 高併發、IO 密集

celery_worker_default:
  command: celery -A c2_core worker -Q default,scans_light -c 4 -l info
```

4. **設定佇列優先級** (Redis broker 支援):
```python
# priority queue 使用 x-max-priority
app.conf.task_queues = (
    Queue('control', routing_key='control.#', queue_arguments={'x-max-priority': 10}),
    Queue('priority', routing_key='priority.#', queue_arguments={'x-max-priority': 5}),
    # ...
)

# 發送任務時指定優先級
perform_nmap_scan.apply_async(args=[target_id], priority=8)  # 高優先級
start_subfinder.apply_async(args=[target_id], priority=2)    # 低優先級
```

## Verification

1. 部署多 worker 架構
2. `celery -A c2_core inspect active_queues` 確認各 worker 綁定正確佇列
3. 壓測: 並發提交 重掃描 + 即時掃描 + AI 任務，觀察延遲隔離效果
4. 故障注入: 讓 AI worker OOM，確認其他 worker 不受影響

## Resolution criteria

- 定義 ≥ 5 個語義明確的佇列
- 部署 ≥ 3 個專用 worker 服務 (control, scans_heavy, ai_queue 至少分離)
- 關鍵任務類別有明確佇列路由規則
- 高優先級佇列任務延遲 < 1s (無負載時)

## Notes

- 遷移策略: 先加佇列路由配置，再逐步拆分 worker 服務
- `prefetch_multiplier=1` 適合長任務佇列，短任務佇列可調高 (如 4-8)
- AI worker 建議單獨部署、可掛載 GPU、設定記憶體限制
- 參考: Celery docs "Routing Tasks", "Worker Guide - Concurrency"