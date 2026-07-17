# 開啟中的問題

| ID | Severity | Domain | Title | File | Status |
|----|----------|--------|-------|-------|--------|
| CR-0001 | P3 | Documentation | Agents.md 為 CLAUDE.md 的重複副本 | Agents.md | Accepted risk |
| CR-0002 | P2 | Frontend | 前端頁面檔案僅存在備份版本 | frontend/src/pages/*/ | Open |
| CR-0003 | P2 | Frontend | 前端響應式斷點未覆蓋所有要求的 viewport | frontend/src/global.css | Open |
| CR-0004 | P2 | Frontend | AI Workbench 使用固定 grid-template-columns 缺乏流體響應 | frontend/src/global.css | Open |
| CR-0005 | P3 | Frontend | 前端存在低於可讀性閾值的字體大小 | frontend/src/global.css | Open |
| CR-0006 | P2 | Frontend | 狀態資訊僅透過顏色表達，缺乏文字/圖示輔助 | frontend/src/global.css, SubAgentContainerBlock.tsx, ExecutionTimelineViewer.tsx | **Partially Fixed** |
| CR-0007 | P3 | Frontend | 輸入框使用 placeholder 當作 label | frontend/features/ai/pages/AICenterPage.tsx | Open |
| CR-0008 | P2 | Frontend | 全域樣式檔過大且職責不清 | frontend/src/global.css | Open |
| CR-0009 | P2 | Frontend | useEffect 缺乏清理函數可能導致記憶體洩漏 | frontend/features/ai/pages/AICenterPage.tsx | **Partially Fixed** |
| CR-0010 | P1 | Docker | docker-compose.yml 含硬編碼預設密碼 | docker/docker-compose.yml | Accepted risk |
| CR-0011 | P2 | Docker | docker-compose.yml 多服務直接暴露埠至宿主機 | docker/docker-compose.yml | **Partially Fixed** |
| CR-0012 | P2 | Celery | CELERY_IMPORTS 遺漏任務模組 | c2_core/settings.py | **Fixed - Verified** |
| CR-0013 | P2 | Cross-cutting | GraphQL 與 REST API 存在重複資料流 (22+ CRUD endpoints) | c2_core/urls.py, Hasura schema | Open |
| CR-0014 | P2 | Celery | Celery 任務缺乏 time_limit/soft_time_limit | apps/*/tasks/ | Open |
| CR-0015 | P2 | Celery | Celery 大型資料庫交易阻塞連線池 | apps/scanners/nmap_scanner/tasks/, apps/flaresolverr/tasks/, apps/scanners/subfinder/tasks/ | Open |
| CR-0016 | P3 | Celery | Celery 佇列隔離不足 (僅 default/ai_queue) | c2_core/celery.py, docker-compose.yml | Open |
| CR-0017 | P3 | Celery | Celery 結果保留與監控配置缺失 | c2_core/celery.py | Open |
| CR-0018 | P2 | Cross-cutting | 安全配置缺口 (CSRF/DEBUG/安全標頭/速率限制/硬編碼金鑰) | c2_core/settings.py | Open |
| CR-0019 | P2 | Cross-cutting | 錯誤處理與可觀測性不足 (Sentry/Prometheus/追蹤/日誌/告警) | c2_core/settings.py, 全專案 | Open |
| CR-0020 | P2 | Cross-cutting | 測試覆蓋率與 CI/CD 缺口 (覆蓋率門檻/契約測試/靜態分析/pre-commit) | requirements, CI, 測試配置 | Open |

*目前共 20 個開啟問題（15 Open、1 Fixed已驗證、3 Partially Fixed、2 Accepted risk）*

## Cycle 6 (Frontend + Verification) 複審摘要

| ID | 狀態變化 | 備註 |
|----|----------|------|
| CR-0002 | 維持 Open | src/pages/ 仍有 .bak 檔案，建議刪除 |
| CR-0003 | 維持 Open | 斷點未覆蓋 8 個標準 viewport (缺 360, 390, 768, 1366, 1440, 1920, 2560, 3840) |
| CR-0004 | 維持 Open | 固定 grid，中間尺寸擠壓，缺 768px 斷點；Shell 已簡化為雙欄但斷點策略未更新 |
| CR-0005 | 維持 Open | 17 處 < 12px 字體，最小 9.3px |
| CR-0006 | **Partially Fixed** | SubAgentContainerBlock、ExecutionTimelineViewer 已有文字/圖示；.tree-live-dot、.c2-badge、.ai-status-badge 仍需改善 |
| CR-0007 | 維持 Open | 聊天輸入框無 label/aria-label |
| CR-0008 | 維持 Open | global.css 1265 行未拆分 |
| CR-0009 | **Partially Fixed** | 5 個 useEffect 有 cancelled 模式，SSE/輪詢 effect 完整清理；loadThreads、handleSend 仍需改善 |
| CR-0011 | **Partially Fixed** | 關鍵風險已修復 (nginx 0.0.0.0→127.0.0.1, kali_sandbox host→bridge, flaresolverr 8192 移除)；內部服務 ports 映射待移除 |
| CR-0012 | **Fixed - Verified** | CELERY_IMPORTS 含 13 生產模組，79 任務全部可發現 |
| CR-0013 | 維持 Open | 22+ CRUD endpoints 重複，待移除 |
| CR-0014 | 維持 Open | 任務缺乏 time_limit/soft_time_limit |
| CR-0015 | 維持 Open | 大型交易阻塞連線池 |
| CR-0016 | 維持 Open | 佇列隔離不足 |
| CR-0017 | 維持 Open | 結果保留/監控配置缺失 |
| CR-0018 | 維持 Open | CSRF/DEBUG/安全標頭/速率限制/硬編碼金鑰 |
| CR-0019 | 維持 Open | Sentry/Prometheus/追蹤/日誌/告警缺口 |
| CR-0020 | 維持 Open | 覆蓋率門檻/契約測試/靜態分析/pre-commit 缺口 |

改善項目：
- SubAgentContainerBlock.tsx：標題列改為 `<button>` + `aria-expanded`/`aria-controls`，展開區塊用 `hidden` 屬性，提升無障礙
- ExecutionTimelineViewer.tsx：節點狀態篩選器有圖示 + 文字，狀態顯示多重編碼
- AICenterPage.tsx：SSE/輪詢 effect (Lines 326-394) 具備完整 cancelled 清理、maxAttempts 限制
- docker-compose.yml：nginx 綁定 127.0.0.1:80，kali_sandbox 改 bridge network，flaresolverr 8192 移除
- c2_core/settings.py：CELERY_IMPORTS 新增 3 個關鍵模組 (http_action, js_trigger, http_sender.tasks)