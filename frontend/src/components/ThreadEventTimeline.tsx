import { useEffect, useMemo, useRef, useState } from 'react';
import { assistantApi, type ThreadEvent } from '../services/assistantApi';
import { useThreadEventStream } from '../hooks/useThreadEventStream';
import './ThreadEventTimeline.css';

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

  if (!threadId) {
    return <div className="tet empty">Select a thread to view events.</div>;
  }

  const visibleError = loadError || error;

  return (
    <div className="tet">
      <div className="tet-header">
        <div>
          <h3>Thread Events</h3>
          <div className="tet-subtitle">Thread #{threadId}</div>
        </div>
        <div className="tet-status-row">
          <span className={`tet-live ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? 'LIVE' : 'OFFLINE'}
          </span>
          <span className="tet-sequence">seq#{lastSequence}</span>
        </div>
      </div>

      {visibleError && <div className="tet-error">{visibleError.message}</div>}

      <div className="tet-list">
        {loading && filteredEvents.length === 0 && (
          <div className="tet-empty">Loading events...</div>
        )}
        {!loading && filteredEvents.length === 0 && (
          <div className="tet-empty">No events yet.</div>
        )}
        {filteredEvents.map((event) => (
          <div key={`${event.sequence}-${event.id}`} className={`tet-event ${statusClass(event.status)}`}>
            <div className="tet-event-header">
              <span className="tet-event-icon">{eventIcon(event.event_type)}</span>
              <span className="tet-event-type">{event.event_type}</span>
              {event.status && <span className={`tet-pill ${statusClass(event.status)}`}>{event.status}</span>}
              {event.tool_name && <span className="tet-tool">{event.tool_name}</span>}
              <span className="tet-seq">#{event.sequence}</span>
              <span className="tet-time">{new Date(event.created_at).toLocaleTimeString()}</span>
            </div>
            {event.content && (
              <div className="tet-event-content">{event.content}</div>
            )}
            {Object.keys(event.payload || {}).length > 0 && (
              <pre className="tet-event-payload">{JSON.stringify(event.payload, null, 2)}</pre>
            )}
          </div>
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
