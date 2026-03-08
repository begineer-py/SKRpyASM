# Core App 基礎設施

`core` 應用是整個系統的基石，負責定義核心數據模型、維護共享的 Schema 以及提供基礎的 API 路由結構。

## 功能概論

- **數據持久化**: 集中管理所有掃描發現的資產，包括 Target,## 核心數據結構

本應用定義了多個核心模型與對應的 Schema，用於在各 App 間傳遞數據：

- **`URLResult`**: 存儲所有發現的 URL 及其特徵。
    - **屬性**: `url`, `status_code`, `title`, `content_length`, `is_important`, `final_url` 等。
- **`AnalysisFinding`**: 存儲 AI 或正則分析發現的敏感資訊。
    - **屬性**: `pattern_name`, `line_number`, `match_content`, `match_start`, `match_end`。
- **`IP`**: 存儲解析出的 IP 地址及其地理/掃描資訊。
- **`Subdomain`**: 存儲子域名及其解析狀態（CDN, WAF 偵測結果）。

## API 接口 (共用部分)

詳見 `apps/core/schemas.py` 中的通用定義。其他 App 在處理批量 IDs 請求時，通常遵循以下結構成：

- **`ScanIdsSchema`**: 包含一個 `ids: List[int]`。
- **`ErrorSchema`**: 包含 `detail: str` 用於返回錯誤訊息。
 紀錄重要資產（如子域名、IP）的變更歷史。
- **共享數據結構**: 提供全系統統一的 Pydantic/Ninja Schema，確保各模塊間數據傳遞的一致性。
- **全局配置**: 提供日誌紀錄與函數調用追蹤等基礎功能輔助。

## API 接口

`apps/core/api.py` 主要作為 Router 實體，供其他應用掛載。

- **Router**: 本身不直接提供大量 Endpoint，而是作為基礎框架。
- **靜態資源**: 處理掃描產生的日誌或輸出文件訪問（視配置而定）。

## 內部 Tasks

核心應用不主動發起掃描任務，其內部的 Task 主要集中在數據清理（如果有設置）或輔助性的日誌維護。

## 核心模型 (Models)

- **Target**: 項目或目標組織。
- **Seed**: 掃描起點（Root Domain, IP 範圍, URL）。
- **Subdomain**: 發現的子域名資產，包含 WAF/CDN 識別資訊。
- **IP**: IP 地址資產與關聯端口。
- **URLResult**: 爬取到的網頁內容、表單、JS 文件與敏感資訊。
