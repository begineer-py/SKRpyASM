# C2 Django AI 技術文檔中心 (Documentation Center)

歡迎來到 C2 Django AI 的技術文檔中心。本文件庫詳細介紹了系統中各個應用模塊的功能、API 接口以及內部任務流。

## 核心架構模塊

### 1. 基礎設施與核心
- **[Core](./core.md)**: 系統基礎模型（Target, Seed, Subdomain, IP）與共享數據結構。
- **[Targets](./targets.md)**: 目標與種子管理，資產偵察的起點。

### 2. 資產偵察與發現
- **[Subfinder](./subfinder.md)**: 子域名枚舉與主動發現。
- **[Nmap Scanner](./nmap_scanner.md)**: 端口掃描與服務識別。
- **[Get All URL](./get_all_url.md)**: 網頁鏈接爬取與端點映射。

### 3. 深層分析與掃描
- **[FlareSolverr](./flaresolverr.md)**: 反爬蟲繞過、網頁內容抓取與 JavaScript 分析。
- **[Nuclei Scanner](./nuclei_scanner.md)**: 基於模板的漏洞掃描與技術棧識別。
- **[Analyze AI](./analyze_ai.md)**: AI 驅動的自動化安全分析與資產分類。

### 4. 工具與自動化
- **[Scheduler](./scheduler.md)**: 自動化掃描觸發器與任務編排中心。
- **[HTTP Sender](./http_sender.md)**: 網絡請求工具與 Fuzzing 支持。

---

## 快速導航
如果您是第一次使用本系統，建議先閱讀項目的 [README.md](../README.md) 和 [BUILD_GUIDE.md](../BUILD_GUIDE.md)。
