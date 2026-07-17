import { useCallback, useEffect, useRef, useState } from 'react';
import { GLOBAL_CONFIG } from '../config';

// ── Internal types ──────────────────────────────────────────────────

type ParsedEvent<T> =
  | { kind: 'data'; data: T }
  | { kind: 'checkpoint'; sequence: number | undefined }
  | { kind: 'error'; message: string | undefined }
  | { kind: 'done' }
  | { kind: 'start' }
  | { kind: 'stats' }
  | { kind: 'unknown' };

// ── Internal helpers ────────────────────────────────────────────────

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function getMessageData(event: Event): string {
  if (event instanceof MessageEvent) {
    return typeof event.data === 'string' ? event.data : '{}';
  }
  return '{}';
}

// ── Public types ────────────────────────────────────────────────────

type SSEDoneHandler = () => void;
type SSECheckpointHandler = (sequence: number) => void;
type SSEErrorHandler = (error: Error) => void;

export interface UseSSEStreamOptions<T> {
  /** SSE endpoint URL path (relative to DJANGO_API_BASE, no leading slash). null = don't connect. */
  url: string | null;
  /** Initial events to populate the stream with */
  initialEvents?: T[];
  /** Auto-reconnect on 'done' event (default: true) */
  autoReconnect?: boolean;
  /** Max reconnection attempts before giving up (default: 5) */
  maxRetries?: number;
  /** Type guard: identifies whether a parsed JSON object is a data event of type T */
  isEventType: (data: Record<string, unknown>) => data is T & Record<string, unknown>;
  /** Additional named SSE event types to listen for (e.g. 'tool_call', 'graph_started') */
  namedEvents?: string[];
  /** Called when a checkpoint event is received */
  onCheckpoint?: SSECheckpointHandler;
  /** Called when the stream ends (done event) */
  onDone?: SSEDoneHandler;
  /** Called when a stream error occurs */
  onError?: SSEErrorHandler;
  /** Label for the data event type (e.g. 'thread_event', 'execution_event') — for documentation */
  eventDiscriminator: string;
  /** Fallback error message when the server doesn't provide one */
  errorMessage: string;
  /** Maximum number of events to keep in memory (default: 500). Older events are evicted.
   *  Historical events can still be fetched via paginated REST API (listEvents with after/limit). */
  maxEvents?: number;
}

export interface UseSSEStreamReturn<T> {
  events: T[];
  isConnected: boolean;
  error: Error | null;
  lastSequence: number;
  reconnect: (fromSequence?: number) => void;
  disconnect: () => void;
}

// ── Hook ────────────────────────────────────────────────────────────

export function useSSEStream<T extends { sequence: number }>(
  options: UseSSEStreamOptions<T>,
): UseSSEStreamReturn<T> {
  const {
    url,
    initialEvents = [],
    autoReconnect = true,
    maxRetries = 5,
    isEventType,
    namedEvents = [],
    onCheckpoint,
    onDone,
    onError,
    errorMessage,
    maxEvents = 500,
  } = options;

  // ── State ──

  const [events, setEvents] = useState<T[]>(initialEvents);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [lastSequence, setLastSequence] = useState(() =>
    Math.max(0, ...initialEvents.map((e) => e.sequence)),
  );

  // ── Refs ──

  const eventSourceRef = useRef<EventSource | null>(null);
  const retryCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const eventsRef = useRef<T[]>(initialEvents);
  const lastSequenceRef = useRef(lastSequence);

  // Callback refs — avoid re-creating connect/parseSSEEvent when these change
  const isEventTypeRef = useRef(isEventType);
  isEventTypeRef.current = isEventType;
  const namedEventsRef = useRef(namedEvents);
  namedEventsRef.current = namedEvents;
  const onCheckpointRef = useRef(onCheckpoint);
  onCheckpointRef.current = onCheckpoint;
  const onDoneRef = useRef(onDone);
  onDoneRef.current = onDone;
  const onErrorRef = useRef(onError);
  onErrorRef.current = onError;

  // ── Sync initialEvents prop → state ──

  useEffect(() => {
    eventsRef.current = initialEvents;
    const sequence = Math.max(0, ...initialEvents.map((e) => e.sequence));
    lastSequenceRef.current = sequence;
    setEvents(initialEvents);
    setLastSequence(sequence);
  }, [initialEvents]);

  // ── Add event with deduplication + sort + eviction ──

  const addEvent = useCallback((event: T) => {
    if (eventsRef.current.some((existing) => existing.sequence === event.sequence)) return;
    const next = [...eventsRef.current, event].sort((a, b) => a.sequence - b.sequence);
    if (next.length > maxEvents) {
      eventsRef.current = next.slice(-maxEvents);
    } else {
      eventsRef.current = next;
    }
    lastSequenceRef.current = event.sequence;
    setEvents(eventsRef.current);
    setLastSequence(event.sequence);
  }, [maxEvents]);

  // ── Parse raw SSE text into typed event ──

  const parseSSEEvent = useCallback((eventType: string, dataStr: string): ParsedEvent<T> => {
    try {
      const parsed = JSON.parse(dataStr);
      if (!isRecord(parsed)) {
        return { kind: 'unknown' };
      }

      // Data event — identified by the caller-supplied type guard
      if (isEventTypeRef.current(parsed)) {
        return { kind: 'data', data: parsed };
      }

      // Control events
      if (eventType === 'checkpoint' && parsed.type === 'checkpoint') {
        return {
          kind: 'checkpoint',
          sequence: typeof parsed.sequence === 'number' ? parsed.sequence : undefined,
        };
      }
      if (eventType === 'stats' && parsed.elapsed_ms !== undefined) {
        return { kind: 'stats' };
      }
      if (eventType === 'error' && parsed.error) {
        return {
          kind: 'error',
          message: typeof parsed.error === 'string' ? parsed.error : undefined,
        };
      }
      if (eventType === 'start' && parsed.status === 'started') {
        return { kind: 'start' };
      }
      return { kind: 'unknown' };
    } catch {
      if (eventType === 'done' && dataStr === '[DONE]') {
        return { kind: 'done' };
      }
      return { kind: 'unknown' };
    }
  }, []);

  // ── Disconnect & cleanup ──

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

  // ── Connect to SSE endpoint ──

  const connect = useCallback(
    (resumeFromSequence = 0) => {
      if (!url) return;

      disconnect();

      const fullUrl = new URL(
        `${GLOBAL_CONFIG.DJANGO_API_BASE}/${url}`,
        window.location.origin,
      );
      if (resumeFromSequence > 0) {
        fullUrl.searchParams.set('last_sequence', String(resumeFromSequence));
      }

      const eventSource = new EventSource(fullUrl.toString());
      eventSourceRef.current = eventSource;

      // Stream started
      eventSource.addEventListener('start', () => {
        setIsConnected(true);
        setError(null);
        retryCountRef.current = 0;
      });

      // Checkpoint — update sequence for resume
      eventSource.addEventListener('checkpoint', (rawEvent: Event) => {
        const parsed = parseSSEEvent('checkpoint', getMessageData(rawEvent));
        if (parsed.kind === 'checkpoint' && parsed.sequence !== undefined) {
          lastSequenceRef.current = parsed.sequence;
          setLastSequence(parsed.sequence);
          onCheckpointRef.current?.(parsed.sequence);
        }
      });

      // Done — close and optionally reconnect with exponential backoff
      eventSource.addEventListener('done', () => {
        eventSource.close();
        setIsConnected(false);
        onDoneRef.current?.();

        if (autoReconnect && retryCountRef.current < maxRetries) {
          retryCountRef.current += 1;
          const backoffMs = Math.min(1000 * Math.pow(2, retryCountRef.current - 1), 30000);
          reconnectTimeoutRef.current = setTimeout(
            () => connect(lastSequenceRef.current),
            backoffMs,
          );
        }
      });

      // Error — parse server error message, close connection
      eventSource.addEventListener('error', (rawEvent: Event) => {
        const parsed = parseSSEEvent('error', getMessageData(rawEvent));
        if (parsed.kind === 'error') {
          const err = new Error(parsed.message || errorMessage);
          setError(err);
          onErrorRef.current?.(err);
        }
        eventSource.close();
        setIsConnected(false);
      });

      // Default messages (unnamed SSE events)
      eventSource.onmessage = (rawEvent: MessageEvent) => {
        const parsed = parseSSEEvent(rawEvent.type, rawEvent.data);
        if (parsed.kind !== 'data') return;
        addEvent(parsed.data);
      };

      // Named event types (e.g. scanner_dispatched, graph_started, etc.)
      for (const eventName of namedEventsRef.current) {
        eventSource.addEventListener(eventName, (rawEvent: Event) => {
          const parsed = parseSSEEvent(eventName, getMessageData(rawEvent));
          if (parsed.kind !== 'data') return;
          addEvent(parsed.data);
        });
      }
    },
    [url, disconnect, parseSSEEvent, autoReconnect, maxRetries, errorMessage, addEvent],
  );

  // ── Manual reconnect (resets retry counter) ──

  const reconnect = useCallback(
    (fromSequence?: number) => {
      retryCountRef.current = 0;
      connect(fromSequence ?? lastSequenceRef.current);
    },
    [connect],
  );

  // ── Auto-connect on mount / URL change; cleanup on unmount ──

  useEffect(() => {
    connect(lastSequenceRef.current);
    return disconnect;
  }, [connect, disconnect]);

  return { events, isConnected, error, lastSequence, reconnect, disconnect };
}
