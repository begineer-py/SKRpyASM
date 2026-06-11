import { useEffect, useMemo, useState } from 'react';
import { executionApi } from '../services/executionApi';
import type { ExecutionGraph } from '../services/executionApi';
import './TargetActivityMonitor.css';

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
      .catch((err: any) => {
        if (!cancelled) setError(err?.message || 'Failed to load executions');
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

  if (!targetId) {
    return <div className="target-activity-monitor empty"><p>Select a target to view activity</p></div>;
  }

  if (loading) {
    return <div className="target-activity-monitor loading"><div className="spinner" /><p>Loading executions...</p></div>;
  }

  if (error) {
    return <div className="target-activity-monitor error"><p>Error: {error}</p></div>;
  }

  if (graphs.length === 0) {
    return <div className="target-activity-monitor empty"><p>No execution graphs yet.</p></div>;
  }

  return (
    <div className={`target-activity-monitor ${compact ? 'compact' : 'expanded'}`}>
      <div className="activity-header">
        <h3>Execution Activity</h3>
        <div className="activity-stats">
          {stats.active > 0 && <span className="stat active"><span className="dot" />{stats.active} active</span>}
          <span className="stat completed">{stats.completed} done</span>
          {stats.failed > 0 && <span className="stat failed">{stats.failed} failed</span>}
          <span className="stat total">Total: {graphs.length}</span>
        </div>
      </div>

      <div className="activity-timeline">
        {graphs.map((graph, idx) => {
          const statusColor = STATUS_COLORS[graph.status] || STATUS_COLORS.RUNNING;
          return (
            <div key={graph.id} className="activity-item">
              <div className="timeline-point">
                <div className="point" style={{ backgroundColor: statusColor.bg, borderColor: statusColor.text }}>{statusColor.icon}</div>
                {idx < graphs.length - 1 && <div className="line" />}
              </div>
              <div className="activity-content">
                <div className="activity-title">
                  <span>Graph #{graph.id}</span>
                  <span className="status-badge" style={{ backgroundColor: statusColor.bg, color: statusColor.text }}>{graph.status}</span>
                </div>
                <div className="activity-meta">
                  {graph.title || graph.assistant_id} · thread {graph.thread_id ?? '-'}
                </div>
                <div className="activity-time">{new Date(graph.started_at).toLocaleString()}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
