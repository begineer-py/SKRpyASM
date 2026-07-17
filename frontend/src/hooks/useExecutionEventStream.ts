import { useSSEStream } from './useSSEStream';
import type { ExecutionEvent } from '../services/executionApi';

export interface UseExecutionEventStreamReturn {
  events: ExecutionEvent[];
  isConnected: boolean;
  error: Error | null;
  lastSequence: number;
  reconnect: (fromSequence?: number) => void;
  disconnect: () => void;
}

/**
 * SSE stream hook for execution (graph) events.
 * Delegates to the generic useSSEStream hook.
 */
export function useExecutionEventStream(
  graphId: number | null,
  initialEvents: ExecutionEvent[] = [],
  autoReconnect = true,
  maxRetries = 5,
  maxEvents = 500,
): UseExecutionEventStreamReturn {
  const url = (graphId && graphId > 0) ? `core/executions/${graphId}/events/stream/` : null;

  return useSSEStream({
    url,
    initialEvents,
    autoReconnect,
    maxRetries,
    maxEvents,
    eventDiscriminator: 'execution_event',
    errorMessage: 'Execution event stream error',
    isEventType: (data): data is ExecutionEvent & Record<string, unknown> =>
      !!(data.id && data.graph_id && data.sequence && data.event_type),
    namedEvents: [
      'graph_started',
      'graph_completed',
      'graph_failed',
      'node_started',
      'node_waiting',
      'node_completed',
      'node_failed',
    ],
  });
}
