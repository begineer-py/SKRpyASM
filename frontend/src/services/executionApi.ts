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

export interface ContentBlobSummary {
  blob_id: number;
  ai_summary?: string | null;
  content_size: number;
  page_count?: number | null;
  source_type?: string | null;
  created_at?: string | null;
}

export interface DispatchGraphInfo {
  graph_id: number;
  status: string;
  title: string;
  assistant_id?: string;
}

export interface SubAgentDispatchItem {
  dispatch_id: number;
  sub_agent_type: string;
  objective: string;
  result_summary: string;
  synthesized: boolean;
  dispatched_at?: string | null;
  completed_at?: string | null;
  status: string;
  dispatcher_thread_id?: number | null;
  callee_thread_id?: number | null;
  overview_id?: number | null;
  graph?: DispatchGraphInfo | null;
  content_blobs: ContentBlobSummary[];
}

export interface ContentBlobPage {
  blob_id: number;
  page: number;
  total_pages: number;
  title: string;
  content: string;
}

export const executionApi = {
  listGraphs: async (params?: {
    thread_id?: number;
    target_id?: number;
    status?: string;
    limit?: number;
    offset?: number;
    include_archived?: boolean;
    search?: string;
  }): Promise<ExecutionGraph[]> => {
    const response = await api.get<ExecutionGraph[]>('/executions', { params });
    return Array.isArray(response.data) ? response.data : [];
  },

  getGraph: async (graphId: number | string): Promise<ExecutionGraphDetail> => {
    const response = await api.get<ExecutionGraphDetail>(`/executions/${graphId}`);
    return response.data;
  },

  updateGraph: async (
    graphId: number | string,
    data: { title?: string; archived?: boolean },
  ): Promise<ExecutionGraph> => {
    const response = await api.patch<ExecutionGraph>(`/executions/${graphId}`, data);
    return response.data;
  },

  deleteGraph: async (graphId: number | string): Promise<void> => {
    await api.delete(`/executions/${graphId}`);
  },

  archiveGraph: async (graphId: number | string, archived = true): Promise<ExecutionGraph> => {
    const response = await api.patch<ExecutionGraph>(`/executions/${graphId}`, { archived });
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

  listDispatches: async (callerThreadId: number | string): Promise<SubAgentDispatchItem[]> => {
    const response = await api.get<SubAgentDispatchItem[]>(`/threads/${callerThreadId}/dispatches/`);
    return Array.isArray(response.data) ? response.data : [];
  },

  getBlobPage: async (blobId: number | string, pageNum: number): Promise<ContentBlobPage> => {
    const response = await api.get<ContentBlobPage>(`/blobs/${blobId}/page/${pageNum}/`);
    return response.data;
  },
};
