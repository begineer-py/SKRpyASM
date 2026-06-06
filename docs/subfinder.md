# Subfinder App

`apps/scanners/subfinder` 提供 domain recon 鏈的兩個入口：Subfinder 與 Amass。

## 公開 API 現況

來源：`apps/scanners/subfinder/api.py`

- `POST /api/scanners/subdomain/start_subfinder`
- `POST /api/scanners/subdomain/start_amass`

## 實際職責

- 驗證 `Seed` 是否存在且為活躍 `DOMAIN`
- 建立 `SubfinderScan` 或 `AmassScan` 記錄
- 觸發對應 Celery recon chain

## 實作細節

### Subfinder 路徑

- 用於啟動基礎子域名發現流程

### Amass 路徑

- 用於啟動增強發現流程
- 有額外限制：
  - 必須先存在對應 seed 的 `SubfinderScan`

### 通用防呆

- 非 `DOMAIN` seed 會直接拒絕
- 非活躍 seed 會直接拒絕
- 若已有進行中的掃描，會回 `409`

### 背景任務

- `start_subfinder`
- `start_amass_scan`
- 以及相關子任務：
  - `dns_tasks.py`
  - `protection_tasks.py`
  - `amass_brute.py`

## 文檔注意事項

- 應把它描述成 recon chain dispatcher，而不只是單次工具包裝器
- 應明確寫出 Amass 依賴先跑過 Subfinder

## 相關檔案

- `apps/scanners/subfinder/api.py`
- `apps/scanners/subfinder/tasks/__init__.py`
- `apps/scanners/subfinder/tasks/subfinder_tasks.py`

---

_最后更新：2026-06-06_
