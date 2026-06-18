import axios from 'axios';
import { GLOBAL_CONFIG } from '../config';

const api = axios.create({
  baseURL: `${GLOBAL_CONFIG.DJANGO_API_BASE}/assistant`,
});

export interface ThreadEvent {
  id: number;
  thread_id: number;
  event_type: string;
  node_name: string | null;
  tool_name: string | null;
  status: string | null;
  content: string;
  payload: Record<string, unknown>;
  sequence: number;
  created_at: string;
}

export const assistantApi = {
  // Create a new thread assigned to hacker_assistant_agent
  createThread: async (name?: string) => {
    const response = await api.post('/threads/', {
      assistant_id: 'hacker_assistant_agent',
      ...(name ? { name } : {}),
    });
    return response.data;
  },

  // Rename/update a thread
  updateThread: async (threadId: number | string, payload: { name: string }) => {
    const response = await api.patch(`/threads/${threadId}/`, payload);
    return response.data;
  },

  // Get messages for a thread
  getMessages: async (threadId: number | string): Promise<any[]> => {
    const response = await api.get(`/threads/${threadId}/messages/`);
    return Array.isArray(response.data) ? response.data : [];
  },

  // Post a message (blocking — kept for backward compatibility / fallback)
  postMessage: async (threadId: number | string, content: string) => {
    const response = await api.post(`/threads/${threadId}/messages/`, {
      assistant_id: 'hacker_assistant_agent',
      content,
    });
    return response.data;
  },

  /**
   * Stream a message via SSE.
   * Calls GET /api/assistant/threads/{threadId}/messages/stream/
   * 
   * @param threadId  - The thread to post the message in
   * @param content   - The user message text
   * @param onChunk   - Called with each streamed text token
   * @param onDone    - Called when the stream finishes successfully
   * @param onError   - Called on stream error (backend exception forwarded as SSE event)
   * @returns a cleanup function to abort the EventSource
   */
  streamMessage: (
    threadId: number | string,
    content: string,
    assistantId: string = 'hacker_assistant_agent',
    onChunk: (chunk: string) => void,
    onDone: () => void,
    onError: (err: string) => void,
    onStats?: (elapsedMs: number) => void,
  ): (() => void) => {
    const params = new URLSearchParams({
      assistant_id: assistantId,
      content,
    });
    const url = `${GLOBAL_CONFIG.DJANGO_API_BASE}/assistant/threads/${threadId}/messages/stream/?${params.toString()}`;
    const es = new EventSource(url);

    // Raw token chunk — the default `message` event
    es.onmessage = (e) => {
      if (e.data && e.data !== '[DONE]') {
        onChunk(e.data);
      }
    };

    // Custom events from the backend
    es.addEventListener('start', () => { /* streaming started */ });

    es.addEventListener('stats', (e: MessageEvent) => {
      try {
        const payload = JSON.parse(e.data);
        if (payload.elapsed_ms !== undefined && onStats) {
          onStats(payload.elapsed_ms);
        }
      } catch { /* ignore */ }
    });

    es.addEventListener('done', () => {
      es.close();
      onDone();
    });

    es.addEventListener('error', (e: MessageEvent) => {
      es.close();
      try {
        const payload = JSON.parse(e.data);
        onError(payload.error || 'Unknown streaming error');
      } catch {
        onError('Stream error (unparseable)');
      }
    });

    // Network-level error (e.g., server unreachable)
    es.onerror = () => {
      es.close();
      onError('Connection lost — the server may have crashed or timed out.');
      onDone();
    };

    // Return a cleanup function
    return () => es.close();
  },

  // Get all threads
  getThreads: async (params?: { assistant_id?: string; target_id?: number; include_hidden?: boolean }): Promise<any[]> => {
    const response = await api.get('/threads/', { params });
    return Array.isArray(response.data) ? response.data : [];
  },

  // Delete a thread
  deleteThread: async (threadId: number | string) => {
    const response = await api.delete(`/threads/${threadId}/`);
    return response.data;
  },

  // Delete a message in a thread
  deleteMessage: async (threadId: number | string, messageId: number | string) => {
    const response = await api.delete(`/threads/${threadId}/messages/${messageId}/`);
    return response.data;
  },

  // Bind a target to a thread (also callable by the AI agent via tools)
  bindTarget: async (threadId: number | string, targetId: number) => {
    const response = await api.patch(`/threads/${threadId}/bind_target/`, { target_id: targetId });
    return response.data;
  },

  // Remove target binding from a thread
  unbindTarget: async (threadId: number | string) => {
    const response = await api.delete(`/threads/${threadId}/bind_target/`);
    return response.data;
  },

  // Get thread events (ThreadEvent records)
  getThreadEvents: async (threadId: number | string, after?: number): Promise<ThreadEvent[]> => {
    const params: Record<string, unknown> = {};
    if (after !== undefined) params.after = after;
    const response = await api.get(`/threads/${threadId}/events/`, { params });
    return Array.isArray(response.data) ? response.data : [];
  },

  /**
   * 持久化訂閱：監聽指定 thread 的 Message 表變更（新訊息寫入 DB）。
   *
   * 與 streamMessage 的差異：
   *   - streamMessage 是一次性請求-回應（送出訊息 → 串流回覆 → 關閉）
   *   - 本方法在 mount 時開啟、unmount 時關閉，持續接收「新訊息已寫入 DB」事件
   *
   * 用途：解決「刷新時 AI 回應尚未寫入 DB → 永遠看不到」的問題。
   * 當背景 graph 完成並寫入 AI message 時，前端會即時收到通知並重新載入。
   *
   * @param threadId    目標 thread ID
   * @param onNewMessage 收到 message_created 事件時的 callback（攜帶新 message summary）
   * @returns cleanup 函式，呼叫以關閉 EventSource
   */
  streamMessageEvents: (
    threadId: number | string,
    onNewMessage: (summary: { id: number; thread_id: number; role: string; created_at: string }) => void,
  ): (() => void) => {
    const url = `${GLOBAL_CONFIG.DJANGO_API_BASE}/assistant/threads/${threadId}/messages/events/stream/`;
    const es = new EventSource(url);

    es.addEventListener('message_created', (e: MessageEvent) => {
      try {
        const payload = JSON.parse(e.data);
        onNewMessage(payload);
      } catch {
        /* ignore malformed payload */
      }
    });

    // checkpoint / stats / start 事件不需處理；error 由 onerror 兜底
    es.onerror = () => {
      // EventSource 會自動重連；這裡不自動關閉，讓瀏覽器重連機制處理
    };

    return () => es.close();
  },
};
