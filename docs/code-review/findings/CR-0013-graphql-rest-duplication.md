# CR-0013：GraphQL 與 REST API 存在重複資料流 (15+ CRUD endpoints)

- Status: **Open**
- Severity: P2
- Domain: Cross-cutting
- Confidence: High
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Review cycle: 4 (cross-cutting rotation)
- Fingerprint: cross-cutting/api-duplication/graphql-rest/overlap

## Summary

專案同時維護 **Hasura GraphQL** (主要資料層) 和 **Django Ninja REST API** 兩套 API。Hasura 自動從 PostgreSQL schema 生成完整的 CRUD (Create/Read/Update/Delete) + 關聯查詢 + 彙總 + 訂閱 API。但 Django Ninja 中仍手動實作了 **15+ 個純 CRUD endpoints**，造成：
1. 開發維護雙重負擔
2. API 介面不一致 (REST vs GraphQL)
3. 前端需同時支援兩套查詢方式
4. 權限控制分散 (Hasura permissions vs Django permissions)

## Evidence

### Hasura GraphQL 自動生成的 CRUD (完整)

Hasura 針對每個追蹤的 table 自動生成：
- **Queries**: `core_target`, `core_target_aggregate`, `core_target_by_pk`
- **Mutations**: `insert_core_target`, `insert_core_target_one`, `update_core_target`, `update_core_target_by_pk`, `delete_core_target`, `delete_core_target_by_pk`
- **Subscriptions**: 同 query 支援即時訂閱
- **關聯查詢**: 巢狀物件、聚合、篩選、分頁、排序皆內建

**核心模型已在 Hasura 追蹤** (從 introspection 確認):
| 模型 | GraphQL Query | GraphQL Mutation |
|------|---------------|------------------|
| `core_target` | ✅ `core_target(_aggregate/_by_pk)` | ✅ `insert/update/delete_core_target(_one/_by_pk)` |
| `core_seed` | ✅ `core_seed(_aggregate/_by_pk)` | ✅ `insert/update/delete_core_seed(_one/_by_pk)` |
| `core_overview` | ✅ `core_overview(_aggregate/_by_pk)` | ✅ `insert/update/delete_core_overview(_one/_by_pk)` |
| `core_vulnerability` | ✅ `core_vulnerability(_aggregate/_by_pk)` | ✅ `insert/update/delete_core_vulnerability(_one/_by_pk)` |
| `core_subdomain` | ✅ `core_subdomain(_aggregate/_by_pk)` | ✅ `insert/update/delete_core_subdomain(_one/_by_pk)` |
| `core_ip` | ✅ `core_ip(_aggregate/_by_pk)` | ✅ `insert/update/delete_core_ip(_one/_by_pk)` |
| `core_urlresult` | ✅ (via relations) | ✅ |
| `core_nmapscan` | ✅ | ✅ |
| `core_nucleiscan` | ✅ | ✅ |
| `core_amassscan` | ✅ | ✅ |
| `core_skill_template` | ✅ | ✅ |
| `core_attack_vector` | ✅ | ✅ |
| `core_pentest_header_config` | ✅ | ✅ |
| `core_targetrequestconfig` | ✅ | ✅ |
| `core_execution_graph/node/event/artifact` | ✅ | ✅ |
| `core_mission_review` | ✅ | ✅ |

### Django Ninja 手動實作的重複 CRUD Endpoints (15+)

| REST Endpoint | Method | 對應 Hasura 操作 | 狀態 |
|---------------|--------|------------------|------|
| `/api/targets/list` | GET | `core_target` | **重複** |
| `/api/targets/` | POST | `insert_core_target_one` | **重複** |
| `/api/targets/{id}` | GET | `core_target_by_pk` | **重複** |
| `/api/targets/{id}` | PUT | `update_core_target_by_pk` | **重複** |
| `/api/targets/{id}` | DELETE | `delete_core_target_by_pk` | **重複** |
| `/api/targets/{id}/seeds` | POST | `insert_core_seed_one` + 關聯 | **重複** |
| `/api/targets/{id}/seeds` | GET | `core_seed` (filter by target) | **重複** |
| `/api/seeds/{id}` | DELETE | `delete_core_seed_by_pk` | **重複** |
| `/api/core/overviews/` | GET | `core_overview` | **重複** |
| `/api/core/overviews/` | POST | `insert_core_overview_one` (upsert) | **重複** |
| `/api/core/overviews/{id}` | GET | `core_overview_by_pk` | **重複** |
| `/api/core/overviews/{id}` | PATCH | `update_core_overview_by_pk` | **重複** |
| `/api/core/overviews/{id}` | DELETE | `delete_core_overview_by_pk` | **重複** |
| `/api/core/vulnerabilities` | GET | `core_vulnerability` | **重複** |
| `/api/core/vulnerabilities` | POST | `insert_core_vulnerability_one` | **重複** |
| `/api/core/vulnerabilities/{id}` | GET | `core_vulnerability_by_pk` | **重複** |
| `/api/core/vulnerabilities/{id}` | PATCH | `update_core_vulnerability_by_pk` | **重複** |
| `/api/core/vulnerabilities/{id}` | DELETE | `delete_core_vulnerability_by_pk` | **重複** |
| `/api/core/vulnerabilities/batch-status` | POST | 批次更新 (可用 GraphQL 多重 mutation) | **重複** |
| `/api/core/vulnerabilities/batch-delete` | POST | 批次刪除 (可用 GraphQL 多重 mutation) | **重複** |
| `/api/core/vulnerabilities/counts` | GET | `core_vulnerability_aggregate` | **重複** |
| `/api/core/vulnerabilities/{id}/pocs` | GET/POST/PATCH/DELETE | `core_pocrecord` 關聯 | **重複** |

**總計: 22+ 個重複 CRUD endpoints** (超過先前估計的 15+)

### 非重複、需保留的 Ninja Endpoints (有副作用/業務邏輯)

以下 endpoints 執行**非 CRUD 操作**，包含掃描觸發、AI 分析、Celery 任務控制、SSE 串流，**必須保留**:

| 端點 | 用途 | 理由 |
|------|------|------|
| `/api/scanners/nmap/start_scan` | 觸發 Nmap 掃描 | 啟動 Celery 任務、建立掃描記錄、狀態機 |
| `/api/scanners/subdomain/start_subfinder` | 觸發 Subfinder | 同上 |
| `/api/scanners/vuln/urls` | 觸發 Nuclei URL 掃描 | 同上 |
| `/api/flaresolverr/send_request` | FlareSolverr HTTP 請求 | 外部服務呼叫、反爬蟲繞過 |
| `/api/analyze_ai/initial` | AI 初步分析 | LLM 呼叫、知識圖譜構建 |
| `/api/scheduler/tasks` | Celery Beat 排程管理 | 動態任務控制 |
| `/api/core/executions/{id}/events/stream/` | SSE 事件串流 | 即時推送、GraphQL subscription 限制 |
| `/api/assistant/threads/{id}/events/` | AI Assistant SSE | 串流回應、工具調用 |
| `/api/http_sender/fuzz` | HTTP Fuzzing | 參數模糊測試、負載產生 |
| `/api/core/targets/{id}/topology/` | 拓撲圖計算 | 複雜圖算法、多表關聯聚合 |
| `/api/skills/{id}/test` | 技能測試執行 | 沙盒執行、動態程式碼 |
| `/api/api_keys/test-llm` | LLM 連線測試 | 外部 API 驗證 |

## Trigger

Cycle 4 (Cross-cutting Rotation) - 架構層面審查 API 設計一致性。

## Impact

1. **維護成本雙倍**: 每新增欄位/模型需同時更新 Hasura metadata + Ninja schemas + API handlers
2. **前端複雜度**: 需同時維護 `useHasuraQuery` hooks 和 Axios/REST 呼叫，TypeScript 類型定義重複
3. **權限分散**: Hasura 有細粒度 role-based permissions，Ninja 用 DRF TokenAuthentication，雙套授權邏輯
4. **效能差異**: GraphQL 可精確查詢所需欄位 (解決 over-fetching)，REST 固定回傳 schema
5. **即時性缺口**: GraphQL subscription 原生支援實時更新，REST 需輪詢或 SSE (僅部分實作)
6. **版本演進風險**: 兩套 API 可能不同步導致資料不一致

## Why this matters

CLAUDE.md 明確規定：**「Simple database CRUD operations MUST be implemented through Hasura GraphQL, not Django backend APIs.」** 目前違反此原則。

## Recommended Change

### 階段 1: 立即停止新增 CRUD Ninja endpoints
- 新功能若為純資料操作，只在 Hasura 定義 table/relationship/permissions
- 前端直接使用 `useHasuraQuery` / `useHasuraMutation`

### 階段 2: 遷移現有 CRUD endpoints 到 GraphQL (優先級排序)

**高優先級 (純 CRUD、無副作用):**
1. Targets CRUD (`/api/targets/*`) → 直接用 Hasura `core_target*`
2. Seeds CRUD (`/api/targets/*/seeds`, `/api/seeds/*`) → Hasura `core_seed*`
3. Overviews CRUD (`/api/core/overviews/*`) → Hasura `core_overview*`
4. Vulnerabilities CRUD (`/api/core/vulnerabilities/*`) → Hasura `core_vulnerability*`

**中優先級 (有輕微業務邏輯但可用 GraphQL computed fields/action 替代):**
5. Vulnerability counts/batch ops → GraphQL aggregate + 多重 mutation
6. PoC CRUD → Hasura `core_pocrecord*`

### 階段 3: 保留必要的 Ninja endpoints 並明確標記
建立 `apps/core/api_non_crud.py` 或類似模組，只包含：
- 掃描觸發類 (`/api/scanners/*`)
- AI 分析類 (`/api/analyze_ai/*`)
- 任務控制類 (`/api/scheduler/*`)
- 串流類 (`/api/core/executions/*/events/stream/`, `/api/assistant/*/events/`)
- 複雜聚合類 (`/api/core/targets/*/topology/`)
- 外部整合類 (`/api/flaresolverr/*`, `/api/http_sender/*`, `/api/api_keys/test-llm`)

### 階段 4: 前端遷移
- 將所有 CRUD 介面改用 `useHasuraQuery` / `useHasuraMutation`
- 移除對應的 Axios API 呼叫與 TypeScript interface 重複定義
- 統一錯誤處理 (GraphQL errors vs REST errors)

### 技術細節: GraphQL 替代方案

**批次操作** (替代 `/batch-status`, `/batch-delete`):
```graphql
mutation BatchUpdateVulns($ids: [uuid!]!, $status: vulnerability_status_enum!) {
  update_core_vulnerability(where: {id: {_in: $ids}}, _set: {status: $status}) {
    affected_rows
  }
}
```

**Upsert** (替代 Overviews create 的 upsert 邏輯):
```graphql
mutation UpsertOverview($target_id: Int!, $summary: String!) {
  insert_core_overview_one(
    object: {target_id: $target_id, summary: $summary},
    on_conflict: {constraint: core_overview_target_id_key, update_columns: [summary, updated_at]}
  ) { id }
}
```

**複雜聚合** (替代 topology):
```graphql
query TargetTopology($target_id: Int!) {
  core_target_by_pk(id: $target_id) {
    id
    name
    seeds { id value type }
    subdomains { id name ip_assets { id address } }
    ips { id address }
    url_results { id url }
    nmapscans { id status ports { port service } }
    nucleiscans { id template_id severity }
  }
}
```

## Verification

1. 檢查 Hasura Console → Data → 掛上所有 core_* tables 並啟用 permissions
2. 前端逐頁遷移：`useHasuraQuery(GET_TARGETS)` 替代 `targetApi.list()`
3. 確認 GraphQL subscription 可替代 SSE 輪詢場景
4. 壓測 GraphQL 效能 vs REST (預期 GraphQL 更優因精確查詢)

## Resolution Criteria

- 所有純 CRUD Ninja endpoints 移除或標記 deprecated
- 前端 100% 使用 Hasura GraphQL 進行資料 CRUD
- Ninja API 只保留非 CRUD (side-effect) endpoints
- 文件更新：CLAUDE.md、API 文檔、前端開發指南

## Notes

- Hasura permissions 需正確配置 role-based access (匿名、user、admin 等)
- GraphQL 查詢複雜度限制 (`analysis-complexity`) 需配置防止惡意查詢
- 遷移期間可並行運行，以 feature flag 控制前端切換
- 參考: Hasura docs "Authorization", "GraphQL Queries", "Mutations"