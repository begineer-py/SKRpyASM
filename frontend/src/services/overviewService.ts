import axios from 'axios';
import { GLOBAL_CONFIG } from '../config';

const coreApi = axios.create({
  baseURL: `${GLOBAL_CONFIG.DJANGO_API_BASE}/core`,
  headers: { 'Content-Type': 'application/json' },
});

export interface OverviewUpdatePayload {
  summary?: string | null;
  recon_summary?: string | null;
  status?: string | null;
  risk_score?: number | null;
  business_impact?: string | null;
  knowledge?: any;
  tech_stack?: any;
  subdomain_intel?: any;
  port_service?: any;
  vuln_intel?: any;
}

export interface OverviewCreatePayload {
  target_id?: number | null;
  summary?: string | null;
  status?: string | null;
  risk_score?: number | null;
  business_impact?: string | null;
}

export interface OverviewData {
  id: number;
  target_id?: number | null;
  target_name?: string | null;
  status: string;
  risk_score: number;
  summary?: string | null;
  recon_summary?: string | null;
  business_impact?: string | null;
  plan?: any;
  knowledge?: any;
  techs?: any;
  tech_stack?: any;
  subdomain_intel?: any;
  port_service?: any;
  vuln_intel?: any;
  seed_id?: number | null;
  ips?: number[];
  subdomains?: number[];
  url_results?: number[];
  thread_id?: number | null;
  parent_thread_id?: number | null;
  needs_human_review?: boolean;
  latest_mission_review_id?: number | null;
  created_at: string;
  updated_at: string;
}

export const OverviewService = {
  list: async (params?: { target_id?: number }): Promise<OverviewData[]> => {
    const res = await coreApi.get<OverviewData[]>('/overviews/', { params });
    return Array.isArray(res.data) ? res.data : [];
  },
  get: async (overviewId: number): Promise<OverviewData> => {
    return (await coreApi.get<OverviewData>(`/overviews/${overviewId}`)).data;
  },
  // 後端 POST 採 upsert 語意：因 Target ↔ Overview 已為 1:1 (OneToOneField)，
  // 若該 target 已存在 overview 則更新，否則建立。payload.target_id 決定對應的 target。
  create: async (payload: OverviewCreatePayload) => {
    return (await coreApi.post('/overviews/', payload)).data;
  },
  update: async (overviewId: number, payload: OverviewUpdatePayload) => {
    return (await coreApi.patch(`/overviews/${overviewId}`, payload)).data;
  },
  delete: async (overviewId: number) => {
    return (await coreApi.delete(`/overviews/${overviewId}`)).data;
  },
};
