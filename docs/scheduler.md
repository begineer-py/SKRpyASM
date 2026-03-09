# Scheduler App 自動化編排

`scheduler` 是系統的自動化中心與任務觸發器，它監控系統狀態並自動啟動後續掃描。

## 功能概論

- **狀態驅動掃描**: 根據資產的發現情況自動鏈接下一個掃描動作（例如：發現 IP 後自動啟動 Nmap）。
- **資產流水線**: 管理從「域名發現 -> IP 掃描 -> 技術識別 -> AI 分析」的完整自動化流程。
- **分批處理**: 通過 Celery Beat 定時觸發，合理控制系統負載。

## API 接口

通常作為內部調度使用，部分調度策略可通過 `api.py` 查詢或臨時觸發。
關於自動化任務的詳細邏輯，請參閱 [自動化任務系統 (Auto Tasks)](file:///home/hacker/Desktop/share/C2_Django_AI_git/docs/auto_tasks.md)。
關於 API Key 的管理，請參閱 [API Keys 管理系統](file:///home/hacker/Desktop/share/C2_Django_AI_git/docs/api_keys.md)。

詳見 `apps/scheduler/api.py`：

- **`POST /scheduler/tasks`**: 創建一個新的週期性任務（自動處理 Interval/Crontab 創建）。
    - **參數 (Payload)**:
        - `name` (string, 必填): 任務名稱（需唯一）。
        - `task` (string, 必填): Celery 任務路徑（如 `apps.subfinder.tasks.start_subfinder`）。
        - `interval` (object, 選填): 頻率配置，包含 `every` (int) 與 `period` (`seconds`, `minutes`, `hours`, `days`)。
        - `crontab` (object, 選填): 定時配置，包含 `minute`, `hour`, `day_of_week` 等。
        - `args`, `kwargs` (JSON, 選填): 傳遞給任務的參數。
- **`PUT /scheduler/tasks/{task_id}`**: 更新定時任務設定。
- **`GET /scheduler/tasks`**: 列出所有當前任務與最後執行狀態。

## 內部 Tasks (Triggers)

詳見 `apps/scheduler/tasks/`：

- **`ai_triggers.py`**:
    - `trigger_scan_ips_without_ai_results`: 自動對未分析的 IP 啟動 AI 任務。
    - `trigger_scan_subdomains_without_ai_results`: 自動對新子域名啟動 AI 分析。
- **`nuclei_triggers.py`**:
    - 自動對未掃描漏洞的資產啟動 Nuclei。
- **`nmap_triggers.py`**:
    - `scan_ips_without_nmap_results`: 自動對新 IP 啟動端口掃描。
- **`content_triggers.py`**:
    - `scan_subdomains_without_url_results`: 自動對子域名進行 URL 爬取。
    - `scan_urls_missing_response`: 自動抓取 PENDING 狀態的 URL 內容。
