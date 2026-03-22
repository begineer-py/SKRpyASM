# Nuclei Scanner App 漏洞與技術掃描

`nuclei_scanner` 集成了強大的 Nuclei 引擎，用於大規模的模板化漏洞掃描與技術棧識別。

## 功能概論

- **漏洞探測**: 利用 Nuclei 龐大的社群模板庫掃描已知漏洞。
- **技術棧識別**: 使用特定的技術識別模板（如 `sub_tech`, `url_tech`）自動檢測目標使用的 Web 框架與組件。
- **多目標支持**: 支持針對 IP、子域名或單個 URL 進行掃描。

## API 接口

詳見 `apps/nuclei_scanner/api.py`：

- **`POST /nuclei_scanner/ips`**: 對 IP 進行基礎設施與服務掃描。
    - **參數 (Payload)**:
        - `ids` (List[int], 必填): IP ID 列表。
        - `tags` (List[str], 選填): Nuclei 標籤（如 `cves`, `misconfig`）。
        - `callback_step_id` (int, 選填): 自動化循環中的 Step ID，完成後會喚醒。
- **`POST /nuclei_scanner/subdomains`**: 對子域名進行漏洞掃描。
    - **參數 (Payload)**: `ids`, `tags`, `callback_step_id` (同上)。
- **`POST /nuclei_scanner/urls`**: 對特定 URL 進行深度分析（包含智能技術棧偵測）。
    - **參數 (Payload)**: `ids`, `tags`, `callback_step_id` (同上)。

## 內部架構 (Factory Pattern)

本模塊為了擴展性與代碼複用，採用了工廠模式進行重構，核心邏輯位於 `apps/nuclei_scanner/tasks/asset_configs.py`：

- **`NucleiAssetConfig`**: 定義了各資產（IP, Subdomain, URL）掃描的差異化邏輯。
    - **`prepare_targets`**: 負責解析資產 ID、建立 `NucleiScan` 記錄，並根據類型生成初始 Tags。
- **`get_nuclei_asset_registry`**: 提供一個 Registry，讓執行器能獲取對應的資產配置。

### 智能 URL 掃描 (Smart URL Scanning)
針對 URL 資產，系統會自動根據 `URLResult` 記錄中已識別的 **Technologies (技術棧)**，通過 `map_tech_to_nuclei_tags` 助手將其映射為對應的 Nuclei 標籤（如發現 WordPress 則自動加入 `wordpress-tina` 等標籤），實現精確掃描。

### 執行與回調 (Callback)
- **`_execute_nuclei_batch`**: 通用執行器，負責建構 CLI 指令、並行執行掃描，並在結束後聚合結果。
- **自動化回調 (Callback)**: 若提供 `callback_step_id`，執行完畢後會自動將摘要發送至 `resume_step_execution`，驅動後續的 AI 評估環節。

## 內部 Tasks

- **`perform_nuclei_scan_batch`**: (由各資產 Task 調用的共用邏輯)。
- **`scan_subdomain_tech`**: 使用 Nuclei 指紋模板識別子域名技術棧。
- **`scan_url_tech_stack`**: 使用 Nuclei 指紋模板識別 URL 技術棧。
