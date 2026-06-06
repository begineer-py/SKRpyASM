# Nmap Scanner App

`apps/scanners/nmap_scanner` 負責對已存在的 `IP` 資產派發 Nmap 掃描。

## 公開 API 現況

來源：`apps/scanners/nmap_scanner/api.py`

- `POST /api/scanners/nmap/start_scan`

## 實際職責

- 驗證目標 IP 是否已存在於資產庫
- 驗證傳入的 `seed_ids`
- 把 IP 與傳入 seed 建立關聯
- 避免對同一 IP 重複派發進行中的掃描
- 建立 `NmapScan` 記錄並觸發 Celery task

## 實作細節

### 前置條件

- 必須提供至少一個 `seed_id`
- 指定 IP 必須已存在於 `apps.core.models.IP`

### 去重邏輯

若同一 IP 已有 `PENDING` 或 `RUNNING` 的 `NmapScan`，API 會回 `409`。

### 背景任務

- `perform_nmap_scan`

## 文檔注意事項

- 不要把它寫成「任意 IP 掃描器」
- 目前它是面向已存在 core asset 的異步掃描派發器

## 相關檔案

- `apps/scanners/nmap_scanner/api.py`
- `apps/scanners/nmap_scanner/tasks/__init__.py`

---

_最后更新：2026-06-06_
