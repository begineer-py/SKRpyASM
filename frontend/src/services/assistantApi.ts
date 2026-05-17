import axios from 'axios';
import { GLOBAL_CONFIG } from '../config';

const api = axios.create({
  baseURL: `${GLOBAL_CONFIG.DJANGO_API_BASE}/assistant`,
});

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
  getThreads: async (): Promise<any[]> => {
    const response = await api.get('/threads/');
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
};
