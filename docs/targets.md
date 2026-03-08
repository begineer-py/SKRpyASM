# Targets App 目標管理

`targets` 應用負責掃描任務的初始化與目標規模管理。它是用戶與系統交互、啟動資產偵察的第一站。

## 功能概論

- **目標創建**: 定義新的掃描項目（Target）。
- **種子管理**: 向目標添加掃描起點（Seed），支持根域名、IP 段和具體網址。
- **資產關聯**: 確保所有掃描產生的資產都能追溯到對應的 Target。

## API 接口

詳見 `apps/targets/api.py`：

- **`POST /targets/`**: 創建一個新目標。
    - **參數 (Payload)**:
        - `name` (string, 必填): 目標名稱（如專案名稱）。
        - `description` (string, 選填): 目標描述。
- **`PUT /targets/{target_id}`**: 更新目標資訊。
    - **參數 (Path)**: `target_id` (int)。
    - **參數 (Payload)**: `name`, `description` (皆為選填)。
- **`GET /targets/list`**: 列出所有目標。
- **`POST /targets/{target_id}/seeds`**: 為目標添加掃描種子。
    - **參數 (Path)**: `target_id` (int)。
    - **參數 (Payload)**:
        - `value` (string, 必填): 種子內容（如 `example.com`, `1.1.1.1`）。
        - `type` (string, 必填): 類型，可選 `DOMAIN`, `IP`, `URL`。
- **`GET /targets/{target_id}/seeds`**: 列出某目標下的所有種子。
- **`DELETE /targets/seeds/{seed_id}`**: 刪除特定種子。

## 內部 Tasks

`targets` 應用通常不直接包含耗時的掃描任務，它的 API 會直接調用其他應用（如 `subfinder` 或 `nmap_scanner`）的任務。
