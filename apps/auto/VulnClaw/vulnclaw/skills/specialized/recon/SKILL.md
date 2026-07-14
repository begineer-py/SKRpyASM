---
name: recon-playbook
description: 偵察方法論 — 決策樹式攻擊面探索流程，涵蓋被動/主動/技術棧識別三階段，含工具組合建議與終止條件
tags: ['recon', 'methodology']
skill_type: documentation
short_description: 偵察方法論決策樹
---

# 偵察方法論 Playbook

本 Playbook 是 ReconAgent 的方法論層，提供「如何思考偵察」的決策框架。
它不是線性步驟清單（線性流程已在 system prompt 中），而是依目標類型與
階段產出對應決策樹，讓 Agent 在每個節點選擇正確工具組合與終止時機。

核心原則：
- **先查再掃**：每次發動掃描前，先用 `check_scanned_*` 工具確認資料庫現況
- **價值導向**：資源有限，優先投入高價值資產 (admin / api / dev / staging)
- **分階段收斂**：被動 → 主動 → 技術棧，每階段都有明確終止條件
- **不重複勞動**：非同步掃描結果用 `query_urls` 輪詢，不重複觸發

---

## 決策樹：目標類型分類

進入偵察前，先用 `get_target_context(target_name=...)` 取得目標輪廓，依下表分流：

| 目標特徵 | 偵察策略 | 首發工具 |
|---------|---------|---------|
| 單一 domain (無 IP 資訊) | 子域名優先擴展 | `run_subfinder_discovery` → DNS resolve → `run_nmap_port_scan` |
| 已知 IP 範圍 | 端口掃描優先 | `run_nmap_port_scan` (top-ports) → service fingerprint |
| Web 應用 (有 URL) | 內容發現優先 | `run_gau_url_discovery` + `run_katana_crawl` → `run_nuclei_tech_scan_subdomains` |
| API 端點 | 端點枚舉優先 | `run_gau_url_discovery` → `query_urls(has_endpoints=True)` → parameter mining |
| 雲端資產 (cloud) | 元數據優先 | 169.254.169.254 探測 → S3 bucket enum → IAM 枚舉 |
| 憑證/Token 已知 | 直接存取驗證 | 跳過被動偵察，直接進入主動驗證流程 |

決策規則：
- **若目標同時具備 domain 與 IP** → 走「子域名優先」，IP 由 DNS resolve 自動產出
- **若目標是純內網 IP (RFC1918)** → 跳過被動 OSINT，直接主動掃描
- **若資料庫已有該 Target 的 Subdomain/IP 記錄** → 跳過首發擴展，直接進入階段二

---

## 階段一：被動情報收集

### 子域名枚舉策略

| 情境 | 動作 |
|------|------|
| 首次掃描該 Target | `run_subfinder_discovery(overview_id=...)` 觸發非同步子域名收集 |
| 已有子域名記錄 | `check_scanned_subdomains(target_id=...)` 先查再決定是否補掃 |
| 子域名 < 10 個 | 補用 OSINT (crt.sh / DNS 歷史) 擴展來源 |
| 子域名 > 50 個 | 停止擴展，轉入高價值篩選 (見決策規則) |

工具組合建議：
- 主力：`run_subfinder_discovery` (聚合多來源)
- 補充：OSINT 透過 `run_command` 查詢 crt.sh / SecurityTrails API
- 驗證解析：等待 subfinder 任務完成後，用 `check_scanned_subdomains(resolvable_filter=True)` 確認可解析清單

### 已有資產盤點

在進行任何主動掃描前，**必須**呼叫：
- `check_scanned_ips(target_id=...)` — 確認資料庫現有 IP 與端口覆蓋狀況
- `check_scanned_subdomains(target_id=..., tech_analyzed_filter=False)` — 找出尚未做技術棧分析的子域名

決策規則：
- **若 IP 已有 `last_scan_type` 且 ports > 0** → 跳過重複 nmap，改用既有結果
- **若 Subdomain `is_tech_analyzed=False` 數量 > 0** → 優先排入 nuclei tech scan 佇列

### OSINT 情報來源

| 來源 | 用途 | 工具 |
|------|------|------|
| 搜尋引擎 dorking | 找暴露頁面、敏感路徑 | `run_command` (透過 FlareSolverr 處理反爬) |
| 憑證透明度日誌 (crt.sh) | 子域名擴展 | `run_command` curl 查詢 |
| DNS 歷史 (SecurityTrails) | 歷史 IP、子域名變遷 | `run_command` + API key |
| GitHub/GitLab 搜索 | 源碼洩露、配置洩露 | `run_command` (gh CLI / gitdorker) |
| Wayback Machine | 歷史 URL、已下架內容 | `run_gau_url_discovery` (內建整合) |

### 決策規則

> **若子域名 > 50 個 → 優先聚焦 high-value subdomain (admin/api/dev/staging/vpn/jenkins/gitlab)**
>
> 篩選條件：用 `check_scanned_subdomains` 取得清單後，
> 優先對名稱含 `admin|api|dev|staging|test|vpn|ci|jenkins|gitlab|grafana`
> 的子域名做 tech scan 與內容發現。

> **若所有子域名皆 `is_resolvable=False` → 回報 blocker，終止被動階段**
>
> 可能是 DNS 防火牆或目標已下線，應通知 AutomationAgent 評估是否換 IP 範圍。

---

## 階段二：主動偵察

### 端口掃描策略

| 情境 | 掃描模式 | 理由 |
|------|---------|------|
| 快速偵察 / 時間有限 | top-1000 TCP | 涵蓋 90% 常見服務 |
| 重點目標 / 完整覆蓋 | full 65535 TCP | 發現非標準端口上的服務 |
| 已知 SNMP/DNS/NTP 可能存在 | 加 UDP top-50 | 找社群協議漏洞 |
| 高安全目標 / 紅隊 | `-sV -A` 完整指紋 | 取得精確版本與腳本輸出 |

決策規則：
- **首輪一律用 top-1000**，等高價值目標出現再對特定 IP 補 full scan
- **服務指紋 (`-sV` / `-A`) 是必要項** — 沒有版本資訊無法做 CVE 對應
- **UDP 掃描成本高 (慢)** — 僅在提示有 SNMP/DNS/NTP/NetBIOS 指紋時觸發

### URL 內容發現

| 工具 | 來源 | 性質 | 適用情境 |
|------|------|------|---------|
| `run_gau_url_discovery` | Wayback / Common Crawl / OTX | 被動歷史 URL | 取得歷史攻擊面、已下架路徑 |
| `run_katana_crawl` | 目標即時回應 | 主動動態爬蟲 | SPA 單頁應用、JS 渲染內容 |

動態渲染觸發條件（任一成立即應使用 katana）：
- 偵測到 React/Vue/Angular 指紋 (`run_nuclei_tech_scan_subdomains` 已識別)
- `run_gau_url_discovery` 結果 < 10 個 URL (可能為 SPA，被動來源稀少)
- 首頁 HTML `<div id="root">` 或 `<div id="app">` 且 body 幾乎無內容

### 目錄爆破

當被動 + 爬蟲仍無法發現關鍵路徑時，使用 `run_command` 調用 ffuf / dirb / feroxbuster：
- 字典選擇：SecLists (`raft-medium-directories.txt`、`quickhits.txt`)
- 過濾：`-fc 404`、`-mc 200,301,302,401,403`
- 速率：若偵測到 WAF (見階段三)，先降低 rate 或改用隱蔽模式

> Payload 與字典細節請見 `search_skills("rapid checklist")` 與 `rapid-checklist` Skill，
> 本 Playbook 僅定義決策點。

### 決策規則

> **若只有 80/443 開放 → 跳過 UDP，專注 Web 攻擊面**
>
> 資料庫端口 (3306/5432/27017) 與管理端口 (22/3389/5985) 缺席時，
> UDP 與內網橫向機率低，應將預算投入 Web 內容發現。

> **若有資料庫端口 (3306/5432/27017) 暴露 → 考慮後滲透機會**
>
> 回報給 AutomationAgent 評估是否 `spawn_post_exploit_agent`，
> 並在偵察報告中標記為極高價值目標。

> **若有 6379 (Redis) / 27017 (Mongo) 無認證徵兆 → 立即標記為 critical**
>
> 未授權訪問是常見的快速淪陷點，應在 `notify_caller_agent` 中優先級最高。

---

## 階段三：技術棧識別

### Nuclei tech scan 的價值

`run_nuclei_tech_scan_subdomains` 是此階段的主力工具，能識別：
- CMS (WordPress / Drupal / Joomla / Ghost)
- 框架 (Spring Boot / Django / Laravel / Express / Next.js)
- CDN / WAF (Cloudflare / Akamai / Imperva / AWS WAF)
- 伺服器 (Nginx / Apache / IIS / Caddy)
- 第三方服務 (Jenkins / Grafana / Kibana / GitLab)

決策規則：
- **先批次掃所有子域名，再對高價值目標單獨深度掃**
- **掃描結果以 Subdomain `is_tech_analyzed=True` 標記** — 用 `check_scanned_subdomains` 追蹤進度

### CMS 偵測 → 路由到對應 Playbook

偵測到特定技術棧時，**不要憑記憶找 playbook**，應使用 `search_skills` 工具查找對應專項指引：

| Nuclei 偵測結果 | 搜尋關鍵字 | 預期路由 |
|----------------|-----------|---------|
| WordPress | `search_skills("wordpress")` | WP 外掛/主題枚舉、wpscan 流程 |
| Drupal | `search_skills("drupal")` | Drupalgeddon 系列檢測 |
| Jenkins | `search_skills("ci cd")` 或 `search_skills("jenkins")` | Script Console RCE、憑證洩露 |
| GitLab | `search_skills("gitlab")` | SSRF (CVE-2021-22201)、未授權註冊 |
| Spring Boot | `search_skills("spring boot actuator")` | Actuator env / heapdump 洩露 |
| Grafana | `search_skills("grafana")` | SSRF (CVE-2021-43798)、未授權儀表板 |
| Kibana | `search_skills("kibana")` | Prototype pollution、Console RCE |
| Tomcat | `search_skills("tomcat")` | Manager 部署、AJP Ghostcat |
| Next.js | `search_skills("nextjs")` | Middleware bypass、SSR 注入 |

### WAF 偵測

若 Nuclei tech scan 或響應行為顯示 WAF 指紋：
- **立即使用** `search_skills("waf bypass")` 查找繞過指引
- **降低掃描速率**：所有後續爆破改用低併發 + 隨機延遲
- **改用 FlareSolverr**：對反爬保護的頁面使用 `run_flaresolverr_crawler`
- **回報 blocker**：在偵察報告中明確標註 WAF 類型，供後續 Agent 評估

### 版本指紋 → CVE 查詢

| 取得資訊 | 動作 |
|---------|------|
| 精確版本號 (如 Apache 2.4.49) | `run_command` 查 NVD / searchsploit |
| 框架版本 (如 Spring Boot 2.5.x) | 查對應 CVE 列表，路由到專項 playbook |
| 不確定版本 | 用 `-A` 補掃或 `run_command` 抓 banner |

決策規則：
- **EOL 版本 (End-of-Life) 一律標記為高風險** — 通常無修補可用
- **版本號帶有 CVE > 9.0 的重大漏洞** → 優先級最高，立即回報

---

## 偵察終止條件

當**任一組合**滿足時，應停止偵察並進入報告階段：

- ✅ 已覆蓋所有子域名的端口掃描 (top-1000 或完整掃描)
- ✅ 已收集足夠 URL 進行漏洞測試 (建議 > 50 個 URL，可用 `query_urls` 計數)
- ✅ 技術棧已識別 (至少識別出主要框架，`is_tech_analyzed=True` 覆蓋率 > 80%)
- ✅ 已偵測到明顯高價值目標 (admin panel / API doc / 暴露的敏感端口)
- ⚠️ 達到 recursion_limit 或 time budget — 立即收斂並回報已完成部分
- ⚠️ 觸發 WAF 封鎖 / IP 黑名單 — 暫停主動掃描，評估是否換出口
- ⚠️ 所有子域名皆 `is_resolvable=False` — 目標可能已下線或受 DNS 防火牆保護

終止後動作：
1. 呼叫 `update_overview_status` 更新 Overview 狀態與摘要
2. 整理偵察報告 (格式見下節)
3. 呼叫 `notify_caller_agent(overview_id, message=...)` 回報 AutomationAgent

---

## 高價值目標識別

「什麼看起來值得打」的快速參考表：

| 發現 | 價值 | 下一步建議 |
|------|------|-----------|
| /admin, /manager, /console, /phpmyadmin | 極高 | 憑證測試、預設密碼、暴力破解 |
| login form (任何) | 高 | SQLi / 弱密碼 / XSS / 邏輯繞過 |
| /api/, /api/v1/, swagger.json, openapi.yaml | 高 | API 漏洞測試 (BOLA / mass assignment) |
| 上傳功能 (multipart form, /upload) | 高 | 文件上傳 RCE (副檔名繞過、Content-Type) |
| Spring Actuator (`/actuator`, `/actuator/env`) | 極高 | env / heapdump / jolokia RCE |
| .git/, .svn/, .hg/, backup.zip | 極高 | 源碼洩露 → 靜態審計路徑 |
| 3306 / 5432 / 27017 exposed | 高 | 資料庫弱密碼 / 未授權查詢 |
| 6379 (Redis) exposed | 極高 | 未授權訪問 → 寫 SSH key / cron RCE |
| 9200 (Elasticsearch) exposed | 極高 | 未授權查詢、scripting RCE |
| 2375/2376 (Docker API) exposed | 極高 | 容器逃逸 → 宿主 root |
| .env, config.php, wp-config.php | 極高 | 憑證洩露 → 橫向移動 |
| JWT token in response | 中高 | 算法篡改、密鑰爆破、jku 注入 |
| GraphQL endpoint (`/graphql`) | 高 | Introspection、batch query、IDO R |
| Debug mode (Werkzeug / Django debug) | 極高 | PIN leak / console RCE |
| Old HTTP methods (PUT / DELETE / TRACE) | 中高 | WebDAV PUT 上傳、TRACE XSS |

決策規則：
- **極高價值目標發現即應優先回報** — 不必等其他掃描完成
- **多個高價值目標並存** → 在報告中排序，建議 AutomationAgent 依序派工

---

## 偵察報告格式

ReconAgent 透過 `notify_caller_agent` 回報給 AutomationAgent 時，訊息應結構化包含以下欄位
(以 Markdown 或 JSON 字串傳遞)：

```text
## 偵察報告 — Target: <name>

### discovered_assets
- 子域名數量：<N> (可解析：<M>)
- IP 數量：<N>
- URL 數量：<N> (可用 query_urls 過濾)
- 開放端口清單：<port/service 列表>

### scans_started
- subfinder: <task_id 或完成>
- nmap: <task_id 或完成，範圍>
- gau: <task_id 或完成>
- katana: <task_id 或完成>
- nuclei tech: <task_id 或完成>

### tech_stack
- 主要框架：<例如 Nginx 1.18 + Spring Boot 2.5>
- CMS：<例如 WordPress 5.8>
- CDN/WAF：<例如 Cloudflare；無>

### high_value_targets
1. <URL/IP> — <類型> — <價值等級>
2. ...

### blockers
- <例如：偵測到 Cloudflare WAF，需評估繞過策略>
- <例如：所有 admin 路徑回 403，需憑證或 IP 白名單>
- <例如：無>

### recommended_next_actions
- <例如：spawn_post_exploit_agent 針對 6379 Redis>
- <例如：自行展開 SQLi 測試針對 /login>
- <例如：需要更多偵察 — 補 UDP 掃描與目錄爆破>
```

回報後應呼叫 `update_overview_status(new_status="recon_completed", new_summary=<精簡摘要>)`
讓 AutomationAgent 能透過 Overview 狀態追蹤進度。

---

## 與其他 Playbook 的協作

| 觸發條件 | 動作 | 目標 |
|---------|------|------|
| 偵察階段完成 | `notify_caller_agent` 回報報告 | AutomationAgent 評估下一步 |
| 偵測到高價值目標且需深入滲透 | AutomationAgent 決定 → `spawn_post_exploit_agent` | 用偵察成果作為 foothold 進行後滲透 |
| 偵測到 Web 漏洞方向 | `search_skills("web pentest")` 路由 | 載入 web-pentest / web-security-advanced |
| 偵測到特定技術棧 | `search_skills(<tech>)` 路由 | 載入對應專項 playbook |
| 漏洞確認且需報告 | AutomationAgent → `spawn_reporting_agent` | 整理發現、產出最終報告 |
| 遭遇 WAF / 阻礙 | `search_skills("waf bypass")` 或回報 blocker | 評估是否暫停或調整策略 |

關鍵協作原則：
- **ReconAgent 不做漏洞利用** — 偵察完成即回報，由 AutomationAgent 決派工
- **偵察成果是後續所有 Agent 的共用上下文** — 透過 Overview + ExecutionGraph 持久化
- **若偵察中發現 critical 級暴露 (如未授權 Redis)** — 可立即回報，不必等完整報告

---

*本 Playbook 由 ReconAgent 自動載入，方法論層指引；具體 payload 與字典請見
各專項 Skill 的 `search_skills("rapid checklist")` 與 `rapid-checklist` Skill。*
