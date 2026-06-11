import { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import ExecutionTimelineViewer from '../../components/ExecutionTimelineViewer';
import { executionApi } from '../../services/executionApi';
import type { ExecutionGraph, ExecutionGraphDetail, ExecutionNode } from '../../services/executionApi';
import './ExecutionMonitor.css';

const STATUS_OPTIONS = ['RUNNING', 'WAITING', 'SUCCEEDED', 'FAILED', 'CANCELLED', 'BLOCKED'];

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

export default function ExecutionMonitorPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialGraphId = Number(searchParams.get('graph')) || null;

  const [graphs, setGraphs] = useState<ExecutionGraph[]>([]);
  const [selectedGraphId, setSelectedGraphId] = useState<number | null>(initialGraphId);
  const [selectedGraph, setSelectedGraph] = useState<ExecutionGraphDetail | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [threadFilter, setThreadFilter] = useState<string>('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadGraphs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: { status?: string; thread_id?: number; limit: number } = { limit: 100 };
      if (statusFilter) params.status = statusFilter;
      if (threadFilter.trim()) params.thread_id = Number(threadFilter.trim());
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
  }, [selectedGraphId, statusFilter, threadFilter]);

  useEffect(() => {
    void loadGraphs();
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
    const q = search.trim().toLowerCase();
    if (!q) return graphs;
    return graphs.filter((graph) => [
      graph.title,
      graph.assistant_id,
      graph.status,
      String(graph.id),
      String(graph.thread_id || ''),
    ].some((value) => String(value || '').toLowerCase().includes(q)));
  }, [graphs, search]);

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
    <div className="execution-monitor-page" style={{ minHeight: '100vh', background: '#070b12', color: '#dbeafe' }}>
      <div style={{ padding: '24px', borderBottom: '1px solid rgba(148, 163, 184, 0.22)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: 12, letterSpacing: '0.18em', color: '#38bdf8', textTransform: 'uppercase' }}>Execution Graph Operations</div>
            <h1 style={{ margin: '6px 0 0', fontSize: 34, lineHeight: 1, color: '#f8fafc' }}>Runtime Flight Deck</h1>
            <p style={{ margin: '10px 0 0', color: '#94a3b8', maxWidth: 720 }}>
              LangGraph-native execution monitoring. Nodes are the execution unit; events stream real-time status; artifacts carry notes, HTTP traces, skill runs, and long content.
            </p>
          </div>
          <button className="filter-btn active" onClick={() => void loadGraphs()} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(120px, 1fr))', gap: 12, marginTop: 20 }}>
          <Stat label="Running" value={stats.running} tone="#22c55e" />
          <Stat label="Waiting" value={stats.waiting} tone="#a78bfa" />
          <Stat label="Succeeded" value={stats.succeeded} tone="#38bdf8" />
          <Stat label="Failed" value={stats.failed} tone="#f87171" />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '360px minmax(320px, 1fr) minmax(420px, 1.1fr)', minHeight: 'calc(100vh - 190px)' }}>
        <aside style={{ borderRight: '1px solid rgba(148, 163, 184, 0.18)', padding: 16, overflow: 'auto' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 14 }}>
            <input className="search-input" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search graph, assistant, thread..." />
            <input className="search-input" value={threadFilter} onChange={(event) => setThreadFilter(event.target.value)} placeholder="Thread ID filter" />
            <select className="filter-select" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="">All statuses</option>
              {STATUS_OPTIONS.map((status) => <option key={status} value={status}>{status}</option>)}
            </select>
          </div>

          {error && <div style={{ color: '#f87171', marginBottom: 12 }}>{error}</div>}
          {filteredGraphs.length === 0 ? (
            <div style={{ color: '#64748b', padding: 16 }}>No execution graphs found.</div>
          ) : filteredGraphs.map((graph) => (
            <button
              key={graph.id}
              type="button"
              onClick={() => { setSelectedGraphId(graph.id); setSelectedNodeId(null); }}
              style={{
                width: '100%',
                textAlign: 'left',
                padding: 14,
                marginBottom: 10,
                borderRadius: 14,
                border: selectedGraphId === graph.id ? '1px solid #38bdf8' : '1px solid rgba(148, 163, 184, 0.18)',
                background: selectedGraphId === graph.id ? 'rgba(56, 189, 248, 0.12)' : 'rgba(15, 23, 42, 0.66)',
                color: '#e2e8f0',
                cursor: 'pointer',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                <strong>Graph #{graph.id}</strong>
                <span className={`status-badge ${statusClass(graph.status)}`}>{graph.status}</span>
              </div>
              <div style={{ marginTop: 8, color: '#cbd5e1', fontSize: 13 }}>{graph.title || graph.assistant_id}</div>
              <div style={{ marginTop: 8, display: 'flex', gap: 10, color: '#64748b', fontSize: 12 }}>
                <span>thread {graph.thread_id ?? '-'}</span>
                <span>{formatDuration(graph.started_at, graph.completed_at)}</span>
              </div>
            </button>
          ))}
        </aside>

        <main style={{ borderRight: '1px solid rgba(148, 163, 184, 0.18)', padding: 16, overflow: 'auto' }}>
          <section style={{ marginBottom: 16 }}>
            <h2 style={{ margin: 0, color: '#f8fafc' }}>{selectedGraph ? `Graph #${selectedGraph.id}` : 'No graph selected'}</h2>
            {selectedGraph && (
              <div style={{ marginTop: 8, color: '#94a3b8', fontSize: 13 }}>
                {selectedGraph.assistant_id} · thread {selectedGraph.thread_id ?? '-'} · started {formatTime(selectedGraph.started_at)}
              </div>
            )}
          </section>

          <section style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {(selectedGraph?.nodes ?? []).map((node) => (
              <button
                key={node.id}
                type="button"
                onClick={() => setSelectedNodeId(node.id)}
                style={{
                  textAlign: 'left',
                  padding: 14,
                  borderRadius: 12,
                  border: selectedNodeId === node.id ? '1px solid #22c55e' : '1px solid rgba(148, 163, 184, 0.16)',
                  background: selectedNodeId === node.id ? 'rgba(34, 197, 94, 0.10)' : 'rgba(2, 6, 23, 0.72)',
                  color: '#e2e8f0',
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                  <strong>#{node.sequence} {node.name}</strong>
                  <span className={`status-badge ${statusClass(node.status)}`}>{node.status}</span>
                </div>
                <div style={{ marginTop: 8, color: '#94a3b8', fontSize: 12 }}>
                  {node.kind} · id {node.id} · task {node.external_task_id || '-'} · {formatDuration(node.started_at, node.completed_at)}
                </div>
                {node.wait_reason && <div style={{ marginTop: 6, color: '#c084fc', fontSize: 12 }}>wait: {node.wait_reason}</div>}
              </button>
            ))}
            {selectedGraph && selectedGraph.nodes.length === 0 && <div style={{ color: '#64748b' }}>No nodes recorded yet.</div>}
          </section>

          {selectedNode && (
            <section style={{ marginTop: 18, padding: 14, borderRadius: 12, background: 'rgba(15, 23, 42, 0.72)', border: '1px solid rgba(148, 163, 184, 0.16)' }}>
              <h3 style={{ marginTop: 0 }}>Selected Node</h3>
              <pre style={{ whiteSpace: 'pre-wrap', color: '#cbd5e1', fontSize: 12 }}>{JSON.stringify({ input: selectedNode.input, output: selectedNode.output, error: selectedNode.error }, null, 2)}</pre>
            </section>
          )}
        </main>

        <aside style={{ overflow: 'hidden', minHeight: 0 }}>
          <ExecutionTimelineViewer graphId={selectedGraphId} autoScroll />
        </aside>
      </div>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div style={{ padding: 14, borderRadius: 16, background: 'rgba(15, 23, 42, 0.72)', border: `1px solid ${tone}44` }}>
      <div style={{ color: '#94a3b8', fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.12em' }}>{label}</div>
      <div style={{ color: tone, fontSize: 28, fontWeight: 800 }}>{value}</div>
    </div>
  );
}
