# CR-0017：Celery 結果保留與監控配置缺失

- Status: **Open**
- Severity: P3
- Domain: Celery
- Confidence: High
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Review cycle: 4
- Fingerprint: celery/result-monitoring/celery.py/result_expires

## Summary

Celery 配置缺少關鍵的結果保留、監控與長任務取消設定：未設定 `result_expires`、`result_extended`、`task_ignore_result`、`worker_cancel_long_running_tasks`、`worker_send_task_events`。導致 Redis 結果堆積、無法追蹤任務執行狀態、長跑異常任務無法自動清理。

## Evidence

- File: `c2_core/celery.py`
- Symbol: `app.conf.*` 缺失設定

### 缺失配置項:

| 配置項 | 現狀 | 建議值 | 影響 |
|--------|------|--------|------|
| `result_expires` | 未設定 (預設 24h) | 86400 (1天) 或 604800 (7天) | 結果永久佔用 Redis 記憶體 |
| `result_extended` | 未設定 (預設 False) | True | 啟用完整結果元資料 (traceback, children 等) |
| `task_ignore_result` | 未設定 (預設 False) | 視任務而定 | 無結果需求的任務 (如觸發類) 可關閉儲存 |
| `worker_cancel_long_running_tasks` | 未設定 (預設 False) | **True** (關鍵) | 配合 time_limit 自動清理卡死任務 |
| `worker_send_task_events` | 未設定 (預設 False) | True | 啟用 Flower/監控事件流 |
| `task_send_sent_event` | 未設定 (預設 False) | True | 追蹤任務發送狀態 |
| `worker_prefetch_multiplier` | 1 (已設定) | 1 (維持) | 避免長任務囤積 ✅ |
| `task_acks_late` | True (已設定) | True (維持) | 防止任務遺失 ✅ |
| `task_reject_on_worker_lost` | True (已設定) | True (維持) | Worker 異常時重新佇列 ✅ |

### 現有配置 (celery.py):
```python
app.conf.broker_url = settings.CELERY_BROKER_URL
app.conf.result_backend = settings.CELERY_RESULT_BACKEND
app.conf.task_serializer = settings.CELERY_TASK_SERIALIZER
app.conf.result_serializer = settings.CELERY_RESULT_SERIALIZER
app.conf.accept_content = settings.CELERY_ACCEPT_CONTENT
app.conf.timezone = settings.CELERY_TIMEZONE
app.conf.beat_scheduler = "django_celery_beat.schedulers:DatabaseScheduler"
app.conf.task_acks_late = settings.CELERY_TASK_ACKS_LATE
app.conf.task_reject_on_worker_lost = True
app.conf.worker_prefetch_multiplier = settings.CELERY_WORKER_PREFETCH_MULTIPLIER
# 缺失上述 6 項關鍵配置
```

### Redis 結果堆積風險估算:
- 79 任務類型，假設每日各執行 10 次 = 790 結果/天
- 每結果約 1-10 KB (含 traceback、return value)
- 7 天約 5.5-55 MB (可接受)，但無 `result_expires` 會無限增長
- 高頻排程任務 (watchdog 10min、triggers 5min) 產生大量小結果

## Trigger

Cycle 4 (Celery Rotation) - 審查 Celery 完整配置與監控就緒度。

## Impact

1. **Redis 記憶體洩漏**: 無過期機制，結果永久堆積，最終導致 Redis OOM 或驅逐緩存
2. **無法監控**: 無 `worker_send_task_events`，Flower、Prometheus exporter 無法採集任務事件
3. **卡死任務無法自動清理**: 無 `worker_cancel_long_running_tasks=True`，配合 CR-0014 缺失 time_limit，雙重風險
4. **除錯困難**: 無 `result_extended=True`，結果缺少 traceback、children、task args 等關鍵除錯資訊
5. **不必要的結果儲存**: 觸發類任務 (如 `trigger_scan_*`, `wake_agent_on_scan_completion`) 無需保留結果，浪費空間

## Why this matters

生產環境 Celery **必須**配置結果生命週期管理與監控事件。這是運維基礎設施的最小可行配置。

## Recommended change

1. **完善 Celery 配置** (celery.py):
```python
# 結果生命週期
app.conf.result_expires = 604800  # 7 天 (秒)
app.conf.result_extended = True   # 完整元資料

# 任務預設不儲存結果 (需結果的任務單獨開啟)
app.conf.task_ignore_result = True

# 長任務自動取消 (需配合 time_limit/soft_time_limit - 見 CR-0014)
app.conf.worker_cancel_long_running_tasks = True

# 監控事件 (供 Flower、Prometheus、Datadog 等)
app.conf.worker_send_task_events = True
app.conf.task_send_sent_event = True

# 可選: 結果壓縮 (大結果時)
# app.conf.result_compression = 'gzip'

# 可選: 結果序列化安全
# app.conf.result_accept_content = ['json']
```

2. **任務級覆蓋** (需保留結果的任務):
```python
@shared_task(ignore_result=False)  # 覆蓋全域預設
def perform_nmap_scan(...):
    return {"scan_id": scan.id, "ports_found": len(ports)}

@shared_task(ignore_result=True)   # 明確不需結果
def trigger_scan_urls_missing_response(...):
    # 僅發送觸發，不關心回傳值
    pass
```

3. **部署監控** (選項):
- **Flower**: `pip install flower` → `celery -A c2_core flower --port=5555`
- **Prometheus Exporter**: `pip install celery-prometheus-exporter`
- **Datadog/New Relic**: 整合 APM

4. **Redis 記憶體策略** (redis.conf):
```conf
maxmemory 256mb
maxmemory-policy allkeys-lru  # 或 volatile-lru
```
確保結果過期機制與 Redis 驅逐策略配合。

## Verification

1. 部署配置後重啟 worker
2. `celery -A c2_core inspect conf | grep -E "result_expires|result_extended|worker_cancel_long_running|worker_send_task_events|task_ignore_result"`
3. 提交測試任務，確認 Redis 中結果 TTL 正確: `TTL celery-task-meta-<uuid>`
4. 開啟 Flower 驗證事件流正常: `celery -A c2_core flower`
5. 人為製造卡死任務 (配合 CR-0014 time_limit)，驗證 `worker_cancel_long_running_tasks` 自動終止

## Resolution criteria

- `result_expires` 設定合理值 (≤ 7 天)
- `result_extended = True` 生效
- `worker_cancel_long_running_tasks = True` 生效 (配合 time_limit)
- `worker_send_task_events = True` 生效，Flower 可正常顯示任務時間線
- 無結果需求的任務設定 `ignore_result=True`
- Redis 記憶體使用穩定，無持續增長趨勢

## Notes

- `result_extended=True` 會增加結果大小 (含 args、kwargs、traceback)，需配合 `result_expires`
- `worker_cancel_long_running_tasks` 僅在設定了 `time_limit`/`soft_time_limit` 時生效 (見 CR-0014)
- `task_ignore_result=True` 會導致 `AsyncResult.ready()` 永遠回傳 False，調用方需注意
- 監控事件會增加 Redis 流量 (~幾 KB/任務)，可接受
- 參考: Celery docs "Configuring the Result Backend", "Monitoring and Management Guide"