import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useSearchParams } from 'react-router-dom';
import ExecutionTimelineViewer from '../../../components/ExecutionTimelineViewer';
import { executionApi, type ExecutionGraph, type ExecutionGraphDetail, type ExecutionNode } from '../services/aiApi';
import { cn } from '@/lib/utils';

const STATUS_OPTIONS = ['RUNNING', 'WAITING', 'SUCCEEDED', 'FAILED', 'CANCELLED', 'BLOCKED'];
const ASSISTANT_OPTIONS = ['automation_agent', 'recon_agent', 'post_exploit_agent', 'reporting_agent', 'hacker_assistant_agent'];

const STATUS_CLASS: Record<string, string> = {
  RUNNING: 'running',
  WAITING: 'waiting',
  SUCCEEDED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'ended',
  BLOCKED: 'waiting',
};

function statusClass(status: string): string {
  return STATUS_CLASS[status] || 'pending';
}

function formatTime(value?: string | null): string {
  if (!value) return '-';
  return new Date(value).toLocaleString();
}

function formatDuration(start?: string | null, end?: string | null): string {
  if (!start) return '-';
  const endDate = end ? new Date(end) : new Date();
  const ms = Math.max(0, endDate.getTime() - new Date(start).getTime());
  const seconds = Math.round(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  return `${Math.round(minutes / 60)}h`;
}

const searchInputCls = "w-full px-3 py-2.5 bg-bg-surface border border-border-normal rounded-md text-text-primary text-sm font-mono outline-none transition-all duration-200 focus:border-cyan focus:shadow-[0_0_8px_rgba(0,240,255,0.2)] placeholder:text-text-muted";
const filterSelectCls = "w-full px-3 py-2.5 bg-bg-surface border border-border-normal rounded-md text-text-primary text-sm font-mono outline-none cursor-pointer";
const statusBadgeCls = "inline-block px-2 py-0.5 bg-black/30 rounded-sm font-mono text-[0.65rem] font-semibold tracking-wide uppercase border border-current/30";

export default function ExecutionMonitorPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialGraphId = Number(searchParams.get('graph')) || null;

  const [graphs, setGraphs] = useState<ExecutionGraph[]>([]);
  const [selectedGraphId, setSelectedGraphId] = useState<number | null>(initialGraphId);
  const [selectedGraph, setSelectedGraph] = useState<ExecutionGraphDetail | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [assistantFilter, setAssistantFilter] = useState<string>('');
  const [threadFilter, setThreadFilter] = useState<string>('');
  const [targetFilter, setTargetFilter] = useState<string>('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadGraphs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: { status?: string; thread_id?: number; target_id?: number; limit: number } = { limit: 100 };
      if (statusFilter) params.status = statusFilter;
      if (threadFilter.trim()) params.thread_id = Number(threadFilter.trim());
      if (targetFilter.trim()) params.target_id = Number(targetFilter.trim());
      const nextGraphs = await executionApi.listGraphs(params);
      setGraphs(nextGraphs);
      if (!selectedGraphId && nextGraphs.length > 0) {
        setSelectedGraphId(nextGraphs[0].id);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load execution graphs');
    } finally {
      setLoading(false);
    }
  }, [selectedGraphId, statusFilter, threadFilter, targetFilter]);

  useEffect(() => {
    void loadGraphs();
  }, [loadGraphs]);

  const location = useLocation();
  const lastLoadRef = useRef<number>(0);
  useEffect(() => {
    const now = Date.now();
    if (now - lastLoadRef.current > 1000) {
      lastLoadRef.current = now;
      void loadGraphs();
    }
  }, [location.pathname, location.search, loadGraphs]);

  useEffect(() => {
    const onFocus = () => {
      const now = Date.now();
      if (now - lastLoadRef.current > 2000) {
        lastLoadRef.current = now;
        void loadGraphs();
      }
    };
    window.addEventListener('focus', onFocus);
    const onVisibility = () => {
      if (document.visibilityState === 'visible') onFocus();
    };
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      window.removeEventListener('focus', onFocus);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [loadGraphs]);

  useEffect(() => {
    let cancelled = false;
    if (!selectedGraphId) {
      setSelectedGraph(null);
      setSelectedNodeId(null);
      return;
    }

    setSearchParams((current) => {
      const next = new URLSearchParams(current);
      next.set('graph', String(selectedGraphId));
      next.delete('node');
      return next;
    });

    void executionApi.getGraph(selectedGraphId)
      .then((graph) => {
        if (cancelled) return;
        setSelectedGraph(graph);
        const running = graph.nodes.find((node) => node.status === 'RUNNING' || node.status === 'WAITING');
        setSelectedNodeId((current) => current ?? running?.id ?? graph.nodes[0]?.id ?? null);
      })
      .catch((err: any) => {
        if (!cancelled) setError(err?.message || 'Failed to load execution graph detail');
      });

    return () => {
      cancelled = true;
    };
  }, [selectedGraphId, setSearchParams]);

  const filteredGraphs = useMemo(() => {
    let result = graphs;
    if (assistantFilter) result = result.filter(g => g.assistant_id === assistantFilter);
    const q = search.trim().toLowerCase();
    if (!q) return result;
    return result.filter((graph) => [
      graph.title,
      graph.assistant_id,
      graph.status,
      String(graph.id),
      String(graph.thread_id || ''),
    ].some((value) => String(value || '').toLowerCase().includes(q)));
  }, [graphs, search, assistantFilter]);

  const selectedNode: ExecutionNode | null = useMemo(() => {
    if (!selectedGraph || !selectedNodeId) return null;
    return selectedGraph.nodes.find((node) => node.id === selectedNodeId) || null;
  }, [selectedGraph, selectedNodeId]);

  const stats = useMemo(() => {
    const counts = { running: 0, waiting: 0, succeeded: 0, failed: 0 };
    for (const graph of graphs) {
      if (graph.status === 'RUNNING') counts.running += 1;
      if (graph.status === 'WAITING') counts.waiting += 1;
      if (graph.status === 'SUCCEEDED') counts.succeeded += 1;
      if (graph.status === 'FAILED') counts.failed += 1;
    }
    return counts;
  }, [graphs]);

  return (
    <div className="min-h-screen bg-bg-base p-5 font-body text-[#dbeafe]">
      <div className="p-6 border-b border-border-subtle">
        <div className="flex justify-between gap-4 items-end flex-wrap">
          <div>
            <div className="text-xs tracking-[0.18em] text-cyan uppercase">Execution Graph Operations</div>
            <h1 className="mt-1.5 text-[34px] leading-none text-[#f8fafc]">Runtime Flight Deck</h1>
            <p className="mt-2.5 text-text-secondary max-w-[720px]">
              LangGraph-native execution monitoring. Nodes are the execution unit; events stream real-time status; artifacts carry notes, HTTP traces, skill runs, and long content.
            </p>
          </div>
          <button className="px-3 py-1.5 bg-[rgba(34,197,94,0.15)] border border-green-500 rounded text-xs text-green-500 font-mono cursor-pointer uppercase tracking-wide shadow-glow-green transition-all duration-200 hover:border-border-normal hover:text-text-primary disabled:opacity-40 disabled:cursor-not-allowed" onClick={() => void loadGraphs()} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        <div className="grid grid-cols-[repeat(4,minmax(120px,1fr))] gap-3 mt-5">
          <Stat label="Running" value={stats.running} tone="#22c55e" />
          <Stat label="Waiting" value={stats.waiting} tone="#a78bfa" />
          <Stat label="Succeeded" value={stats.succeeded} tone="#38bdf8" />
          <Stat label="Failed" value={stats.failed} tone="#f87171" />
        </div>
      </div>

      <div className="grid grid-cols-[360px_minmax(320px,1fr)_minmax(420px,1.1fr)] min-h-[calc(100vh-190px)]">
        <aside className="border-r border-border-subtle p-4 overflow-auto">
          <div className="flex flex-col gap-2.5 mb-3.5">
            <input className={searchInputCls} value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search graph, assistant, thread..." />
            <input className={searchInputCls} value={threadFilter} onChange={(event) => setThreadFilter(event.target.value)} placeholder="Thread ID filter" />
            <input className={searchInputCls} value={targetFilter} onChange={(event) => setTargetFilter(event.target.value)} placeholder="Target ID filter" />
            <select className={filterSelectCls} value={assistantFilter} onChange={(event) => setAssistantFilter(event.target.value)}>
              <option value="">All agents</option>
              {ASSISTANT_OPTIONS.map((a) => <option key={a} value={a}>{a}</option>)}
            </select>
            <select className={filterSelectCls} value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="">All statuses</option>
              {STATUS_OPTIONS.map((status) => <option key={status} value={status}>{status}</option>)}
            </select>
          </div>

          {error && <div className="text-red mb-3">{error}</div>}
          {filteredGraphs.length === 0 ? (
            <div className="text-text-muted p-4">No execution graphs found.</div>
          ) : filteredGraphs.map((graph) => (
            <button
              key={graph.id}
              type="button"
              onClick={() => { setSelectedGraphId(graph.id); setSelectedNodeId(null); }}
              className="w-full text-left p-3.5 mb-2.5 rounded-[14px] text-[#e2e8f0] cursor-pointer"
              style={{
                border: selectedGraphId === graph.id ? '1px solid #38bdf8' : '1px solid rgba(148, 163, 184, 0.18)',
                background: selectedGraphId === graph.id ? 'rgba(56, 189, 248, 0.12)' : 'rgba(15, 23, 42, 0.66)',
              }}
            >
              <div className="flex justify-between gap-2">
                <strong>Graph #{graph.id}</strong>
                <span className={cn(statusBadgeCls, statusClass(graph.status))}>{graph.status}</span>
              </div>
              <div className="mt-2 text-[#cbd5e1] text-[13px]">{graph.title || graph.assistant_id}</div>
              <div className="mt-2 flex gap-2.5 text-text-muted text-xs">
                <span>thread {graph.thread_id ?? '-'}</span>
                <span>{formatDuration(graph.started_at, graph.completed_at)}</span>
              </div>
            </button>
          ))}
        </aside>

        <main className="border-r border-border-subtle p-4 overflow-auto">
          <section className="mb-4">
            <h2 className="m-0 text-[#f8fafc]">{selectedGraph ? `Graph #${selectedGraph.id}` : 'No graph selected'}</h2>
            {selectedGraph && (
              <div className="mt-2 text-text-secondary text-[13px]">
                {selectedGraph.assistant_id} · thread {selectedGraph.thread_id ?? '-'} · started {formatTime(selectedGraph.started_at)}
              </div>
            )}
          </section>

          <section className="flex flex-col gap-2.5">
            {(selectedGraph?.nodes ?? []).map((node) => (
              <button
                key={node.id}
                type="button"
                onClick={() => setSelectedNodeId(node.id)}
                className="text-left p-3.5 rounded-xl text-[#e2e8f0] cursor-pointer"
                style={{
                  border: selectedNodeId === node.id ? '1px solid #22c55e' : '1px solid rgba(148, 163, 184, 0.16)',
                  background: selectedNodeId === node.id ? 'rgba(34, 197, 94, 0.10)' : 'rgba(2, 6, 23, 0.72)',
                }}
              >
                <div className="flex justify-between gap-2">
                  <strong>#{node.sequence} {node.name}</strong>
                  <span className={cn(statusBadgeCls, statusClass(node.status))}>{node.status}</span>
                </div>
                <div className="mt-2 text-text-secondary text-xs">
                  {node.kind} · id {node.id} · task {node.external_task_id || '-'} · {formatDuration(node.started_at, node.completed_at)}
                </div>
                {node.wait_reason && <div className="mt-1.5 text-purple text-xs">wait: {node.wait_reason}</div>}
              </button>
            ))}
            {selectedGraph && selectedGraph.nodes.length === 0 && <div className="text-text-muted">No nodes recorded yet.</div>}
          </section>

          {selectedNode && (
            <section className="mt-[18px] p-3.5 rounded-xl bg-[rgba(15,23,42,0.72)] border border-border-subtle">
              <h3 className="mt-0">Selected Node</h3>
              <pre className="whitespace-pre-wrap text-[#cbd5e1] text-xs">{JSON.stringify({ input: selectedNode.input, output: selectedNode.output, error: selectedNode.error }, null, 2)}</pre>
            </section>
          )}
        </main>

        <aside className="overflow-hidden min-h-0">
          <ExecutionTimelineViewer graphId={selectedGraphId} autoScroll />
        </aside>
      </div>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className="p-3.5 rounded-2xl bg-[rgba(15,23,42,0.72)]" style={{ border: `1px solid ${tone}44` }}>
      <div className="text-text-secondary text-xs uppercase tracking-[0.12em]">{label}</div>
      <div className="text-[28px] font-extrabold" style={{ color: tone }}>{value}</div>
    </div>
  );
}
