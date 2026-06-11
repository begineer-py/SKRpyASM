import axios from 'axios';
import { GLOBAL_CONFIG } from '../config';

const api = axios.create({
  baseURL: `${GLOBAL_CONFIG.DJANGO_API_BASE}/core`,
});

export interface ExecutionGraph {
  id: number;
  thread_id?: number | null;
  assistant_id: string;
  run_id?: string | null;
  title: string;
  status: string;
  metadata: Record<string, unknown>;
  started_at: string;
  updated_at: string;
  completed_at?: string | null;
}

export interface ExecutionNode {
  id: number;
  graph_id: number;
  parent_id?: number | null;
  name: string;
  kind: string;
  status: string;
  tool_call_id?: string | null;
  external_task_id?: string | null;
  wait_reason?: string | null;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  error: Record<string, unknown>;
  metadata: Record<string, unknown>;
  sequence: number;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExecutionEvent {
  id: number;
  graph_id: number;
  node_id?: number | null;
  event_type: string;
  status?: string | null;
  content: string;
  payload: Record<string, unknown>;
  sequence: number;
  created_at: string;
}

export interface ExecutionArtifact {
  id: number;
  graph_id: number;
  node_id?: number | null;
  content_blob_id?: number | null;
  artifact_type: string;
  name: string;
  content: string;
  data: Record<string, unknown>;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ExecutionGraphDetail extends ExecutionGraph {
  nodes: ExecutionNode[];
  events: ExecutionEvent[];
  artifacts: ExecutionArtifact[];
}

export const executionApi = {
  listGraphs: async (params?: { thread_id?: number; target_id?: number; status?: string; limit?: number }): Promise<ExecutionGraph[]> => {
    const response = await api.get<ExecutionGraph[]>('/executions', { params });
    return Array.isArray(response.data) ? response.data : [];
  },

  getGraph: async (graphId: number | string): Promise<ExecutionGraphDetail> => {
    const response = await api.get<ExecutionGraphDetail>(`/executions/${graphId}`);
    return response.data;
  },

  listEvents: async (graphId: number | string, params?: { after?: number; limit?: number }): Promise<ExecutionEvent[]> => {
    const response = await api.get<ExecutionEvent[]>(`/executions/${graphId}/events`, { params });
    return Array.isArray(response.data) ? response.data : [];
  },

  listArtifacts: async (graphId: number | string, params?: { node_id?: number }): Promise<ExecutionArtifact[]> => {
    const response = await api.get<ExecutionArtifact[]>(`/executions/${graphId}/artifacts`, { params });
    return Array.isArray(response.data) ? response.data : [];
  },
};
