# Nmap Scanner App 端口掃描

`nmap_scanner` 應用利用 Nmap 工具進行豐富的網絡資產探測，包括開放端口、服務版本以及操作系統識別。

## 功能概論

- **服務識別**: 通過 `-sV` 參數識別運行在端口上的具體服務與版本。
- **操作系統探測**: 通過 `-O` 參數嘗試識別目標系統環境。
- **異步處理**: 掃描任務由 Celery 異步執行，避免阻塞主 API。
- **自動入庫**: 發現的端口與服務資訊會自動與 `IP` 模型關聯。

## API 接口

詳見 `apps/nmap_scanner/api.py`：

- **`POST /nmap_scanner/start_scan`**: 針對指定 IP 發起 Nmap 掃描。
    - **參數 (Payload)**:
        - `ip` (string, 必填): 目標 IP。
        - `seed_ids` (List[int], 必填): 該 IP 關聯的種子 ID 列表。
        - `scan_ports` (Union[List[int], str]): 連接埠範圍，支持列表或 `top-1000`, `all`（預設 `top-1000`）。
        - `scan_rate` (int): 掃描速率（預設 `4`）。
        - `scan_service_version` (boolean): 是否啟用服務版本偵測 `-sV`（預設 `true`）。
        - `scan_os` (boolean): 是否啟用 OS 偵查 `-O`（預設 `false`）。
需要提供關聯的 Seed IDs 以便資產追蹤。

## 內部 Tasks

- **`perform_nmap_scan(scan_id, ip_address, nmap_args)`**: 核心掃描任務單元。
    1. **命令執行**: 使用 `shlex` 確保參數安全並執行 `nmap`。
    2. **結果解析**: 利用 `ElementTree` 解析 Nmap XML 輸出，提取端口、通訊協定、服務名稱與版本。
    3. **智能入庫**: 調用 `parse_and_save_nmap_results` 實現資產的 `update_or_create` 與 M2M 關聯建立。
    4. **持久化**: 完整存儲原始 XML 輸出於 `NmapScan` 模型中。
