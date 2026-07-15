# CR-0015：Celery 大型資料庫交易阻塞連線池

- Status: **Open**
- Severity: P2
- Domain: Celery
- Confidence: High
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Review cycle: 4
- Fingerprint: celery/large-db-transactions/tasks/*.py/transaction.atomic

## Summary

多個掃描類 Celery 任務在單一資料庫交易 (`transaction.atomic()`) 中處理大量資料寫入，導致 PostgreSQL 連線長時間被佔用，阻塞連線池，影響並發任務與 Django 請求的資料庫存取。

## Evidence

- Files: `apps/scanners/nmap_scanner/tasks/__init__.py`, `apps/flaresolverr/tasks/js_trigger.py`, `apps/scanners/subfinder/tasks/*.py`
- Symbol: `transaction.atomic()` / `with transaction.atomic():`

### 問題任務分析:

| 任務 | 模組 | 交易範圍 | 預估資料量 | 連線佔用時間 |
|------|------|----------|------------|--------------|
| `perform_nmap_scan` | nmap_scanner.tasks | 單一大交易 | 數百 Port/Service 記錄 | 30-120s |
| `ai_scan` | flaresolverr.tasks.js_trigger | 單一大交易 | 數十-數百 JSONObject 記錄 | 10-60s |
| `param_scan` | flaresolverr.tasks.js_trigger | 單一大交易 | 數十 Endpoint 記錄 | 5-30s |
| `start_subfinder` | subfinder.tasks.subfinder_tasks | 單一大交易 | 數百 Subdomain 記錄 | 30-120s |
| `resolve_dns_for_seed` (batch) | subfinder.tasks.dns_tasks | 單一大交易 | 批次 DNS 解析結果 | 10-60s |
| `run_automation_agent_async` | auto.tasks | 多次交易但長鏈 | 複雜圖譜寫入 | 60-300s |

### 代碼片段範例 (nmap_scanner):
```python
# apps/scanners/nmap_scanner/tasks/__init__.py
with transaction.atomic():
    nmap_scan = NmapScan.objects.create(...)
    for port_data in scan_result.ports:
        Port.objects.create(nmap_scan=nmap_scan, ...)  # 逐筆建立
    for service in scan_result.services:
        Service.objects.create(...)  # 逐筆建立
```

### 代碼片段範例 (flaresolverr ai_scan):
```python
# apps/flaresolverr/tasks/js_trigger.py
with transaction.atomic():
    to_create = [
        JSONObject(**{k: v for k, v in res.items() if k in allowed_fields}, **fk_kwargs)
        for res in results
    ]
    JSONObject.objects.bulk_create(to_create)  # 至少用了 bulk_create
    # 但仍在同一交易中更新 ExtractedJS/JavaScriptFile 狀態
```

## Trigger

Cycle 4 (Celery Rotation) - 審查任務資料庫操作模式。

## Impact

1. **連線池耗盡**: PostgreSQL 預設 max_connections=100，Django 連線池通常 20-50。長交易佔用連線導致新請求/任務等待或失敗
2. **鎖競爭加劇**: 長交易持有行級鎖/表級鎖，阻塞其他寫入操作
3. **WAL 膨脹**: 長交易產生大量 WAL，影響 checkpoint、replication、備份
4. **Rollback 成本高**: 任務失敗時回滾大量寫入，耗時且產生鎖爭用
5. **Worker 並發實際受限**: `prefetch_multiplier=1` + `concurrency=8` 理論支援 8 並發，但若每任務佔用連線 60s，實際吞吐量遠低於預期

## Why this matters

Celery worker 使用 prefork 模式，每個 process 維持獨立 DB 連線。長交易直接降低有效並發度。對於批次寫入任務，**必須**拆分交易或使用批次寫入優化。

## Recommended change

1. **拆分交易** - 以合理批次大小分批提交:
```python
BATCH_SIZE = 100
for i in range(0, len(ports), BATCH_SIZE):
    batch = ports[i:i+BATCH_SIZE]
    with transaction.atomic():
        Port.objects.bulk_create([
            Port(nmap_scan=nmap_scan, ...) for p in batch
        ])
```

2. **使用 `bulk_create` + 批次更新** - 已部分採用 (ai_scan)，需擴展到所有任務:
```python
# 避免逐筆 create()
Port.objects.bulk_create(port_objects, batch_size=100)
```

3. **分離讀寫交易** - 讀取掃描結果不需交易，僅寫入才需:
```python
# 讀取階段 (無交易)
scan_result = run_nmap(target)

# 寫入階段 (分批交易)
with transaction.atomic():
    nmap_scan = NmapScan.objects.create(...)

for batch in chunked(ports, 100):
    with transaction.atomic():
        Port.objects.bulk_create(...)
```

4. **考慮 `SELECT FOR UPDATE SKIP LOCKED` 模式** - 對於佇列式任務避免熱點競爭

5. **設定 `CONN_MAX_AGE=0` 或較小值** - 避免長連線持有 (但會增加連線建立開銷，需權衡)

## Verification

1. 監控 `pg_stat_activity` 觀察長交易: `SELECT pid, state, query_start, query FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '30 seconds';`
2. 壓測: 並發執行 8 個 Nmap 任務，觀察連線池使用率與任務排隊情況
3. 確認交易拆分後無資料不一致 (如 NmapScan 建立後 Port 寫入失敗的補償機制)

## Resolution criteria

- 所有批次寫入任務交易時間 < 5 秒
- 單一交易寫入記錄數 < 200 筆
- 並發 8 worker 時無連線池耗盡錯誤
- `pg_stat_activity` 中無長時間 idle in transaction 連線

## Notes

- Django `transaction.atomic()` 預設不支援嵌套提交 (savepoint 可用但複雜)
- `bulk_create` 不觸發 `post_save` signals，需確認無副作用
- 對於「全有或全無」語義需求，可考慮兩階段提交模式：先寫暫存表，最後原子性遷移
- 參考: Celery 官方文檔 "Database Transactions" 章節