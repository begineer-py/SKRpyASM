import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { assistantApi } from '../../services/assistantApi';
import { useHasuraSubscription } from '../../hooks/useHasuraSubscription';
import StepLogViewer from '../../components/StepLogViewer';
import { GET_AGENT_TREE_SUBSCRIPTION } from '../../queries';
import './AICenter.css';

// ── Constants ─────────────────────────────────────────────────────────────

const NOOP_SUB = `subscription { __typename }`;

// ── Status badge helpers ──────────────────────────────────────────────────

const STATUS_CLASS: Record<string, string> = {
  EXECUTING:         'tree-badge--executing',
  PLANNING:          'tree-badge--planning',
  COMPLETED:         'tree-badge--completed',
  FAILED:            'tree-badge--failed',
  NEEDS_GUIDANCE:    'tree-badge--needs-guidance',
  WAITING_FOR_ASYNC: 'tree-badge--waiting',
};

const riskClass = (score: number) =>
  score > 66 ? 'high' : score > 33 ? 'medium' : 'low';

const STEP_STATUS_COLOR: Record<string, string> = {
  RUNNING:           '#4ade80',
  COMPLETED:         '#60a5fa',
  FAILED:            '#f87171',
  PENDING:           '#fbbf24',
  WAITING_FOR_ASYNC: '#a78bfa',
};

// ── Types ─────────────────────────────────────────────────────────────────

interface AgentStep {
  id: number;
  status: string;
  operation_type: string | null;
  created_at: string;
  completed_at: string | null;
}

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
  steps: AgentStep[];
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
  const icon = node.assistant_id === 'hacker_assistant_agent' ? '🧑‍💻' : '🤖';
  const children = allNodes.filter(n => n.parent_thread_id === node.thread_id);

  const runningStep = node.steps.find(s => s.status === 'RUNNING');

  return (
    <div className="tree-node-group">
      <div
        className={`tree-node ${isActive ? 'tree-node--active' : ''}`}
        style={{ paddingLeft: `${8 + depth * 20}px` }}
        onClick={() => onSelect(node)}
        title={node.thread_name}
      >
        {depth > 0 && <span className="tree-connector" />}
        <div className="tree-node-label">
          <span className="tree-node-icon">{icon}</span>
          <span className="tree-node-name">
            {node.target_name && depth > 0 ? node.target_name : node.thread_name}
          </span>
          {runningStep && <span className="tree-running-dot" title="Running" />}
        </div>
        <div className="tree-node-meta">
          {node.overview_status && (
            <span className={`tree-badge ${STATUS_CLASS[node.overview_status] || 'tree-badge--default'}`}>
              {node.overview_status.replace(/_/g, ' ')}
            </span>
          )}
          {node.overview_risk_score !== null && (
            <span className={`tree-badge tree-badge--risk ${riskClass(node.overview_risk_score)}`}>
              ⚡{node.overview_risk_score}
            </span>
          )}
          {node.steps.length > 0 && (
            <span className="tree-badge tree-badge--steps">
              {node.steps.length} step{node.steps.length > 1 ? 's' : ''}
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

function toSteps(raw: any[]): AgentStep[] {
  return (raw || []).map(s => ({
    id: Number(s.id),
    status: s.status,
    operation_type: s.operation_type || null,
    created_at: s.created_at,
    completed_at: s.completed_at || null,
  }));
}

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
    steps: toSteps(ov.core_steps),
  });
  // Recurse into this thread's own overviews (grandchildren)
  for (const childOv of t.core_overviews ?? []) {
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
    steps: [],
  });
  seen.add(Number(root.id));

  // Source A: root thread's overviews → their owning sub-threads (+ grandchildren via recursion)
  for (const ov of root.core_overviews ?? []) {
    const t = ov.aiAssistantThreadByThreadId;
    if (t) _ingestThreadFromOv(t, ov, Number(rootThreadId), nodes, seen);
  }

  // Source B: direct name-pattern match (all subagent_*_for_thread_X threads)
  for (const t of rawData.directChildren ?? []) {
    if (seen.has(Number(t.id))) {
      // Already added via Source A, but may have more overviews → recurse its children
      for (const childOv of t.core_overviews ?? []) {
        const childT = childOv.aiAssistantThreadByThreadId;
        if (childT) _ingestThreadFromOv(childT, childOv, Number(t.id), nodes, seen);
      }
      continue;
    }
    seen.add(Number(t.id));
    const latestOv = t.coreOverviewsByThreadId?.[0];
    nodes.push({
      thread_id: Number(t.id),
      thread_name: t.name,
      assistant_id: t.assistant_id,
      is_hidden: t.is_hidden,
      bound_target_id: t.bound_target_id,
      parent_thread_id: Number(rootThreadId),
      overview_id: latestOv ? Number(latestOv.id) : null,
      overview_status: latestOv?.status ?? null,
      overview_risk_score: latestOv?.risk_score ?? null,
      target_name: latestOv?.core_target?.name ?? null,
      created_at: t.created_at,
      steps: toSteps(latestOv?.core_steps),
    });
    // Recurse into this direct child's own sub-threads
    for (const childOv of t.core_overviews ?? []) {
      const childT = childOv.aiAssistantThreadByThreadId;
      if (childT) _ingestThreadFromOv(childT, childOv, Number(t.id), nodes, seen);
    }
  }

  // Source C: core_overview where parent_thread_id = rootThreadId (FK fallback)
  for (const ov of rawData.childOverviews ?? []) {
    const t = ov.aiAssistantThreadByThreadId;
    if (t) {
      _ingestThreadFromOv(t, ov, Number(rootThreadId), nodes, seen);
    } else if (ov.thread_id && !seen.has(Number(ov.thread_id))) {
      // Overview exists with thread_id but the thread wasn't included in GQL
      seen.add(Number(ov.thread_id));
      nodes.push({
        thread_id: Number(ov.thread_id),
        thread_name: `Thread ${ov.thread_id}`,
        assistant_id: 'automation_agent',
        is_hidden: true,
        bound_target_id: null,
        parent_thread_id: Number(rootThreadId),
        overview_id: Number(ov.id),
        overview_status: ov.status,
        overview_risk_score: ov.risk_score,
        target_name: ov.core_target?.name ?? null,
        created_at: '',
        steps: toSteps(ov.core_steps),
      });
    }
  }

  return nodes;
}

// ── Main page ─────────────────────────────────────────────────────────────

const AICenterPage: React.FC = () => {
  // Chat state
  const [allThreads, setAllThreads] = useState<any[]>([]);
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const [selectedThreadData, setSelectedThreadData] = useState<any>(null);
  const [activeAssistantId, setActiveAssistantId] = useState<string>('hacker_assistant_agent');
  const [messages, setMessages] = useState<any[]>([]);
  const [inputVal, setInputVal] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [streamingText, setStreamingText] = useState<string | null>(null);
  const [displayLimit, setDisplayLimit] = useState(50);

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

  // Tool-call logs panel state
  const [selectedStepId, setSelectedStepId] = useState<number | null>(null);
  const [activeNodeSteps, setActiveNodeSteps] = useState<AgentStep[]>([]);
  const [showLogsPanel, setShowLogsPanel] = useState(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const cleanupStreamRef = useRef<(() => void) | null>(null);

  // ── GQL subscription for agent tree ──────────────────────────────────

  const treeSubVars = useMemo(() => {
    if (!rootThreadId) return undefined;
    return {
      rootThreadId: parseInt(rootThreadId),
      // _ilike prefix match catches all sub-agent naming variants for this root thread
      childPattern: `subagent_%for_thread_${rootThreadId}%`,
    };
  }, [rootThreadId]);

  const { data: treeRawData, isConnected: treeConnected } = useHasuraSubscription(
    rootThreadId ? GET_AGENT_TREE_SUBSCRIPTION : NOOP_SUB,
    treeSubVars
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

  // Auto-follow RUNNING step when tree updates
  useEffect(() => {
    if (!activeNodeThreadId) return;
    const activeNode = agentTree.find(n => String(n.thread_id) === activeNodeThreadId);
    if (!activeNode || activeNode.steps.length === 0) return;

    setActiveNodeSteps(activeNode.steps);

    // Follow new RUNNING step automatically
    const runningStep = activeNode.steps.find(s => s.status === 'RUNNING');
    if (runningStep && runningStep.id !== selectedStepId) {
      setSelectedStepId(runningStep.id);
      setShowLogsPanel(true);
    }
  }, [agentTree, activeNodeThreadId]);

  // ── Scroll helpers ────────────────────────────────────────────────────

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(() => { scrollToBottom(); }, [messages, streamingText]);

  // ── Load threads ──────────────────────────────────────────────────────

  useEffect(() => { loadThreads(); }, [targetSearchId, showInternal]);
  useEffect(() => {
    if (selectedThreadId) loadMessagesForThread(selectedThreadId);
  }, [selectedThreadId]);

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
                t.assistant_id !== 'automation_agent' &&
                !t.name?.startsWith('subagent_') &&
                !t.name?.startsWith('ephemeral_') &&
                !t.name?.includes('Analysis Batch')
            )
            .sort((a, b) => Number(b.id) - Number(a.id));

      setAllThreads(filtered);

      if (filtered.length > 0 && !selectedThreadId) {
        handleSelectSidebarThread(filtered[0]);
      } else if (filtered.length === 0 && selectedThreadId) {
        setSelectedThreadId(null);
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
      const msgArray: any[] = await assistantApi.getMessages(threadId);
      const parsed = msgArray.map(m => {
        let textContent = '';
        const role = m.type === 'human' ? 'user' : 'assistant';
        if (typeof m.content === 'string') textContent = m.content;
        else if (Array.isArray(m.content))
          textContent = m.content.map((c: any) => c.text || JSON.stringify(c)).join('\n');
        if (!textContent.trim()) {
          if (m.tool_calls?.length > 0)
            textContent = `[Tool Call: ${m.tool_calls.map((tc: any) => tc.name).join(', ')}]`;
          else if (m.type === 'tool') textContent = '[Tool Execution Completed]';
          else textContent = '[Empty Message]';
        }
        return { id: m.id, role, textContent };
      });
      setDisplayLimit(50);
      setMessages(parsed);
    } catch (err) {
      console.error('Failed to load messages', err);
      setMessages([]);
    }
  };

  // ── Thread / node selection ───────────────────────────────────────────

  const handleSelectSidebarThread = (thread: any) => {
    setSelectedThreadId(String(thread.id));
    setSelectedThreadData(thread);
    setActiveAssistantId(thread.assistant_id || 'hacker_assistant_agent');
    setActiveNodeThreadId(String(thread.id));
    setBoundTargetId(thread.bound_target_id ?? null);
    setRootThreadId(thread.assistant_id === 'hacker_assistant_agent' ? String(thread.id) : null);
    // Root thread has no steps to monitor
    setShowLogsPanel(false);
    setSelectedStepId(null);
    setActiveNodeSteps([]);
  };

  const handleSelectTreeNode = useCallback((node: TreeNode) => {
    setSelectedThreadId(String(node.thread_id));
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

    // Logs panel: only for automation_agent nodes with steps
    const steps = node.steps || [];
    setActiveNodeSteps(steps);
    if (steps.length > 0 && node.assistant_id !== 'hacker_assistant_agent') {
      const runningStep = steps.find(s => s.status === 'RUNNING') ?? steps[0];
      setSelectedStepId(runningStep.id);
      setShowLogsPanel(true);
    } else {
      setSelectedStepId(null);
      setShowLogsPanel(false);
    }
  }, []);

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
        setSelectedThreadId(null);
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
    if (!selectedThreadData) { alert('This conversation was deleted'); setSelectedThreadId(null); return; }

    const userMsg = inputVal;
    setInputVal('');
    setIsSending(true);
    setStreamingText('');
    setMessages(prev => [...prev, { role: 'user', textContent: userMsg }]);
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
        setMessages(prev => [...prev, { role: 'assistant', textContent: `⚠️ Error: ${errMsg}`, isError: true }]);
        await loadMessagesForThread(selectedThreadId);
      },
      () => { /* onStats noop */ }
    );
    cleanupStreamRef.current = cleanup;
  }, [inputVal, selectedThreadId, selectedThreadData, activeAssistantId, streamingText]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    if (e.currentTarget.scrollTop === 0 && displayLimit < messages.length) {
      const container = e.currentTarget;
      const prevScrollHeight = container.scrollHeight;
      setDisplayLimit(prev => prev + 50);
      requestAnimationFrame(() => { if (container) container.scrollTop = container.scrollHeight - prevScrollHeight; });
    }
  };

  // ── Derived ───────────────────────────────────────────────────────────

  const displayedMessages = messages.slice(-displayLimit);
  const rootNode = agentTree.find(n => n.parent_thread_id === null) ?? null;
  const showTree = showTreePanel && rootThreadId !== null;

  const activeNodeData = agentTree.find(n => String(n.thread_id) === activeNodeThreadId);
  const chatTargetLabel = activeNodeData
    ? `🤖 ${activeNodeData.assistant_id}${activeNodeData.target_name ? ` — ${activeNodeData.target_name}` : ''}`
    : selectedThreadData
      ? `🧑‍💻 ${selectedThreadData.name || 'Hacker AI'}`
      : null;

  const selectedStep = activeNodeSteps.find(s => s.id === selectedStepId);

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
            placeholder="🔍 Filter by Target ID..."
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
            {showInternal ? '👁 顯示系統 Thread' : '👤 僅使用者對話'}
          </button>
        </div>

        {threadsLoading && <div className="sidebar-loading"><span className="pulse">●</span> Loading...</div>}
        {threadsError && <div className="sidebar-error">⚠️ {threadsError}</div>}

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
                  🗑️
                </button>
              )}
            </div>
          ))}
        </div>

        {boundTargetId && (
          <div className="sidebar-footer">
            <div className="target-badge">
              <span>🎯 Target: {boundTargetId}</span>
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
                  {activeNodeSteps.length > 0 && (
                    <button
                      className={`tool-log-toggle-btn ${showLogsPanel ? 'active' : ''}`}
                      onClick={() => setShowLogsPanel(v => !v)}
                      title="Toggle tool call logs"
                    >
                      🔧 {activeNodeSteps.length} step{activeNodeSteps.length > 1 ? 's' : ''}
                    </button>
                  )}
                  {rootThreadId && (
                    <button
                      className={`tree-toggle-btn ${showTreePanel ? 'active' : ''}`}
                      onClick={() => setShowTreePanel(v => !v)}
                      title="Toggle Agent Tree"
                    >
                      🌲 {agentTree.length > 1 ? `${agentTree.length - 1} agent${agentTree.length > 2 ? 's' : ''}` : 'Tree'}
                    </button>
                  )}
                </div>
              </div>

              {/* Upper area: messages + input */}
              <div className="chat-upper">
                <div className="messages-area" onScroll={handleScroll}>
                  {messages.length === 0 && !streamingText && (
                    <div className="empty-chat">
                      <div className="empty-icon">💬</div>
                      <div className="empty-text">Start a conversation</div>
                    </div>
                  )}
                  {displayLimit < messages.length && (
                    <div className="loading-older">Loading older messages...</div>
                  )}
                  {displayedMessages.map((msg: any) => (
                    <div key={msg.id || Math.random()} className={`message message-${msg.role}`}>
                      <div className="message-content">
                        {msg.role === 'user' ? (
                          <div className="user-text">{msg.textContent}</div>
                        ) : (
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.textContent}</ReactMarkdown>
                        )}
                      </div>
                    </div>
                  ))}
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

              {/* ── Tool call logs panel ─────────────────────────────── */}
              {showLogsPanel && (
                <div className="logs-panel">
                  <div className="logs-panel-header">
                    <div className="logs-panel-title">
                      <span>🔧 TOOL CALLS</span>
                      {selectedStep && (
                        <span
                          className="logs-step-status"
                          style={{ color: STEP_STATUS_COLOR[selectedStep.status] || '#94a3b8' }}
                        >
                          {selectedStep.status}
                        </span>
                      )}
                    </div>

                    <div className="logs-panel-controls">
                      {/* Step picker */}
                      {activeNodeSteps.length > 1 && (
                        <select
                          className="step-picker"
                          value={selectedStepId ?? ''}
                          onChange={e => setSelectedStepId(Number(e.target.value))}
                        >
                          {activeNodeSteps.map(s => (
                            <option key={s.id} value={s.id}>
                              #{s.id} [{s.status}]{s.operation_type ? ` · ${s.operation_type}` : ''}
                            </option>
                          ))}
                        </select>
                      )}
                      <button
                        className="logs-close-btn"
                        onClick={() => setShowLogsPanel(false)}
                        title="Close logs panel"
                      >✕</button>
                    </div>
                  </div>

                  <div className="logs-panel-body">
                    {selectedStepId ? (
                      <StepLogViewer stepId={selectedStepId} compact autoScroll />
                    ) : (
                      <div className="logs-empty">No step selected</div>
                    )}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="no-thread">
              <div className="no-thread-icon">🤖</div>
              <div className="no-thread-text">
                {allThreads.length === 0 ? 'Create a new conversation to get started' : 'Select a conversation'}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* ─── Agent tree panel ────────────────────────────────────────── */}
      {showTree && (
        <aside className="agent-tree-panel">
          <div className="tree-panel-header">
            <h4>AGENT TREE</h4>
            <div className="tree-panel-actions">
              <span
                className={`tree-live-dot ${treeConnected ? 'connected' : 'disconnected'}`}
                title={treeConnected ? 'Live — auto-updating' : 'Disconnected'}
              />
              <button className="tree-action-btn" onClick={() => setShowTreePanel(false)} title="Close">✕</button>
            </div>
          </div>

          <div className="tree-body">
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
          </div>
        </aside>
      )}
    </div>
  );
};

export default AICenterPage;
