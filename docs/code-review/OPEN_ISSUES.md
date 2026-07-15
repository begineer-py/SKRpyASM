# 開啟中的問題

| ID | Severity | Domain | Title | File | Status |
|----|----------|--------|-------|-------|--------|
| CR-0001 | P3 | Documentation | Agents.md 為 CLAUDE.md 的重複副本 | Agents.md | Accepted risk |
| CR-0002 | P2 | Frontend | 前端頁面檔案僅存在備份版本 | frontend/src/pages/*/ | Open |
| CR-0003 | P2 | Frontend | 前端響應式斷點未覆蓋所有要求的 viewport | frontend/src/global.css | Open |
| CR-0004 | P2 | Frontend | AI Workbench 使用固定 grid-template-columns 缺乏流體響應 | frontend/src/global.css | Open |
| CR-0005 | P3 | Frontend | 前端存在低於可讀性閾值的字體大小 | frontend/src/global.css | Open |
| CR-0006 | P2 | Frontend | 狀態資訊僅透過顏色表達，缺乏文字/圖示輔助 | frontend/src/global.css | Open |
| CR-0007 | P2 | Frontend | 輸入框使用 placeholder 當作 label | frontend/features/ai/pages/AICenterPage.tsx | Open |
| CR-0008 | P2 | Frontend | 全域樣式檔過大且職責不清 | frontend/src/global.css | Open |
| CR-0009 | P2 | Frontend | useEffect 缺乏清理函數可能導致記憶體洩漏 | frontend/features/ai/pages/AICenterPage.tsx | Open |
| CR-0010 | P1 | Docker | docker-compose.yml 含硬編碼預設密碼 | docker/docker-compose.yml | Accepted risk |
| CR-0011 | P2 | Docker | docker-compose.yml 多服務直接暴露埠至宿主機 | docker/docker-compose.yml | **Fixed - Pending Verification** |
| CR-0012 | P2 | Celery | CELERY_IMPORTS 遺漏任務模組 | c2_core/settings.py | **Fixed - Verified** |
| CR-0013 | P2 | Cross-cutting | GraphQL 與 REST API 存在重複資料流 (22+ CRUD endpoints) | c2_core/urls.py, Hasura schema | Open |
| CR-0014 | P2 | Celery | Celery 任務缺乏 time_limit/soft_time_limit | apps/*/tasks/ | Open |
| CR-0015 | P2 | Celery | Celery 大型資料庫交易阻塞連線池 | apps/scanners/nmap_scanner/tasks/, apps/flaresolverr/tasks/, apps/scanners/subfinder/tasks/ | Open |
| CR-0016 | P3 | Celery | Celery 佇列隔離不足 (僅 default/ai_queue) | c2_core/celery.py, docker-compose.yml | Open |
| CR-0017 | P3 | Celery | Celery 結果保留與監控配置缺失 | c2_core/celery.py | Open |
| CR-0018 | P2 | Cross-cutting | 安全配置缺口 (CSRF/DEBUG/安全標頭/速率限制/硬編碼金鑰) | c2_core/settings.py | Open |
| CR-0019 | P2 | Cross-cutting | 錯誤處理與可觀測性不足 (Sentry/Prometheus/追蹤/日誌/告警) | c2_core/settings.py, 全專案 | Open |
| CR-0020 | P2 | Cross-cutting | 測試覆蓋率與 CI/CD 缺口 (覆蓋率門檻/契約測試/靜態分析/pre-commit) | requirements, CI, 測試配置 | Open |

*目前共 20 個開啟問題（18 Open、1 Fixed已驗證、2 Accepted risk、1 Fixed待驗證）*

## Cycle 6 (Frontend) 複審摘要

| ID | 狀態變化 | 備註 |
|----|----------|------|
| CR-0002 | 維持 Open | src/pages/ 仍有 .bak 檔案，建議刪除 |
| CR-0003 | 維持 Open | 斷點未覆蓋 8 個標準 viewport |
| CR-0004 | 維持 Open | 固定三欄 grid，中間尺寸擠壓，缺 768px 斷點 |
| CR-0005 | 維持 Open | 17 處 < 12px 字體，最小 9.3px |
| CR-0006 | 維持 Open | 徽章/狀態點/選中態僅用顏色 |
| CR-0007 | 維持 Open | 聊天輸入框無 label/aria-label |
| CR-0008 | 維持 Open | global.css 1265 行未拆分 |
| CR-0009 | 部分改善 | 大多數 effect 有 cancelled，但 loadThreads/handleSend 依賴項問題 |
| 新增 | 無 | 本輪專注複審既有問題 |

改善項目：
- SubAgentContainerBlock.tsx：標題列改為 `<button>` + `aria-expanded`/`aria-controls`，展開區塊用 `hidden` 屬性，提升無障礙