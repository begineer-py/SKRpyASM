# Targets App

`apps/targets` 是系統的目標與種子配置入口。它不只是 CRUD，新增 seed 時還會同步建立部分核心資產。

## 實際職責

- 建立、查詢、更新、刪除 `Target`
- 為目標新增、列出、刪除 `Seed`
- 依 seed 類型同步建立對應 core asset

## 公開 API 現況

來源：`apps/targets/api.py`

- `GET /api/targets/list`
- `POST /api/targets/`
- `GET /api/targets/{target_id}`
- `PUT /api/targets/{target_id}`
- `DELETE /api/targets/{target_id}`
- `POST /api/targets/{target_id}/seeds`
- `GET /api/targets/{target_id}/seeds`
- `DELETE /api/targets/seeds/{seed_id}`

## 實作細節

### seed 新增時的副作用

新增 seed 後，系統會依 `Seed.type` 自動補建核心資產：

- `URL`
  - 建立 `URLResult`
  - `content_fetch_status` 預設為 `PENDING`
- `DOMAIN`
  - 建立 `Subdomain`
  - 建立 `which_seed` 關聯
- `IP_RANGE`
  - 若是單一 IP 而不是 CIDR 網段，建立 `IP`
  - 建立 `which_seed` 關聯

### 非同步 ORM

這個 app 目前大量使用 Django async ORM：

- `aget`
- `acreate`
- `adelete`
- `aget_or_create`

## 文檔注意事項

- 不要只寫成 target/seed CRUD
- 應補上「新增 seed 會同步建核心資產」這個行為

## 相關檔案

- `apps/targets/api.py`
- `apps/targets/schemas.py`

---

_最后更新：2026-06-06_
