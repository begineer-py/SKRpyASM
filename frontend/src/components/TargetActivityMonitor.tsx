import { useEffect, useMemo, useState } from 'react';
import { cn } from '@/lib/utils';
import { executionApi } from '../services/executionApi';
import type { ExecutionGraph } from '../services/executionApi';

interface TargetActivityMonitorProps {
  targetId: number | null;
  compact?: boolean;
  maxSteps?: number;
}

const STATUS_COLORS: Record<string, { bg: string; text: string; icon: string }> = {
  RUNNING: { bg: 'rgba(14,165,233,0.16)', text: '#7dd3fc', icon: 'R' },
  WAITING: { bg: 'rgba(245,158,11,0.16)', text: '#fcd34d', icon: 'W' },
  SUCCEEDED: { bg: 'rgba(34,197,94,0.16)', text: '#86efac', icon: 'S' },
  FAILED: { bg: 'rgba(239,68,68,0.16)', text: '#fca5a5', icon: 'F' },
  CANCELLED: { bg: 'rgba(148,163,184,0.16)', text: '#cbd5e1', icon: 'C' },
  BLOCKED: { bg: 'rgba(139,92,246,0.16)', text: '#c4b5fd', icon: 'B' },
};

export default function TargetActivityMonitor({
  targetId,
  compact = false,
  maxSteps = 20,
}: TargetActivityMonitorProps) {
  const [graphs, setGraphs] = useState<ExecutionGraph[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (!targetId) {
      setGraphs([]);
      return;
    }

    setLoading(true);
    setError(null);
    executionApi.listGraphs({ target_id: targetId, limit: maxSteps })
      .then((items) => {
        if (!cancelled) setGraphs(items);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load executions');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [targetId, maxSteps]);

  const stats = useMemo(() => ({
    active: graphs.filter((graph) => graph.status === 'RUNNING' || graph.status === 'WAITING').length,
    completed: graphs.filter((graph) => graph.status === 'SUCCEEDED').length,
    failed: graphs.filter((graph) => graph.status === 'FAILED').length,
  }), [graphs]);

  const rootClass = cn(
    'flex flex-col h-full bg-[#080d1b] border border-[rgba(148,163,184,0.18)] rounded-[12px] overflow-hidden text-[#dbeafe]',
    compact ? 'min-h-[160px]' : 'min-h-[200px]',
  );

  if (!targetId) {
    return <div className={cn(rootClass, 'items-center justify-center text-[#94a3b8] text-[14px] min-h-[220px]')}><p>Select a target to view activity</p></div>;
  }

  if (loading) {
    return (
      <div className={cn(rootClass, 'items-center justify-center text-[#94a3b8] text-[14px] min-h-[220px]')}>
        <div className="w-5 h-5 border-2 border-[rgba(148,163,184,0.22)] border-t-[#38bdf8] rounded-full animate-spin mr-2.5" />
        <p>Loading executions...</p>
      </div>
    );
  }

  if (error) {
    return <div className={cn(rootClass, 'items-center justify-center text-[#fca5a5] text-[14px] min-h-[220px]')}><p>Error: {error}</p></div>;
  }

  if (graphs.length === 0) {
    return <div className={cn(rootClass, 'items-center justify-center text-[#94a3b8] text-[14px] min-h-[220px]')}><p>No execution graphs yet.</p></div>;
  }

  return (
    <div className={rootClass}>
      <div className="flex justify-between items-center px-5 py-4 border-b border-[rgba(148,163,184,0.14)] bg-[#0d1424] [&_h3]:m-0 [&_h3]:text-[15px] [&_h3]:font-semibold [&_h3]:text-[#f8fafc]">
        <h3>Execution Activity</h3>
        <div className="flex gap-3 text-[12px] max-md:flex-wrap max-md:gap-2">
          {stats.active > 0 && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded bg-[rgba(14,165,233,0.16)] text-[#7dd3fc]">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#38bdf8] animate-pulse" />
              {stats.active} active
            </span>
          )}
          <span className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded bg-[rgba(34,197,94,0.16)] text-[#86efac]">{stats.completed} done</span>
          {stats.failed > 0 && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded bg-[rgba(239,68,68,0.16)] text-[#fca5a5]">{stats.failed} failed</span>
          )}
          <span className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded bg-[rgba(148,163,184,0.14)] text-[#cbd5e1] font-semibold">Total: {graphs.length}</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-0">
        {graphs.map((graph, idx) => {
          const statusColor = STATUS_COLORS[graph.status] || STATUS_COLORS.RUNNING;
          return (
            <div key={graph.id} className="flex gap-3 mb-0 rounded-md transition-colors duration-200 hover:bg-[#121d31]">
              <div className="flex flex-col items-center pt-0.5">
                <div
                  className="w-9 h-9 border-2 rounded-full flex items-center justify-center text-sm font-semibold bg-[#0d1424] shrink-0 relative z-[2]"
                  style={{ backgroundColor: statusColor.bg, borderColor: statusColor.text }}
                >
                  {statusColor.icon}
                </div>
                {idx < graphs.length - 1 && (
                  <div className="w-0.5 flex-1 bg-gradient-to-b from-gray-200 to-transparent mt-1 min-h-[20px]" />
                )}
              </div>
              <div className="flex-1 min-w-0 py-2">
                <div className="flex items-center gap-2 flex-wrap py-2 max-md:flex-col max-md:items-start">
                  <span>Graph #{graph.id}</span>
                  <span
                    className="inline-block px-2.5 py-1 rounded text-[12px] font-semibold shrink-0"
                    style={{ backgroundColor: statusColor.bg, color: statusColor.text }}
                  >
                    {graph.status}
                  </span>
                  <span className="inline-block px-2 py-1 text-[#94a3b8] text-[12px] font-mono ml-auto max-md:ml-0 max-md:mt-1">
                    {new Date(graph.started_at).toLocaleString()}
                  </span>
                </div>
                <div className="text-[13px] text-[#94a3b8] mt-1.5">
                  {graph.title || graph.assistant_id} · thread {graph.thread_id ?? '-'}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
