import { useEffect, useMemo, useRef, useState } from 'react';
import { cn } from '@/lib/utils';
import { assistantApi, type ThreadEvent } from '../services/assistantApi';
import { useThreadEventStream } from '../hooks/useThreadEventStream';

interface ThreadEventTimelineProps {
  threadId: number | string | null;
  autoScroll?: boolean;
}

const STATUS_CLASS: Record<string, string> = {
  started: 'started',
  running: 'running',
  completed: 'completed',
  succeeded: 'succeeded',
  failed: 'failed',
  error: 'failed',
};

function statusClass(status?: string | null): string {
  return STATUS_CLASS[status || ''] || '';
}

const STATUS_PILL: Record<string, string> = {
  started: 'text-[#1d4ed8] bg-[#dbeafe]',
  running: 'text-[#1d4ed8] bg-[#dbeafe]',
  completed: 'text-[#047857] bg-[#d1fae5]',
  succeeded: 'text-[#047857] bg-[#d1fae5]',
  failed: 'text-[#b91c1c] bg-[#fee2e2]',
};

const STATUS_BORDER: Record<string, string> = {
  started: 'border-l-[#3b82f6]',
  running: 'border-l-[#2563eb]',
  completed: 'border-l-[#10b981]',
  succeeded: 'border-l-[#10b981]',
  failed: 'border-l-[#ef4444]',
};

function eventIcon(eventType: string): string {
  if (eventType.includes('scanner')) return '🔍';
  if (eventType.includes('sandbox')) return '📦';
  if (eventType.includes('tool_call')) return '🔧';
  if (eventType.includes('tool_result')) return '✅';
  if (eventType.includes('tool_error')) return '❌';
  if (eventType.includes('dispatch')) return '🚀';
  return '📌';
}

export default function ThreadEventTimeline({ threadId, autoScroll = true }: ThreadEventTimelineProps) {
  const [historicalEvents, setHistoricalEvents] = useState<ThreadEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<Error | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!threadId) {
      setHistoricalEvents([]);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setLoadError(null);
    assistantApi.getThreadEvents(threadId)
      .then((events) => {
        if (!cancelled) setHistoricalEvents(events);
      })
      .catch((err) => {
        if (!cancelled) setLoadError(err instanceof Error ? err : new Error('Failed to load events'));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [threadId]);

  const { events, isConnected, error, lastSequence } = useThreadEventStream(threadId, historicalEvents);

  const filteredEvents = useMemo(() => events, [events]);

  useEffect(() => {
    if (autoScroll && endRef.current) {
      endRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [filteredEvents, autoScroll]);

  const pillClass = 'inline-flex items-center rounded-full px-[7px] py-[2px] text-[10px] font-bold leading-tight';

  if (!threadId) {
    return (
      <div className="flex flex-col h-full min-h-0 overflow-hidden border border-[#dbe4f0] rounded-[10px] bg-[#f8fafc] text-[#0f172a] font-mono text-[12px] flex items-center justify-center min-h-[120px] text-[#64748b]">
        Select a thread to view events.
      </div>
    );
  }

  const visibleError = loadError || error;

  return (
    <div className="flex flex-col h-full min-h-0 overflow-hidden border border-[#dbe4f0] rounded-[10px] bg-[#f8fafc] text-[#0f172a] font-mono text-[12px]">
      <div className="flex justify-between items-center gap-3 px-3.5 py-2.5 text-[#e2e8f0] bg-gradient-to-br from-[#0f172a] to-[#1e3a8a] border-b border-[#1e40af] [&_h3]:m-0 [&_h3]:text-white [&_h3]:text-[13px] [&_h3]:font-bold">
        <div>
          <h3>Thread Events</h3>
          <div className="mt-0.5 text-[#bfdbfe] text-[11px]">Thread #{threadId}</div>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={cn(pillClass, isConnected ? 'text-[#bbf7d0] bg-[rgba(34,197,94,0.2)]' : 'text-[#cbd5e1] bg-[rgba(148,163,184,0.2)]')}>
            {isConnected ? 'LIVE' : 'OFFLINE'}
          </span>
          <span className={cn(pillClass, 'text-[#cbd5e1] bg-[rgba(148,163,184,0.2)]')}>seq#{lastSequence}</span>
        </div>
      </div>

      {visibleError && <div className="px-3.5 py-2 text-[#991b1b] bg-[#fee2e2] border-b border-[#fecaca]">{visibleError.message}</div>}

      <div className="flex-1 min-h-0 overflow-y-auto p-2.5">
        {loading && filteredEvents.length === 0 && (
          <div className="flex items-center justify-center min-h-[120px] text-[#64748b]">Loading events...</div>
        )}
        {!loading && filteredEvents.length === 0 && (
          <div className="flex items-center justify-center min-h-[120px] text-[#64748b]">No events yet.</div>
        )}
        {filteredEvents.map((event) => {
          const evStatus = statusClass(event.status);
          return (
            <div
              key={`${event.sequence}-${event.id}`}
              className={cn(
                'mb-2 overflow-hidden border border-[#e2e8f0] border-l-[3px] border-l-[#94a3b8] rounded-lg bg-white',
                evStatus && STATUS_BORDER[evStatus],
              )}
            >
              <div className="flex items-center gap-1.5 px-2.5 py-2 flex-wrap">
                <span className="text-[13px]">{eventIcon(event.event_type)}</span>
                <span className={cn(pillClass, 'text-[#334155] bg-[#e2e8f0]')}>{event.event_type}</span>
                {event.status && (
                  <span className={cn(pillClass, evStatus ? STATUS_PILL[evStatus] : '')}>{event.status}</span>
                )}
                {event.tool_name && <span className={cn(pillClass, 'text-[#334155] bg-[#e2e8f0]')}>{event.tool_name}</span>}
                <span className={cn(pillClass, 'text-[#334155] bg-[#e2e8f0]')}>#{event.sequence}</span>
                <span className="ml-auto text-[#94a3b8] text-[10px]">{new Date(event.created_at).toLocaleTimeString()}</span>
              </div>
              {event.content && (
                <div className="px-2.5 pb-2 break-anywhere whitespace-pre-wrap text-[#334155] text-[11px]">{event.content}</div>
              )}
              {Object.keys(event.payload || {}).length > 0 && (
                <pre className="overflow-x-auto mx-2.5 mb-2 px-2 py-1.5 text-[#e2e8f0] bg-[#0f172a] rounded-md text-[10px]">
                  {JSON.stringify(event.payload, null, 2)}
                </pre>
              )}
            </div>
          );
        })}
        <div ref={endRef} />
      </div>
    </div>
  );
}
