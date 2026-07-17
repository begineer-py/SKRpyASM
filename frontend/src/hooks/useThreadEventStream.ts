import { useSSEStream } from './useSSEStream';
import type { ThreadEvent } from '../services/assistantApi';

export interface UseThreadEventStreamReturn {
  events: ThreadEvent[];
  isConnected: boolean;
  error: Error | null;
  lastSequence: number;
  reconnect: (fromSequence?: number) => void;
  disconnect: () => void;
}

/**
 * SSE stream hook for thread-level events.
 * Delegates to the generic useSSEStream hook.
 */
export function useThreadEventStream(
  threadId: number | string | null,
  initialEvents: ThreadEvent[] = [],
  autoReconnect = true,
  maxRetries = 5,
  maxEvents = 500,
): UseThreadEventStreamReturn {
  const url = threadId ? `assistant/threads/${threadId}/events/stream/` : null;

  return useSSEStream({
    url,
    initialEvents,
    autoReconnect,
    maxRetries,
    maxEvents,
    eventDiscriminator: 'thread_event',
    errorMessage: 'Thread event stream error',
    isEventType: (data): data is ThreadEvent & Record<string, unknown> =>
      !!(data.event_type && data.sequence !== undefined && data.thread_id),
    namedEvents: [
      'scanner_dispatched',
      'scanner_completed',
      'scanner_failed',
      'tool_call',
      'tool_result',
      'tool_error',
      'sandbox_dispatched',
      'sandbox_completed',
      'sandbox_failed',
    ],
  });
}
