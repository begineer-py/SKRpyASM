import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Network,
  RefreshCw,
  Search,
  Settings,
} from 'lucide-react';
import { useLocation, useSearchParams } from 'react-router-dom';
import ExecutionTimelineViewer from '../../../components/ExecutionTimelineViewer';
import { executionApi, type ExecutionGraph, type ExecutionGraphDetail, type ExecutionNode } from '../services/aiApi';
import { cn } from '@/lib/utils';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

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

const searchInputCls = 'h-11 w-full rounded-xl border border-border-subtle bg-bg-surface px-3.5 text-base text-text-primary outline-none transition-colors placeholder:text-text-muted focus:border-cyan focus:shadow-[0_0_0_3px_rgba(6,182,212,0.12)]';
const filterSelectCls = 'h-11 w-full cursor-pointer rounded-xl border border-border-subtle bg-bg-surface px-3.5 text-base text-text-primary outline-none transition-colors focus:border-cyan focus:shadow-[0_0_0_3px_rgba(6,182,212,0.12)]';
const statusBadgeCls = 'inline-flex items-center rounded-md border border-current/25 bg-black/20 px-2 py-1 font-mono text-xs font-semibold tracking-wide';
const panelCls = 'rounded-2xl bg-bg-card shadow-soft backdrop-blur-sm';

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
  const [assistantFilter, setAssistantFilter] = useState<string>('');
  const [threadFilter, setThreadFilter] = useState<string>('');
  const [targetFilter, setTargetFilter] = useState<string>('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [controlsOpen, setControlsOpen] = useState(false);

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
      if (!selectedGraphId && nextGraphs.length > 0) setSelectedGraphId(nextGraphs[0].id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load execution graphs');
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
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load execution graph detail');
      });

    return () => {
      cancelled = true;
    };
  }, [selectedGraphId, setSearchParams]);

  const filteredGraphs = useMemo(() => {
    let result = graphs;
    if (assistantFilter) result = result.filter((graph) => graph.assistant_id === assistantFilter);
    const query = search.trim().toLowerCase();
    if (!query) return result;
    return result.filter((graph) => [
      graph.title,
      graph.assistant_id,
      graph.status,
      String(graph.id),
      String(graph.thread_id || ''),
    ].some((value) => String(value || '').toLowerCase().includes(query)));
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
    <div className="c2-workspace c2-workspace--monitor min-h-screen bg-bg-base p-6 font-body text-text-primary">
      <header className="flex justify-end pb-2">
        <button
          className="inline-flex size-11 shrink-0 items-center justify-center rounded-xl border border-border-subtle bg-bg-surface text-text-secondary transition-colors hover:border-cyan hover:text-cyan focus:outline-none focus:ring-2 focus:ring-cyan/60"
          type="button"
          aria-label="開啟執行控制"
          title="執行控制"
          onClick={() => setControlsOpen(true)}
        >
          <Settings className="size-5" aria-hidden="true" />
        </button>
      </header>

      <Dialog open={controlsOpen} onOpenChange={setControlsOpen}>
        <DialogContent className="max-h-[85vh] max-w-2xl overflow-y-auto border-border-subtle bg-bg-elevated text-text-primary">
          <DialogHeader>
            <DialogTitle>執行控制</DialogTitle>
          </DialogHeader>
          {error && <div className="rounded-lg border border-red/30 bg-red/10 p-3 text-sm text-red">{error}</div>}
          <section aria-labelledby="execution-status-heading">
            <h2 id="execution-status-heading" className="mb-3 text-base font-semibold text-text-primary">執行狀態</h2>
            <dl className="grid grid-cols-2 gap-3">
              <StatusCount label="執行中" value={stats.running} />
              <StatusCount label="等待中" value={stats.waiting} />
              <StatusCount label="已完成" value={stats.succeeded} />
              <StatusCount label="失敗" value={stats.failed} />
            </dl>
          </section>

          <section className="mt-6 border-t border-border-subtle pt-5" aria-labelledby="execution-filter-heading">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h2 id="execution-filter-heading" className="text-base font-semibold text-text-primary">篩選與搜尋</h2>
                <p className="mt-1 text-sm text-text-secondary">{filteredGraphs.length} 筆結果</p>
              </div>
              <button
                className="inline-flex h-11 shrink-0 items-center justify-center gap-2 rounded-xl border border-border-cyan bg-cyan-glow px-4 text-sm font-semibold text-text-cyan transition-colors hover:border-cyan hover:bg-[rgba(6,182,212,0.2)] focus:outline-none focus:ring-2 focus:ring-cyan/60 disabled:cursor-not-allowed disabled:opacity-50"
                type="button"
                onClick={() => void loadGraphs()}
                disabled={loading}
              >
                <RefreshCw className={cn('size-4', loading && 'animate-spin')} aria-hidden="true" />
                {loading ? '重新整理中' : '重新整理'}
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="relative col-span-2">
                <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-cyan" aria-hidden="true" />
                <input id="graph-search" className={cn(searchInputCls, 'pl-10')} value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜尋圖形、代理或對話串" />
              </div>
              <input aria-label="依 Thread ID 篩選" className={searchInputCls} value={threadFilter} onChange={(event) => setThreadFilter(event.target.value)} placeholder="Thread ID" />
              <input aria-label="依 Target ID 篩選" className={searchInputCls} value={targetFilter} onChange={(event) => setTargetFilter(event.target.value)} placeholder="Target ID" />
              <select aria-label="依代理篩選" className={filterSelectCls} value={assistantFilter} onChange={(event) => setAssistantFilter(event.target.value)}>
                <option value="">所有代理</option>
                {ASSISTANT_OPTIONS.map((assistant) => <option key={assistant} value={assistant}>{assistant}</option>)}
              </select>
              <select aria-label="依狀態篩選" className={filterSelectCls} value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                <option value="">所有狀態</option>
                {STATUS_OPTIONS.map((status) => <option key={status} value={status}>{status}</option>)}
              </select>
            </div>
          </section>

          <section className="mt-6 border-t border-border-subtle pt-5" aria-labelledby="execution-list-heading">
            <h2 id="execution-list-heading" className="mb-3 text-base font-semibold text-text-primary">執行清單</h2>
            {filteredGraphs.length === 0 ? (
              <p className="text-sm text-text-secondary">沒有符合目前搜尋與篩選條件的執行圖。</p>
            ) : (
              <div className="max-h-72 space-y-3 overflow-y-auto pr-1">
                {filteredGraphs.map((graph) => (
                  <button
                    key={graph.id}
                    type="button"
                    onClick={() => { setSelectedGraphId(graph.id); setSelectedNodeId(null); setControlsOpen(false); }}
                    className={cn(
                      'w-full rounded-xl border p-4 text-left text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-cyan/60',
                      selectedGraphId === graph.id
                        ? 'border-cyan bg-cyan-glow shadow-glow-cyan'
                        : 'border-border-subtle bg-bg-panel hover:border-border-normal hover:bg-bg-card-hover',
                    )}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <strong className="font-mono text-sm text-text-primary">Graph #{graph.id}</strong>
                      <span className={cn(statusBadgeCls, statusClass(graph.status))}>{graph.status}</span>
                    </div>
                    <p className="mt-3 line-clamp-2 text-sm leading-5 text-text-primary">{graph.title || graph.assistant_id}</p>
                    <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1 font-mono text-xs text-text-muted">
                      <span>thread {graph.thread_id ?? '-'}</span>
                      <span>{formatDuration(graph.started_at, graph.completed_at)}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </section>
        </DialogContent>
      </Dialog>

      <section className="mt-2 grid min-w-0 gap-4 xl:grid-cols-[minmax(0,1fr)_360px]" aria-label="執行監控工作區">
        <main className={cn(panelCls, 'min-h-[560px] overflow-hidden xl:min-h-[calc(100vh-292px)]')}>
          <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border-subtle p-6">
            <div>
              <div className="flex items-center gap-2 font-mono text-xs font-semibold uppercase tracking-[0.12em] text-text-secondary">
                <Network className="size-3.5 text-cyan" aria-hidden="true" /> 執行圖
              </div>
              <h2 className="mt-2 text-xl font-semibold text-text-primary">{selectedGraph ? `Graph #${selectedGraph.id}` : '尚未選擇執行圖'}</h2>
              {selectedGraph && <p className="mt-2 text-sm text-text-secondary">{selectedGraph.assistant_id} · thread {selectedGraph.thread_id ?? '-'} · started {formatTime(selectedGraph.started_at)}</p>}
            </div>
            {selectedGraph && <span className={cn(statusBadgeCls, statusClass(selectedGraph.status))}>{selectedGraph.status}</span>}
          </div>

          {selectedGraph ? (
            <div className="space-y-4 p-6">
              <div className="grid gap-3 sm:grid-cols-3">
                <Summary label="Nodes" value={selectedGraph.nodes.length} />
                <Summary label="Events" value={selectedGraph.events.length} />
                <Summary label="Artifacts" value={selectedGraph.artifacts.length} />
              </div>
              <div className="grid gap-3">
                {selectedGraph.nodes.map((node) => (
                  <button
                    key={node.id}
                    type="button"
                    onClick={() => setSelectedNodeId(node.id)}
                    className={cn(
                      'rounded-xl border p-4 text-left transition-colors focus:outline-none focus:ring-2 focus:ring-green/60',
                      selectedNodeId === node.id
                        ? 'border-green bg-green-glow shadow-glow-green'
                        : 'border-border-subtle bg-bg-panel hover:border-border-normal hover:bg-bg-card-hover',
                    )}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <strong className="text-sm text-text-primary">#{node.sequence} {node.name}</strong>
                      <span className={cn(statusBadgeCls, statusClass(node.status))}>{node.status}</span>
                    </div>
                    <p className="mt-2 text-sm text-text-secondary">{node.kind} · id {node.id} · task {node.external_task_id || '-'} · {formatDuration(node.started_at, node.completed_at)}</p>
                    {node.wait_reason && <p className="mt-2 text-sm text-purple">等待原因：{node.wait_reason}</p>}
                  </button>
                ))}
                {selectedGraph.nodes.length === 0 && <div className="rounded-xl border border-dashed border-border-normal bg-bg-panel p-6 text-sm text-text-secondary">這次執行尚未記錄任何節點。</div>}
              </div>
              {selectedNode && (
                <section className="rounded-xl border border-border-subtle bg-bg-panel p-4">
                  <h3 className="text-base font-semibold text-text-primary">選取節點資料</h3>
                  <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border border-border-subtle bg-bg-base p-4 font-mono text-sm leading-6 text-text-secondary">{JSON.stringify({ input: selectedNode.input, output: selectedNode.output, error: selectedNode.error }, null, 2)}</pre>
                </section>
              )}
            </div>
          ) : error ? (
            <div className="p-6 text-sm text-red">{error}</div>
          ) : null}
        </main>

        <aside className="min-h-[560px] xl:min-h-[calc(100vh-292px)]">
          <ExecutionTimelineViewer graphId={selectedGraphId} autoScroll />
        </aside>
      </section>
    </div>
  );
}

function StatusCount({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-panel p-4">
      <dt className="text-sm text-text-secondary">{label}</dt>
      <dd className="mt-2 text-2xl font-semibold text-text-primary">{value}</dd>
    </div>
  );
}

function Summary({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-panel p-4">
      <p className="font-mono text-xs uppercase tracking-[0.12em] text-text-muted">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-text-primary">{value}</p>
    </div>
  );
}
