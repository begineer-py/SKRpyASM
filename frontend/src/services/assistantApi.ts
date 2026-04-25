import axios from 'axios';
import { GLOBAL_CONFIG } from '../config';

const api = axios.create({
  baseURL: `${GLOBAL_CONFIG.DJANGO_API_BASE}/assistant`,
  // django_ai_assistant might require auth headers depending on config.
  // The user set allow_all and owns_thread, but testing without auth first.
});

export const assistantApi = {
  // Create a new thread assigned to hacker_assistant_agent
  createThread: async () => {
    const response = await api.post('/threads/', {
      assistant_id: 'hacker_assistant_agent'
    });
    return response.data;
  },

  // Get messages for a thread
  getMessages: async (threadId: number | string) => {
    const response = await api.get(`/threads/${threadId}/messages/`);
    return response.data;
  },

  // Post a message (this usually triggers an assistant run and returns the assistant's reply)
  postMessage: async (threadId: number | string, content: string) => {
    const response = await api.post(`/threads/${threadId}/messages/`, {
      assistant_id: 'hacker_assistant_agent',
      content,
    });
    return response.data;
  },

  // Get all threads
  getThreads: async () => {
    const response = await api.get('/threads/');
    return response.data;
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
  }
};
