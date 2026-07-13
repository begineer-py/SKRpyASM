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

  getTargetTopology: async (targetId: number | string): Promise<TargetTopology> => {
    const response = await api.get<TargetTopology>(`/targets/${targetId}/topology/`);
    return response.data;
  },

  getAssetPentestRecords: async (
    assetType: string,
    assetId: number | string,
  ): Promise<AssetPentestRecords> => {
    const response = await api.get<AssetPentestRecords>(
      `/assets/${assetType}/${assetId}/pentest-records/`,
    );
    return response.data;
  },

  getDispatchTree: async (rootThreadId: number | string): Promise<AgentInteractionTree> => {
    const response = await api.get<AgentInteractionTree>(
      `/threads/${rootThreadId}/dispatch-tree/`,
    );
    return response.data;
  },
};

export interface TopologyNode {
  id: string;
  type: string;
  label: string;
  asset_id?: number | null;
  meta?: Record<string, unknown>;
  is_active_attack?: boolean;
}

export interface TopologyEdge {
  id: string;
  source: string;
  target: string;
  edge_type: string;
  source_kind?: string;
}

export interface TopologyActiveAttack {
  node_id?: string | null;
  asset_type?: string | null;
  asset_id?: number | null;
  thread_id?: number | null;
  agent_role?: string | null;
  source?: string;
}

export interface TargetTopology {
  target_id: number;
  target_name: string;
  nodes: TopologyNode[];
  edges: TopologyEdge[];
  active_attacks: TopologyActiveAttack[];
}

export interface PentestRecord {
  action_id: number;
  purpose: string;
  purpose_text: string;
  status: string;
  result_summary: string;
  plan_id?: number | null;
  execution_graph_id?: number | null;
  started_at?: string | null;
  completed_at?: string | null;
  attack_vector_ids: number[];
}

export interface AssetPentestRecords {
  asset_type: string;
  asset_id: number;
  label: string;
  records: PentestRecord[];
  cves: Array<Record<string, unknown>>;
  vulnerabilities: Array<Record<string, unknown>>;
}

export interface AgentInteractionNode {
  thread_id: number;
  dispatch_id?: number | null;
  agent_id: string;
  status: string;
  depth: number;
  round: number;
  objective: string;
  dispatched_at?: string | null;
  completed_at?: string | null;
  graph_id?: number | null;
  children: AgentInteractionNode[];
}

export interface AgentInteractionTree {
  root_thread_id: number;
  root_agent_id: string;
  nodes: AgentInteractionNode[];
}
