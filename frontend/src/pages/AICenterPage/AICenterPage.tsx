import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { assistantApi } from '../../services/assistantApi';
import { useHasuraSubscription } from '../../hooks/useHasuraSubscription';
import { useDraftInput } from '../../hooks/useDraftInput';
import { usePersistentState } from '../../hooks/usePersistentState';
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
import { cn } from '@/lib/utils';
import { TreeNode, buildTreeNodes } from './components/TreePanel';
import { Sidebar } from './components/Sidebar';
import { AgentPanel } from './components/AgentPanel';
import ChatHeader from './components/ChatHeader';
import ExecutionLogsPanel from './components/ExecutionLogsPanel';
import ThreadEventsPanel from './components/ThreadEventsPanel';

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
    <>
      <style>{`@keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }`}</style>
    <div className="flex h-[calc(100vh-var(--navbar-height)+12px)] w-full mt-[var(--navbar-height)] bg-[linear-gradient(135deg,#0f172a_0%,#0a0e27_100%)] text-slate-50 relative overflow-hidden">
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        targetSearchId={targetSearchId}
        onTargetSearchChange={setTargetSearchId}
        showInternal={showInternal}
        onShowInternalChange={(next) => { setShowInternal(next); localStorage.setItem('aiCenter_showInternal', String(next)); }}
        threadsLoading={threadsLoading}
        threadsError={threadsError}
        sidebarTab={sidebarTab}
        onSidebarTabChange={setSidebarTab}
        threads={allThreads}
        selectedThreadId={selectedThreadId}
        onSelectThread={handleSelectSidebarThread}
        onDeleteThread={handleDeleteThread}
        onCreateThread={createNewThread}
        overviews={overviews}
        overviewsLoading={overviewsLoading}
        boundTargetId={boundTargetId}
        onNavigate={navigate}
        onUnbindTarget={async () => { if (!selectedThreadId) return; await assistantApi.unbindTarget(selectedThreadId); setBoundTargetId(null); }}
      />

      {/* ─── Main chat ───────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        {!sidebarOpen && (
          <button className="absolute top-4 left-4 bg-transparent border-0 text-slate-400 text-2xl cursor-pointer p-1 z-50 transition-colors duration-200 hover:text-slate-300" onClick={() => setSidebarOpen(true)} title="Open sidebar">☰</button>
        )}

        <div className="flex flex-col h-full relative">
          {selectedThreadId ? (
            <>
              <ChatHeader
                label={chatTargetLabel}
                graphCount={activeThreadGraphs.length}
                showLogs={showLogsPanel}
                showEvents={showEventsPanel}
                showTree={showTreePanel}
                treeAgentCount={agentTree.length}
                hasTree={!!rootThreadId}
                onToggleLogs={() => setShowLogsPanel(v => !v)}
                onToggleEvents={() => setShowEventsPanel(v => !v)}
                onToggleTree={() => setShowTreePanel(v => !v)}
              />

              {/* Upper area: messages + input */}
              <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
                <MessageFilterBar filter={msgFilter} onChange={setMsgFilter} />
                <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4" onScroll={handleScroll}>
                  {filteredMessages.length === 0 && !streamingText && (
                    <div className="flex-1 flex flex-col items-center justify-center gap-4 text-slate-500">
                      <div className="text-5xl">AI</div>
                      <div className="text-base font-medium">
                        {messages.length === 0 ? 'Start a conversation' : 'No messages match current filters'}
                      </div>
                    </div>
                  )}
                  {displayLimit < filteredMessages.length && (
                    <div className="text-center p-[10px] text-slate-500 text-sm">Loading older messages...</div>
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
                      <div key={msg.id || idx} className={cn(
                            "w-full max-w-[900px] mx-auto flex",
                            msg.role === 'user' ? 'justify-end' : 'justify-start'
                          )}>
                        <div className={cn(
                          "px-4 py-3 break-words text-[0.95rem] leading-relaxed",
                          msg.role === 'user'
                            ? 'bg-green text-[#020617] rounded-[12px_12px_4px_12px] max-w-[70%]'
                            : 'bg-slate-800 text-slate-300 rounded-[12px_12px_12px_4px] border border-slate-700 max-w-[90%]'
                        )}>
                          {msg.role === 'user' ? (
                            <div className="whitespace-pre-wrap">{msg.textContent}</div>
                          ) : (
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.textContent}</ReactMarkdown>
                          )}
                        </div>
                      </div>
                    );
                  })}
                  {streamingText && (
                    <div className="w-full max-w-[900px] mx-auto flex justify-start">
                      <div className="px-4 py-3 break-words text-[0.95rem] leading-relaxed bg-slate-800 text-slate-300 rounded-[12px_12px_12px_4px] border border-slate-700 max-w-[90%]">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamingText}</ReactMarkdown>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                <div className="px-6 pt-4 pb-6 bg-[linear-gradient(180deg,rgba(15,23,42,0)_0%,rgba(15,23,42,0.8)_100%)] border-t border-slate-800">
                  <div className="flex gap-3 max-w-[900px] mx-auto w-full">
                    <textarea
                      className="flex-1 px-4 py-3 bg-slate-900 border border-slate-800 rounded-lg text-slate-50 text-[0.95rem] resize-none outline-none transition-all duration-200 leading-relaxed placeholder:text-slate-500 hover:border-slate-700 hover:bg-[#0a0f1f] focus:border-green focus:bg-[#0a0f1f] focus:shadow-[0_0_0_2px_rgba(34,197,94,0.15),0_0_16px_rgba(34,197,94,0.2)] disabled:opacity-50 disabled:cursor-not-allowed"
                      placeholder="Type your message... (Shift+Enter for new line)"
                      value={inputVal}
                      onChange={e => setInputVal(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                      disabled={isSending}
                      rows={3}
                    />
                    <button
                      className="px-6 py-3 bg-green text-[#020617] border-0 rounded-lg font-semibold text-[0.95rem] cursor-pointer transition-all duration-200 whitespace-nowrap min-w-[100px] hover:bg-green-400 hover:shadow-[0_0_16px_rgba(34,197,94,0.3)] hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:cursor-not-allowed"
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
                <ExecutionLogsPanel
                  selectedGraphId={selectedGraphId}
                  activeThreadGraphs={activeThreadGraphs}
                  graphStatusFilter={graphStatusFilter}
                  graphHasMore={graphHasMore}
                  onSelectGraph={setSelectedGraphId}
                  onStatusFilterChange={(filter) => { setGraphStatusFilter(filter); setGraphPage(1); }}
                  onArchiveGraph={handleArchiveGraph}
                  onDeleteGraph={handleDeleteGraph}
                  onLoadMore={() => setGraphPage((p) => p + 1)}
                  onClose={() => setShowLogsPanel(false)}
                />
              )}

              {/* ── Thread events panel ──────────────────────────────── */}
              {showEventsPanel && (
                <ThreadEventsPanel
                  threadId={selectedThreadId}
                  onClose={() => setShowEventsPanel(false)}
                />
              )}
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center gap-4 text-slate-500">
              <div className="text-5xl">AI</div>
              <div className="text-base font-medium">
                {allThreads.length === 0 ? 'Create a new conversation to get started' : 'Select a conversation'}
              </div>
            </div>
          )}
        </div>
      </main>

      <AgentPanel
        showTree={showTree}
        showTreePanel={showTreePanel}
        onClose={() => setShowTreePanel(false)}
        treeConnected={treeConnected}
        agentPanelTab={agentPanelTab}
        onTabChange={setAgentPanelTab}
        agentTree={agentTree}
        rootNode={rootNode}
        activeNodeThreadId={activeNodeThreadId}
        onSelectTreeNode={handleSelectTreeNode}
        dispatchTree={dispatchTree}
        boundTargetId={boundTargetId}
        onOpenGraph={setSelectedGraphId}
        onOpenLogsPanel={() => setShowLogsPanel(true)}
        topology={topology}
        selectedTopoNode={selectedTopoNode}
        onSelectTopoNode={setSelectedTopoNode}
      />
    </div>
    </>
  );
};

export default AICenterPage;
