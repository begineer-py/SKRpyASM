import { useCallback, useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import ExecutionTimelineViewer from '../../../components/ExecutionTimelineViewer';
import { executionApi, type ExecutionGraph } from '../../../services/executionApi';

interface TargetExecutionsPanelProps {
  readonly targetId: number;
}

export function TargetExecutionsPanel({ targetId }: TargetExecutionsPanelProps) {
  const [graphs, setGraphs] = useState<readonly ExecutionGraph[]>([]);
  const [selectedGraphId, setSelectedGraphId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadGraphs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const items = await executionApi.listGraphs({ target_id: targetId, limit: 50 });
      setGraphs(items);
      setSelectedGraphId((current) => items.some((graph) => graph.id === current) ? current : (items[0]?.id ?? null));
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : '無法載入此 Target 的 Executions。');
      setGraphs([]);
      setSelectedGraphId(null);
    } finally {
      setLoading(false);
    }
  }, [targetId]);

  useEffect(() => {
    void loadGraphs();
  }, [loadGraphs]);

  return (
    <section aria-labelledby="target-executions-heading" className="flex flex-col gap-5">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle pb-5">
        <div>
          <h2 id="target-executions-heading" className="text-lg font-semibold text-text-primary">Executions</h2>
          <p className="mt-2 text-sm text-text-secondary">選取此 Target 的 execution graph 以查看事件與節點。</p>
        </div>
        <button className="c2-btn c2-btn--ghost" type="button" onClick={() => void loadGraphs()} disabled={loading}>
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} aria-hidden="true" />重新整理
        </button>
      </header>

      {error ? <p className="rounded-xl border border-red bg-bg-surface p-4 text-sm text-red" role="alert">{error}</p> : null}
      {loading ? <div className="c2-empty">正在載入 Executions…</div> : null}
      {!loading && !error && graphs.length === 0 ? <div className="c2-empty">此 Target 尚無 execution graphs。</div> : null}
      {!loading && !error && graphs.length > 0 ? (
        <div className="grid gap-5 xl:grid-cols-[minmax(16rem,1fr)_minmax(0,2fr)]">
          <div className="flex max-h-96 flex-col gap-2 overflow-y-auto rounded-xl border border-border-subtle bg-bg-surface p-3">
            {graphs.map((graph) => (
              <button
                key={graph.id}
                type="button"
                className="rounded-xl border border-border-subtle p-4 text-left transition-colors hover:border-cyan focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan/60 data-[selected=true]:border-cyan data-[selected=true]:bg-bg-card"
                data-selected={selectedGraphId === graph.id}
                onClick={() => setSelectedGraphId(graph.id)}
              >
                <span className="block text-sm font-semibold text-text-primary">{graph.title || `Graph #${graph.id}`}</span>
                <span className="mt-2 block font-mono text-xs text-text-muted">{graph.status} · {new Date(graph.started_at).toLocaleString()}</span>
              </button>
            ))}
          </div>
          <ExecutionTimelineViewer graphId={selectedGraphId} compact />
        </div>
      ) : null}
    </section>
  );
}
