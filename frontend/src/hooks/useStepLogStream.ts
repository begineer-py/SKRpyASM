/**
 * useStepLogStream Hook
 * 
 * Manages real-time streaming of Step execution logs via Server-Sent Events.
 * Provides automatic reconnection, sequence-based resumption, and structured log parsing.
 * 
 * Usage:
 * ```tsx
 * const { logs, isConnected, error } = useStepLogStream(stepId);
 * 
 * logs.forEach(log => {
 *   console.log(`[${log.level}] ${log.message}`);
 * });
 * ```
 */

import { useEffect, useState, useRef, useCallback } from 'react';
import { GLOBAL_CONFIG } from '../config';

/**
 * Represents a single StepLog entry from the backend
 */
export interface StepLog {
  id: number;
  step_id: number;
  sequence: number;
  level: 'INFO' | 'DEBUG' | 'WARN' | 'ERROR' | 'AI_THOUGHT' | 'ACTION' | 'RESULT';
  tag: 'SKILL_EXEC' | 'COMMAND' | 'API_CALL' | 'SCAN' | 'PARSE' | 'DECISION' | 'ERROR_HANDLING' | 'STATE_UPDATE' | 'CHECKPOINT';
  message: string;
  action_status?: 'STARTED' | 'IN_PROGRESS' | 'SUCCESS' | 'FAILED' | 'PARTIAL' | 'SKIPPED';
  execution_time_ms?: number;
  created_at: string;
}

/**
 * Internal event type for SSE parsing
 */
interface SSEEvent {
  type: 'log' | 'checkpoint' | 'stats' | 'done' | 'error' | 'start' | 'unknown';
  data: any;
}

/**
 * Hook return type
 */
export interface UseStepLogStreamReturn {
  /** Array of logs received so far */
  logs: StepLog[];
  
  /** Whether the EventSource is currently connected */
  isConnected: boolean;
  
  /** Current error state, if any */
  error: Error | null;
  
  /** Latest checkpoint sequence number */
  lastSequence: number;
  
  /** Manually trigger reconnection with optional resume point */
  reconnect: (fromSequence?: number) => void;
  
  /** Disconnect and cleanup */
  disconnect: () => void;
}

/**
 * Hook: useStepLogStream
 * 
 * Establishes and manages an EventSource connection to stream Step logs.
 * Handles reconnections, sequence-based resumption, and automatic cleanup.
 * 
 * @param stepId - The Step ID to stream logs for
 * @param autoReconnect - Whether to automatically reconnect on error (default: true)
 * @param maxRetries - Maximum number of reconnection attempts (default: 5)
 * 
 * @returns Object containing logs, connection state, and control methods
 */
export function useStepLogStream(
  stepId: number | null,
  autoReconnect: boolean = true,
  maxRetries: number = 5
): UseStepLogStreamReturn {
  const [logs, setLogs] = useState<StepLog[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [lastSequence, setLastSequence] = useState(0);
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const retryCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const logsRef = useRef<StepLog[]>([]);
  const lastSequenceRef = useRef(0);

  /**
   * Parse SSE event based on event type and data
   */
  const parseSSEEvent = useCallback((eventType: string, dataStr: string): SSEEvent => {
    try {
      const data = JSON.parse(dataStr);
      
      if (eventType === 'log' && data.id && data.step_id) {
        // Valid StepLog entry
        return { type: 'log', data: data as StepLog };
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
      
      if (eventType === 'done' && dataStr === '[DONE]') {
        return { type: 'done', data: null };
      }
      
      return { type: 'unknown', data };
    } catch {
      return { type: 'unknown', data: dataStr };
    }
  }, []);

  /**
   * Connect to the SSE endpoint
   */
  const connect = useCallback((resumeFromSequence: number = 0) => {
    if (!stepId || stepId <= 0) {
      setError(new Error('Invalid step ID'));
      return;
    }

    // Close any existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const url = new URL(
      `${GLOBAL_CONFIG.DJANGO_API_BASE}/v1/steps/${stepId}/logs/stream/`,
      window.location.origin
    );
    
    if (resumeFromSequence > 0) {
      url.searchParams.set('last_sequence', String(resumeFromSequence));
    }

    try {
      const eventSource = new EventSource(url.toString());

      eventSource.addEventListener('start', (e) => {
        console.log('[StepLogStream] Connection established for step', stepId);
        setIsConnected(true);
        setError(null);
        retryCountRef.current = 0;
      });

      eventSource.addEventListener('log', (e) => {
        const event = parseSSEEvent('log', e.data);
        if (event.type === 'log') {
          const log = event.data as StepLog;
          logsRef.current = [...logsRef.current, log];
          lastSequenceRef.current = log.sequence;
          setLogs([...logsRef.current]);
          setLastSequence(log.sequence);
        }
      });

      eventSource.addEventListener('checkpoint', (e) => {
        const event = parseSSEEvent('checkpoint', e.data);
        if (event.type === 'checkpoint') {
          lastSequenceRef.current = event.data.sequence;
          setLastSequence(event.data.sequence);
          console.log(`[StepLogStream] Checkpoint: sequence=${event.data.sequence}`);
        }
      });

      eventSource.addEventListener('stats', (e) => {
        const event = parseSSEEvent('stats', e.data);
        if (event.type === 'stats') {
          console.log(`[StepLogStream] Stats: elapsed=${event.data.elapsed_ms}ms`);
        }
      });

      eventSource.addEventListener('done', (e) => {
        console.log('[StepLogStream] Stream completed');
        eventSource.close();
        setIsConnected(false);
      });

      eventSource.addEventListener('error', (e) => {
        const event = parseSSEEvent('error', e.data);
        if (event.type === 'error') {
          const errorMsg = event.data.error || 'Unknown error';
          console.error('[StepLogStream] Error:', errorMsg);
          setError(new Error(errorMsg));
        } else {
          console.error('[StepLogStream] Connection error');
          setError(new Error('Connection error'));
        }
        eventSource.close();
        setIsConnected(false);
      });

      // Handle connection errors (network issues, etc.)
      eventSource.onerror = () => {
        if (eventSource.readyState === EventSource.CLOSED) {
          console.warn('[StepLogStream] EventSource closed');
          setIsConnected(false);

          // Auto-reconnect with exponential backoff
          if (autoReconnect && retryCountRef.current < maxRetries) {
            retryCountRef.current++;
            const backoffMs = Math.min(1000 * Math.pow(2, retryCountRef.current - 1), 30000);
            console.warn(
              `[StepLogStream] Will reconnect in ${backoffMs}ms (attempt ${retryCountRef.current}/${maxRetries})`
            );

            reconnectTimeoutRef.current = setTimeout(() => {
              console.log(`[StepLogStream] Reconnecting... (attempt ${retryCountRef.current})`);
              connect(lastSequenceRef.current);
            }, backoffMs);
          } else if (retryCountRef.current >= maxRetries) {
            setError(new Error(`Failed to connect after ${maxRetries} attempts`));
          }
        }
      };

      eventSourceRef.current = eventSource;
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Unknown error';
      console.error('[StepLogStream] Failed to create EventSource:', errMsg);
      setError(new Error(errMsg));
      setIsConnected(false);
    }
  }, [stepId, autoReconnect, maxRetries, parseSSEEvent]);

  /**
   * Manually reconnect
   */
  const reconnect = useCallback((fromSequence?: number) => {
    retryCountRef.current = 0;
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    connect(fromSequence ?? lastSequenceRef.current);
  }, [connect]);

  /**
   * Disconnect and cleanup
   */
  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    setIsConnected(false);
    setLogs([]);
    logsRef.current = [];
    lastSequenceRef.current = 0;
    retryCountRef.current = 0;
  }, []);

  /**
   * Setup effect: connect on mount or when stepId changes
   */
  useEffect(() => {
    if (stepId && stepId > 0) {
      connect();
    }

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [stepId, connect]);

  return {
    logs,
    isConnected,
    error,
    lastSequence,
    reconnect,
    disconnect,
  };
}

// Explicit re-exports for better module resolution
export type { StepLog, UseStepLogStreamReturn };
