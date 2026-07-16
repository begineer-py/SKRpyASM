import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { MessageSquarePlus } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { assistantApi, executionApi, OverviewService, type OverviewData } from '../services/aiApi';
import type { ThreadSummary } from '../../../services/assistantApi';
import { useHasuraSubscription } from '../../../hooks/useHasuraSubscription';
import { useDraftInput } from '../../../hooks/useDraftInput';
import { usePersistentState } from '../../../hooks/usePersistentState';
import {
  DEFAULT_MSG_FILTER,
  messagePassesFilter,
  type MessageFilterState,
} from '../../../components/MessageFilterBar';
import ToolCallGroup from '../../../components/ToolCallGroup';
import SubAgentContainerBlock, {
  dispatchToView,
  type DispatchedGraphView,
} from '../../../components/SubAgentContainerBlock';
import type {
  AgentInteractionTree,
  ExecutionGraph,
  TargetTopology,
  TopologyNode,
} from '../services/aiApi';
import type { SubAgentDispatchItem as ExecutionDispatchItem } from '../../../services/executionApi';
import { GET_AGENT_TREE_SUBSCRIPTION } from '../../../queries';
import {
  groupMessagesForRender,
  parseRawMessages,
  type DisplayMessage,
} from '../../../types/messages';
import { buildTreeNodes, type TreeNode } from '../components/TreePanel';
import { Sidebar } from '../components/Sidebar';
import { AgentPanel } from '../components/AgentPanel';
import ChatHeader from '../components/ChatHeader';
import ThreadEventsPanel from '../components/ThreadEventsPanel';
import { cn } from '@/lib/utils';

// ── Main page ─────────────────────────────────────────────────────────────

const AICenterPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const initialThreadId = searchParams.get('thread');

  // Chat state
  const [allThreads, setAllThreads] = useState<ThreadSummary[]>([]);
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(initialThreadId);
  const [selectedThreadData, setSelectedThreadData] = useState<ThreadSummary | null>(null);
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
  const [showTreePanel, setShowTreePanel] = useState(false);
  const [activeNodeThreadId, setActiveNodeThreadId] = useState<string | null>(null);
  const [agentPanelTab, setAgentPanelTab] = useState<'tree' | 'interaction' | 'topology'>('tree');
  const [dispatchTree, setDispatchTree] = useState<AgentInteractionTree | null>(null);
  const [topology, setTopology] = useState<TargetTopology | null>(null);
  const [selectedTopoNode, setSelectedTopoNode] = useState<TopologyNode | null>(null);

  const [selectedGraphId, setSelectedGraphId] = useState<number | null>(null);
  const [activeThreadGraphs, setActiveThreadGraphs] = useState<ExecutionGraph[]>([]);

  // Thread events panel state
  const [showEventsPanel, setShowEventsPanel] = useState(false);

  const [overviews, setOverviews] = useState<OverviewData[]>([]);
  const [overviewsLoading, setOverviewsLoading] = useState(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const cleanupStreamRef = useRef<(() => void) | null>(null);
  const cleanupMessageEventsRef = useRef<(() => void) | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const agentTriggerRef = useRef<HTMLButtonElement>(null);
  const eventsTriggerRef = useRef<HTMLButtonElement>(null);

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

  const { data: treeRawData } = useHasuraSubscription(
    GET_AGENT_TREE_SUBSCRIPTION,
    treeSubVars,
    Boolean(rootThreadId && treeSubVars)
  );

  useEffect(() => {
    if (!rootThreadId) { setAgentTree([]); return; }
    if (import.meta.env.DEV) {
      console.debug('[AgentTree] raw GQL data:', treeRawData);
    }
    const nodes = buildTreeNodes(treeRawData, rootThreadId);
    if (import.meta.env.DEV) {
      console.debug('[AgentTree] built nodes:', nodes.map(n => ({ id: n.thread_id, name: n.thread_name, parent: n.parent_thread_id })));
    }
    setAgentTree(nodes);
  }, [treeRawData, rootThreadId]);

  useEffect(() => {
    let cancelled = false;
    if (!activeNodeThreadId) {
      setActiveThreadGraphs([]);
      setSelectedGraphId(null);
      return;
    }

    void executionApi
      .listGraphs({
        thread_id: Number(activeNodeThreadId),
        limit: 5,
      })
      .then((graphs) => {
        if (cancelled) return;
        setActiveThreadGraphs(graphs);
        const running = graphs.find((graph) => graph.status === 'RUNNING' || graph.status === 'WAITING');
        setSelectedGraphId((current) => current ?? running?.id ?? graphs[0]?.id ?? null);
      })
      .catch(() => {
        if (!cancelled) {
          setActiveThreadGraphs([]);
          setSelectedGraphId(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [activeNodeThreadId]);

  useEffect(() => {
    let cancelled = false;
    if (!selectedThreadId) {
      setDispatchedGraphs([]);
      return;
    }
    void executionApi
      .listDispatches(selectedThreadId)
      .then((items: ExecutionDispatchItem[]) => {
        if (!cancelled) setDispatchedGraphs(items.map(dispatchToView));
      })
      .catch(() => {
        if (!cancelled) setDispatchedGraphs([]);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedThreadId]);

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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(() => { scrollToBottom(); }, [messages, streamingText]);

  // loadThreads also updates the selected thread and would make this effect loop.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { loadThreads(); }, [showInternal]);

  const loadThreads = async () => {
    setThreadsLoading(true);
    setThreadsError(null);
    try {
      const params = { include_hidden: showInternal };

      const res = await assistantApi.getThreads(params);
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
        const cur = filtered.find((t) => String(t.id) === selectedThreadId);
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

  const openGraph = useCallback((graphId: number) => {
    if (Number.isSafeInteger(graphId) && graphId > 0) {
      navigate(`/execution-monitor?graph=${graphId}`);
    }
  }, [navigate]);

  useEffect(() => {
    if (!selectedThreadId) return;

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

      const hasPending =
        parsed.length > 0 && parsed[parsed.length - 1].role === 'user';

      cleanupMessageEventsRef.current = assistantApi.streamMessageEvents(
        selectedThreadId,
        () => {
          if (pollTimerRef.current) {
            clearInterval(pollTimerRef.current);
            pollTimerRef.current = null;
          }
          loadMessagesForThread(selectedThreadId);
        },
      );

      if (hasPending) {
        let attempts = 0;
        const maxAttempts = 60;
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

  const handleSelectSidebarThread = (thread: ThreadSummary) => {
    selectThread(String(thread.id));
    setSelectedThreadData(thread);
    setActiveAssistantId(thread.assistant_id || 'hacker_assistant_agent');
    setActiveNodeThreadId(String(thread.id));
    setBoundTargetId(thread.bound_target_id ?? null);
    setRootThreadId(thread.assistant_id === 'hacker_assistant_agent' ? String(thread.id) : null);
    setShowEventsPanel(false);
    setSelectedGraphId(null);
    setActiveThreadGraphs([]);
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
  }, [selectThread]);

  const createNewThread = async (targetId?: number) => {
    let createdThread: ThreadSummary | null = null;
    try {
      createdThread = await assistantApi.createThread('New chat');
      if (targetId !== undefined) await assistantApi.bindTarget(createdThread.id, targetId);
      await loadThreads();
      handleSelectSidebarThread({ ...createdThread, bound_target_id: targetId ?? null });
    } catch (err) {
      if (createdThread && targetId !== undefined) {
        try { await assistantApi.deleteThread(createdThread.id); } catch (deleteError) { console.error('Failed to remove unbound conversation after bind failure', deleteError); }
      }
      setThreadsError(`Failed to create conversation: ${err instanceof Error ? err.message : 'Unknown error'}`);
      console.error('Failed to create thread', err);
    }
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
      }
      await loadThreads();
    } catch (err) { console.error('Failed to delete thread', err); }
  };

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
  // loadThreads/selectThread are stable in behavior but recreated with the page state;
  // including them would restart an active stream on every thread-list update.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inputVal, selectedThreadId, selectedThreadData, activeAssistantId, streamingText, clearDraft]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    if (e.currentTarget.scrollTop === 0 && displayLimit < filteredMessages.length) {
      const container = e.currentTarget;
      const prevScrollHeight = container.scrollHeight;
      setDisplayLimit(prev => prev + 50);
      requestAnimationFrame(() => { if (container) container.scrollTop = container.scrollHeight - prevScrollHeight; });
    }
  };

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

  const resetWorkbenchFilters = useCallback(() => {
    setTargetSearchId('');
    setMsgFilter(DEFAULT_MSG_FILTER);
  }, [setMsgFilter]);

  return (
    <div className={`c2-workspace c2-workspace--ai ai-workbench-shell ${sidebarOpen ? '' : 'is-conversations-collapsed'} ${showTree ? '' : 'is-inspector-collapsed'}`}>
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        targetSearchId={targetSearchId}
        onTargetSearchChange={setTargetSearchId}
        showInternal={showInternal}
        onShowInternalChange={(next) => { setShowInternal(next); localStorage.setItem('aiCenter_showInternal', String(next)); }}
        msgFilter={msgFilter}
        onMessageFilterChange={setMsgFilter}
        onResetFilters={resetWorkbenchFilters}
        threadsLoading={threadsLoading}
        threadsError={threadsError}
        threads={allThreads}
        selectedThreadId={selectedThreadId}
        onSelectThread={handleSelectSidebarThread}
        onDeleteThread={handleDeleteThread}
        onCreateThread={createNewThread}
        overviews={overviews}
        overviewsLoading={overviewsLoading}
        boundTargetId={boundTargetId}
        onNavigate={navigate}
        onUnbindTarget={async () => {
          if (!selectedThreadId) return;
          await assistantApi.unbindTarget(selectedThreadId);
          setBoundTargetId(null);
          setSelectedThreadData((thread) => thread ? { ...thread, bound_target_id: null } : null);
          await loadThreads();
        }}
      />

      {/* ─── Main chat ───────────────────────────────────────────────── */}
      <main className="ai-chat-pane">
        {!sidebarOpen && (
          <button className="ai-open-sidebar" onClick={() => setSidebarOpen(true)} title="Open conversations" aria-label="Open conversations">☰</button>
        )}

        <div className="ai-chat-pane__inner">
          {selectedThreadId ? (
            <>
              <ChatHeader
                label={chatTargetLabel}
                graphCount={activeThreadGraphs.length}
                showEvents={showEventsPanel}
                showTree={showTreePanel}
                treeAgentCount={agentTree.length}
                hasTree={!!rootThreadId}
                selectedGraphId={selectedGraphId}
                onOpenGraph={openGraph}
                onToggleEvents={() => setShowEventsPanel(v => !v)}
                onToggleTree={() => setShowTreePanel(v => !v)}
                agentTriggerRef={agentTriggerRef}
                eventsTriggerRef={eventsTriggerRef}
              />

              {/* Upper area: messages + input */}
              <div className="ai-chat-content">
                <div className="ai-message-scroll" onScroll={handleScroll}>
                  {filteredMessages.length === 0 && !streamingText && (
                    <div className="ai-chat-empty">
                      <div className="ai-chat-empty__mark">AI</div>
                      <div className="ai-chat-empty__title">
                        {messages.length === 0 ? 'Start a conversation' : 'No messages match current filters'}
                      </div>
                      <p>{messages.length === 0 ? 'Ask the active agent to inspect a target, explain evidence, or start a workflow.' : 'Open Filter to adjust what is visible in this thread.'}</p>
                    </div>
                  )}
                  {displayLimit < filteredMessages.length && (
                    <div className="ai-loading-history">Loading older messages...</div>
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
                            onViewGraph={openGraph}
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
                        "ai-message-row",
                        msg.role === 'user' ? 'justify-end' : 'justify-start',
                      )}>
                        <div className={cn(
                          "ai-message-card",
                          msg.role === 'user'
                            ? "ai-message-card--user"
                            : "ai-message-card--assistant"
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
                    <div className="ai-message-row justify-start">
                      <div className="ai-message-card ai-message-card--assistant">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamingText}</ReactMarkdown>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                <div className="ai-composer-wrap">
                  <div className="ai-composer">
                    <textarea
                      className="ai-composer__input"
                      placeholder="Message the active agent…"
                      value={inputVal}
                      onChange={e => setInputVal(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                      disabled={isSending}
                      rows={3}
                    />
                    <button
                      className="ai-send-button"
                      onClick={handleSend}
                      disabled={isSending || !inputVal.trim() || !selectedThreadId}
                      title={isSending ? 'Sending...' : 'Send message (Enter)'}
                    >
                      {isSending ? 'Sending…' : 'Send'}
                    </button>
                  </div>
                  <div className="ai-composer__hint"><span>↵ Send</span><span>⇧ ↵ New line</span><span className="ai-composer__hint-status"><span className="ai-status-dot" /> Agent ready</span></div>
                </div>
              </div>

              <ThreadEventsPanel
                open={showEventsPanel}
                threadId={selectedThreadId}
                onOpenChange={setShowEventsPanel}
                triggerRef={eventsTriggerRef}
              />
            </>
          ) : (
            <div className="ai-workbench-empty">
              <div className="ai-chat-empty__mark">AI</div>
              <div className="ai-chat-empty__title">
                {allThreads.length === 0 ? 'Create a new conversation to get started' : 'Select a conversation'}
              </div>
              <p>{allThreads.length === 0 ? 'Your agent workspace will appear here once a conversation is active.' : 'Choose a thread from the conversation index to inspect its messages and execution context.'}</p>
              {allThreads.length === 0 && <button className="ai-primary-button" type="button" onClick={() => createNewThread()}> <MessageSquarePlus size={15} /> New Chat</button>}
            </div>
          )}
        </div>
      </main>

      <AgentPanel
        showTree={showTree}
        onClose={() => setShowTreePanel(false)}
        triggerRef={agentTriggerRef}
        agentPanelTab={agentPanelTab}
        onTabChange={setAgentPanelTab}
        agentTree={agentTree}
        rootNode={rootNode}
        activeNodeThreadId={activeNodeThreadId}
        onSelectTreeNode={handleSelectTreeNode}
        dispatchTree={dispatchTree}
        boundTargetId={boundTargetId}
        onOpenGraph={openGraph}
        topology={topology}
        selectedTopoNode={selectedTopoNode}
        onSelectTopoNode={setSelectedTopoNode}
      />
    </div>
  );
};

export default AICenterPage;
