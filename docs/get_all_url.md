# Get All URL App

`apps/scanners/get_all_url` 目前是基於 `GAU` 的 URL 收集入口，掛在 scanner namespace 的 crawler 子路由下。

## 公開 API 現況

來源：`apps/scanners/get_all_url/api.py`

- `POST /api/scanners/crawler/get_all_url`

## 實際職責

- 根據 `subdomain_id` 或 hostname 查找對應 `Subdomain`
- 驗證目標 `Subdomain` 是否 active / resolvable
- 派發 `scan_all_url` 任務

## 實作細節

### Subdomain 定位方式

優先順序如下：

1. `subdomain_id`
2. `name` 對應的 hostname
3. 若帶 `callback_step_id`，優先找該 step 所屬 target 下的 subdomain

### 狀態限制

若 subdomain：

- `is_active == False`
- 或 `is_resolvable == False`

則 API 會直接拒絕。

### 背景任務

- `scan_all_url`

此任務會執行 GAU，並將結果寫入 `URLResult`。

## 文檔注意事項

- 雖然路由叫 crawler，但實際核心是 GAU historical URL collection
- 應明確寫出它依賴已存在、可用的 `Subdomain`

## 相關檔案

- `apps/scanners/get_all_url/api.py`
- `apps/scanners/get_all_url/tasks/__init__.py`

---

_最后更新：2026-06-06_
