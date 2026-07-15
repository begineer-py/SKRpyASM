import { useEffect, useMemo, useRef, useState } from 'react';
import { Activity, MousePointer2, Radio } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useExecutionEventStream } from '../hooks/useExecutionEventStream';
import { executionApi } from '../services/executionApi';
import type { ExecutionEvent, ExecutionGraphDetail } from '../services/executionApi';

const EMPTY_EVENTS: ExecutionEvent[] = [];

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

const STATUS_PILL: Record<string, string> = {
  running: 'text-[#7dd3fc] bg-[rgba(14,165,233,0.16)]',
  waiting: 'text-[#fcd34d] bg-[rgba(245,158,11,0.16)]',
  succeeded: 'text-[#86efac] bg-[rgba(34,197,94,0.16)]',
  failed: 'text-[#fca5a5] bg-[rgba(239,68,68,0.16)]',
  cancelled: 'text-[#fca5a5] bg-[rgba(239,68,68,0.16)]',
  blocked: 'text-[#fca5a5] bg-[rgba(239,68,68,0.16)]',
  neutral: 'text-[#cbd5e1] bg-[rgba(148,163,184,0.16)]',
};

const STATUS_BORDER: Record<string, string> = {
  running: 'border-l-[#2563eb]',
  waiting: 'border-l-[#f59e0b]',
  succeeded: 'border-l-[#10b981]',
  failed: 'border-l-[#ef4444]',
  cancelled: 'border-l-[#ef4444]',
  blocked: 'border-l-[#ef4444]',
};

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

  const { events, isConnected, error, lastSequence } = useExecutionEventStream(graphId, graph?.events ?? EMPTY_EVENTS);

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

  const pillClass = 'inline-flex items-center rounded-full px-2 py-[3px] text-[11px] font-bold leading-tight';
  const rowClass = 'flex items-center gap-2 flex-wrap';

  if (!graphId) {
    return (
      <div className="flex h-full min-h-[560px] items-center justify-center overflow-hidden rounded-2xl border border-border-subtle bg-bg-card p-6 text-center shadow-soft backdrop-blur-sm xl:min-h-[calc(100vh-292px)]">
        <div className="max-w-xs">
          <span className="mx-auto flex size-14 items-center justify-center rounded-2xl border border-border-cyan bg-cyan-glow text-cyan"><Activity className="size-6" aria-hidden="true" /></span>
          <p className="mt-5 font-mono text-xs font-semibold uppercase tracking-[0.14em] text-cyan">Timeline inspector</p>
          <h2 className="mt-3 text-xl font-semibold text-text-primary">No graph selected</h2>
          <p className="mt-3 text-sm leading-6 text-text-secondary">Select an execution from the list to inspect event sequence, node transitions, and real-time activity.</p>
          <div className="mt-5 flex items-center justify-center gap-2 text-sm text-text-secondary"><MousePointer2 className="size-4 text-cyan" aria-hidden="true" /> Choose a workflow on the left</div>
        </div>
      </div>
    );
  }

  if (loading && !graph) {
    return <div className="flex items-center justify-center min-h-[180px] text-[#94a3b8]">Loading execution graph...</div>;
  }

  const visibleError = loadError || error;

  return (
    <div className={cn(
      'flex flex-col h-full min-h-0 overflow-hidden border border-[rgba(148,163,184,0.18)] rounded-[12px] bg-[#080d1b] text-[#dbeafe] font-mono text-[14px]',
      compact && 'text-[13px]',
    )}>
      <div className="flex justify-between items-center gap-4 px-5 py-4 text-[#e2e8f0] bg-gradient-to-br from-[#0f172a] to-[#1e3a8a] border-b border-[#1e40af] [&_h3]:m-0 [&_h3]:text-white [&_h3]:text-base [&_h3]:font-bold">
        <div>
          <h3 className="flex items-center gap-2"><Radio className="size-4 text-cyan" aria-hidden="true" /> Execution Timeline</h3>
          <div className="mt-1 text-[#bfdbfe] text-sm">
            Graph #{graphId}{graph?.title ? `: ${graph.title}` : ''}
          </div>
        </div>
        <div className={rowClass}>
          {graph?.status && (
            <span className={cn(pillClass, STATUS_PILL[statusClass(graph.status)] || STATUS_PILL.neutral)}>
              {graph.status}
            </span>
          )}
          <span className={cn(pillClass, isConnected ? 'text-[#bbf7d0] bg-[rgba(34,197,94,0.2)]' : 'text-[#cbd5e1] bg-[rgba(148,163,184,0.2)]')}>
            {isConnected ? 'LIVE' : 'OFFLINE'}
          </span>
          <span className={cn(pillClass, 'text-[#cbd5e1] bg-[rgba(148,163,184,0.2)]')}>seq#{lastSequence}</span>
        </div>
      </div>

      {visibleError && <div className="px-4 py-2.5 text-[#fca5a5] bg-[rgba(239,68,68,0.12)] border-b border-[rgba(248,113,113,0.24)]">{visibleError.message}</div>}

      <div className={`${rowClass} px-4 py-4 bg-[#0d1424] border-b border-[rgba(148,163,184,0.14)]`}>
        <input
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
          placeholder="Search events..."
          className="h-10 flex-1 min-w-[180px] px-3 text-sm text-[#e2e8f0] bg-[#080d1b] border border-[rgba(148,163,184,0.24)] rounded-lg font-[inherit] focus:outline-none focus:border-[#38bdf8] focus:shadow-[0_0_0_3px_rgba(56,189,248,0.12)] placeholder:text-[#64748b]"
        />
        <span className={cn(pillClass, 'text-[#cbd5e1] bg-[rgba(148,163,184,0.14)]')}>{filteredEvents.length} / {events.length} events</span>
        <span className={cn(pillClass, 'text-[#cbd5e1] bg-[rgba(148,163,184,0.14)]')}>{graph?.nodes.length ?? 0} nodes</span>
        <span className={cn(pillClass, 'text-[#cbd5e1] bg-[rgba(148,163,184,0.14)]')}>{graph?.artifacts.length ?? 0} artifacts</span>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto p-3">
        {filteredEvents.length === 0 ? (
          <div className="flex items-center justify-center min-h-[180px] text-[#94a3b8]">No execution events yet.</div>
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
  const sc = statusClass(event.status);
  const pillClass = 'inline-flex items-center rounded-full px-2 py-[3px] text-[11px] font-bold leading-tight';

  return (
    <div className={cn(
      'mb-3 overflow-hidden border border-[rgba(148,163,184,0.16)] border-l-4 border-l-[#64748b] rounded-[10px] bg-[#0d1424]',
      STATUS_BORDER[sc],
    )}>
      <button
        className="w-full px-3.5 py-3 text-inherit text-left bg-transparent border-0 cursor-pointer hover:bg-[#121d31]"
        onClick={onToggle}
        type="button"
      >
        <div className="flex items-center gap-2 flex-wrap">
          <span className={cn(pillClass, 'text-[#cbd5e1] bg-[rgba(148,163,184,0.14)]')}>#{event.sequence}</span>
          <span className={cn(pillClass, 'text-[#cbd5e1] bg-[rgba(148,163,184,0.14)]')}>{event.event_type}</span>
          {event.status && (
            <span className={cn(pillClass, STATUS_PILL[sc] || STATUS_PILL.neutral)}>{event.status}</span>
          )}
          {nodeName && <span className={cn(pillClass, 'text-[#cbd5e1] bg-[rgba(148,163,184,0.14)]')}>{nodeName}</span>}
        </div>
        <div className="mt-2 break-anywhere whitespace-pre-wrap">{event.content || '(no content)'}</div>
        <div className="mt-1.5 text-sm text-[#94a3b8]">{new Date(event.created_at).toLocaleTimeString()}</div>
      </button>

      {expanded && (
        <div className="px-3.5 py-3 text-sm text-[#cbd5e1] bg-[#080d1b] border-t border-[rgba(148,163,184,0.14)] [&_pre]:overflow-x-auto [&_pre]:mt-2 [&_pre]:mx-0 [&_pre]:p-2.5 [&_pre]:text-[#e2e8f0] [&_pre]:bg-[#050814] [&_pre]:rounded-lg">
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
