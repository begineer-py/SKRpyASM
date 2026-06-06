# SKRpyASM App 文档稽核

本文件按 app 盘点「实际实现」与「当前文档」是否一致，作为后续补写 app 专属文档的基线。

## 稽核结论

| App | 实际职责 | 当前文档状态 | 主要出入 |
| --- | --- | --- | --- |
| `apps/targets` | Target/Seed CRUD，新增 seed 时同步创建核心资产 | 大致准确 | 缺少 app 专属文档 |
| `apps/scanners` | 统一挂载 `nmap/subdomain/vuln/crawler/cve` 五类扫描入口 | 部分准确 | scanner 子模块除 CVE 外缺少独立文档 |
| `apps/flaresolverr` | FlareSolverr 爬取、单次请求、反机器人绕过、会话复用 | 部分准确 | 说明散落在白皮书，无 app 专属文档 |
| `apps/core` | 核心模型中心，公开 API 目前主要是 steps/overviews | 部分准确 | 文档把 `/api/core` 写得比实际公开 API 更广 |
| `apps/analyze_ai` | Initial AI analysis、Overview 转换、规划任务触发 | 部分准确 | 公开 API 目前仅 `/api/analyze_ai/initial`，文档描述过宽 |
| `apps/scheduler` | PeriodicTask CRUD 与后台 trigger/watchdog/cleanup 编排 | 部分准确 | 公开 helper endpoint 与后台行为文档不足 |
| `apps/http_sender` | Endpoint fuzzing，调用 ffuf/Hasura/FlareSolverr | 不准确 | 当前 API 只有 `/api/http_sender/fuzz`，不是泛用 HTTP sender |
| `apps/api_keys` | API Key CRUD、工具配置下载、Agent LLM config、测试接口 | 部分准确 | 文档低估了 AgentLLMConfig 与测试能力 |
| `apps/auto` | 内部自动化框架、automation loop、skill tasks、agent registry | 不准确 | 文档容易让人误会 `/api/auto` 是主入口；实际公开 API 已废弃 |
| `apps/ai_assistant` | assistant/thread/message REST + SSE 流式输出 | 部分准确 | 路由大致正确，但缺少完整 app 文档 |

## 逐个 App 说明

### `apps/targets`

- 实际公开 API：`/api/targets`
- 主要能力：Target CRUD、Seed add/list/delete
- 实作细节：新增 URL/DOMAIN/IP_RANGE seed 时，会同步创建 `URLResult`、`Subdomain` 或 `IP`
- 文档建议：补一页 targets app 文档，说明 seed 类型与副作用

### `apps/scanners`

- 实际公开 API：`/api/scanners/*`
- 当前子路由：
  - `/api/scanners/nmap`
  - `/api/scanners/subdomain`
  - `/api/scanners/vuln`
  - `/api/scanners/crawler`
  - `/api/scanners/cve`
- 文档现状：README 和白皮书已覆盖整体结构，但缺少 `nmap_scanner`、`subfinder`、`nuclei_scanner`、`get_all_url` 的专页

### `apps/flaresolverr`

- 实际公开 API：
  - `POST /api/flaresolverr/start_scanner`
  - `POST /api/flaresolverr/check_flaresolverr`
  - `POST /api/flaresolverr/json_analyze`
  - `POST /api/flaresolverr/send_request`
- 实作重点：Celery 爬虫任务、单次请求任务、Session 复用、内容与资产回写
- 文档建议：补一页说明 crawler/request 两条路径与 session 行为

### `apps/core`

- 实际公开 API：当前主要来自
  - `apps/core/step_api.py`
  - `apps/core/overview_api.py`
- `apps/core/api.py` 目前仅空 `Router()`，没有对外 endpoint
- 实作重点：是系统模型中心，不等于当前公开 API 的全部入口
- 文档建议：把 `core` 分成「模型层」与「公开 API」两部分说明

### `apps/analyze_ai`

- 实际公开 API：`POST /api/analyze_ai/initial`
- 实作重点：
  - 初步 AI 分析
  - 将高价值分析转为 `Overview`
  - 触发规划与后续自动化
- 代码疑点：API 调用 `trigger_initial_ai_analysis.delay(analysis_ids=...)`，但 task 定义参数为 `ip_ids/subdomain_ids/url_ids/overview_id`
- 文档建议：把它写成「内部 AI 流程入口」，不要写成广泛的分析 API 平台

### `apps/scheduler`

- 实际公开 API：PeriodicTask CRUD、`/task-requirements`、`/registered_tasks`
- 实作重点：watchdog、cleanup、自动触发 Nmap/Nuclei/URL 抓取/AI 分析
- 文档建议：补写排程任务分类与「通过 HTTP 回打本系统 API」的实现模式

### `apps/http_sender`

- 实际公开 API：`POST /api/http_sender/fuzz`
- 实作重点：按 Endpoint 参数进行 fuzz，底层用 Hasura 取数据、`ffuf` 发包、FlareSolverr 获取 cookies
- 文档建议：改名或至少在文档中强调这是 fuzzing app，而不是通用 HTTP client

### `apps/api_keys`

- 实际公开 API：
  - API key CRUD
  - bulk import
  - supported services
  - 工具配置下载
  - Agent LLM config CRUD
  - LLM 测试接口
- 文档建议：将 `AgentLLMConfig` 单独列出，避免误认为只是密钥仓库

### `apps/auto`

- 实际公开 API：`POST /api/auto/convert/{asset_type}`，已废弃，返回 `410 Gone`
- 实际价值在内部：
  - `auto_execute_plan`
  - `run_automation_agent_async`
  - skill verification / merge task
  - agent registry / feature flags
- 文档建议：明确写成「内部自动化框架」，不要把 `/api/auto` 当成主入口宣传

### `apps/ai_assistant`

- 实际公开 API：`/api/assistant/`
- 实际路由包含：
  - `threads/`
  - `threads/{thread_id}/messages/`
  - `threads/{thread_id}/messages/stream/`
  - `v1/steps/{step_id}/logs/stream/`
- 实作重点：REST + SSE；`Thread`/`Message` 实际模型已在 `core`
- 文档建议：补一页说明 assistant API、SSE 行为、与 `core` 模型关系

## 优先修正文档项

1. 把 `apps/auto` 从“公开 API 层”改写成“内部自动化框架”。
2. 缩小 `apps/core`、`apps/analyze_ai`、`apps/http_sender` 的公开 API 描述范围。
3. 修正 CVE 相关旧 endpoint 名称。
4. 为缺少 app 文档的模块补最小化说明页。

## 建议新增的 app 文档

- `docs/targets.md`
- `docs/core.md`
- `docs/flaresolverr.md`
- `docs/analyze_ai.md`
- `docs/scheduler.md`
- `docs/http_sender.md`
- `docs/api_keys.md`
- `docs/auto.md`
- `docs/ai_assistant.md`
- `docs/nmap_scanner.md`
- `docs/subfinder.md`
- `docs/nuclei_scanner.md`
- `docs/get_all_url.md`

---

_最后更新：2026-06-06_
