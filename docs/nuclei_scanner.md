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
- **`POST /nuclei_scanner/subdomains`**: 對子域名進行漏洞掃描。
    - **參數 (Payload)**: `ids`, `tags` (同上)。
- **`POST /nuclei_scanner/subs_tech`**: 辨識子域名的技術堆疊（Web Tech Only）。
    - **參數 (Payload)**: `ids`, `tags` (同上)。
- **`POST /nuclei_scanner/urls`**: 對特定 URL 進行深度分析。
    - **參數 (Payload)**: `ids`, `tags` (同上)。
- **`POST /nuclei_scanner/urls_tech`**: 辨識 URL 級別的技術堆疊。
    - **參數 (Payload)**: `ids`, `tags` (同上)。
- **`POST /nuclei/urls`**: 特定網址掃描。
- **`POST /nuclei/urls_tech`**: 網址技術辨識接口。

## 內部 Tasks

- **`perform_nuclei_scans_for_ip_batch`**: 對 IP 列表執行漏洞掃描。
- **`scan_subdomain_tech`**: 使用 Nuclei 指紋模板識別子域名技術棧，結果寫入 `Subdomain` 的技術標籤欄位。
