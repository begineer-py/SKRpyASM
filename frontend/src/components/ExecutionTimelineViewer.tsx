import { useEffect, useMemo, useRef, useState } from 'react';
import { useExecutionEventStream } from '../hooks/useExecutionEventStream';
import { executionApi } from '../services/executionApi';
import type { ExecutionEvent, ExecutionGraphDetail } from '../services/executionApi';
import './ExecutionTimelineViewer.css';

interface ExecutionTimelineViewerProps {
  graphId: number | null;
  autoScroll?: boolean;
  compact?: boolean;
}

const STATUS_CLASS: Record<string, string> = {
  RUNNING: 'running',
  WAITING: 'waiting',
  SUCCEEDED: 'succeeded',
  COMPLETED: 'succeeded',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
  BLOCKED: 'blocked',
};

function statusClass(status?: string | null): string {
  return STATUS_CLASS[status || ''] || 'neutral';
}

function formatJson(value: Record<string, unknown>): string {
  if (!value || Object.keys(value).length === 0) return '';
  return JSON.stringify(value, null, 2);
}

export default function ExecutionTimelineViewer({ graphId, autoScroll = true, compact = false }: ExecutionTimelineViewerProps) {
  const [graph, setGraph] = useState<ExecutionGraphDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<Error | null>(null);
  const [filter, setFilter] = useState('');
  const [expandedEventId, setExpandedEventId] = useState<number | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    if (!graphId) {
      setGraph(null);
      return;
    }

    setLoading(true);
    setLoadError(null);
    executionApi.getGraph(graphId)
      .then((detail) => {
        if (!cancelled) setGraph(detail);
      })
      .catch((err: unknown) => {
        if (!cancelled) setLoadError(err instanceof Error ? err : new Error('Failed to load execution graph'));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [graphId]);

  const { events, isConnected, error, lastSequence } = useExecutionEventStream(graphId, graph?.events ?? []);

  const nodeById = useMemo(() => {
    const map = new Map<number, string>();
    for (const node of graph?.nodes ?? []) {
      map.set(node.id, node.name);
    }
    return map;
  }, [graph?.nodes]);

  const filteredEvents = useMemo(() => {
    const query = filter.trim().toLowerCase();
    if (!query) return events;
    return events.filter((event) => {
      const nodeName = event.node_id ? nodeById.get(event.node_id) || '' : '';
      return [event.event_type, event.status || '', event.content, nodeName]
        .some((value) => value.toLowerCase().includes(query));
    });
  }, [events, filter, nodeById]);

  useEffect(() => {
    if (autoScroll && endRef.current) {
      endRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [filteredEvents, autoScroll]);

  if (!graphId) {
    return <div className="execution-timeline empty">Select an execution graph to view its timeline.</div>;
  }

  if (loading && !graph) {
    return <div className="execution-timeline empty">Loading execution graph...</div>;
  }

  const visibleError = loadError || error;

  return (
    <div className={`execution-timeline ${compact ? 'compact' : ''}`}>
      <div className="etv-header">
        <div>
          <h3>Execution Timeline</h3>
          <div className="etv-subtitle">
            Graph #{graphId}{graph?.title ? `: ${graph.title}` : ''}
          </div>
        </div>
        <div className="etv-status-row">
          {graph?.status && <span className={`etv-pill ${statusClass(graph.status)}`}>{graph.status}</span>}
          <span className={`etv-live ${isConnected ? 'connected' : 'disconnected'}`}>{isConnected ? 'LIVE' : 'OFFLINE'}</span>
          <span className="etv-sequence">seq#{lastSequence}</span>
        </div>
      </div>

      {visibleError && <div className="etv-error">{visibleError.message}</div>}

      <div className="etv-controls">
        <input
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
          placeholder="Search events..."
          className="etv-search"
        />
        <span className="etv-count">{filteredEvents.length} / {events.length} events</span>
        <span className="etv-count">{graph?.nodes.length ?? 0} nodes</span>
        <span className="etv-count">{graph?.artifacts.length ?? 0} artifacts</span>
      </div>

      <div className="etv-list">
        {filteredEvents.length === 0 ? (
          <div className="etv-empty">No execution events yet.</div>
        ) : (
          filteredEvents.map((event) => (
            <TimelineEvent
              key={`${event.sequence}-${event.id}`}
              event={event}
              nodeName={event.node_id ? nodeById.get(event.node_id) : undefined}
              expanded={expandedEventId === event.id}
              onToggle={() => setExpandedEventId((current) => current === event.id ? null : event.id)}
            />
          ))
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
}

function TimelineEvent({
  event,
  nodeName,
  expanded,
  onToggle,
}: {
  event: ExecutionEvent;
  nodeName?: string;
  expanded: boolean;
  onToggle: () => void;
}) {
  const payload = formatJson(event.payload);

  return (
    <div className={`etv-event ${statusClass(event.status)}`}>
      <button className="etv-event-main" onClick={onToggle} type="button">
        <div className="etv-event-meta">
          <span className="etv-seq">#{event.sequence}</span>
          <span className="etv-type">{event.event_type}</span>
          {event.status && <span className={`etv-pill ${statusClass(event.status)}`}>{event.status}</span>}
          {nodeName && <span className="etv-node">{nodeName}</span>}
        </div>
        <div className="etv-content">{event.content || '(no content)'}</div>
        <div className="etv-time">{new Date(event.created_at).toLocaleTimeString()}</div>
      </button>

      {expanded && (
        <div className="etv-details">
          <div>ID: {event.id}</div>
          <div>Graph: {event.graph_id}</div>
          {event.node_id && <div>Node: {event.node_id}</div>}
          <div>Created: {new Date(event.created_at).toLocaleString()}</div>
          {payload && <pre>{payload}</pre>}
        </div>
      )}
    </div>
  );
}
