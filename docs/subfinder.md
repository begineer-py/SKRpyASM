# Subfinder App 子域名發現

`subfinder` 應用集成多種被動與主動工具，用於快速發現目標的所有子域名。

## 功能概論

- **多模式枚舉**: 調用 `subfinder` 工具進行被動發現，調用 `amass` 進行深度掃描（視配置）。
- **資產自動更新**: 自動將掃描結果與資料庫比對，更新子域名的在線/離線狀態。
- **自動關聯**: 將發現的域名自動與其來源種子（Seed）進行關聯。

## API 接口

詳見 `apps/subfinder/api.py`：

- **`POST /subfinder/start_subfinder`**: 對指定的 DOMAIN 種子啟動一個完整的偵察鏈。
    - **參數 (Payload)**:
        - `seed_id` (int, 必填): 類別必須為 `DOMAIN` 且狀態為 `is_active` 的種子 ID。
    - **回應**: 返回包含掃描 ID 的 `SubfinderScanSchema`，並立即在此背景啟動 Celery 任務。
- **`GET /subfinder/results/{seed_id}`**: 獲取特定種子的掃描結果摘要。

## 內部 Tasks

本模塊採用任務鏈（Task Chaining）架構，自動完成從發現到解析的完整流程：

- **`start_subfinder(scan_id)`**: 
    1. 調用 `subfinder` 被動枚舉子域名。
    2. 調用 `utils.update_subdomain_assets` 進行高效的資產同步。
    3. **鏈接下一環節**: 觸發 `resolve_dns_for_seed`。
- **`resolve_dns_for_seed(seed_id, ...)`**:
    1. 利用 **`dnsx`** 對所有發現的子域名進行 A/AAAA/CNAME 解析。
    2. 自動創建或更新對應的 `IP` 資產物件。
    3. **鏈接下一環節**: 觸發 `check_protection_for_seed`。
- **`check_protection_for_seed(seed_id, ...)`**:
    1. 利用 **`cdncheck`** 識別資產是否受 CDN（如 Cloudflare, Akamai）或 WAF 保護。
    2. 使用 `eventlet.GreenPool` 進行高並發檢測。
- **`start_amass_scan(scan_id)`**: 
    - 使用 **`Amass`** 工具進行深度的被動或主動枚舉（重型模式），完成後同樣會觸發上述 DNS 解析鏈。
