import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { assistantApi } from '../../services/assistantApi';
import { useHasuraSubscription } from '../../hooks/useHasuraSubscription';
import { useDraftInput } from '../../hooks/useDraftInput';
import { usePersistentState } from '../../hooks/usePersistentState';
import ExecutionTimelineViewer from '../../components/ExecutionTimelineViewer';
import ThreadEventTimeline from '../../components/ThreadEventTimeline';
import MessageFilterBar, {
  DEFAULT_MSG_FILTER,
  messagePassesFilter,
  type MessageFilterState,
} from '../../components/MessageFilterBar';
import ToolCallGroup from '../../components/ToolCallGroup';
import SubAgentContainerBlock, {
  dispatchToView,
  type DispatchedGraphView,
} from '../../components/SubAgentContainerBlock';
import AgentInteractionTimeline from '../../components/AgentInteractionTimeline';
import AssetTopologyMap from '../../components/AssetTopologyMap';
import AssetDetailPanel from '../../components/AssetDetailPanel';
import { executionApi } from '../../services/executionApi';
import type {
  AgentInteractionTree,
  ExecutionGraph,
  SubAgentDispatchItem,
  TargetTopology,
  TopologyNode,
} from '../../services/executionApi';
import { OverviewService, type OverviewData } from '../../services/overviewService';
import { GET_AGENT_TREE_SUBSCRIPTION } from '../../queries';
import {
  groupMessagesForRender,
  parseRawMessages,
  type DisplayMessage,
} from '../../types/messages';
import './AICenter.css';

// ── Constants ─────────────────────────────────────────────────────────────

// ── Status badge helpers ──────────────────────────────────────────────────

const STATUS_CLASS: Record<string, string> = {
  EXECUTING:         'tree-badge--executing',
  PLANNING:          'tree-badge--planning',
  COMPLETED:         'tree-badge--completed',
  FAILED:            'tree-badge--failed',
  NEEDS_GUIDANCE:    'tree-badge--needs-guidance',
  WAITING_FOR_ASYNC: 'tree-badge--waiting',
};

const STATUS_ICON: Record<string, string> = {
  EXECUTING:         '⟳',  // spin
  PLANNING:          '◯',  // circle
  COMPLETED:         '✓',  // check
  FAILED:            '✗',  // cross
  NEEDS_GUIDANCE:    '?',
  WAITING_FOR_ASYNC: '⏳',
};

const riskClass = (score: number) =>
  score > 66 ? 'high' : score > 33 ? 'medium' : 'low';

// ── Types ─────────────────────────────────────────────────────────────────

interface TreeNode {
  thread_id: number;
  thread_name: string;
  assistant_id: string;
  is_hidden: boolean;
  bound_target_id: number | null;
  parent_thread_id: number | null;
  overview_id: number | null;
  overview_status: string | null;
  overview_risk_score: number | null;
  target_name: string | null;
  created_at: string;
}

// ── Tree node component ───────────────────────────────────────────────────

function TreeNodeItem({
  node,
  depth,
  allNodes,
  activeNodeThreadId,
  onSelect,
}: {
  node: TreeNode;
  depth: number;
  allNodes: TreeNode[];
  activeNodeThreadId: string | null;
  onSelect: (node: TreeNode) => void;
}) {
  const isActive = activeNodeThreadId === String(node.thread_id);
  const icon = node.assistant_id === 'hacker_assistant_agent' ? 'HA' : 'AI';
  const children =
    node.thread_id != null
      ? allNodes.filter(n => n.parent_thread_id === node.thread_id)
      : [];

  return (
    <div className="tree-node-group">
      <div
        className={`tree-node ${isActive ? 'tree-node--active' : ''}`}
        style={{ paddingLeft: `${8 + depth * 20}px` }}
        onClick={() => onSelect(node)}
        title={node.thread_name}
        data-testid={`tree-node-${node.thread_id}`}
        data-status={node.overview_status || 'unknown'}
        data-depth={depth}
      >
        {depth > 0 && <span className="tree-connector" />}
        <div className="tree-node-label">
          <span className="tree-node-icon">{icon}</span>
          <span className="tree-node-name">
            {node.target_name && depth > 0 ? node.target_name : node.thread_name}
          </span>
        </div>
        {node.overview_status && (
          <span
            className={`tree-node-status-icon tree-node-status-icon--${(STATUS_CLASS[node.overview_status] || 'tree-badge--default').replace('tree-badge--', '')}`}
          >
            {STATUS_ICON[node.overview_status] || '•'}
          </span>
        )}
        <div className="tree-node-meta">
          {isActive && !node.overview_status && (
            <span
              className="tree-node-skeleton"
              data-testid={`skeleton-${node.thread_id}`}
            />
          )}
          {node.overview_status && (
            <span className={`tree-badge ${STATUS_CLASS[node.overview_status] || 'tree-badge--default'}`}>
              {node.overview_status.replace(/_/g, ' ')}
            </span>
          )}
          {node.overview_risk_score !== null && (
            <span className={`tree-badge tree-badge--risk ${riskClass(node.overview_risk_score)}`}>
              Risk {node.overview_risk_score}
            </span>
          )}
        </div>
      </div>
      {children.map(child => (
        <TreeNodeItem
          key={child.thread_id}
          node={child}
          depth={depth + 1}
          allNodes={allNodes}
          activeNodeThreadId={activeNodeThreadId}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}

// ── Helper: build flat TreeNode[] from GQL subscription data ─────────────

// Push a thread node from an overview's aiAssistantThreadByThreadId relationship.
// Also recurse into that thread's own overviews to discover grandchildren.
function _ingestThreadFromOv(
  t: any,
  ov: any,
  parentThreadId: number,
  nodes: TreeNode[],
  seen: Set<number>,
) {
  const tid = Number(t.id);
  if (seen.has(tid)) return;
  seen.add(tid);
  nodes.push({
    thread_id: tid,
    thread_name: t.name,
    assistant_id: t.assistant_id,
    is_hidden: t.is_hidden,
    bound_target_id: t.bound_target_id,
    parent_thread_id: parentThreadId,
    overview_id: Number(ov.id),
    overview_status: ov.status,
    overview_risk_score: ov.risk_score,
    target_name: ov.core_target?.name ?? null,
    created_at: t.created_at,
  });
  // Recurse into this thread's own overviews (grandchildren)
  for (const childOv of Array.isArray(t.core_overviews) ? t.core_overviews : []) {
    const childT = childOv.aiAssistantThreadByThreadId;
    if (childT) _ingestThreadFromOv(childT, childOv, tid, nodes, seen);
  }
}

function buildTreeNodes(rawData: any, rootThreadId: string): TreeNode[] {
  if (!rawData?.ai_assistant_thread_by_pk) return [];

  const root = rawData.ai_assistant_thread_by_pk;
  const nodes: TreeNode[] = [];
  const seen = new Set<number>();

  nodes.push({
    thread_id: Number(root.id),
    thread_name: root.name,
    assistant_id: root.assistant_id,
    is_hidden: root.is_hidden,
    bound_target_id: root.bound_target_id,
    parent_thread_id: null,
    overview_id: null,
    overview_status: null,
    overview_risk_score: null,
    target_name: null,
    created_at: root.created_at,
  });
  seen.add(Number(root.id));

  for (const ov of Array.isArray(root.core_overviews) ? root.core_overviews : []) {
    const t = ov.aiAssistantThreadByThreadId;
    if (t) _ingestThreadFromOv(t, ov, Number(rootThreadId), nodes, seen);
  }

  return nodes;
}

// ── Main page ─────────────────────────────────────────────────────────────

const AICenterPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const initialThreadId = searchParams.get('thread');

  // Chat state
  const [allThreads, setAllThreads] = useState<any[]>([]);
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(initialThreadId);
  const [selectedThreadData, setSelectedThreadData] = useState<any>(null);
  const [activeAssistantId, setActiveAssistantId] = useState<string>('hacker_assistant_agent');
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [inputVal, setInputVal, clearDraft] = useDraftInput(selectedThreadId);
  const [isSending, setIsSending] = useState(false);
  const [streamingText, setStreamingText] = useState<string | null>(null);
  const [displayLimit, setDisplayLimit] = useState(50);
  const [msgFilter, setMsgFilter] = usePersistentState<MessageFilterState>(
    'aiCenter_msgFilter',
    DEFAULT_MSG_FILTER,
  );
  const [dispatchedGraphs, setDispatchedGraphs] = useState<DispatchedGraphView[]>([]);
  const [graphPage, setGraphPage] = useState(1);
  const [graphStatusFilter, setGraphStatusFilter] = useState('');
  const [graphHasMore, setGraphHasMore] = useState(false);
  const GRAPHS_PER_PAGE = 5;

  // Sidebar state
  const [threadsLoading, setThreadsLoading] = useState(true);
  const [threadsError, setThreadsError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [targetSearchId, setTargetSearchId] = useState('');
  const [showInternal, setShowInternal] = useState<boolean>(() =>
    localStorage.getItem('aiCenter_showInternal') === 'true'
  );

  // Target binding
  const [boundTargetId, setBoundTargetId] = useState<number | null>(null);

  // Agent tree state
  const [rootThreadId, setRootThreadId] = useState<string | null>(null);
  const [agentTree, setAgentTree] = useState<TreeNode[]>([]);
  const [showTreePanel, setShowTreePanel] = useState(true);
  const [activeNodeThreadId, setActiveNodeThreadId] = useState<string | null>(null);
  const [agentPanelTab, setAgentPanelTab] = useState<'tree' | 'interaction' | 'topology'>('tree');
  const [dispatchTree, setDispatchTree] = useState<AgentInteractionTree | null>(null);
  const [topology, setTopology] = useState<TargetTopology | null>(null);
  const [selectedTopoNode, setSelectedTopoNode] = useState<TopologyNode | null>(null);

  // Execution graph panel state
  const [selectedGraphId, setSelectedGraphId] = useState<number | null>(null);
  const [activeThreadGraphs, setActiveThreadGraphs] = useState<ExecutionGraph[]>([]);
  const [showLogsPanel, setShowLogsPanel] = useState(false);

  // Thread events panel state
  const [showEventsPanel, setShowEventsPanel] = useState(false);

  // Overview sidebar state
  const [sidebarTab, setSidebarTab] = useState<'threads' | 'overviews'>('threads');
  const [overviews, setOverviews] = useState<OverviewData[]>([]);
  const [overviewsLoading, setOverviewsLoading] = useState(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const cleanupStreamRef = useRef<(() => void) | null>(null);
  // 持久 message SSE 訂閱 cleanup（mount 時開啟、thread 切換/unmount 時關閉）
  const cleanupMessageEventsRef = useRef<(() => void) | null>(null);
  // 輪詢兜底 timer（SSE 失效或仍在等 ai msg 時使用）
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const selectThread = useCallback((id: string | null) => {
    setSelectedThreadId(id);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (id) next.set('thread', id);
      else next.delete('thread');
      return next;
    });
  }, [setSearchParams]);

  // ── GQL subscription for agent tree ──────────────────────────────────

  const treeSubVars = useMemo(() => {
    if (!rootThreadId) return undefined;
    return {
      rootThreadId: parseInt(rootThreadId),
    };
  }, [rootThreadId]);

  const { data: treeRawData, isConnected: treeConnected } = useHasuraSubscription(
    GET_AGENT_TREE_SUBSCRIPTION,
    treeSubVars,
    Boolean(rootThreadId && treeSubVars)
  );

  // Convert GQL data → flat TreeNode[]
  useEffect(() => {
    if (!rootThreadId) { setAgentTree([]); return; }
    if (import.meta.env.DEV) {
      console.debug('[AgentTree] raw GQL data:', treeRawData);
    }
    const nodes = buildTreeNodes(treeRawData, rootThreadId);
    if (import.meta.env.DEV) {
      console.debug('[AgentTree] built nodes:', nodes.map(n => ({ id: n.thread_id, name: n.thread_name, parent: n.parent_thread_id })));
    }
    // Always update: even 1-node result (root only) is valid state
    setAgentTree(nodes);
  }, [treeRawData, rootThreadId]);

  // Lazy-load execution graphs (paginated + status filter)
  useEffect(() => {
    let cancelled = false;
    if (!activeNodeThreadId) {
      setActiveThreadGraphs([]);
      setSelectedGraphId(null);
      setGraphPage(1);
      setGraphHasMore(false);
      return;
    }

    const offset = (graphPage - 1) * GRAPHS_PER_PAGE;
    void executionApi
      .listGraphs({
        thread_id: Number(activeNodeThreadId),
        limit: GRAPHS_PER_PAGE,
        offset,
        status: graphStatusFilter || undefined,
      })
      .then((graphs) => {
        if (cancelled) return;
        setActiveThreadGraphs((prev) => (graphPage === 1 ? graphs : [...prev, ...graphs]));
        setGraphHasMore(graphs.length >= GRAPHS_PER_PAGE);
        if (graphPage === 1) {
          const running = graphs.find((graph) => graph.status === 'RUNNING' || graph.status === 'WAITING');
          setSelectedGraphId((current) => current ?? running?.id ?? graphs[0]?.id ?? null);
          setShowLogsPanel(graphs.length > 0);
        }
      })
      .catch(() => {
        if (!cancelled && graphPage === 1) {
          setActiveThreadGraphs([]);
          setSelectedGraphId(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [activeNodeThreadId, graphPage, graphStatusFilter]);

  // Load SubAgentDispatch records for container blocks
  useEffect(() => {
    let cancelled = false;
    if (!selectedThreadId) {
      setDispatchedGraphs([]);
      return;
    }
    void executionApi
      .listDispatches(selectedThreadId)
      .then((items: SubAgentDispatchItem[]) => {
        if (!cancelled) setDispatchedGraphs(items.map(dispatchToView));
      })
      .catch(() => {
        if (!cancelled) setDispatchedGraphs([]);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedThreadId]);

  // Agent interaction tree (Phase 3)
  useEffect(() => {
    let cancelled = false;
    if (!rootThreadId) {
      setDispatchTree(null);
      return;
    }
    void executionApi
      .getDispatchTree(rootThreadId)
      .then((tree) => {
        if (!cancelled) setDispatchTree(tree);
      })
      .catch(() => {
        if (!cancelled) setDispatchTree(null);
      });
    return () => {
      cancelled = true;
    };
  }, [rootThreadId, dispatchedGraphs.length]);

  // Asset topology for bound target
  useEffect(() => {
    let cancelled = false;
    if (!boundTargetId) {
      setTopology(null);
      setSelectedTopoNode(null);
      return;
    }
    void executionApi
      .getTargetTopology(boundTargetId)
      .then((t) => {
        if (!cancelled) setTopology(t);
      })
      .catch(() => {
        if (!cancelled) setTopology(null);
      });
    return () => {
      cancelled = true;
    };
  }, [boundTargetId]);

  // ── Overview fetch ─────────────────────────────────────────────────────

  useEffect(() => {
    let cancelled = false;
    if (!boundTargetId) { setOverviews([]); return; }
    setOverviewsLoading(true);
    OverviewService.list({ target_id: boundTargetId })
      .then(data => { if (!cancelled) setOverviews(data); })
      .catch(() => { if (!cancelled) setOverviews([]); })
      .finally(() => { if (!cancelled) setOverviewsLoading(false); });
    return () => { cancelled = true; };
  }, [boundTargetId]);

  // ── Scroll helpers ────────────────────────────────────────────────────

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(() => { scrollToBottom(); }, [messages, streamingText]);

  // ── Load threads ──────────────────────────────────────────────────────

  useEffect(() => { loadThreads(); }, [targetSearchId, showInternal]);
  // 訊息載入與持久 SSE 訂閱改由下方的獨立 useEffect 統一管理（避免重複載入）

  const loadThreads = async () => {
    setThreadsLoading(true);
    setThreadsError(null);
    try {
      const params: any = { include_hidden: showInternal };
      if (targetSearchId.trim()) params.target_id = parseInt(targetSearchId);

      const res: any[] = (await assistantApi.getThreads(params)) as any[];
      const filtered = showInternal
        ? res.sort((a, b) => Number(b.id) - Number(a.id))
        : res
            .filter(
              t =>
                !t.is_hidden &&
                (t.assistant_id !== 'automation_agent' || t.bound_overview_id) &&
                !t.name?.startsWith('subagent_') &&
                !t.name?.startsWith('ephemeral_') &&
                !t.name?.includes('Analysis Batch')
            )
            .sort((a, b) => Number(b.id) - Number(a.id));

      setAllThreads(filtered);

      if (filtered.length > 0 && !selectedThreadId) {
        handleSelectSidebarThread(filtered[0]);
      } else if (filtered.length === 0 && selectedThreadId) {
        selectThread(null);
        setSelectedThreadData(null);
        setMessages([]);
      } else if (selectedThreadId) {
        const cur = filtered.find((t: any) => String(t.id) === selectedThreadId);
        if (cur) { setBoundTargetId(cur.bound_target_id ?? null); setSelectedThreadData(cur); }
      }
    } catch (err) {
      console.error('Failed to load threads', err);
      setThreadsError(`Failed to load: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setThreadsLoading(false);
    }
  };

  const loadMessagesForThread = async (threadId: string) => {
    try {
      // include_tools=true unlocks tool_call / tool_result rendering (G5)
      const msgArray = await assistantApi.getMessages(threadId, true);
      const parsed = parseRawMessages(msgArray);
      setDisplayLimit(50);
      setMessages(parsed);
      return parsed;
    } catch (err) {
      console.error('Failed to load messages', err);
      setMessages([]);
      return [];
    }
  };

  const matchDispatchForMessage = useCallback(
    (msg: DisplayMessage): DispatchedGraphView | undefined => {
      if (dispatchedGraphs.length === 0) return undefined;
      const toolNames = new Set(
        (msg.toolCalls ?? []).map((tc) => tc.name).concat(msg.toolName ? [msg.toolName] : []),
      );
      // Prefer exact agent-type match; fall back to first unmatched dispatch
      const byType = dispatchedGraphs.find((g) => toolNames.has(g.sub_agent_type));
      if (byType) return byType;
      if (toolNames.has('automation_agent')) {
        return dispatchedGraphs.find((g) => g.sub_agent_type === 'automation_agent')
          ?? dispatchedGraphs[0];
      }
      return dispatchedGraphs[0];
    },
    [dispatchedGraphs],
  );

  const handleArchiveGraph = async (graphId: number) => {
    try {
      await executionApi.archiveGraph(graphId, true);
      setActiveThreadGraphs((prev) => prev.filter((g) => g.id !== graphId));
      if (selectedGraphId === graphId) {
        setSelectedGraphId(null);
      }
    } catch (err) {
      console.error('Failed to archive graph', err);
    }
  };

  const handleDeleteGraph = async (graphId: number) => {
    if (!window.confirm(`Delete execution graph #${graphId}?`)) return;
    try {
      await executionApi.deleteGraph(graphId);
      setActiveThreadGraphs((prev) => prev.filter((g) => g.id !== graphId));
      if (selectedGraphId === graphId) setSelectedGraphId(null);
    } catch (err) {
      console.error('Failed to delete graph', err);
    }
  };

  // ── Thread / node selection ───────────────────────────────────────────

  // 持久 message SSE 訂閱 + 輪詢兜底
  // 解決「刷新時 AI 回應尚未寫入 DB → 永遠看不到」的問題：
  //   1. thread 切換時關閉舊訂閱、載入歷史、開啟新訂閱
  //   2. 收到 message_created 事件 → reload messages（補上背景完成的 AI 回應）
  //   3. 若歷史最後一條是 user msg 而無對應 ai msg → 啟動輪詢兜底
  useEffect(() => {
    if (!selectedThreadId) return;

    // 關閉舊訂閱與輪詢
    cleanupMessageEventsRef.current?.();
    cleanupMessageEventsRef.current = null;
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }

    let cancelled = false;

    const init = async () => {
      const parsed = await loadMessagesForThread(selectedThreadId);
      if (cancelled) return;

      // 偵測：最後一條是 user msg 而無 ai msg → 可能有進行中的回應
      const hasPending =
        parsed.length > 0 && parsed[parsed.length - 1].role === 'user';

      // (1) 持久 SSE 訂閱：收到新訊息即 reload
      cleanupMessageEventsRef.current = assistantApi.streamMessageEvents(
        selectedThreadId,
        () => {
          // 收到新訊息 → reload；同時停止輪詢（SSE 已接通）
          if (pollTimerRef.current) {
            clearInterval(pollTimerRef.current);
            pollTimerRef.current = null;
          }
          loadMessagesForThread(selectedThreadId);
        },
      );

      // (2) 輪詢兜底：只在 hasPending 時啟動，SSE 接通後自動停止
      if (hasPending) {
        let attempts = 0;
        const maxAttempts = 60; // 最多輪詢 60 次（約 2 分鐘）
        pollTimerRef.current = setInterval(async () => {
          if (cancelled || attempts >= maxAttempts) {
            if (pollTimerRef.current) {
              clearInterval(pollTimerRef.current);
              pollTimerRef.current = null;
            }
            return;
          }
          attempts++;
          try {
            const msgs = await loadMessagesForThread(selectedThreadId);
            // AI 回應已到（最後一條變成 assistant）→ 停止輪詢
            if (msgs.length > 0 && msgs[msgs.length - 1].role === 'assistant') {
              if (pollTimerRef.current) {
                clearInterval(pollTimerRef.current);
                pollTimerRef.current = null;
              }
            }
          } catch {
            /* ignore transient errors */
          }
        }, 2000);
      }
    };

    init();

    return () => {
      cancelled = true;
      cleanupMessageEventsRef.current?.();
      cleanupMessageEventsRef.current = null;
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
  }, [selectedThreadId]);

  const handleSelectSidebarThread = (thread: any) => {
    selectThread(String(thread.id));
    setSelectedThreadData(thread);
    setActiveAssistantId(thread.assistant_id || 'hacker_assistant_agent');
    setActiveNodeThreadId(String(thread.id));
    setBoundTargetId(thread.bound_target_id ?? null);
    setRootThreadId(thread.assistant_id === 'hacker_assistant_agent' ? String(thread.id) : null);
    setShowLogsPanel(false);
    setShowEventsPanel(false);
    setSelectedGraphId(null);
    setActiveThreadGraphs([]);
    setGraphPage(1);
    setGraphStatusFilter('');
  };

  const handleSelectTreeNode = useCallback((node: TreeNode) => {
    selectThread(String(node.thread_id));
    setSelectedThreadData({
      id: node.thread_id,
      name: node.thread_name,
      assistant_id: node.assistant_id,
      is_hidden: node.is_hidden,
      bound_target_id: node.bound_target_id,
    });
    setActiveAssistantId(node.assistant_id || 'hacker_assistant_agent');
    setActiveNodeThreadId(String(node.thread_id));
    if (node.bound_target_id) setBoundTargetId(node.bound_target_id);

    setSelectedGraphId(null);
    setActiveThreadGraphs([]);
    setGraphPage(1);
    setGraphStatusFilter('');
    setShowLogsPanel(node.assistant_id !== 'hacker_assistant_agent');
  }, [selectThread]);

  // ── Create / delete ───────────────────────────────────────────────────

  const createNewThread = async () => {
    try {
      const res: any = await assistantApi.createThread('New chat');
      await loadThreads();
      handleSelectSidebarThread(res);
    } catch (err) { console.error('Failed to create thread', err); }
  };

  const handleDeleteThread = async (threadId: string | null) => {
    if (!threadId) return;
    if (!window.confirm('確定要刪除這個對話嗎？')) return;
    try {
      await assistantApi.deleteThread(threadId);
      if (selectedThreadId === threadId) {
        selectThread(null);
        setSelectedThreadData(null);
        setMessages([]);
        setRootThreadId(null);
        setAgentTree([]);
        setShowLogsPanel(false);
      }
      await loadThreads();
    } catch (err) { console.error('Failed to delete thread', err); }
  };

  // ── Send message ──────────────────────────────────────────────────────

  const handleSend = useCallback(async () => {
    if (!inputVal.trim() || !selectedThreadId) return;
    if (!selectedThreadData) { alert('This conversation was deleted'); selectThread(null); return; }

    const userMsg = inputVal;
    clearDraft();
    setIsSending(true);
    setStreamingText('');
    setMessages(prev => [
      ...prev,
      {
        id: `local-user-${Date.now()}`,
        role: 'user',
        category: 'user',
        textContent: userMsg,
      },
    ]);
    cleanupStreamRef.current?.();

    const shouldAutoRename =
      selectedThreadData?.assistant_id === 'hacker_assistant_agent' &&
      (selectedThreadData?.name === 'New chat' || !selectedThreadData?.name);

    const cleanup = assistantApi.streamMessage(
      selectedThreadId,
      userMsg,
      activeAssistantId,
      (chunk: string) => { setStreamingText(prev => (prev ?? '') + chunk); scrollToBottom(); },
      async () => {
        setStreamingText(null);
        setIsSending(false);
        cleanupStreamRef.current = null;
        if (shouldAutoRename && streamingText) {
          const firstLine = (streamingText.split('\n').find(l => l.trim().length > 0) || '').trim();
          const title = firstLine.slice(0, 60) || 'New chat';
          try { await assistantApi.updateThread(selectedThreadId, { name: title }); } catch { /* non-fatal */ }
        }
        await loadThreads();
        await loadMessagesForThread(selectedThreadId);
      },
      async (errMsg: string) => {
        console.error('[SSE error]', errMsg);
        setStreamingText(null);
        setIsSending(false);
        cleanupStreamRef.current = null;
        setMessages(prev => [
          ...prev,
          {
            id: `local-err-${Date.now()}`,
            role: 'assistant',
            category: 'ai_response',
            textContent: `Error: ${errMsg}`,
            isError: true,
          },
        ]);
        await loadMessagesForThread(selectedThreadId);
      },
      () => { /* onStats noop */ }
    );
    cleanupStreamRef.current = cleanup;
  }, [inputVal, selectedThreadId, selectedThreadData, activeAssistantId, streamingText, clearDraft]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    if (e.currentTarget.scrollTop === 0 && displayLimit < filteredMessages.length) {
      const container = e.currentTarget;
      const prevScrollHeight = container.scrollHeight;
      setDisplayLimit(prev => prev + 50);
      requestAnimationFrame(() => { if (container) container.scrollTop = container.scrollHeight - prevScrollHeight; });
    }
  };

  // ── Derived ───────────────────────────────────────────────────────────

  const filteredMessages = useMemo(
    () =>
      messages.filter((m) =>
        messagePassesFilter(m.category, msgFilter, m.assistantId || activeAssistantId),
      ),
    [messages, msgFilter, activeAssistantId],
  );
  const displayedMessages = filteredMessages.slice(-displayLimit);
  const renderItems = useMemo(
    () => groupMessagesForRender(displayedMessages),
    [displayedMessages],
  );
  const rootNode = agentTree.find(n => n.parent_thread_id === null) ?? null;
  const showTree = showTreePanel && rootThreadId !== null;

  const activeNodeData = agentTree.find(n => String(n.thread_id) === activeNodeThreadId);
  const chatTargetLabel = activeNodeData
    ? `AI ${activeNodeData.assistant_id}${activeNodeData.target_name ? ` — ${activeNodeData.target_name}` : ''}`
    : selectedThreadData
      ? `${selectedThreadData.name || 'Hacker AI'}`
      : null;

  // ── Render ────────────────────────────────────────────────────────────

  return (
    <div className="aicenter-container">
      {/* ─── Sidebar ─────────────────────────────────────────────────── */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <h3>CONVERSATIONS</h3>
          <button className="sidebar-toggle" onClick={() => setSidebarOpen(false)} title="Collapse">✕</button>
        </div>

        <button className="new-chat-btn" onClick={createNewThread} disabled={threadsLoading}>
          + New Chat
        </button>

        <div className="sidebar-filter">
          <input
            type="text"
            placeholder="Filter by Target ID..."
            value={targetSearchId}
            onChange={e => setTargetSearchId(e.target.value)}
          />
          {targetSearchId && (
            <button className="clear-filter" onClick={() => setTargetSearchId('')}>✕</button>
          )}
        </div>

        <div style={{ padding: '4px 8px 8px' }}>
          <button
            className={`c2-btn c2-btn--sm ${showInternal ? 'c2-btn--primary' : 'c2-btn--ghost'}`}
            onClick={() => { const next = !showInternal; setShowInternal(next); localStorage.setItem('aiCenter_showInternal', String(next)); }}
            style={{ width: '100%', justifyContent: 'center', fontSize: '0.7rem' }}
          >
            {showInternal ? 'Show system threads' : 'User conversations only'}
          </button>
        </div>

        {threadsLoading && <div className="sidebar-loading"><span className="pulse">●</span> Loading...</div>}
        {threadsError && <div className="sidebar-error">Error: {threadsError}</div>}

        <div className="sidebar-tabs" style={{ display: 'flex', gap: 4, padding: '4px 8px 0' }}>
          <button
            className={`c2-btn c2-btn--sm ${sidebarTab === 'threads' ? 'c2-btn--primary' : 'c2-btn--ghost'}`}
            style={{ flex: 1, justifyContent: 'center', fontSize: '0.7rem' }}
            onClick={() => setSidebarTab('threads')}
          >
            THREADS
          </button>
          <button
            className={`c2-btn c2-btn--sm ${sidebarTab === 'overviews' ? 'c2-btn--primary' : 'c2-btn--ghost'}`}
            style={{ flex: 1, justifyContent: 'center', fontSize: '0.7rem' }}
            onClick={() => setSidebarTab('overviews')}
          >
            OVERVIEWS{overviews.length > 0 ? ' ✓' : ''}
          </button>
        </div>

        {sidebarTab === 'threads' && (
          <div className="threads-list">
            {allThreads.length === 0 && !threadsLoading && (
              <div className="empty-state">No conversations yet</div>
            )}
            {allThreads.map(thread => (
              <div
                key={thread.id}
                className={`thread-item ${selectedThreadId === String(thread.id) ? 'active' : ''}`}
                onClick={() => handleSelectSidebarThread(thread)}
              >
                <div className="thread-name">{thread.name || 'Untitled'}</div>
                {selectedThreadId === String(thread.id) && (
                  <button
                    className="delete-btn"
                    onClick={e => { e.stopPropagation(); handleDeleteThread(String(thread.id)); }}
                    title="Delete conversation"
                  >
                    Delete
                  </button>
                )}
              </div>
            ))}
          </div>
        )}

        {sidebarTab === 'overviews' && (
          <div className="threads-list">
            {overviewsLoading && <div className="sidebar-loading"><span className="pulse">●</span> Loading...</div>}
            {!boundTargetId && !overviewsLoading && (
              <div className="empty-state">Select a thread bound to a target to see its overviews</div>
            )}
            {overviews.map(ov => (
              <div key={ov.id} className="thread-item" style={{ flexDirection: 'column', alignItems: 'stretch', gap: 6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div className="thread-name">Overview #{ov.id}</div>
                    <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{ov.status} · risk {ov.risk_score}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 4 }}>
                  {ov.thread_id && (
                    <button
                      className="c2-btn c2-btn--ghost c2-btn--sm"
                      style={{ flex: 1, fontSize: '0.65rem' }}
                      onClick={() => handleSelectSidebarThread({
                        id: ov.thread_id,
                        name: `Overview #${ov.id}`,
                        assistant_id: 'automation_agent',
                        is_hidden: true,
                        bound_target_id: null,
                      })}
                    >
                      VIEW THREAD
                    </button>
                  )}
                  <button
                    className="c2-btn c2-btn--ghost c2-btn--sm"
                    style={{ flex: 1, fontSize: '0.65rem' }}
                    onClick={() => navigate(`/overviews/${ov.id}`)}
                  >
                    EDIT DETAIL
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {boundTargetId && (
          <div className="sidebar-footer">
            <div className="target-badge">
              <span>Target: {boundTargetId}</span>
              <button
                onClick={async () => { if (!selectedThreadId) return; await assistantApi.unbindTarget(selectedThreadId); setBoundTargetId(null); }}
                title="Release target"
              >✕</button>
            </div>
          </div>
        )}
      </aside>

      {/* ─── Main chat ───────────────────────────────────────────────── */}
      <main className="chat-main">
        {!sidebarOpen && (
          <button className="sidebar-toggle-main" onClick={() => setSidebarOpen(true)} title="Open sidebar">☰</button>
        )}

        <div className="chat-container">
          {selectedThreadId ? (
            <>
              {/* Chat header */}
              <div className="chat-header-bar">
                <div className="chat-header-label">{chatTargetLabel}</div>
                <div className="chat-header-actions">
                  {activeThreadGraphs.length > 0 && (
                    <button
                      className={`tool-log-toggle-btn ${showLogsPanel ? 'active' : ''}`}
                      onClick={() => setShowLogsPanel(v => !v)}
                      title="Toggle execution timeline"
                    >
                      {activeThreadGraphs.length} graph{activeThreadGraphs.length > 1 ? 's' : ''}
                    </button>
                  )}
                  <button
                    className={`tool-log-toggle-btn ${showEventsPanel ? 'active' : ''}`}
                    onClick={() => setShowEventsPanel(v => !v)}
                    title="Toggle thread events"
                  >
                    Events
                  </button>
                  {rootThreadId && (
                    <button
                      className={`tree-toggle-btn ${showTreePanel ? 'active' : ''}`}
                      onClick={() => setShowTreePanel(v => !v)}
                      title="Toggle Agent Tree"
                    >
                      {agentTree.length > 1 ? `${agentTree.length - 1} agent${agentTree.length > 2 ? 's' : ''}` : 'Tree'}
                    </button>
                  )}
                </div>
              </div>

              {/* Upper area: messages + input */}
              <div className="chat-upper">
                <MessageFilterBar filter={msgFilter} onChange={setMsgFilter} />
                <div className="messages-area" onScroll={handleScroll}>
                  {filteredMessages.length === 0 && !streamingText && (
                    <div className="empty-chat">
                      <div className="empty-icon">AI</div>
                      <div className="empty-text">
                        {messages.length === 0 ? 'Start a conversation' : 'No messages match current filters'}
                      </div>
                    </div>
                  )}
                  {displayLimit < filteredMessages.length && (
                    <div className="loading-older">Loading older messages...</div>
                  )}
                  {renderItems.map((item, idx) => {
                    if (item.kind === 'tool_group') {
                      return (
                        <ToolCallGroup
                          key={`tg-${item.calls[0]?.id ?? idx}`}
                          calls={item.calls}
                          results={item.results}
                        />
                      );
                    }
                    if (item.kind === 'subagent') {
                      const matched = matchDispatchForMessage(item.message);
                      if (matched) {
                        return (
                          <SubAgentContainerBlock
                            key={`sa-${item.message.id}`}
                            graph={matched}
                            onViewGraph={(gid) => {
                              setSelectedGraphId(gid);
                              setShowLogsPanel(true);
                            }}
                            onViewThread={(tid) => {
                              handleSelectSidebarThread({
                                id: tid,
                                name: `Sub-agent #${tid}`,
                                assistant_id: matched.sub_agent_type,
                                is_hidden: true,
                                bound_target_id: boundTargetId,
                              });
                            }}
                          />
                        );
                      }
                      // Fallback: no dispatch record yet — show tool call group style
                      return (
                        <ToolCallGroup
                          key={`sa-fallback-${item.message.id}`}
                          calls={[item.message]}
                          results={[]}
                        />
                      );
                    }
                    const msg = item.message;
                    return (
                      <div key={msg.id || idx} className={`message message-${msg.role}${msg.isError ? ' message-error' : ''}`}>
                        <div className="message-content">
                          {msg.role === 'user' ? (
                            <div className="user-text">{msg.textContent}</div>
                          ) : (
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.textContent}</ReactMarkdown>
                          )}
                        </div>
                      </div>
                    );
                  })}
                  {streamingText && (
                    <div className="message message-assistant">
                      <div className="message-content">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamingText}</ReactMarkdown>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                <div className="input-area">
                  <div className="input-wrapper">
                    <textarea
                      placeholder="Type your message... (Shift+Enter for new line)"
                      value={inputVal}
                      onChange={e => setInputVal(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                      disabled={isSending}
                      rows={3}
                    />
                    <button
                      className="send-btn"
                      onClick={handleSend}
                      disabled={isSending || !inputVal.trim() || !selectedThreadId}
                      title={isSending ? 'Sending...' : 'Send message (Enter)'}
                    >
                      {isSending ? '...' : 'Send'}
                    </button>
                  </div>
                </div>
              </div>

              {/* ── Execution timeline panel ─────────────────────────── */}
              {showLogsPanel && (
                <div className="logs-panel">
                  <div className="logs-panel-header">
                    <div className="logs-panel-title">
                      <span>EXECUTION GRAPH</span>
                      {selectedGraphId && <span className="logs-graph-status">Graph #{selectedGraphId}</span>}
                    </div>

                    <div className="logs-panel-controls">
                      <select
                        className="graph-picker"
                        value={graphStatusFilter}
                        onChange={(e) => {
                          setGraphStatusFilter(e.target.value);
                          setGraphPage(1);
                        }}
                        title="Filter by status"
                      >
                        <option value="">All</option>
                        <option value="RUNNING">Running</option>
                        <option value="WAITING">Waiting</option>
                        <option value="SUCCEEDED">Succeeded</option>
                        <option value="FAILED">Failed</option>
                      </select>
                      {activeThreadGraphs.length > 0 && (
                        <select
                          className="graph-picker"
                          value={selectedGraphId ?? ''}
                          onChange={e => setSelectedGraphId(Number(e.target.value))}
                        >
                          {activeThreadGraphs.map(graph => (
                            <option key={graph.id} value={graph.id}>
                              #{graph.id} [{graph.status}] {graph.title || graph.assistant_id}
                            </option>
                          ))}
                        </select>
                      )}
                      {selectedGraphId && (
                        <>
                          <button
                            className="logs-close-btn"
                            onClick={() => handleArchiveGraph(selectedGraphId)}
                            title="Archive graph"
                          >Archive</button>
                          <button
                            className="logs-close-btn"
                            onClick={() => handleDeleteGraph(selectedGraphId)}
                            title="Delete graph"
                          >Delete</button>
                        </>
                      )}
                      <button
                        className="logs-close-btn"
                        onClick={() => setShowLogsPanel(false)}
                        title="Close logs panel"
                      >✕</button>
                    </div>
                  </div>

                  <div className="logs-panel-body">
                    {selectedGraphId ? (
                      <ExecutionTimelineViewer graphId={selectedGraphId} compact autoScroll />
                    ) : (
                      <div className="logs-empty">No execution graph selected</div>
                    )}
                    {graphHasMore && (
                      <div style={{ padding: 8, textAlign: 'center' }}>
                        <button
                          className="c2-btn c2-btn--ghost c2-btn--sm"
                          onClick={() => setGraphPage((p) => p + 1)}
                        >
                          Load More
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* ── Thread events panel ──────────────────────────────── */}
              {showEventsPanel && (
                <div className="logs-panel">
                  <div className="logs-panel-header">
                    <div className="logs-panel-title">
                      <span>THREAD EVENTS</span>
                    </div>
                    <div className="logs-panel-controls">
                      <button
                        className="logs-close-btn"
                        onClick={() => setShowEventsPanel(false)}
                        title="Close events panel"
                      >✕</button>
                    </div>
                  </div>
                  <div className="logs-panel-body">
                    <ThreadEventTimeline threadId={selectedThreadId} autoScroll />
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="no-thread">
              <div className="no-thread-icon">AI</div>
              <div className="no-thread-text">
                {allThreads.length === 0 ? 'Create a new conversation to get started' : 'Select a conversation'}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* ─── Agent / Topology panel ──────────────────────────────────── */}
      {showTree && (
        <aside className="agent-tree-panel agent-tree-panel--wide">
          <div className="tree-panel-header">
            <h4>AGENTS</h4>
            <div className="tree-panel-actions">
              <span
                className={`tree-live-dot ${treeConnected ? 'connected' : 'disconnected'}`}
                title={treeConnected ? 'Live — auto-updating' : 'Disconnected'}
              />
              <button className="tree-action-btn" onClick={() => setShowTreePanel(false)} title="Close">✕</button>
            </div>
          </div>

          <div className="agent-panel-tabs">
            {([
              ['tree', 'Tree'],
              ['interaction', 'Interaction'],
              ['topology', 'Topology'],
            ] as const).map(([key, label]) => (
              <button
                key={key}
                type="button"
                className={`agent-panel-tab ${agentPanelTab === key ? 'active' : ''}`}
                onClick={() => setAgentPanelTab(key)}
              >
                {label}
              </button>
            ))}
          </div>

          <div className="tree-body">
            {agentPanelTab === 'tree' && (
              <>
                {agentTree.length === 0 && (
                  <div className="tree-empty">No sub-agents yet</div>
                )}
                {rootNode && (
                  <TreeNodeItem
                    node={rootNode}
                    depth={0}
                    allNodes={agentTree}
                    activeNodeThreadId={activeNodeThreadId}
                    onSelect={handleSelectTreeNode}
                  />
                )}
              </>
            )}

            {agentPanelTab === 'interaction' && (
              <AgentInteractionTimeline
                tree={dispatchTree}
                selectedThreadId={activeNodeThreadId ? Number(activeNodeThreadId) : null}
                onSelectNode={(n) => {
                  if (!n.thread_id) return;
                  handleSelectTreeNode({
                    thread_id: n.thread_id,
                    thread_name: n.agent_id || `Thread ${n.thread_id}`,
                    assistant_id: n.agent_id || 'automation_agent',
                    is_hidden: true,
                    bound_target_id: boundTargetId,
                    parent_thread_id: null,
                    overview_id: null,
                    overview_status: null,
                    overview_risk_score: null,
                    target_name: null,
                    created_at: n.dispatched_at || '',
                  });
                  if (n.graph_id) {
                    setSelectedGraphId(n.graph_id);
                    setShowLogsPanel(true);
                  }
                }}
              />
            )}

            {agentPanelTab === 'topology' && (
              <div className="topology-panel-stack">
                <AssetTopologyMap
                  topology={topology}
                  selectedNodeId={selectedTopoNode?.id ?? null}
                  onSelectNode={setSelectedTopoNode}
                />
                {selectedTopoNode && (
                  <AssetDetailPanel
                    node={selectedTopoNode}
                    onClose={() => setSelectedTopoNode(null)}
                    onOpenGraph={(gid) => {
                      setSelectedGraphId(gid);
                      setShowLogsPanel(true);
                    }}
                  />
                )}
              </div>
            )}
          </div>
        </aside>
      )}
    </div>
  );
};

export default AICenterPage;
