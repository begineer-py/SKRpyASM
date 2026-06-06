# Scheduler App

`apps/scheduler` 同時包含兩個層面：

- 對外的 `django_celery_beat` 任務管理 API
- 內部的 watchdog / cleanup / trigger 背景任務

## 實際職責

- 列出、建立、更新、刪除 `PeriodicTask`
- 暴露 task requirements 與 registered tasks 查詢接口
- 執行 watchdog、cleanup、內容抓取、Nmap/Nuclei/AI trigger 等排程任務

## 公開 API 現況

來源：`apps/scheduler/api.py`

- `GET /api/scheduler/tasks`
- `POST /api/scheduler/tasks`
- `GET /api/scheduler/tasks/{task_id}`
- `PUT /api/scheduler/tasks/{task_id}`
- `DELETE /api/scheduler/tasks/{task_id}`
- `GET /api/scheduler/schedules/intervals`
- `GET /api/scheduler/task-requirements`
- `GET /api/scheduler/registered_tasks`

## 背景任務

主要匯總在：

- `apps/scheduler/tasks/__init__.py`

目前活躍任務包含：

- `watchdog_stalled_overviews`
- `scan_ips_without_nmap_results`
- `scan_subdomains_without_url_results`
- `scan_urls_missing_response`
- `trigger_scan_ips_without_nuclei_results`
- `trigger_scan_subdomains_without_nuclei_results`
- `trigger_scan_urls_without_nuclei_results`
- `trigger_nuclei_tech_scan`
- `trigger_nuclei_tech_scan_subdomain`
- `trigger_scan_js`

## 實作細節

### 任務建立前驗證

`create_periodic_task()` 與 `update_periodic_task()` 會透過：

- `check_task_api_requirements()`

檢查指定 task 是否需要 AI API key 或其他條件。

### 任務來源查詢

- `registered_tasks` 會列出 Celery 中已登記的任務
- `task-requirements` 會回傳某 task 的需求資訊，供前端動態提示

### 調度模式

此 app 內很多 trigger task 並不是直接調用內部 service，而是透過 HTTP 回打本系統 API 來派發掃描或分析任務。

## 文檔注意事項

- 不要只把它寫成「定時任務 CRUD」
- 真正重要的還有：
  - watchdog
  - cleanup
  - 自動 trigger 掃描/分析

## 相關檔案

- `apps/scheduler/api.py`
- `apps/scheduler/agent_requirements.py`
- `apps/scheduler/tasks/__init__.py`
- `apps/scheduler/tasks/watchdog.py`
- `apps/scheduler/tasks/cleanup.py`

---

_最后更新：2026-06-06_
