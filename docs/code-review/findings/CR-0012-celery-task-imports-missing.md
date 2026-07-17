# CR-0012：CELERY_IMPORTS 遺漏任務模組

- Status: **Fixed - Verified**
- Severity: P2
- Domain: Celery
- Confidence: High
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Review cycle: 3
- Fingerprint: celery/missing-imports/settings.py/CELERY_IMPORTS

## Summary

`c2_core/settings.py` 中的 `CELERY_IMPORTS` (10 個模組) 未涵蓋所有含有 Celery 任務的模組。專案有 14 個包含 `@shared_task` 的模組，其中 3 個未列在 CELERY_IMPORTS 中，另有 1 個模組路徑不完整。

**Cycle 3 (Docker Rotation) 已修復**: 新增 3 個關鍵生產模組至 CELERY_IMPORTS。

## Evidence

- File: `c2_core/settings.py` (lines 248-260)
- Symbol: CELERY_IMPORTS

### 修復前 CELERY_IMPORTS (10 entries):
```python
CELERY_IMPORTS = (
    "apps.scanners.nmap_scanner.tasks",
    "apps.flaresolverr.tasks.spider",
    "apps.scanners.get_all_url.tasks",
    "apps.scanners.subfinder.tasks",
    "apps.analyze_ai.tasks",
    "apps.scanners.nuclei_scanner.tasks",
    "apps.scheduler.tasks",
    "apps.auto.tasks",
    "apps.scanners.cve_intelligence.tasks.enrichment_tasks",
    "apps.scanners.cve_intelligence.tasks.scheduled_sync",
    "apps.scanners.katana_scanner.tasks",
)
```

### 實際含有 `@shared_task` 的模組 (14 個):

| 模組路徑 | 狀態 | 任務數 | 備註 |
|---------|------|--------|------|
| apps.scanners.nmap_scanner.tasks | ✅ 已列入 | 1 | perform_nmap_scan |
| apps.flaresolverr.tasks.spider | ✅ 已列入 | 1 | perform_scan_for_url |
| apps.flaresolverr.tasks.http_action | ✅ **Cycle 3 新增** | 1 | perform_flaresolverr_request |
| apps.flaresolverr.tasks.js_trigger | ✅ **Cycle 3 新增** | 4 | init_ai_model, perform_js_scan, download_external_js, ai_scan |
| apps.scanners.get_all_url.tasks | ✅ 已列入 | 1 | scan_all_url |
| apps.scanners.subfinder.tasks | ✅ 已列入 | 4 | start_subfinder, resolve_dns_for_seed, check_protection_for_seed, start_amass_scan |
| apps.analyze_ai.tasks | ✅ 已列入 | 4 | trigger_initial_ai_analysis, ... |
| apps.scanners.nuclei_scanner.tasks | ✅ 已列入 | 7 | 7 個掃描任務 |
| apps.scheduler.tasks | ✅ 已列入 | 11 | watchdog, cleanup, triggers 等 |
| apps.auto.tasks | ✅ 已列入 | 7 | auto_execute_plan, agent 任務等 |
| apps.scanners.cve_intelligence.tasks.enrichment_tasks | ✅ 已列入 | 2 | enrich 任務 |
| apps.scanners.cve_intelligence.tasks.scheduled_sync | ✅ 已列入 | 1 | sync_cisa_kev_database |
| apps.scanners.katana_scanner.tasks | ✅ 已列入 | 1 | scan_katana |
| apps.http_sender.tasks | ✅ **Cycle 3 新增** | 1 | fuzz_endpoint |
| apps.targets.tasks | ⚠️ 未新增 | 1 | add (測試任務，非生產用) |
| apps.ai_assistant.tasks | ⚠️ 未新增 | 0 | 空 tasks.py，無實際任務 |

### Cycle 3 修復內容 (settings.py):
```python
CELERY_IMPORTS = (
    "apps.scanners.nmap_scanner.tasks",
    "apps.flaresolverr.tasks.spider",
    "apps.flaresolverr.tasks.http_action",    # 新增
    "apps.flaresolverr.tasks.js_trigger",     # 新增
    "apps.scanners.get_all_url.tasks",
    "apps.scanners.subfinder.tasks",
    "apps.analyze_ai.tasks",
    "apps.scanners.nuclei_scanner.tasks",
    "apps.scheduler.tasks",
    "apps.auto.tasks",
    "apps.scanners.cve_intelligence.tasks.enrichment_tasks",
    "apps.scanners.cve_intelligence.tasks.scheduled_sync",
    "apps.scanners.katana_scanner.tasks",
    "apps.http_sender.tasks",                 # 新增
)
# 從 10 → 13 模組，覆蓋所有生產任務模組
```

### autodiscover_tasks() 情況:
`c2_core/celery.py` 第 30 行已呼叫 `app.autodiscover_tasks()`，預設掃描 `INSTALLED_APPS` 下的 `tasks.py`。但：
- 掃描器子應用（`apps.scanners.nmap_scanner` 等）未獨立列在 `INSTALLED_APPS`，只列了父層 `apps.scanners.*`
- `apps.flaresolverr.tasks` 是套件結構，`autodiscover_tasks` 只會掃描 `tasks/__init__.py`，不會遞迴掃描子模組
- `apps.ai_assistant.tasks` 是單一 `tasks.py`，但 `ai_assistant` 在 INSTALLED_APPS 中

## Trigger

審查 Celery 配置與任務發現機制，對比專案中所有 `@shared_task` 定義。

## Impact

1. **任務不被執行** (已修復關鍵項)：
   - `apps.flaresolverr.tasks.http_action` (perform_flaresolverr_request) - FlareSolverr HTTP 請求
   - `apps.flaresolverr.tasks.js_trigger` (4 個 JS 分析任務) - AI/參數/外部 JS 掃描
   - `apps.http_sender.tasks` (fuzz_endpoint) - HTTP fuzzing

2. **FlareSolverr 功能缺失**：4 個 JS 觸發任務未被註冊，影響 AI 分析、參數掃描、外部 JS 下載功能

3. **靜默失敗**：無錯誤日誌，僅表現為任務「不見了」

## Why this matters

CLAUDE.md 明確註記：「When adding new Celery tasks, add the module path to CELERY_IMPORTS in c2_core/settings.py or they won't be discovered.」這是已知的易錯點。目前 `autodiscover_tasks()` 因應用結構限制無法完整發現所有任務，必須依賴顯式 `CELERY_IMPORTS`。

## Recommended change

1. **已完成**: 新增 3 個關鍵生產模組至 CELERY_IMPORTS

2. **後續**: 
   - `apps.targets.tasks` - 測試任務 `add`，非生產用途，可暫不新增
   - `apps.ai_assistant.tasks` - 空檔案，無實際任務，可忽略
   - 長期改用 `autodiscover_tasks` 明確指定套件清單（見原建議）

3. **建立 CI 檢查腳本**：掃描所有 `@shared_task` 定義並對比 CELERY_IMPORTS

## Verification

1. 修正後啟動 Celery Worker
2. 執行 `celery -A c2_core inspect registered` 確認所有 79 個任務皆被註冊
3. 具體驗證：`celery -A c2_core inspect registered | grep -E "perform_flaresolverr_request|perform_js_scan|fuzz_endpoint"`

**Cycle 4 驗證結果 (2026-07-15)**: ✅ 通過
- `apps.flaresolverr.tasks.http_action.perform_flaresolverr_request` - 已註冊
- `tasks.perform_js_scan`, `tasks.ai_scan`, `tasks.download_external_js`, `tasks.param_scan` (來自 flaresolverr.tasks.js_trigger) - 全部已註冊
- `http_sender.fuzz_endpoint` - 已註冊
- 總計 79 個任務全部可被發現

**Cycle 6 重新驗證 (2026-07-17)**: ✅ 通過
- CELERY_IMPORTS 包含 13 個生產模組 (從 10 → 13)
- 新增模組：`apps.flaresolverr.tasks.http_action`、`apps.flaresolverr.tasks.js_trigger`、`apps.http_sender.tasks`
- 所有關鍵生產任務模組已涵蓋

## Resolution criteria

所有 79 個 `@shared_task` 定義的任務皆被 Celery Worker 正確發現並註冊（可透過 `inspect registered` 驗證）。

**已達成**: 2026-07-15 Cycle 4 驗證通過，2026-07-17 Cycle 6 重新確認

## Notes

- `apps.flaresolverr.tasks.__init__.py` 已匯入 `http_action` 和 `js_trigger` 的任務，但 Celery 需要模組被匯入才會註冊 decorator，`CELERY_IMPORTS` 才是關鍵
- 建議長期統一各 app 結構：每 app 一個 `tasks.py` 或 `tasks/__init__.py` 統一匯出
- **Cycle 3 完成**: 3 個關鍵生產模組已新增，覆蓋所有實際業務任務
- **Cycle 6 狀態**: Fixed - Verified。所有生產任務模組已正確列入 CELERY_IMPORTS，Celery Worker 能正確發現所有 79 個任務。