# Get All URL App 鏈接枚舉

`get_all_url` 應用利用 **GAU (GetAllUrls)** 工具，針對子域名進行全面、快速的被動 URL 發現。

## 功能概論

- **全面枚舉**: 調用 Docker 容器化的 `GAU` 工具，從多個被動來源（如 AlienVault, Wayback Machine 等）獲取子域名下已知的 URL。
- **擴展名過濾**: 自動排除圖片、字體、影片等非網頁內容的靜態資產。
- **資產管理**: 將發現的所有 URL 持久化存儲，並與對應的子域名及掃描任務建立多對多（M2M）關聯，供後續掃描（如 Nuclei, FlareSolverr）使用。

## API 接口

詳見 `apps/get_all_url/api.py`：

- **`POST /get_all_url/get_all_url`**: 針對指定的子域名啟動 GAU 枚舉任務。
    - **參數 (Payload)**:
        - `name` (string, 必填): 子域名名稱（Hostname）。
        - `scan_type` (string, 選填): `passive` (被動) 或 `initiative` (主動，預設被動)。

## 內部 Tasks

- **`scan_all_url(subdomain_id)`**:
    1. 啟動 `sxcurity/gau` Docker 容器執行掃描。
    2. 即時解析輸出並過濾符合子域名的有效 URL。
    3. **靜態過濾**: 使用預設黑名單過濾常見靜態文件擴展名。
    4. **資產入庫**: 批量創建 `URLResult` 並建立與 `Subdomain` 及 `URLScan` 的 M2M 關聯。
