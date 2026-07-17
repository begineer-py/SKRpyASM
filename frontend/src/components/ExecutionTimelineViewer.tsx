import { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import { Activity, MousePointer2, Radio, Filter, X, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useExecutionEventStream } from '../hooks/useExecutionEventStream';
import { executionApi } from '../services/executionApi';
import type { ExecutionEvent, ExecutionGraphDetail } from '../services/executionApi';
import { useVirtualizer } from '@tanstack/react-virtual';

const EMPTY_EVENTS: ExecutionEvent[] = [];

interface ExecutionTimelineViewerProps {
  graphId: number | null;
  autoScroll?: boolean;
  compact?: boolean;
  maxEvents?: number;
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

// Node status filter configuration
const NODE_STATUSES = [
  { value: 'RUNNING', label: 'Running', icon: '▶' },
  { value: 'WAITING', label: 'Waiting', icon: '⏸' },
  { value: 'SUCCEEDED', label: 'Succeeded', icon: '✓' },
  { value: 'COMPLETED', label: 'Completed', icon: '✓' },
  { value: 'FAILED', label: 'Failed', icon: '✗' },
  { value: 'CANCELLED', label: 'Cancelled', icon: '⊘' },
  { value: 'BLOCKED', label: 'Blocked', icon: '⛔' },
  { value: 'PENDING', label: 'Pending', icon: '○' },
] as const;

type NodeStatus = typeof NODE_STATUSES[number]['value'];

interface NodeFilterState {
  selectedStatuses: NodeStatus[];
}

const DEFAULT_NODE_FILTER: NodeFilterState = {
  selectedStatuses: NODE_STATUSES.map(s => s.value),
};

function formatJson(value: Record<string, unknown>): string {
  if (!value || Object.keys(value).length === 0) return '';
  return JSON.stringify(value, null, 2);
}

// Filter popover component for node status selection
function NodeFilterPopover({
  filter,
  onChange,
}: {
  filter: NodeFilterState;
  onChange: (next: NodeFilterState) => void;
}) {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const activeCount = NODE_STATUSES.length - filter.selectedStatuses.length;

  const toggleStatus = (status: NodeStatus) => {
    const has = filter.selectedStatuses.includes(status);
    onChange({
      ...filter,
      selectedStatuses: has
        ? filter.selectedStatuses.filter(s => s !== status)
        : [...filter.selectedStatuses, status],
    });
  };

  const selectAll = () => onChange({ ...filter, selectedStatuses: NODE_STATUSES.map(s => s.value) });
  const selectNone = () => onChange({ ...filter, selectedStatuses: [] });

  return (
    <div className="relative">
      <button
        ref={triggerRef}
        type="button"
        className={cn(
          'ai-secondary-button ai-secondary-button--utility',
          activeCount > 0 && 'is-active'
        )}
        aria-expanded={open}
        aria-haspopup="true"
        onClick={() => setOpen(!open)}
      >
        <Filter size={15} />
        <span>Node Status</span>
        {activeCount > 0 && <span className="ml-1 bg-red-500 text-[10px] font-bold px-1.5 py-0.5 rounded-full">{activeCount}</span>}
      </button>

      {open && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />
          <div
            className="fixed z-20 right-0 mt-2 w-56 rounded-xl border border-[#334155] bg-[#1e293b] shadow-lg py-2"
            role="menu"
            aria-label="Node status filter"
          >
            <div className="px-3 py-2 border-b border-[#334155] flex items-center justify-between">
              <span className="text-sm font-semibold text-[#e2e8f0]">Node Status Filter</span>
              <button
                type="button"
                className="text-[#94a3b8] hover:text-[#e2e8f0] text-xs"
                onClick={(e) => { e.stopPropagation(); setOpen(false); }}
              >
                <X size={14} />
              </button>
            </div>
            <div className="py-2 space-y-1 px-2">
              {NODE_STATUSES.map(({ value, label, icon }) => {
                const active = filter.selectedStatuses.includes(value);
                const pillColor = STATUS_PILL[statusClass(value)] || STATUS_PILL.neutral;
                return (
                  <label
                    key={value}
                    className="flex items-center gap-2 cursor-pointer px-2 py-1.5 rounded-lg hover:bg-[#334155]"
                    onClick={(e) => { e.stopPropagation(); toggleStatus(value); }}
                  >
                    <input
                      type="checkbox"
                      checked={active}
                      onChange={() => {}}
                      className="w-4 h-4 accent-green-500"
                      aria-checked={active}
                    />
                    <span className={cn('inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-bold', pillColor)}>
                      {icon} {label}
                    </span>
                  </label>
                );
              })}
            </div>
            <div className="px-3 py-2 border-t border-[#334155] flex gap-2">
              <button
                type="button"
                className="flex-1 text-xs text-[#94a3b8] hover:text-[#e2e8f0] py-1.5"
                onClick={(e) => { e.stopPropagation(); selectAll(); }}
              >
                <Check size={12} className="inline mr-1" /> All
              </button>
              <button
                type="button"
                className="flex-1 text-xs text-[#94a3b8] hover:text-[#e2e8f0] py-1.5"
                onClick={(e) => { e.stopPropagation(); selectNone(); }}
              >
                <X size={12} className="inline mr-1" /> None
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default function ExecutionTimelineViewer({ graphId, autoScroll = true, compact = false, maxEvents = 500 }: ExecutionTimelineViewerProps) {
  const [graph, setGraph] = useState<ExecutionGraphDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<Error | null>(null);
  const [filter, setFilter] = useState('');
  const [nodeFilter, setNodeFilter] = useState<NodeFilterState>(DEFAULT_NODE_FILTER);
  const [expandedEventId, setExpandedEventId] = useState<number | null>(null);
  const parentRef = useRef<HTMLDivElement>(null);
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

  const { events, isConnected, error, lastSequence } = useExecutionEventStream(graphId, graph?.events ?? EMPTY_EVENTS, true, 5, maxEvents);

  const nodeById = useMemo(() => {
    const map = new Map<number, string>();
    for (const node of graph?.nodes ?? []) {
      map.set(node.id, node.name);
    }
    return map;
  }, [graph?.nodes]);

  // Node status filter: create a set of allowed statuses for quick lookup
  const allowedNodeStatuses = useMemo(() => new Set(nodeFilter.selectedStatuses), [nodeFilter.selectedStatuses]);

  // Filter nodes by selected statuses
  const filteredNodes = useMemo(() => {
    if (!graph) return [];
    return graph.nodes.filter((node) => allowedNodeStatuses.has(node.status as NodeStatus));
  }, [graph, allowedNodeStatuses]);

  // Filter events: only show events from nodes that match the status filter
  const filteredEvents = useMemo(() => {
    const query = filter.trim().toLowerCase();
    const allowedNodeIds = new Set(filteredNodes.map(n => n.id));
    
    const result = events.filter((event) => {
      // If event has a node_id, check if that node is in the allowed set
      if (event.node_id && !allowedNodeIds.has(event.node_id)) {
        return false;
      }
      // Text search filter
      if (query) {
        const nodeName = event.node_id ? nodeById.get(event.node_id) || '' : '';
        return [event.event_type, event.status || '', event.content, nodeName]
          .some((value) => value.toLowerCase().includes(query));
      }
      return true;
    });
    return result;
  }, [events, filter, nodeById, filteredNodes]);

  // Virtualizer for efficient rendering of large event lists
  const virtualizer = useVirtualizer({
    count: filteredEvents.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (index) => {
      const event = filteredEvents[index];
      if (!event) return compact ? 80 : 120;
      // Expanded events are much taller due to payload display
      return expandedEventId === event.id ? (compact ? 280 : 420) : (compact ? 80 : 120);
    },
    overscan: 5,
    measureElement: (element) => element.getBoundingClientRect().height,
  });

  // Auto-scroll to bottom when new events arrive
  const scrollToBottom = useCallback(() => {
    if (autoScroll && parentRef.current) {
      parentRef.current.scrollTop = parentRef.current.scrollHeight;
    }
  }, [autoScroll]);

  useEffect(() => {
    scrollToBottom();
  }, [filteredEvents.length, scrollToBottom]);

  // Re-measure when expanded event changes (height changes significantly)
  useEffect(() => {
    virtualizer.measure();
  }, [expandedEventId, virtualizer]);

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
        <div className="flex flex-wrap items-center gap-2 flex-1 min-w-0">
          <input
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            placeholder="Search events..."
            className="h-10 flex-1 min-w-[180px] px-3 text-sm text-[#e2e8f0] bg-[#080d1b] border border-[rgba(148,163,184,0.24)] rounded-lg font-[inherit] focus:outline-none focus:border-[#38bdf8] focus:shadow-[0_0_0_3px_rgba(56,189,248,0.12)] placeholder:text-[#64748b]"
          />
          <NodeFilterPopover
            filter={nodeFilter}
            onChange={setNodeFilter}
          />
        </div>
        <span className={cn(pillClass, 'text-[#cbd5e1] bg-[rgba(148,163,184,0.14)]')}>{filteredEvents.length} / {events.length} events</span>
        <span className={cn(pillClass, 'text-[#cbd5e1] bg-[rgba(148,163,184,0.14)]')}>{filteredNodes.length} / {graph?.nodes.length ?? 0} nodes</span>
        <span className={cn(pillClass, 'text-[#cbd5e1] bg-[rgba(148,163,184,0.14)]')}>{graph?.artifacts.length ?? 0} artifacts</span>
      </div>

      <div className="flex-1 min-h-0 overflow-hidden p-3">
        <div
          ref={parentRef}
          className="h-full overflow-y-auto"
          style={{ contain: 'layout' }}
        >
          {filteredEvents.length === 0 ? (
            <div className="flex items-center justify-center min-h-[180px] text-[#94a3b8]">No execution events yet.</div>
          ) : (
            <>
              <div
                style={{
                  height: virtualizer.getTotalSize(),
                  width: '100%',
                  position: 'relative',
                }}
              >
                {virtualizer.getVirtualItems().map((virtualRow) => (
                  <div
                    key={virtualRow.key}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: `${virtualRow.size}px`,
                      transform: `translateY(${virtualRow.start}px)`,
                    }}
                  >
                    {(() => {
                      const event = filteredEvents[virtualRow.index];
                      if (!event) return null;
                      return (
                        <TimelineEvent
                          key={`${event.sequence}-${event.id}`}
                          event={event}
                          nodeName={event.node_id ? nodeById.get(event.node_id) : undefined}
                          expanded={expandedEventId === event.id}
                          onToggle={() => setExpandedEventId((current) => current === event.id ? null : event.id)}
                        />
                      );
                    })()}
                  </div>
                ))}
              </div>
            </>
          )}
          <div ref={endRef} />
        </div>
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
