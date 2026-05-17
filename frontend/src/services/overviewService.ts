import axios from 'axios';
import { GLOBAL_CONFIG } from '../config';

const coreApi = axios.create({
  baseURL: `${GLOBAL_CONFIG.DJANGO_API_BASE}/core`,
  headers: { 'Content-Type': 'application/json' },
});

export interface OverviewUpdatePayload {
  summary?: string | null;
  status?: string | null;
  risk_score?: number | null;
  business_impact?: string | null;
  plan?: any;
}

export interface OverviewCreatePayload {
  target_id?: number | null;
  summary?: string | null;
  status?: string | null;
  risk_score?: number | null;
  business_impact?: string | null;
  plan?: any;
}

export const OverviewService = {
  list: async () => {
    return (await coreApi.get('/overviews/')).data;
  },
  get: async (overviewId: number) => {
    return (await coreApi.get(`/overviews/${overviewId}`)).data;
  },
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
