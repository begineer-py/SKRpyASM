import { useCallback, useEffect, useRef, useState } from 'react';
import { GLOBAL_CONFIG } from '../config';
import type { ThreadEvent } from '../services/assistantApi';

type StreamEventType = 'thread_event' | 'checkpoint' | 'stats' | 'done' | 'error' | 'start' | 'unknown';

interface ParsedStreamEvent {
  type: StreamEventType;
  data: unknown;
}

export interface UseThreadEventStreamReturn {
  events: ThreadEvent[];
  isConnected: boolean;
  error: Error | null;
  lastSequence: number;
  reconnect: (fromSequence?: number) => void;
  disconnect: () => void;
}

export function useThreadEventStream(
  threadId: number | string | null,
  initialEvents: ThreadEvent[] = [],
  autoReconnect = true,
  maxRetries = 5,
): UseThreadEventStreamReturn {
  const [events, setEvents] = useState<ThreadEvent[]>(initialEvents);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [lastSequence, setLastSequence] = useState(() => Math.max(0, ...initialEvents.map((e) => e.sequence)));

  const eventSourceRef = useRef<EventSource | null>(null);
  const retryCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const eventsRef = useRef<ThreadEvent[]>(initialEvents);
  const lastSequenceRef = useRef(lastSequence);

  useEffect(() => {
    eventsRef.current = initialEvents;
    const sequence = Math.max(0, ...initialEvents.map((e) => e.sequence));
    lastSequenceRef.current = sequence;
    setEvents(initialEvents);
    setLastSequence(sequence);
  }, [initialEvents]);

  const parseSSEEvent = useCallback((eventType: string, dataStr: string): ParsedStreamEvent => {
    try {
      const data = JSON.parse(dataStr) as Record<string, unknown>;

      if (data.event_type && data.sequence !== undefined && data.thread_id) {
        return { type: 'thread_event', data: data as unknown as ThreadEvent };
      }
      if (eventType === 'checkpoint' && data.type === 'checkpoint') {
        return { type: 'checkpoint', data };
      }
      if (eventType === 'stats' && data.elapsed_ms !== undefined) {
        return { type: 'stats', data };
      }
      if (eventType === 'error' && data.error) {
        return { type: 'error', data };
      }
      if (eventType === 'start' && data.status === 'started') {
        return { type: 'start', data };
      }
      return { type: 'unknown', data };
    } catch {
      if (eventType === 'done' && dataStr === '[DONE]') {
        return { type: 'done', data: null };
      }
      return { type: 'unknown', data: dataStr };
    }
  }, []);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const connect = useCallback((resumeFromSequence = 0) => {
    if (!threadId) return;

    disconnect();

    const url = new URL(
      `${GLOBAL_CONFIG.DJANGO_API_BASE}/assistant/threads/${threadId}/events/stream/`,
      window.location.origin,
    );
    if (resumeFromSequence > 0) {
      url.searchParams.set('last_sequence', String(resumeFromSequence));
    }

    const eventSource = new EventSource(url.toString());
    eventSourceRef.current = eventSource;

    eventSource.addEventListener('start', () => {
      setIsConnected(true);
      setError(null);
      retryCountRef.current = 0;
    });

    eventSource.addEventListener('checkpoint', (rawEvent: Event) => {
      const parsed = parseSSEEvent('checkpoint', (rawEvent as MessageEvent).data);
      if (parsed.type === 'checkpoint') {
        const data = parsed.data as { sequence?: number };
        if (typeof data.sequence === 'number') {
          lastSequenceRef.current = data.sequence;
          setLastSequence(data.sequence);
        }
      }
    });

    eventSource.addEventListener('done', () => {
      eventSource.close();
      setIsConnected(false);

      if (autoReconnect && retryCountRef.current < maxRetries) {
        retryCountRef.current += 1;
        const backoffMs = Math.min(1000 * Math.pow(2, retryCountRef.current - 1), 30000);
        reconnectTimeoutRef.current = setTimeout(() => connect(lastSequenceRef.current), backoffMs);
      }
    });

    eventSource.addEventListener('error', (rawEvent: Event) => {
      const parsed = parseSSEEvent('error', (rawEvent as MessageEvent).data || '{}');
      if (parsed.type === 'error') {
        const data = parsed.data as { error?: string };
        setError(new Error(data.error || 'Thread event stream error'));
      }
      eventSource.close();
      setIsConnected(false);
    });

    eventSource.onmessage = (rawEvent: MessageEvent) => {
      const parsed = parseSSEEvent(rawEvent.type, rawEvent.data);
      if (parsed.type !== 'thread_event') return;

      const event = parsed.data as ThreadEvent;
      if (eventsRef.current.some((existing) => existing.sequence === event.sequence)) return;
      eventsRef.current = [...eventsRef.current, event].sort((a, b) => a.sequence - b.sequence);
      lastSequenceRef.current = event.sequence;
      setEvents(eventsRef.current);
      setLastSequence(event.sequence);
    };

    const namedEventTypes = [
      'scanner_dispatched', 'scanner_completed', 'scanner_failed',
      'tool_call', 'tool_result', 'tool_error',
      'sandbox_dispatched', 'sandbox_completed', 'sandbox_failed',
    ];
    for (const eventName of namedEventTypes) {
      eventSource.addEventListener(eventName, (rawEvent: Event) => {
        const parsed = parseSSEEvent(eventName, (rawEvent as MessageEvent).data);
        if (parsed.type !== 'thread_event') return;
        const event = parsed.data as ThreadEvent;
        if (eventsRef.current.some((existing) => existing.sequence === event.sequence)) return;
        eventsRef.current = [...eventsRef.current, event].sort((a, b) => a.sequence - b.sequence);
        lastSequenceRef.current = event.sequence;
        setEvents(eventsRef.current);
        setLastSequence(event.sequence);
      });
    }
  }, [autoReconnect, disconnect, maxRetries, parseSSEEvent, threadId]);

  const reconnect = useCallback((fromSequence?: number) => {
    retryCountRef.current = 0;
    connect(fromSequence ?? lastSequenceRef.current);
  }, [connect]);

  useEffect(() => {
    connect(lastSequenceRef.current);
    return disconnect;
  }, [connect, disconnect]);

  return { events, isConnected, error, lastSequence, reconnect, disconnect };
}
