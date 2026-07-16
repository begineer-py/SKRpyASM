# 任務：安全整合兩個 Git Worktree，完成測試後合併至 main

你現在位於以下 Git Repository：

```text
/home/hacker/Desktop/share/AI/c2-source
```

目前有三個 worktree：

```text
/home/hacker/Desktop/share/AI/c2-source
  branch: main
  HEAD: f1159ed

/home/hacker/Desktop/share/AI/c2-source-ai-center-content-first
  branch: work/ai-center-content-first
  HEAD: 822b346，加上大量尚未提交修改

/home/hacker/Desktop/share/AI/c2-source-target-asset-map-hasura
  branch: work/target-asset-map-hasura
  HEAD: 822b346，加上大量尚未提交修改
```

你的任務是：

1. 審查並整理兩個 worktree 的修改。
2. 分別測試並提交兩個功能分支。
3. 建立安全的 integration branch。
4. 將兩個功能分支合理整合。
5. 處理跨分支衝突與相容性問題。
6. 執行完整前端、後端與 Docker 測試。
7. 確認網站可以實際訪問。
8. 確認 Docker 容器正常且健康。
9. 檢查是否發生版面 collapse、功能退化、API 契約錯誤或資料流中斷。
10. 全部通過後才合併至 `main` 並建立最終提交。

---

# 核心原則

## 禁止無腦合併

不要只是連續執行：

```bash
git add .
git commit
git merge
```

必須先理解每一組修改的目的、相依性與風險。

必須特別檢查：

* 同一個元件被兩個分支以不同方式修改。
* 一個分支刪除的元件是否仍被另一個分支引用。
* package dependency 是否衝突。
* GraphQL source 與 generated files 是否一致。
* 前端期待的 API 是否真的存在。
* Docker、Django settings 與 Compose 修改是否會影響開發環境。
* UI 是否因 CSS、layout 或 container 修改而 collapse。
* 測試是否只是假通過，實際瀏覽器仍然無法使用。

## 不得執行破壞性操作

沒有明確必要時，不得執行：

```bash
git reset --hard
git clean -fd
git push --force
git checkout -- .
git restore .
```

不得刪除使用者尚未提交的修改。

所有現有工作必須先建立安全快照。

## 問題分級

### 可以自行處理

以下問題可以自行修復，但必須記錄：

* import 順序。
* lint 或 format。
* 簡單 TypeScript 型別錯誤。
* 明確的檔案移動。
* lockfile 重新生成。
* 已能從上下文判斷的機械式 merge conflict。
* 測試檔路徑或 mock 小幅調整。

### 必須立即停止並回報

出現以下情況時，不得擅自選擇其中一邊：

* 兩個分支對同一功能有互斥的產品設計。
* 合併會刪除其中一個主要功能。
* API request／response schema 不相容。
* 資料庫 migration 或 Hasura metadata 存在衝突。
* 必須大量重寫其中一個分支才能繼續。
* 無法判斷某個未追蹤檔案是否應納入版本控制。
* 合併前原本就有測試失敗。
* Docker 容器持續 unhealthy 或反覆重啟。
* 瀏覽器頁面無法載入，且原因不是單純的小型語法問題。
* 修復需要改變功能需求或資料模型。

回報格式：

```text
[INTEGRATION BLOCKER]

問題：
證據：
影響範圍：
可能原因：

方案 A：
優點：
缺點：

方案 B：
優點：
缺點：

建議：
```

不要只回報「有 conflict」，必須說明衝突代表的實際行為差異。

---

# Phase 0：讀取專案規範

開始修改前，先閱讀：

```text
CLAUDE.md
Agents.md
DESIGN.md
README.md
Makefile
frontend/package.json
docker/docker-compose.yml
Dockerfile
docker/kali_sandbox/Dockerfile
```

確認：

* 專案指定的開發流程。
* 前端 package manager。
* lint、typecheck、test、build 指令。
* Docker Compose 啟動方式。
* Django check 與測試方式。
* GraphQL codegen 指令。
* 服務端口。
* healthcheck 定義。
* 哪些檔案是 generated files。

優先遵守 repository 已存在的 Makefile、CLAUDE.md 與 package scripts，不要自行發明另一套流程。

---

# Phase 1：建立完整安全快照

先在每個 worktree 記錄狀態：

```bash
git status --short
git diff --stat
git diff --name-status
git rev-parse HEAD
git branch --show-current
```

對三個 worktree 都執行。

將結果整理成：

```text
main：
- 修改檔案：
- 未追蹤檔案：
- 是否包含功能修改：
- 是否包含環境修改：

ai-center-content-first：
- 修改檔案：
- 新增檔案：
- 刪除檔案：
- 已暫存檔案：

target-asset-map-hasura：
- 修改檔案：
- 新增檔案：
- generated files：
- 測試檔案：
```

## 保護 main 的 dirty working tree

目前 `main` 有以下修改：

```text
CLAUDE.md
Dockerfile
c2_core/settings.py
docker/docker-compose.yml
docker/kali_sandbox/Dockerfile
frontend/src/components/SubAgentContainerBlock.tsx
.claude/
.playwright-mcp/
Agents.md
```

不得直接在 dirty `main` 上合併。

先建立安全整合分支：

```bash
cd /home/hacker/Desktop/share/AI/c2-source
git switch -c integration/ai-center-asset-map
```

然後建立包含未追蹤檔案的 stash：

```bash
git stash push -u -m "pre-integration-main-snapshot"
```

確認：

```bash
git status
git stash list
```

工作區必須乾淨。

注意：

* 不要立即把這個 stash 混入功能分支。
* 完成功能分支整合後，再恢復並逐項判斷。
* `.claude/`、`.playwright-mcp/` 等工具設定不得未經檢查直接提交。
* 如果這些資料夾包含 cache、session、runtime 資料或 secret，應加入 `.gitignore`，不能提交。

---

# Phase 2：審查 AI Center 分支

工作目錄：

```bash
cd /home/hacker/Desktop/share/AI/c2-source-ai-center-content-first
```

分支：

```text
work/ai-center-content-first
```

先查看：

```bash
git status
git diff --cached
git diff
git diff --stat
```

目前特別需要檢查：

```text
DESIGN.md
apps/core/api.py
frontend/package.json
frontend/package-lock.json
frontend/src/app/layouts/MainLayout.tsx
frontend/src/components/Navbar.tsx
frontend/src/components/SubAgentContainerBlock.tsx
frontend/src/features/ai/components/AgentPanel.tsx
frontend/src/features/ai/components/ChatHeader.tsx
frontend/src/features/ai/components/ExecutionLogsPanel.tsx
frontend/src/features/ai/components/Sidebar.tsx
frontend/src/features/ai/components/ThreadEventsPanel.tsx
frontend/src/features/ai/components/WorkbenchControls.tsx
frontend/src/features/ai/components/TargetConversationGroups.tsx
frontend/src/features/ai/pages/AICenterPage.tsx
frontend/src/features/ai/pages/ExecutionMonitorPage.tsx
frontend/src/features/ai/pages/execution-monitor/
frontend/src/global.css
frontend/src/main.tsx
test_execution_api.py
```

## 必須確認的語義

1. `ExecutionLogsPanel.tsx` 被刪除是否是刻意設計。
2. 全 repository 是否還有引用：

```bash
rg "ExecutionLogsPanel"
```

3. `TargetConversationGroups.tsx` 是否取代舊有元件。
4. `ExecutionMonitorPage.tsx` 與新目錄 `execution-monitor/` 的責任是否重疊。
5. `apps/core/api.py` 修改是否與前端 request／response 相符。
6. `test_execution_api.py` 為什麼已暫存，但其他修改未暫存。
7. `main.tsx` 修改是否會影響全域 provider、router、GraphQL client 或 CSS 載入。
8. `global.css` 是否存在過度廣泛 selector，例如：

```css
div {}
button {}
main {}
section {}
* {}
```

避免破壞其他頁面。

## AI Center 分支測試

依專案既有命令執行，至少包含：

```bash
cd frontend
npm install
npm run lint
npm run typecheck
npm run test
npm run build
```

如果沒有其中某個 script，讀取 `package.json` 後使用實際存在的等效命令。

後端至少執行：

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
```

再執行專案現有的 backend test command。

如果專案規定 Docker-first，改用 Makefile 或 Docker Compose 內的命令，不要強行在 host 執行。

## 提交 AI Center 分支

不要直接 `git add .`。

依責任拆分 staging，例如：

```bash
git add apps/core/api.py test_execution_api.py
git commit -m "feat(api): support AI execution monitoring data"
```

```bash
git add frontend/src/features/ai \
        frontend/src/app/layouts/MainLayout.tsx \
        frontend/src/components/Navbar.tsx \
        frontend/src/components/SubAgentContainerBlock.tsx \
        frontend/src/main.tsx \
        frontend/src/global.css
git commit -m "feat(ai-center): reorganize AI workspace around target conversations"
```

```bash
git add frontend/package.json frontend/package-lock.json DESIGN.md
git commit -m "chore(ai-center): update dependencies and design documentation"
```

實際 commit 分組應依 diff 內容調整。

要求：

* 每個 commit 應具有單一清楚目的。
* 不得把測試、依賴、UI、API 全部塞進無法審查的大型 commit，除非它們確實不可分割。
* commit 前重新查看：

```bash
git diff --cached --stat
git diff --cached
```

最後確認：

```bash
git status
```

必須乾淨。

---

# Phase 3：審查 Target Asset Map 分支

工作目錄：

```bash
cd /home/hacker/Desktop/share/AI/c2-source-target-asset-map-hasura
```

分支：

```text
work/target-asset-map-hasura
```

先查看：

```bash
git status
git diff
git diff --stat
```

目前特別需要檢查：

```text
frontend/package.json
frontend/package-lock.json
frontend/src/components/AssetTopologyMap.tsx
frontend/src/components/AssetTopologyMap.spec.tsx
frontend/src/features/ai/components/AgentPanel.tsx
frontend/src/features/ai/components/AgentPanel.spec.tsx
frontend/src/features/ai/legacyTopologyAdapter.ts
frontend/src/features/ai/legacyTopologyAdapter.spec.ts
frontend/src/features/target/assetMap/
frontend/src/features/target/components/AssetMapInspector.tsx
frontend/src/features/target/components/AssetMapTabContent.tsx
frontend/src/features/target/components/AssetMapTabContent.spec.tsx
frontend/src/features/target/pages/TargetDashboard.tsx
frontend/src/features/target/pages/TargetDashboard.spec.tsx
frontend/src/features/target/services/assetMapService.ts
frontend/src/features/target/services/assetMapService.spec.ts
frontend/src/graphql/asset-map.graphql
frontend/src/gql/gql.ts
frontend/src/gql/graphql.ts
frontend/src/global.css
frontend/src/spec/
frontend/vite.config.ts
```

## 必須確認的語義

1. Asset Map 的資料來源是否真的使用 Hasura／GraphQL。
2. `asset-map.graphql` 是否是 source of truth。
3. `frontend/src/gql/gql.ts` 與 `frontend/src/gql/graphql.ts` 是否為 generated files。
4. 如果是 generated files，不要手動解 conflict。
5. 必須先合併 `.graphql` source，再執行 codegen。
6. `legacyTopologyAdapter.ts` 是否只是過渡層。
7. 過渡層是否有明確移除條件，還是會永久形成雙重資料模型。
8. `AssetTopologyMap.tsx` 與新 `assetMap/` 模組是否責任重複。
9. `AgentPanel.tsx` 為什麼需要依賴 Asset Map。
10. `vite.config.ts` 修改是否只為測試環境，還是改變 production build。
11. `frontend/src/spec/` 是否包含測試 setup，是否應納入正式版本控制。
12. 測試是否 mock 太多，導致完全沒有驗證真實 GraphQL mapping。

## Target Asset Map 分支測試

至少執行：

```bash
cd frontend
npm install
npm run lint
npm run typecheck
npm run test
npm run build
```

如果有 codegen script，必須執行：

```bash
npm run codegen
```

執行 codegen 後檢查：

```bash
git status
git diff frontend/src/gql
```

如果 codegen 產生未預期的大量變更，立即分析來源，不得直接提交。

## 提交 Target Asset Map 分支

依責任拆分提交，例如：

```bash
git add frontend/src/graphql/asset-map.graphql \
        frontend/src/gql/gql.ts \
        frontend/src/gql/graphql.ts \
        frontend/src/features/target/services
git commit -m "feat(asset-map): add Hasura-backed asset topology queries"
```

```bash
git add frontend/src/features/target/assetMap \
        frontend/src/features/target/components \
        frontend/src/features/target/pages/TargetDashboard.tsx \
        frontend/src/components/AssetTopologyMap.tsx \
        frontend/src/features/ai/legacyTopologyAdapter.ts
git commit -m "feat(asset-map): add interactive target asset map"
```

```bash
git add frontend/src/**/*.spec.ts \
        frontend/src/**/*.spec.tsx \
        frontend/src/spec \
        frontend/vite.config.ts
git commit -m "test(asset-map): cover topology mapping and dashboard integration"
```

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/global.css
git commit -m "chore(frontend): update asset map dependencies and shared styles"
```

實際分組依 diff 調整。

最後：

```bash
git status
```

必須乾淨。

---

# Phase 4：決定合併順序

回到 integration worktree：

```bash
cd /home/hacker/Desktop/share/AI/c2-source
```

確認：

```bash
git branch --show-current
git status
```

預設合併順序：

```text
1. work/ai-center-content-first
2. work/target-asset-map-hasura
```

原因：

* AI Center 分支對整體 layout、navigation、AI workspace 結構的修改較廣。
* Asset Map 應適配最終 AI Center shell，而不是反過來讓整體 layout 適配單一功能。
* 第二個分支可在 AI Center 最終結構上解決 `AgentPanel.tsx`、`global.css` 和依賴衝突。

但在執行前必須比較：

```bash
git diff integration/ai-center-asset-map...work/ai-center-content-first --stat
git diff integration/ai-center-asset-map...work/target-asset-map-hasura --stat
```

並檢查共同修改檔案：

```bash
git diff --name-only integration/ai-center-asset-map...work/ai-center-content-first | sort > /tmp/ai-center-files
git diff --name-only integration/ai-center-asset-map...work/target-asset-map-hasura | sort > /tmp/asset-map-files
comm -12 /tmp/ai-center-files /tmp/asset-map-files
```

輸出合併順序與理由後再執行。

---

# Phase 5：合併第一個功能分支

執行：

```bash
git merge --no-ff work/ai-center-content-first
```

如果發生 conflict：

```bash
git status
git diff --name-only --diff-filter=U
```

逐個分析，不要全部選 ours 或 theirs。

解決後執行最低限度驗證：

```bash
cd frontend
npm run typecheck
npm run test
npm run build
```

後端如果受影響：

```bash
python manage.py check
```

只有第一個分支整合後仍可正常建置，才能繼續第二個分支。

---

# Phase 6：合併第二個功能分支

執行：

```bash
git merge --no-ff work/target-asset-map-hasura
```

預期高風險衝突：

```text
frontend/package.json
frontend/package-lock.json
frontend/src/global.css
frontend/src/features/ai/components/AgentPanel.tsx
```

## package.json 與 package-lock.json

處理方式：

1. 人工整合 `package.json` 中兩邊需要的 dependencies 和 scripts。
2. 不要逐行手工拼接 `package-lock.json`。
3. 刪除衝突中的 lockfile 後，依 repository package manager 重新生成。

如果使用 npm：

```bash
rm frontend/package-lock.json
cd frontend
npm install
```

再檢查：

```bash
git diff package.json package-lock.json
npm ls
```

不得在沒有理解 dependency 的情況下保留兩個不同 major version。

## AgentPanel.tsx

必須保留兩邊功能：

* AI Center 的主要 Agent 工作區。
* Target Asset Map 所需的 topology／asset context。

不要簡單選取其中一邊完整覆蓋。

應優先拆分責任，例如：

```text
AgentPanel
├── conversation / agent execution responsibility
└── asset context adapter or child component
```

不要讓 `AgentPanel.tsx` 變成同時負責：

* GraphQL query。
* topology mapping。
* modal。
* execution status。
* conversation rendering。
* layout。
* global state。

如合併後元件過度肥大，應做最小必要重構。

## global.css

不要把兩邊 CSS 直接串接。

檢查：

* 重複 CSS variable。
* 重複 class。
* 相同 selector 不同定義。
* 全域 element selector。
* overflow 設定。
* height: 100vh／100% 鏈。
* flex child 缺少 `min-width: 0`。
* flex child 缺少 `min-height: 0`。
* 絕對定位造成 overlay。
* z-index 衝突。
* mobile breakpoint 衝突。
* 4K 螢幕內容無限拉寬。

## GraphQL generated files

先解決：

```text
frontend/src/graphql/asset-map.graphql
```

再執行：

```bash
cd frontend
npm run codegen
```

不得手工合併 generated GraphQL types。

---

# Phase 7：恢復 main 原始修改

兩個功能分支整合且基本測試通過後，查看 stash：

```bash
git stash list
git stash show --stat stash@{0}
git stash show -p stash@{0}
```

不要直接無條件 `git stash pop`。

先使用：

```bash
git stash apply stash@{0}
```

這樣即使發生問題，stash 仍保留。

逐項分類：

## A. 應納入整合的修改

可能包括：

```text
Dockerfile
c2_core/settings.py
docker/docker-compose.yml
docker/kali_sandbox/Dockerfile
CLAUDE.md
Agents.md
frontend/src/components/SubAgentContainerBlock.tsx
```

只有在確認修改與目前專案方向一致後才納入。

## B. 工具設定

```text
.claude/
.playwright-mcp/
```

檢查是否包含：

* token。
* credential。
* absolute local paths。
* browser profile。
* cache。
* logs。
* session。
* temporary screenshots。
* machine-specific configuration。

有敏感資訊或 runtime 資料時不得提交。

## C. 無關的本地工作

如果某些修改與本次整合無關：

* 不得偷偷塞入最終 commit。
* 保留在 stash。
* 或建立另一個清楚命名的 branch／commit。
* 在最終報告列出。

## SubAgentContainerBlock.tsx

此檔案同時受到 main 與 AI Center 分支修改。

必須做語義比較：

```bash
git diff HEAD stash@{0} -- frontend/src/components/SubAgentContainerBlock.tsx
```

確認：

* main 的修改目的。
* AI Center 的修改目的。
* 是否能同時保留。
* 是否存在 props、layout 或 state 行為衝突。

如果不能從程式碼判斷產品需求，立即回報，不得擅自覆蓋。

---

# Phase 8：建立 integration fix commit

所有跨分支相容性修正應建立獨立 commit，例如：

```bash
git add <經過審查的檔案>
git commit -m "fix(integration): reconcile AI center and target asset map"
```

Docker 或主幹原始設定可另外提交：

```bash
git add Dockerfile \
        c2_core/settings.py \
        docker/docker-compose.yml \
        docker/kali_sandbox/Dockerfile
git commit -m "chore(docker): align integrated application runtime"
```

工具與 agent 指南另外提交：

```bash
git add CLAUDE.md Agents.md .claude
git commit -m "docs(agent): update repository development instructions"
```

只有在 `.claude` 內容安全且適合版本控制時才能提交。

不要使用：

```text
fix stuff
merge changes
update files
final changes
```

這類無法追蹤目的的 commit message。

---

# Phase 9：完整靜態檢查

## Git 完整性

```bash
git status
git diff --check
git log --oneline --graph --decorate -15
```

要求：

* 沒有 conflict marker。
* 沒有未預期 staged files。
* 沒有 trailing whitespace 錯誤。
* 沒有 secret。
* 沒有大型 runtime artifact。

搜尋 conflict marker：

```bash
rg '^(<<<<<<<|=======|>>>>>>>)' .
```

搜尋可能的敏感資訊：

```bash
rg -i '(api[_-]?key|secret|token|password)\s*[:=]' \
  --glob '!package-lock.json' \
  --glob '!*.example' \
  --glob '!*.md'
```

不得只因搜尋結果出現字串就刪除，必須判斷是否為真正 credential。

## 前端檢查

依 package scripts 執行完整流程：

```bash
cd frontend
npm install
npm run lint
npm run typecheck
npm run test
npm run build
```

若有 coverage：

```bash
npm run test -- --coverage
```

如果測試存在 snapshot，不得未經檢查直接全部更新 snapshot。

## 後端檢查

依 repository 流程執行：

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
```

再執行 backend tests。

特別測試：

* AI execution API。
* Target／asset API。
* GraphQL／Hasura 接口。
* authentication／permission。
* 空資料狀態。
* API 錯誤狀態。
* 非法 ID。
* 找不到 target 時的回應。

---

# Phase 10：Docker 完整整合測試

以專案指定方式清理並重建。

優先使用 Makefile，例如：

```bash
make down
make rebuild
make up
make ps
```

如果沒有對應 Makefile，再使用實際 Compose 檔：

```bash
docker compose -f docker/docker-compose.yml config
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up -d
docker compose -f docker/docker-compose.yml ps
```

## 檢查 Compose 配置

```bash
docker compose -f docker/docker-compose.yml config
```

確認：

* environment variable 有定義。
* volume path 正確。
* service dependency 正確。
* port 沒有衝突。
* healthcheck command 存在且容器內可以執行。
* 前後端 hostname 使用 Docker service name，而不是錯誤的 localhost。
* production 與 development config 沒有混用。

## 檢查容器狀態

```bash
docker compose -f docker/docker-compose.yml ps
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

對每個容器檢查：

```bash
docker inspect --format='{{json .State}}' <container-name>
```

要求：

* 沒有 `Exited`。
* 沒有持續 `Restarting`。
* 有 healthcheck 的容器必須為 `healthy`。
* 不得只看到容器 `Up` 就宣稱健康。

## 檢查 restart 次數

```bash
docker inspect --format='{{.RestartCount}}' <container-name>
```

如果 restart count 非 0，必須分析 logs。

## 檢查 logs

```bash
docker compose -f docker/docker-compose.yml logs --tail=200
```

搜尋：

```bash
docker compose -f docker/docker-compose.yml logs \
  | rg -i 'error|exception|traceback|fatal|panic|unhealthy|connection refused|failed'
```

必須區分：

* 真正錯誤。
* 正常啟動過程中的 warning。
* 測試刻意產生的 4xx。
* 可忽略的第三方 dependency warning。

---

# Phase 11：實際網站訪問測試

先從 Compose 找出實際 port，不要假設固定為 3000、5173、8000 或 8080。

使用：

```bash
docker compose -f docker/docker-compose.yml port <service> <container-port>
```

```

對 health endpoint、AI execution endpoint、target endpoint、GraphQL endpoint 分別測試。

不能只測首頁 HTTP 200。

必須確認：

* HTML 不是 error page。
* JS bundle 成功載入。
* CSS bundle 成功載入。
* API 沒有 500。
* GraphQL request 沒有 schema error。
* 瀏覽器端沒有 CORS 錯誤。
* WebSocket／SSE 如有使用，可以建立連線。

---


---

# Phase 13：功能級整合檢查

必須驗證以下跨功能行為：

## AI Center

* 可以顯示 conversation groups。
* 可以切換 thread。
* Agent Panel 正常顯示。
* Execution Monitor 正常顯示。
* 刪除 `ExecutionLogsPanel` 後仍然有對應日誌或事件呈現方式。
* loading、empty、error 三種狀態不會崩潰。

## Target Asset Map

* Target Dashboard 可以進入 Asset Map。
* GraphQL query 成功。
* 沒有資料時顯示合理 empty state。
* topology node／edge mapping 正確。
* Inspector 可以選取資產。
* legacy adapter 不會產生 duplicate node。
* API error 不會讓整個 Dashboard 白屏。

## 跨功能

* 從 Target／Asset Context 進入 Agent Panel 時資料仍然正確。
* AI Center 的 layout 修改沒有破壞 Target Dashboard。
* Asset Map 的 CSS 沒有污染 AI Center。
* Agent Panel 同時保留兩個分支需要的行為。
* MainLayout、Navbar、Sidebar 不存在互斥狀態。
* 切換頁面後不會殘留舊 target、thread 或 topology state。

---

# Phase 14：最終 clean-room 重建

整合測試通過後，執行一次乾淨重建。

不得刪除使用者資料 volume，除非確認是純開發資料。

可執行：

```bash
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml build 
docker compose -f docker/docker-compose.yml up -d
```

再次確認：

```bash
docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml logs --tail=100
```

重新進行：

* 首頁訪問。
* AI Center 訪問。
* Target Dashboard 訪問。
* Asset Map 訪問。
* API smoke tests。
* 容器 healthcheck。

這一步用來排除：

* 本地 node_modules 遺留。
* build cache 假成功。
* 舊容器殘留。
* generated files 未提交。
* host 環境與 Docker 環境不一致。

---

# Phase 15：合併至 main

只有以下條件全部成立，才能更新 `main`：

```text
[ ] 兩個功能分支都已提交且工作區乾淨
[ ] integration branch 無未解 conflict
[ ] frontend lint 通過
[ ] frontend typecheck 通過
[ ] frontend tests 通過
[ ] frontend production build 通過
[ ] backend check 通過
[ ] backend tests 通過
[ ] migration check 通過
[ ] GraphQL codegen 一致
[ ] Docker build 通過
[ ] 所有必要容器 healthy
[ ] 容器沒有 restart loop
[ ] 網站可以實際訪問
[ ] 主要 API 沒有 500
[ ] AI Center 正常
[ ] Target Asset Map 正常
[ ] 手機、桌面與大螢幕沒有明顯 collapse
[ ] console 沒有主要 runtime error
[ ] 沒有 secret 或 runtime artifact 被提交
```

然後切回 `main`：

```bash
git switch main
```

由於目前 `main` 被這個 worktree 使用，必須確認工作區乾淨。

將 integration branch fast-forward 到 main：

```bash
git merge --ff-only integration/ai-center-asset-map
```

如果不能 fast-forward，不要改用強制方式，先分析 main 是否在整合期間出現新 commit。

最後：

```bash
git status
git log --oneline --graph --decorate -20
```

如果需要一個最終驗證提交，只能用於確實存在的整合修正或測試文件，不要建立內容空洞的「final commit」。

---

# Phase 16：輸出完整報告

完成後輸出以下格式：

```text
# Integration Result

## 結果

狀態：
- SUCCESS
- PARTIAL
- BLOCKED

## 合併分支

1. work/ai-center-content-first
   - commits：
   - 主要功能：
   - 測試：

2. work/target-asset-map-hasura
   - commits：
   - 主要功能：
   - 測試：

## 衝突與解決

- 檔案：
- 兩邊差異：
- 最終選擇：
- 選擇理由：

## Main 原有修改

- 已納入：
- 保留在 stash：
- 未納入原因：
- 是否有敏感或 runtime 檔案：

## Frontend Checks

- install：
- lint：
- typecheck：
- test：
- build：
- codegen：

## Backend Checks

- django check：
- migration check：
- tests：
- API smoke tests：

## Docker Checks

- compose config：
- build：
- container status：
- health：
- restart count：
- log errors：

## Browser Checks

- 375 × 812：
- 768 × 1024：
- 1440 × 900：
- 2560 × 1440：
- console errors：
- failed requests：

## 功能驗證

- AI Center：
- Execution Monitor：
- Target Dashboard：
- Asset Map：
- Agent Panel：
- 跨頁面狀態：

## 仍未完成事項

### 前端債務

- 尚未完成：
- 暫時 adapter：
- UI 問題：
- 測試缺口：

### 後端工作

- 缺少的 API：
- schema／contract 問題：
- permission：
- performance：
- migration：

### 前後端整合風險

- 問題：
- 影響：
- 建議處理順序：

## 最終 Git 狀態

- main HEAD：
- working tree：
- stash：
- integration branch：
```

---

# 關於後續後端開發

不要在本次整合結束時簡單宣稱「前端已完成」。

必須產生一份清楚的剩餘工作清單，至少區分：

```text
1. 純前端問題
2. 前端等待後端 API
3. 後端尚未實作
4. GraphQL／Hasura schema 問題
5. 前後端契約不一致
6. 暫時 compatibility adapter
7. 缺少整合測試
8. UI 可用但資料仍為 mock
```

後續進入後端開發時，仍要持續回歸測試前端，因為以下修改可能讓前端再次故障：

* response schema 改變。
* nullable 欄位改變。
* enum 值改變。
* pagination 改變。
* permission 改變。
* SSE／event payload 改變。
* GraphQL generated types 更新。
* Docker service hostname 或 port 改變。

每完成一組後端 API，都應至少重新執行：

```bash
cd frontend
npm run typecheck
npm run test
npm run build
```

並在 Docker 環境中實際打開對應頁面。

---

# 最重要的執行要求

你不是單純的 Git merge agent，而是 integration reviewer。

你的任務不是「讓 conflict 消失」，而是確保：

```text
兩個功能都被保留
行為是合理的
資料契約是一致的
測試真的驗證功能
Docker 可以乾淨啟動
網站可以實際使用
沒有發生 UI collapse
沒有把問題藏在最終 commit 裡
```

遇到語義不明確或具有產品決策性質的問題，立即停止並提出具體證據、選項與建議。
