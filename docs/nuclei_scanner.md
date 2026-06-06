# Nuclei Scanner App

`apps/scanners/nuclei_scanner` 負責對 IP、Subdomain、URL 進行漏洞掃描，以及對 URL/Subdomain 進行技術辨識。

## 公開 API 現況

來源：`apps/scanners/nuclei_scanner/api.py`

### 漏洞掃描

- `POST /api/scanners/vuln/ips`
- `POST /api/scanners/vuln/subdomains`
- `POST /api/scanners/vuln/urls`

### 技術辨識

- `POST /api/scanners/vuln/subs_tech`
- `POST /api/scanners/vuln/urls_tech`

## 實際職責

- 驗證指定 asset ID 是否存在
- 針對 URL 額外檢查是否已完成抓取
- 觸發對應 batch Celery task

## 實作細節

### URL readiness 檢查

URL 掃描與 URL 技術辨識都要求：

- `final_url` 已存在，或
- `content_length` 不為 0

若 URL 尚未被爬取，API 會拒絕掃描。

### 背景任務

- `perform_nuclei_scans_for_ip_batch`
- `perform_nuclei_scans_for_subdomain_batch`
- `perform_nuclei_scans_for_url_batch`
- `scan_subdomain_tech`
- `scan_url_tech_stack`

## 文檔注意事項

- 應把「漏洞掃描」與「技術辨識」分開說明
- 應補上 URL readiness gate，避免誤以為只要 URL ID 存在就能掃描

## 相關檔案

- `apps/scanners/nuclei_scanner/api.py`
- `apps/scanners/nuclei_scanner/tasks/__init__.py`
- `apps/scanners/nuclei_scanner/tasks/executor.py`

---

_最后更新：2026-06-06_
