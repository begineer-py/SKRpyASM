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
  RUNNING: { bg: '#dbeafe', text: '#2563eb', icon: 'R' },
  WAITING: { bg: '#fef3c7', text: '#92400e', icon: 'W' },
  SUCCEEDED: { bg: '#dcfce7', text: '#059669', icon: 'S' },
  FAILED: { bg: '#fee2e2', text: '#dc2626', icon: 'F' },
  CANCELLED: { bg: '#e5e7eb', text: '#374151', icon: 'C' },
  BLOCKED: { bg: '#f3e8ff', text: '#7e22ce', icon: 'B' },
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

  const rootClass = 'flex flex-col h-full bg-white border border-gray-200 rounded-lg overflow-hidden';

  if (!targetId) {
    return <div className={cn(rootClass, 'items-center justify-center text-gray-500 text-[13px] min-h-[200px]')}><p>Select a target to view activity</p></div>;
  }

  if (loading) {
    return (
      <div className={cn(rootClass, 'items-center justify-center text-gray-500 text-[13px] min-h-[200px]')}>
        <div className="w-5 h-5 border-2 border-gray-200 border-t-blue-500 rounded-full animate-spin mr-2.5" />
        <p>Loading executions...</p>
      </div>
    );
  }

  if (error) {
    return <div className={cn(rootClass, 'items-center justify-center text-red-600 text-[13px] min-h-[200px]')}><p>Error: {error}</p></div>;
  }

  if (graphs.length === 0) {
    return <div className={cn(rootClass, 'items-center justify-center text-gray-500 text-[13px] min-h-[200px]')}><p>No execution graphs yet.</p></div>;
  }

  return (
    <div className={rootClass}>
      <div className="flex justify-between items-center px-4 py-3 border-b border-gray-200 bg-gray-50 [&_h3]:m-0 [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:text-gray-900">
        <h3>Execution Activity</h3>
        <div className="flex gap-3 text-[12px] max-md:flex-wrap max-md:gap-2">
          {stats.active > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-blue-100 text-blue-600">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse" />
              {stats.active} active
            </span>
          )}
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-green-100 text-emerald-600">{stats.completed} done</span>
          {stats.failed > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-red-100 text-red-600">{stats.failed} failed</span>
          )}
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-gray-100 text-gray-700 font-semibold">Total: {graphs.length}</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-0">
        {graphs.map((graph, idx) => {
          const statusColor = STATUS_COLORS[graph.status] || STATUS_COLORS.RUNNING;
          return (
            <div key={graph.id} className="flex gap-3 mb-0 rounded-md transition-colors duration-200 hover:bg-gray-50">
              <div className="flex flex-col items-center pt-0.5">
                <div
                  className="w-8 h-8 border-2 border-gray-200 rounded-full flex items-center justify-center text-sm bg-white shrink-0 relative z-[2]"
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
                    className="inline-block px-2 py-1 rounded text-[11px] font-semibold shrink-0"
                    style={{ backgroundColor: statusColor.bg, color: statusColor.text }}
                  >
                    {graph.status}
                  </span>
                  <span className="inline-block px-2 py-1 text-gray-400 text-[11px] font-mono ml-auto max-md:ml-0 max-md:mt-1">
                    {new Date(graph.started_at).toLocaleString()}
                  </span>
                </div>
                <div className="text-[12px] text-gray-500 mt-1">
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
