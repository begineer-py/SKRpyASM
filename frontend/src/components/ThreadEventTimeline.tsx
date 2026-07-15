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
  started: 'text-[#7dd3fc] bg-[rgba(14,165,233,0.16)]',
  running: 'text-[#7dd3fc] bg-[rgba(14,165,233,0.16)]',
  completed: 'text-[#86efac] bg-[rgba(34,197,94,0.16)]',
  succeeded: 'text-[#86efac] bg-[rgba(34,197,94,0.16)]',
  failed: 'text-[#fca5a5] bg-[rgba(239,68,68,0.16)]',
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

  const pillClass = 'inline-flex items-center rounded-full px-2 py-[3px] text-[11px] font-bold leading-tight';

  if (!threadId) {
    return (
      <div className="flex flex-col h-full min-h-0 overflow-hidden border border-[rgba(148,163,184,0.18)] rounded-[12px] bg-[#080d1b] text-[#dbeafe] font-mono text-[14px] flex items-center justify-center min-h-[160px] text-[#94a3b8]">
        Select a thread to view events.
      </div>
    );
  }

  const visibleError = loadError || error;

  return (
    <div className="flex flex-col h-full min-h-0 overflow-hidden border border-[rgba(148,163,184,0.18)] rounded-[12px] bg-[#080d1b] text-[#dbeafe] font-mono text-[14px]">
      <div className="flex justify-between items-center gap-3 px-4 py-3.5 text-[#e2e8f0] bg-gradient-to-br from-[#0f172a] to-[#1e3a8a] border-b border-[#1e40af] [&_h3]:m-0 [&_h3]:text-white [&_h3]:text-[15px] [&_h3]:font-bold">
        <div>
          <h3>Thread Events</h3>
          <div className="mt-1 text-[#bfdbfe] text-[13px]">Thread #{threadId}</div>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={cn(pillClass, isConnected ? 'text-[#bbf7d0] bg-[rgba(34,197,94,0.2)]' : 'text-[#cbd5e1] bg-[rgba(148,163,184,0.2)]')}>
            {isConnected ? 'LIVE' : 'OFFLINE'}
          </span>
          <span className={cn(pillClass, 'text-[#cbd5e1] bg-[rgba(148,163,184,0.2)]')}>seq#{lastSequence}</span>
        </div>
      </div>

      {visibleError && <div className="px-4 py-2.5 text-[#fca5a5] bg-[rgba(239,68,68,0.12)] border-b border-[rgba(248,113,113,0.24)]">{visibleError.message}</div>}

      <div className="flex-1 min-h-0 overflow-y-auto p-2.5">
        {loading && filteredEvents.length === 0 && (
          <div className="flex items-center justify-center min-h-[160px] text-[#94a3b8]">Loading events...</div>
        )}
        {!loading && filteredEvents.length === 0 && (
          <div className="flex items-center justify-center min-h-[160px] text-[#94a3b8]">No events yet.</div>
        )}
        {filteredEvents.map((event) => {
          const evStatus = statusClass(event.status);
          return (
            <div
              key={`${event.sequence}-${event.id}`}
              className={cn(
                'mb-3 overflow-hidden border border-[rgba(148,163,184,0.16)] border-l-4 border-l-[#64748b] rounded-[10px] bg-[#0d1424]',
                evStatus && STATUS_BORDER[evStatus],
              )}
            >
              <div className="flex items-center gap-2 px-3.5 py-3 flex-wrap">
                <span className="text-sm">{eventIcon(event.event_type)}</span>
                <span className={cn(pillClass, 'text-[#cbd5e1] bg-[rgba(148,163,184,0.14)]')}>{event.event_type}</span>
                {event.status && (
                  <span className={cn(pillClass, evStatus ? STATUS_PILL[evStatus] : '')}>{event.status}</span>
                )}
                {event.tool_name && <span className={cn(pillClass, 'text-[#cbd5e1] bg-[rgba(148,163,184,0.14)]')}>{event.tool_name}</span>}
                <span className={cn(pillClass, 'text-[#cbd5e1] bg-[rgba(148,163,184,0.14)]')}>#{event.sequence}</span>
                <span className="ml-auto text-[#94a3b8] text-[12px]">{new Date(event.created_at).toLocaleTimeString()}</span>
              </div>
              {event.content && (
                <div className="px-3.5 pb-3 break-anywhere whitespace-pre-wrap text-[#cbd5e1] text-[14px] leading-6">{event.content}</div>
              )}
              {Object.keys(event.payload || {}).length > 0 && (
                <pre className="overflow-x-auto mx-3.5 mb-3 px-3 py-2 text-[#e2e8f0] bg-[#050814] border border-[rgba(148,163,184,0.12)] rounded-md text-[12px] leading-5">
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
