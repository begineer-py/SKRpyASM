AI Workbench UI/UX 設計優化方案
基於 SKRpyASM 現有架構（Django + GraphQL Hasura + React/Vite）的深度分析，針對三大優化議題提出具體實作路線。

> ## ⚠️ 代碼庫審查報告（2026-07-13）
>
> 本計畫經過代碼庫深度驗證，發現多處與實際程式碼不符的假設。以下為審查結論摘要。
>
> ### 常識性錯誤（已修正）
>
> | # | 原計畫假設 | 實際程式碼 |
> |---|-----------|-----------|
> | C1 | 「不需要新建 SubAgentDispatch model」 | SubAgentDispatch 已存在（`apps/core/models/analyze/SubAgentDispatch.py`，migration 0030），具備 `dispatcher_thread`/`sub_thread` FK、`objective`、`result_summary`、`synthesized` 等完整欄位 |
> | C2 | 在 ExecutionGraph 加 caller_thread FK + dispatch_instruction 欄位 | 完全冗餘。SubAgentDispatch 的 dispatcher_thread→sub_thread 鏈已提供相同功能；dispatch_instruction 重複 SubAgentDispatch.objective |
> | C3 | 「AutomationAgent.as_tool() 建立 ExecutionGraph 時填入」 | 錯誤。as_tool() 只 dispatch run_automation_agent_async.delay()；graph 在 _run_as_tool() 中建立 |
> | C4 | Phase 2「Dispatch API + SSE stream」需從零建立 | query_dispatched_agents AI 工具已存在（spawn_tools.py:246）；notify_caller_agent 已有 SubAgentDispatch 路由優先序（reconnaissance_tools.py:391） |
> | C5 | PATCH /core/executions/{id} 更新 archived 欄位 | ExecutionGraph 無 archived 欄位；需先加欄位或用 metadata JSONField |
> | C6 | getActiveAttackNode() 用 regex 解析 event content | AssetLock、WalkCursor 已提供結構化攻擊位置追蹤（attack_planning.py） |
> | C7 | AssetTopologyMap 從 FK 關係推斷 edges | AssetEdge model 已存在（attack_planning.py:310），含 RESOLVES_TO/HOSTS/LINKS_TO/DISCOVERED_FROM 等邊類型 |
> | C8 | 只列 6 種資產節點 | 遺漏 Port、Endpoint、DNSRecord、TechStack、AttackVector 等既有 model |
>
> ### 真正的 Gap
>
> | # | 缺口 | 修正方案 |
> |---|------|---------|
> | G1 | run_automation_agent_async 不建立 SubAgentDispatch 記錄 | 加 _record_dispatch() 呼叫 + 擴充 DISPATCH_AGENT_CHOICES |
> | G2 | 前端無 REST API 讀取 SubAgentDispatch | 新增 GET /api/core/threads/{caller_id}/dispatches/ |
> | G3 | 前端無 REST API 讀取 ContentBlob 分頁（AI 工具 read_content_blob 已支援 page） | 新增 GET /api/core/blobs/{blob_id}/page/{page_num}/ |
> | G4 | ExecutionGraph 無 DELETE/PATCH 端點 | 新增端點（archived 用 metadata JSONField） |
> | G5 | 後端 get_thread_messages() 預設 include_extra_messages=False → 過濾 tool 訊息 | 前端 tool call 渲染是 dead code；需改為 API query param |
> | G6 | read_page() 工具存在但未暴露為 API | 既有工具在 apps/core/services/pagination.py:85-118 |
> | G7 | 前端訊息使用 any[] 無 TypeScript 型別 | 需定義 RawMessage type |
>
> ### 既有資料流（不需重建）
>
> ```
> HackerAgent thread
>   └─ as_tool() → run_automation_agent_async.delay(caller_thread_id)
>        └─ AutomationAgent._run_as_tool(message)
>             ├─ creates sub_thread + ExecutionGraph(thread=sub_thread)
>             ├─ tools produce ContentBlob via save_long_content()
>             │    └─ ContentBlob → ExecutionArtifact(content_blob FK) → ExecutionGraph
>             └─ spawns sub-agents via spawn_recon_agent() etc.
>                  └─ run_recon_agent_async → _record_dispatch() → SubAgentDispatch
>                       ├─ dispatcher_thread = AutomationAgent's thread
>                       ├─ sub_thread = sub-agent's thread
>                       └─ notify_caller_agent() → updates SubAgentDispatch
> ```
> **⚠️ 缺口**: run_automation_agent_async（HackerAgent→AutomationAgent）不呼叫 _record_dispatch()
>
> ### 既有 API（不需新建）
>
> Overview CRUD / Vulnerability CRUD / AttackPlan CRUD / Thread CRUD / Message CRUD / SSE streaming 皆已存在，不需從零建立。
>
> ---

一、Container Blob ID 機制（Sub-agent 訊息統一架構）
現況痛點（重新確認）
讀完實際程式碼後：AICenterPage.tsx 的 loadMessagesForThread() 把 tool_calls 渲染成 [Tool Call: xxx]、tool result 渲染成 [Tool Execution Completed]，完全丟棄了 sub-agent 的輸出資訊。

關鍵發現：系統早已有完整的 ContentBlob 設計，這正是 Container Block 的正確基礎。

ContentBlob 現有能力（不需新建 Model）
ContentBlob
├── id ← 這就是 Container Blob ID
├── raw_content ← Sub-agent 的完整輸出
├── ai_summary ← 自動生成的摘要（前端可直接顯示）
├── page_breakdown ← [{title, content}] 按語義分頁
├── source_type ← 'curl' / 'nuclei' / 'other'
└── content_size ← 字元數
ExecutionArtifact (已有 FK → ContentBlob)
├── graph_id ← 連到哪個 ExecutionGraph
├── node_id ← 連到哪個 ExecutionNode
├── artifact_type = 'content_blob'
├── data.blob_id ← 直接存 blob.id
└── content_blob FK ← 直接 FK 到 ContentBlob
ExecutionGraph (Sub-agent 執行圖)
└── thread_id ← 連回 Sub-agent Thread
現有資料流已經是：Sub-agent 工具呼叫 save_long_content() → 建立 ContentBlob → 自動 attach 到 ExecutionArtifact → 掛在 ExecutionGraph 下。

前端缺失的只是：把這個 blob_id 往上浮到主 thread 的訊息串。

設計方案：以 ContentBlob 為中心的 Container Block
1.1 後端：不改動 ExecutionGraph，改用既有 SubAgentDispatch 鏈

現有 ExecutionGraph 已有 `thread_id`（Sub-agent 自己的 thread）。不需新增 `caller_thread` FK——
既有的 **SubAgentDispatch** model（migration 0030）已提供：
- `dispatcher_thread`（caller thread）→ `sub_thread`（callee thread）→ `ExecutionGraph.thread`

查詢範例（Django ORM）：
```python
# 找出 caller thread 派發的所有 ExecutionGraph
from apps.core.models import SubAgentDispatch

dispatches = SubAgentDispatch.objects.filter(dispatcher_thread_id=caller_thread_id)
graph_ids = ExecutionGraph.objects.filter(
    thread__in=dispatches.values('sub_thread_id')
).values_list('id', flat=True)
```

**注意**：目前只有 recon/post_exploit/reporting 三種 sub-agent 會建立 SubAgentDispatch 記錄（`apps/auto/tasks/__init__.py:644,681,728`）。
AutomationAgent 的派發尚未建立記錄（見 §1.6），這是需要用 `_record_dispatch()` 修復的 gap。

⚠️ **修正**：原計畫說 as_tool() 建立 ExecutionGraph，但實際上 `as_tool()`（`planning_agent.py:562`）只 dispatch `run_automation_agent_async.delay()`。ExecutionGraph 是在 `AutomationAgent._run_as_tool()` → `AIAssistant.invoke()` 中由 LangGraph 自動建立。

1.2 後端 API：新增 /core/threads/{caller_id}/dispatches/（基於既有 SubAgentDispatch）
GET /api/core/threads/{caller_thread_id}/dispatches/
→ 回傳該 thread 透過 SubAgentDispatch 派發的所有子代理記錄，每筆帶上：
{
dispatch_id, sub_agent_type, objective, result_summary, synthesized,
dispatched_at, completed_at, status,
graph: { graph_id, status, title },
content_blobs: [ ← 從 ExecutionArtifact 聚合
{ blob_id, ai_summary, content_size, page_count, created_at }
]
}
⚠️ `query_dispatched_agents` AI 工具已存在（`spawn_tools.py:246`），此 API 是其 REST 等價物。
這讓前端只需要一個 API 呼叫，就能拿到 caller thread 下所有 SubAgentDispatch 記錄 + 對應的 ExecutionGraph + ContentBlob。

1.3 前端：SubAgentContainerBlock 元件
ContentBlob 的 ai_summary + page_breakdown 完美支援「收合預覽 / 展開分頁閱讀」的 UI 模式：

tsx
// components/SubAgentContainerBlock.tsx
interface DispatchedGraph {
graph*id: number;
status: string;
title: string;
dispatch_instruction: string;
callee_thread_id: number | null;
content_blobs: ContentBlobSummary[];
}
interface ContentBlobSummary {
blob_id: number;
ai_summary: string; // 直接顯示，不需重新請求
content_size: number;
page_count: number | null; // null = 未分頁
created_at: string;
}
export function SubAgentContainerBlock({ graph, onViewGraph, onViewThread }: ...) {
const [expanded, setExpanded] = useState(false);
const [activeBlobPage, setActiveBlobPage] = useState<{ blobId: number; page: number } | null>(null);
return (
<div className="subagent-container-block">
{/* ── 頭部 Label（永遠顯示）── */}
<div className="scb-header" onClick={() => setExpanded(v => !v)}>
<span className="scb-badge">🤖 AI Sub-agent</span>
<span className="scb-agent-type">automation_agent</span>
<span className={`scb-status scb-status--${graph.status.toLowerCase()}`}>
{graph.status}
</span>
{graph.content_blobs.length > 0 && (
<span className="scb-blob-count">
{graph.content_blobs.length} blob{graph.content_blobs.length > 1 ? 's' : ''}
</span>
)}
<span className="scb-toggle">{expanded ? '▲' : '▼'}</span>
</div>
{/* ── 指令摘要（永遠顯示）── */}
<div className="scb-instruction">
<code>{graph.dispatch_instruction.slice(0, 150)}</code>
{graph.dispatch_instruction.length > 150 && '...'}
</div>
{/* ── 展開區域 ── */}
{expanded && (
<div className="scb-body">
{/* ContentBlob 列表 */}
{graph.content_blobs.map(blob => (
<div key={blob.blob_id} className="scb-blob-item">
<div className="scb-blob-header">
<span>Blob #{blob.blob_id}</span>
<span className="scb-blob-size">{(blob.content_size / 1000).toFixed(1)}k chars</span>
{blob.page_count && (
<span className="scb-blob-pages">{blob.page_count} pages</span>
)}
</div>
{/* ai_summary — 不需額外 API，直接顯示 */}
<div className="scb-blob-summary">{blob.ai_summary}</div>
{/* 分頁瀏覽（如果有 page_breakdown）*/}
{blob.page_count && blob.page_count > 1 && (
<div className="scb-blob-pages-nav">
{Array.from({ length: blob.page_count }, (*, i) => i + 1).map(p => (
<button
key={p}
className={`scb-page-btn ${activeBlobPage?.page === p ? 'active' : ''}`}
onClick={() => setActiveBlobPage({ blobId: blob.blob_id, page: p })} >
P{p}
</button>
))}
</div>
)}
</div>
))}
{/_ ExecutionTimeline（快速預覽）_/}
<ExecutionTimelineViewer graphId={graph.graph_id} compact autoScroll={false} />
</div>
)}
{/_ ── 快速動作 ── _/}
<div className="scb-actions">
{graph.callee_thread_id && (
<button className="scb-btn" onClick={() => onViewThread(graph.callee_thread_id!)}>Thread</button>
)}
<button className="scb-btn" onClick={() => onViewGraph(graph.graph_id)}>Full Graph</button>
</div>
</div>
);
}
1.4 分頁內容讀取（BlobPageViewer）
ContentBlob.page_breakdown 已存在 DB，前端只需新增一個簡單的讀取端點：

GET /api/core/blobs/{blob_id}/page/{page_num}/
→ 直接回傳 page_breakdown[page_num-1] 的 title + content
不需要 LLM，直接從 DB 讀取
⚠️ `apps/core/services/pagination.py:85-118` 已有 `read_page(page_breakdown, page_num, blob_id)` 工具函數——新 API 端點應直接呼叫此函數，不需重新實作分頁邏輯。
tsx
// BlobPageViewer — 點擊分頁時動態載入
function BlobPageViewer({ blobId, page }: { blobId: number; page: number }) {
const [content, setContent] = useState<string | null>(null);

useEffect(() => {
fetch(`/api/core/blobs/${blobId}/page/${page}/`)
.then(r => r.json())
.then(d => setContent(d.content));
}, [blobId, page]);

return <ReactMarkdown>{content ?? 'Loading...'}</ReactMarkdown>;
}
1.5 整合進 AICenterPage 訊息渲染（最小改動）
tsx
// AICenterPage.tsx — 在 selectedThreadId 變更時額外拉取 dispatched graphs
const [dispatchedGraphs, setDispatchedGraphs] = useState<DispatchedGraph[]>([]);
useEffect(() => {
if (!selectedThreadId) return;
fetch(`/api/core/threads/${selectedThreadId}/dispatched-graphs/`)
.then(r => r.json())
.then(setDispatchedGraphs);
}, [selectedThreadId]);
// 訊息渲染：tool_calls 含 automation_agent 時插入 Container Block
{displayedMessages.map(msg => {
if (msg.hasAutomationToolCall) {
// 用 tool_call_id 或 sequence 匹配對應的 graph
const graph = dispatchedGraphs.find(g => matchesMessage(g, msg));
if (graph) return <SubAgentContainerBlock key={msg.id} graph={graph} ... />;
}
return <MessageBubble key={msg.id} msg={msg} />;
})}
IMPORTANT

核心優勢：不需要新建 SubAgentDispatch model —— 它早在 migration 0030 就建好了（`apps/core/models/analyze/SubAgentDispatch.py`），具備：
- `dispatcher_thread` FK → 派發者的 Thread（caller）
- `sub_thread` FK → 被派發者的 Thread（callee）
- `overview` FK → 隸屬的 Overview
- `sub_agent_type` → 子代理類型（recon_agent / post_exploit_agent / reporting_agent）
- `objective` → 派發時賦予的任務目標
- `status` → RUNNING / COMPLETED / FAILED
- `result_summary` → 回報結果摘要
- `synthesized` → 是否已被父代理消化
- `dispatched_at` / `completed_at` → 時間戳

既有 ContentBlob → ExecutionArtifact → ExecutionGraph → Thread 的鏈已完整。
再加上 SubAgentDispatch 的 `dispatcher_thread` → `sub_thread` 鏈，就不需要新增 caller_thread FK——直接查 `SubAgentDispatch.objects.filter(dispatcher_thread_id=caller_id)` 即可找到這個 caller thread 發出的所有 sub-agent graph。

1.6 真正的 Gap：AutomationAgent 派發不建立追蹤記錄

雖然 SubAgentDispatch model 已存在，但並非所有派發路徑都建立了記錄：

| 派發路徑 | 建立 SubAgentDispatch？ | 位置 |
|---------|----------------------|------|
| AutomationAgent → ReconAgent | ✅ 是 | `apps/auto/tasks/__init__.py:644` |
| AutomationAgent → PostExploitAgent | ✅ 是 | `apps/auto/tasks/__init__.py:681` |
| AutomationAgent → ReportingAgent | ✅ 是 | `apps/auto/tasks/__init__.py:728` |
| HackerAgent → AutomationAgent | ❌ **否** | `apps/auto/tasks/__init__.py:459` |

**這就是為什麼前端看不到 AutomationAgent 的派發記錄。**

修正方案（兩個步驟）：
1. 在 `SubAgentDispatch.DISPATCH_AGENT_CHOICES`（`SubAgentDispatch.py:21-25`）加入 `("automation_agent", "Automation Agent")`
2. 在 `run_automation_agent_async`（`__init__.py:459`）中，於 `_run_as_tool()` 呼叫後，用 `_record_dispatch()` 建立記錄（需先從 thread 或 agent instance 解析 overview_id）

這是讓前端能追蹤 AutomationAgent 派發的**前置條件**——需在 Dispatch REST API 和 SubAgentContainerBlock 之前完成。

二、系統訊息過濾與顯示顆粒度控制
現況痛點
現有的 showInternal toggle 只做了「user conversation only vs 全部 threads」的二元切換
每個 thread 的 messages 都未按 agent 類型分類
Tool call / tool result 訊息未能摺疊
設計方案
### 前置條件：後端 tool 訊息目前被過濾（dead code 問題）

⚠️ **重大發現**：後端 `get_thread_messages()` 預設 `include_extra_messages=False`（`apps/ai_assistant/helpers/use_cases.py:311`），**會過掉所有 tool_call 和 tool_result 訊息**。

這意味著：
- `loadMessagesForThread()`（`AICenterPage.tsx:401-403`）中的 `[Tool Call: xxx]` 和 `[Tool Execution Completed]` 渲染是 **dead code**——後端根本不回傳這些訊息
- 後端 `Message` model 有 rich `role` 欄位（`human`/`ai`/`tool_call`/`tool_result`/`system`）（`ai_models.py:126-138`），但前端降維成二元 `'user'`/`'assistant'`（`AICenterPage.tsx:396`）
- 前端訊息使用 `any[]` 無 TypeScript 型別（`assistantApi.ts`）

**修正方案**：將 `include_extra_messages` 改為 API query param（如 `?include_tools=true`），讓前端控制是否要看到 tool 訊息。這是在 §2.1 訊息分類方案之前必須完成的後端改動。

2.1 訊息分類標籤化（後端不需改動）
在前端 loadMessagesForThread() 中，對每條訊息加上 category 標籤：

tsx
type MessageCategory =
| 'user' // 使用者輸入
| 'ai_response' // AI 文字回覆
| 'tool_call' // AI 呼叫工具
| 'tool_result' // 工具執行回傳
| 'subagent_dispatch' // 派發 sub-agent
| 'system'; // 其他系統訊息
function categorizeMessage(m: RawMessage): MessageCategory {
if (m.type === 'human') return 'user';
if (m.type === 'tool') return 'tool_result';
if (m.tool_calls?.some(tc => tc.name === 'automation_agent')) return 'subagent_dispatch';
if (m.tool_calls?.length > 0) return 'tool_call';
if (m.type === 'ai' && hasTextContent(m)) return 'ai_response';
return 'system';
}
2.2 過濾器 UI 元件
tsx
// components/MessageFilterBar.tsx
interface FilterState {
showUserConv: boolean; // 使用者對話
showAiResponse: boolean; // AI 回覆
showToolCalls: boolean; // 工具呼叫
showSubagent: boolean; // Sub-agent 派發
showSystem: boolean; // 系統訊息
agentFilter: string[]; // 勾選的 assistant_id 清單
}
export function MessageFilterBar({ filter, onChange, availableAgents }: ...) {
return (
<div className="msg-filter-bar">
<div className="filter-presets">
<button onClick={() => onChange({ ...ALL_ON })}>全部</button>
<button onClick={() => onChange({ ...USER_ONLY })}>僅使用者對話</button>
<button onClick={() => onChange({ ...AUTO_PENTEST })}>Auto Pentest</button>
</div>

      <div className="filter-toggles">
        {[
          ['user', '👤 User', filter.showUserConv],
          ['ai_response', '🤖 AI', filter.showAiResponse],
          ['tool_call', '🔧 Tools', filter.showToolCalls],
          ['subagent', '🕸 Sub-agent', filter.showSubagent],
        ].map(([key, label, active]) => (
          <button
            key={key}
            className={`filter-chip ${active ? 'active' : ''}`}
            onClick={() => onChange({ ...filter, [`show${key}`]: !active })}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Agent 清單：動態列出所有出現過的 assistant_id */}
      <div className="filter-agents">
        <span>Agents:</span>
        {availableAgents.map(agentId => (
          <label key={agentId}>
            <input
              type="checkbox"
              checked={filter.agentFilter.includes(agentId)}
              onChange={() => toggleAgent(agentId)}
            />
            {agentId}
          </label>
        ))}
      </div>
    </div>

);
}
2.3 可摺疊的 Tool Call 群組
Tool calls + tool results 通常成對出現，把它們合組成一個可摺疊的 <ToolCallGroup>：

tsx
function ToolCallGroup({ calls, results }: { calls: Message[], results: Message[] }) {
const [open, setOpen] = useState(false);

return (
<div className="tool-call-group">
<button className="tcg-header" onClick={() => setOpen(v => !v)}>
<span className="tcg-icon">🔧</span>
<span>{calls.length} tool call{calls.length > 1 ? 's' : ''}</span>
<span className="tcg-names">{calls.map(c => c.toolName).join(', ')}</span>
<span>{open ? '▲' : '▼'}</span>
</button>
{open && (
<div className="tcg-body">
{calls.map(c => <ToolCallItem key={c.id} msg={c} />)}
{results.map(r => <ToolResultItem key={r.id} msg={r} />)}
</div>
)}
</div>
);
}
2.4 狀態持久化
tsx
// 儲存到 localStorage，跨頁保持使用者的篩選偏好
const [msgFilter, setMsgFilter] = usePersistentState<FilterState>('aiCenter_msgFilter', DEFAULT_FILTER);
三、Agent 互動視覺化與資產攻擊地圖
現況痛點
AgentTree 只是一個 CSS indent 的平面列表，無法直觀呈現互動層次
ExecutionGraph 有視覺化但沒有在 Agent 層級整合
資產（Subdomain、IP、URL）之間的拓撲關係無法可視化
無法知道 AI 當前正在攻擊哪個資產
設計方案
3.1 Agent 互動時序圖（AgentInteractionTimeline）
用時間軸橫向排列的方式，取代現有的縮排樹狀列表：

時間 ──────────────────────────────────────────────────────▶
┌─────────────────┐
│ HackerAssistant │─────────────── dispatches ───▶ ┌──────────────────────┐
│ (Thread #42) │◀── reports back ───────────────│ AutomationAgent │
│ Round: 3 │ │ (Thread #43) │
└─────────────────┘ │ Graph #87 [RUNNING] │
└──────────────────────┘
│ spawns
▼
┌──────────────────────┐
│ ReconAgent │
│ (Thread #44) │
│ Graph #88 [DONE] │
└──────────────────────┘
元件設計：

tsx
// components/AgentInteractionTimeline.tsx
interface AgentNode {
threadId: number;
dispatchId: number; // SubAgentDispatch.id
agentId: string;
status: string;
round: number; // 第幾輪互動（by caller→callee pairs）
depth: number; // 層級深度
dispatchedAt: string;
completedAt?: string;
graphId?: number;
children: AgentNode[];
}
export function AgentInteractionTimeline({ rootNode, onSelectNode }: ...) {
// 使用 SVG 或 CSS Grid 繪製 swimlane 式時間軸
// X 軸：時間
// Y 軸：Agent 層級
// 連接線：dispatch → report back 的箭頭

return (
<div className="agent-timeline">
<svg viewBox="0 0 800 300">
{renderSwimLanes(nodes)}
{renderDispatchArrows(edges)}
{renderRoundBadges(rounds)}
</svg>
</div>
);
}
互動輪次計算：

tsx
// from apps.core.models import SubAgentDispatch
// 從 SubAgentDispatch 記錄計算 round
// 每次 caller → callee 再回到 caller = 一個完整 round
// Django ORM: SubAgentDispatch.objects.filter(dispatcher_thread_id=root_thread).order_by('dispatched_at')
function computeRounds(dispatches: SubAgentDispatch[]): RoundGroup[] {
return dispatches.reduce((acc, d, i) => {
const round = { id: i + 1, dispatch: d, startTime: d.dispatched_at, endTime: d.completed_at };
// children: 查 SubAgentDispatch.objects.filter(dispatcher_thread_id=d.sub_thread_id)
return [...acc, round];
}, []);
}

⚠️ HackerAgent→AutomationAgent 派發目前無 SubAgentDispatch 記錄（見 §1.6），所以 AgentInteractionTimeline 只能顯示 AutomationAgent→sub-agent 的互動，無法顯示 HackerAgent→AutomationAgent 的互動，直到 G1 修正完成。
3.2 資產拓撲網路圖（AssetTopologyMap）
使用 D3.js 或 React Flow 繪製資產關係圖：

Target: example.com
│
┌──────────┼──────────┐
│ │ │
[Seed] [Subdomain] [Subdomain]
example api.ex.com www.ex.com
│ │ │
[IP] [URL] [IP]
192.168.x /admin 10.x.x.x
│
[Vuln] ← CVE-2024-xxxxx

⚠️ **修正**：Subdomain→IP 是 ManyToManyField（`domain.py:64-69`，透過 `subdomain.ips`），Subdomain→URLResult 也是 ManyToManyField（`url_assets.py:38-43`，透過 `URLResult.related_subdomains`）。上圖簡化為 1:N 關係，實際拓撲圖需要渲染 M:N edges。

節點類型與顏色：

類型 顏色 圖示
Target #a78bfa 紫色 🎯
Seed #60a5fa 藍色 🌱
Subdomain #34d399 綠色 🌐
IP #fbbf24 黃色 🖥
URL #94a3b8 灰色 🔗
Vulnerability #ef4444 紅色 ⚠️
Port #f59e0b 橙色 🔌
Endpoint #8b5cf6 紫色 🔗
DNSRecord #06b6d4 青色 📋
TechStack #10b981 綠色 📊
AttackVector #ec4899 粉色 🎯
AI攻擊位置 閃爍動畫 🤖

### 既有 Edge 資料來源：AssetEdge

`apps/core/models/analyze/attack_planning.py:310` 已有通用 asset→asset edge model，含：
- `from_asset_type` / `to_asset_type` → 資產類型
- `edge_type` → RESOLVES_TO / HOSTS / LINKS_TO / DISCOVERED_FROM
- 型別特定的 FK（`from_ip_asset` / `to_subdomain_asset` 等）

AssetTopologyMap 可直接用 AssetEdge 作為 edge 資料來源，不需從 FK 關係手動推斷。

⚠️ 無直接 asset→CVE FK。CVE 查詢路徑：
- `Vulnerability.cve_intelligence`（`Vulnerability.py:66-73`）
- `TechStack → TechStackCVEMapping → CVEIntelligence`（`cve_intelligence.py:151-199`）

⚠️ 無 PentestRecord model。滲透記錄查詢路徑：
`Action.asset_links`（M:N to AssetVectorLink）→ `Action.execution_graph` → `ExecutionNode`/`ExecutionEvent`

動態攻擊狀態標示：

tsx
// 用 AssetLock 查詢當前 AI 正在攻擊的資產（attack_planning.py:258-307）
// AssetLock 記錄哪個 Thread 持有哪個資產的鎖
// 查詢範例：AssetLock.objects.filter(target_id=overview.target_id, lock_status='HELD').select_related('thread')
// Fallback: WalkCursor.current_asset_link → AssetVectorLink → 解析具體 asset FK
// Regex 僅用於歷史資料的最後手段（attack_planning.py:370-408）
function getActiveAttackNode(overview: Overview): string | null {
// 優先：查 AssetLock（attack_planning.py:258-307）
// AssetLock 有 explicit FK：ip_asset / subdomain_asset / url_asset / endpoint_asset / port_asset
// 次選：查 WalkCursor（attack_planning.py:370-408）
// 最後：regex fallback 解析 event content（僅限歷史資料）
return null;
}
點擊資產展開滲透記錄：

tsx
// 點選任意資產節點，側面板展開顯示：
// - InitialAIAnalysis（如果有）
// - 相關 ExecutionEvent 記錄（過濾出涉及此資產的 events）
// - CVE 清單（如果是 URL/Subdomain）
// - Overview 狀態
function AssetDetailPanel({ asset }: { asset: AssetNode }) {
return (
<aside className="asset-detail-panel">
<h3>{asset.type}: {asset.name}</h3>

      <section>
        <h4>AI 分析</h4>
        <AIAnalysisSummary assetId={asset.id} assetType={asset.type} />
      </section>

      <section>
        <h4>滲透記錄</h4>
        <PentestRecordList assetId={asset.id} assetType={asset.type} />
      </section>

      <section>
        <h4>相關 CVE</h4>
        <CVEList assetId={asset.id} />
      </section>
    </aside>

);
}
3.3 圖表 CRUD 與按需載入
CRUD 操作（目前缺失）：

tsx
// 對 ExecutionGraph 的管理操作
const graphCRUD = {
// 刪除單一 graph
delete: (graphId: number) => executionApi.deleteGraph(graphId),

// 標記 graph 為 archived（不預設顯示）
archive: (graphId: number) => executionApi.archiveGraph(graphId),

// 重命名 graph
rename: (graphId: number, title: string) => executionApi.updateGraph(graphId, { title }),
};
// UI: Graph 管理列
function GraphManagementRow({ graph }: { graph: ExecutionGraph }) {
return (
<div className="graph-row">
<span>#{graph.id} {graph.title}</span>
<span className={`status-${graph.status.toLowerCase()}`}>{graph.status}</span>
<div className="graph-actions">
<button onClick={() => graphCRUD.archive(graph.id)}>Archive</button>
<button onClick={() => graphCRUD.delete(graph.id)}>Delete</button>
</div>
</div>
);
}
按需載入（Lazy Load）：

tsx
// 預設只載入最近 5 個 graphs，「Load More」按鈕分頁載入
const [graphPage, setGraphPage] = useState(1);
const GRAPHS_PER_PAGE = 5;
useEffect(() => {
executionApi.listGraphs({
thread_id: Number(activeNodeThreadId),
limit: GRAPHS_PER_PAGE,
offset: (graphPage - 1) \* GRAPHS_PER_PAGE,
}).then(g => setActiveThreadGraphs(prev => graphPage === 1 ? g : [...prev, ...g]));
}, [activeNodeThreadId, graphPage]);
篩選：

tsx
// 圖表篩選器
function GraphFilterBar({ filter, onChange }: ...) {
return (
<div className="graph-filter-bar">
<select value={filter.status} onChange={e => onChange({ ...filter, status: e.target.value })}>
<option value="">All</option>
<option value="RUNNING">Running</option>
<option value="COMPLETED">Completed</option>
<option value="FAILED">Failed</option>
</select>
<input placeholder="Search title..." value={filter.search} onChange={...} />
</div>
);
}
實作優先順序建議
2026-07-15
2026-07-17
2026-07-19
2026-07-21
2026-07-23
2026-07-25
2026-07-27
2026-07-29
2026-07-31
2026-08-01
2026-08-03
2026-08-05
2026-08-07
2026-08-09
訊息分類標籤化（純前端）
摺疊 Tool Call Group（純前端）
MessageFilterBar UI
Graph CRUD API + 前端
SubAgentDispatch 資料模型
✅ 已存在（migration 0030）——不需新建，只需擴充 DISPATCH_AGENT_CHOICES
Dispatch REST API（基於既有 SubAgentDispatch + query_dispatched_agents）
修正 AutomationAgent 派發追蹤 Gap（G1）——需修改 run_automation_agent_async + DISPATCH_AGENT_CHOICES
SubAgentContainerBlock UI
AgentInteractionTimeline（SVG）（需 G1 修正完成才能顯示 HackerAgent→AutomationAgent 互動）
AssetTopologyMap（D3/ReactFlow）
動態攻擊位置標示
資產點擊 Detail Panel
Phase 1（高 ROI，低風險）
Phase 2（中複雜度）
Phase 2.5：後端 API：include_extra_messages 改為 query param — 解鎖前端 tool 訊息渲染（見 §2 前置條件）
Phase 3（高複雜度）
實作 Roadmap
後端 API 補充需求
端點 方法 說明 是否需要新增
/core/executions DELETE /{id} 刪除 ExecutionGraph ✅ 需新增
/core/executions PATCH /{id} 更新 title/archived ✅ 需新增（需先在 ExecutionGraph 的 metadata JSONField 加 archived 標記，或新增 archived 欄位）
/assistant/threads/{id}/dispatches/ GET 列出 dispatches ✅ 需新增（改為 /core/threads/{caller_id}/dispatches/，基於 SubAgentDispatch.dispatcher_thread）
/assistant/threads/{id}/dispatches/stream/ SSE GET 即時 dispatch 更新 ✅ 需新增（可參考既有 execution_stream_views.py 的 SSE pattern）
/core/targets/{id}/topology/ GET 資產拓撲圖資料 ✅ 需新增
/core/assets/{type}/{id}/pentest-records/ GET 資產滲透記錄 ✅ 需新增
/core/blobs/{blob_id}/page/{page_num}/ GET ContentBlob 分頁讀取（read_page 工具已存在） ✅ 需新增

### 既有 API 路由（不需新建，供參考）

| 端點 | 操作 | 說明 |
|------|------|------|
| /core/overviews/ | GET/POST | Overview CRUD |
| /core/overviews/{id} | GET/PATCH/DELETE | 單一 Overview |
| /core/vulnerabilities/ | GET/POST | Vulnerability CRUD |
| /core/vulnerabilities/{id} | GET/PATCH/DELETE | 單一 Vulnerability |
| /core/vulnerabilities/{id}/pocs | GET/POST | PoC 子資源 |
| /core/attack-plans/ | GET/POST | AttackPlan CRUD |
| /core/attack-plans/{id} | GET/PATCH | 單一 AttackPlan |
| /core/attack-plans/{id}/actions | GET | Plan 下的 Actions |
| /core/actions/{id} | GET/PATCH | 單一 Action |
| /core/attack-vectors/ | GET | AttackVector 列表 |
| /core/attack-vectors/{id} | GET/PATCH | 單一 AttackVector |
| /core/mission-reviews/ | GET | MissionReview 查詢 |
| /assistant/threads/ | GET/POST | Thread CRUD |
| /assistant/threads/{id} | GET/PATCH/DELETE | 單一 Thread |
| /assistant/threads/{id}/messages/ | GET/POST | Message CRUD |
| /assistant/threads/{id}/messages/{mid} | DELETE | 刪除單一 Message |
| /assistant/threads/{id}/messages/stream/ | SSE | LLM token 串流 |
| /assistant/threads/{id}/events/stream/ | SSE | Thread 事件串流 |
| /core/executions/{id}/events/stream/ | SSE | Execution 事件串流 |

### 既有 AI 工具（不需重建，只需加 REST 層）

| 工具 | 位置 | 說明 |
|------|------|------|
| query_dispatched_agents | spawn_tools.py:246 | 查詢 SubAgentDispatch by overview_id |
| read_content_blob | memory_tools.py:383 | 讀取 ContentBlob（支援 page 參數） |
| save_long_content | memory_tools.py:291 | 儲存超長內容為 ContentBlob + auto-attach 到 ExecutionArtifact |
| notify_caller_agent | reconnaissance_tools.py:391 | 子代理回報 parent（優先 SubAgentDispatch 路由） |
| _record_dispatch | __init__.py:599 | 建立 SubAgentDispatch 記錄（helper） |
| read_page | pagination.py:85 | 從 page_breakdown 讀取分頁（utility，未暴露為 API） |

前端新增依賴
json
{
"reactflow": "^11.x", // 拓撲網路圖（或用 d3）
"d3": "^7.x", // 如果選 D3 方案
"@dagrejs/dagre": "^1.x" // 自動佈局 DAG（Agent 樹狀圖）
}
TIP

建議從 Phase 1 開始：純前端的訊息分類與摺疊優化完全不需要後端配合，可以立刻上線，且對使用者體驗改善最直接。

IMPORTANT

SubAgentDispatch 資料模型已存在（migration 0030），重點是修復 G1（AutomationAgent 派發不建立記錄）並擴充 DISPATCH_AGENT_CHOICES，讓前端能追蹤所有層級的派發。

NOTE

AssetTopologyMap 的資料已存在（Subdomain、IP、URL、Seed 都在 Hasura 可查），只需新增一個聚合 API 把它們整理成 graph nodes/edges 格式即可，不需要新的 Django model
