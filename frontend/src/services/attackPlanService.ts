import axios from 'axios';
import { GLOBAL_CONFIG } from '../config';
import type {
  AttackPlanOut,
  ActionOut,
  AttackVectorOut,
  PaginatedResponse,
} from '../types/attackPlan';

const coreApi = axios.create({
  baseURL: `${GLOBAL_CONFIG.DJANGO_API_BASE}/core`,
  headers: { 'Content-Type': 'application/json' },
});

export type AttackPlanCreatePayload = {
  target_id: number;
  objective: string;
  scope?: Record<string, unknown>;
  status?: string;
  thread_id?: number | null;
  parent_plan_id?: number | null;
};

export type AttackPlanUpdatePayload = {
  objective?: string;
  scope?: Record<string, unknown>;
  status?: string;
  thread_id?: number | null;
  parent_plan_id?: number | null;
};

export type ActionUpdatePayload = {
  status?: string;
  result_summary?: string | null;
  purpose_text?: string | null;
  purpose?: Record<string, unknown>;
};

export type AttackVectorUpdatePayload = {
  status?: string;
  risk_score?: number;
  evidence?: string | null;
  description?: string | null;
};

export const AttackPlanService = {
  listPlans: async (targetId?: number): Promise<PaginatedResponse<AttackPlanOut>> => {
    const params: Record<string, unknown> = {};
    if (targetId !== undefined) params.target_id = targetId;
    const res = await coreApi.get<PaginatedResponse<AttackPlanOut>>('/attack-plans', { params });
    return res.data;
  },

  getPlan: async (id: number): Promise<AttackPlanOut> => {
    const res = await coreApi.get<AttackPlanOut>(`/attack-plans/${id}`);
    return res.data;
  },

  createPlan: async (payload: AttackPlanCreatePayload): Promise<AttackPlanOut> => {
    const res = await coreApi.post<AttackPlanOut>('/attack-plans', payload);
    return res.data;
  },

  updatePlan: async (id: number, payload: AttackPlanUpdatePayload): Promise<AttackPlanOut> => {
    const res = await coreApi.patch<AttackPlanOut>(`/attack-plans/${id}`, payload);
    return res.data;
  },

  getPlanActions: async (planId: number): Promise<PaginatedResponse<ActionOut>> => {
    const res = await coreApi.get<PaginatedResponse<ActionOut>>(`/attack-plans/${planId}/actions`);
    return res.data;
  },

  getAction: async (id: number): Promise<ActionOut> => {
    const res = await coreApi.get<ActionOut>(`/actions/${id}`);
    return res.data;
  },

  updateAction: async (id: number, payload: ActionUpdatePayload): Promise<ActionOut> => {
    const res = await coreApi.patch<ActionOut>(`/actions/${id}`, payload);
    return res.data;
  },

  listVectors: async (overviewId?: number): Promise<PaginatedResponse<AttackVectorOut>> => {
    const params: Record<string, unknown> = {};
    if (overviewId !== undefined) params.overview_id = overviewId;
    const res = await coreApi.get<PaginatedResponse<AttackVectorOut>>('/attack-vectors', { params });
    return res.data;
  },

  getVector: async (id: number): Promise<AttackVectorOut> => {
    const res = await coreApi.get<AttackVectorOut>(`/attack-vectors/${id}`);
    return res.data;
  },

  updateVector: async (id: number, payload: AttackVectorUpdatePayload): Promise<AttackVectorOut> => {
    const res = await coreApi.patch<AttackVectorOut>(`/attack-vectors/${id}`, payload);
    return res.data;
  },
};
