import axios from 'axios';
import { GLOBAL_CONFIG } from '../config';

// ==========================================
// 漏洞管理 REST API service
// 對應後端 /api/core/vulnerabilities
// ==========================================

const vulnApi = axios.create({
  baseURL: `${GLOBAL_CONFIG.DJANGO_API_BASE}/core/vulnerabilities`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

// ===== 類型定義 =====

export interface AssetRef {
  id: number;
  label: string;
}

export interface PoCRecord {
  id: number;
  vulnerability_id: number;
  title: string;
  content: string;
  language: 'curl' | 'python' | 'bash' | 'http_request' | 'manual';
  result: string | null;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface PoCRecordPayload {
  title: string;
  content: string;
  language?: 'curl' | 'python' | 'bash' | 'http_request' | 'manual';
  result?: string | null;
  is_verified?: boolean;
}

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type VulnStatus = 'unverified' | 'confirmed' | 'false_positive';
export type EnrichmentStatus = 'pending' | 'enriched' | 'no_cve' | 'failed';

export interface VulnerabilityData {
  id: number;
  target_id: number | null;
  target_name: string | null;
  ip_asset: AssetRef | null;
  subdomain_asset: AssetRef | null;
  url_asset: AssetRef | null;
  source_attack_vector_id: number | null;
  overview_id: number | null;
  cve_intelligence_id: number | null;
  enrichment_status: EnrichmentStatus;
  enrichment_attempted_at: string | null;
  tool_source: string;
  template_id: string;
  name: string;
  severity: Severity | string;
  matched_at: string;
  extracted_results: unknown;
  request_raw: string | null;
  response_raw: string | null;
  fingerprint: string | null;
  status: VulnStatus | string;
  description: string | null;
  remediation: string | null;
  pocs: PoCRecord[];
  created_at: string;
  updated_at: string;
  last_seen: string;
}

export interface VulnerabilityCreatePayload {
  target_id?: number | null;
  name: string;
  severity: Severity;
  template_id?: string;
  matched_at: string;
  tool_source?: string;
  description?: string;
  remediation?: string;
  extracted_results?: unknown;
  request_raw?: string;
  response_raw?: string;
  status?: VulnStatus;
  ip_asset_id?: number | null;
  subdomain_asset_id?: number | null;
  url_asset_id?: number | null;
  overview_id?: number | null;
  cve_intelligence_id?: number | null;
}

export interface VulnerabilityUpdatePayload {
  target_id?: number | null;
  name?: string;
  severity?: Severity;
  template_id?: string;
  matched_at?: string;
  description?: string | null;
  remediation?: string | null;
  extracted_results?: unknown;
  request_raw?: string | null;
  response_raw?: string | null;
  status?: VulnStatus;
  ip_asset_id?: number | null;
  subdomain_asset_id?: number | null;
  url_asset_id?: number | null;
  overview_id?: number | null;
  cve_intelligence_id?: number | null;
}

export interface VulnerabilityListParams {
  severity?: string;
  status?: string;
  search?: string;
  target_id?: number;
  overview_id?: number;
  limit?: number;
  offset?: number;
}

export interface VulnerabilityListResponse {
  items: VulnerabilityData[];
  total: number;
}

export interface VulnerabilityCounts {
  total: number;
  critical?: number;
  high?: number;
  medium?: number;
  low?: number;
  info?: number;
  [key: string]: number | undefined;
}

// ===== API 方法 =====

export const VulnerabilityService = {
  list: async (params: VulnerabilityListParams = {}): Promise<VulnerabilityListResponse> => {
    const response = await vulnApi.get<VulnerabilityListResponse>('', { params });
    return response.data;
  },

  getCounts: async (): Promise<VulnerabilityCounts> => {
    const response = await vulnApi.get<VulnerabilityCounts>('/counts');
    return response.data;
  },

  get: async (id: number): Promise<VulnerabilityData> => {
    const response = await vulnApi.get<VulnerabilityData>(`/${id}`);
    return response.data;
  },

  create: async (payload: VulnerabilityCreatePayload): Promise<VulnerabilityData> => {
    const response = await vulnApi.post<VulnerabilityData>('', payload);
    return response.data;
  },

  update: async (id: number, payload: VulnerabilityUpdatePayload): Promise<VulnerabilityData> => {
    const response = await vulnApi.patch<VulnerabilityData>(`/${id}`, payload);
    return response.data;
  },

  updateStatus: async (id: number, status: string): Promise<VulnerabilityData> => {
    return VulnerabilityService.update(id, { status: status as VulnStatus });
  },

  delete: async (id: number): Promise<{ deleted: number }> => {
    const response = await vulnApi.delete<{ deleted: number }>(`/${id}`);
    return response.data;
  },

  batchUpdateStatus: async (ids: number[], status: string): Promise<{ updated: number }> => {
    const response = await vulnApi.post<{ updated: number }>('/batch-status', { ids, status });
    return response.data;
  },

  batchDelete: async (ids: number[]): Promise<{ deleted: number }> => {
    const response = await vulnApi.post<{ deleted: number }>('/batch-delete', { ids });
    return response.data;
  },
};

export const PoCService = {
  list: async (vulnId: number): Promise<PoCRecord[]> => {
    const response = await vulnApi.get<PoCRecord[]>(`/${vulnId}/pocs`);
    return response.data;
  },

  create: async (vulnId: number, payload: PoCRecordPayload): Promise<PoCRecord> => {
    const response = await vulnApi.post<PoCRecord>(`/${vulnId}/pocs`, payload);
    return response.data;
  },

  update: async (vulnId: number, pocId: number, payload: Partial<PoCRecordPayload>): Promise<PoCRecord> => {
    const response = await vulnApi.patch<PoCRecord>(`/${vulnId}/pocs/${pocId}`, payload);
    return response.data;
  },

  delete: async (vulnId: number, pocId: number): Promise<{ deleted: number }> => {
    const response = await vulnApi.delete<{ deleted: number }>(`/${vulnId}/pocs/${pocId}`);
    return response.data;
  },
};
