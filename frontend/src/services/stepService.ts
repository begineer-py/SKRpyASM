import axios from 'axios';
import { GLOBAL_CONFIG } from '../config';

// Step/StepNote write APIs are served by Django Ninja under /api/core
const coreApi = axios.create({
  baseURL: `${GLOBAL_CONFIG.DJANGO_API_BASE}/core`,
  headers: { 'Content-Type': 'application/json' },
});

export interface StepNoteUpsertPayload {
  content?: string | null;
  ai_thoughts?: string | null;
}

export interface StepCreatePayload {
  overview_id?: number | null;
  parent_step_id?: number | null;
  order?: number | null;
  status?: string | null;
  note?: StepNoteUpsertPayload | null;
}

export interface StepUpdatePayload {
  overview_id?: number | null;
  parent_step_id?: number | null;
  order?: number | null;
  status?: string | null;
}

export const StepService = {
  create: async (payload: StepCreatePayload) => {
    return await coreApi.post('/steps/', payload);
  },
  update: async (stepId: number, payload: StepUpdatePayload) => {
    return await coreApi.patch(`/steps/${stepId}`, payload);
  },
  delete: async (stepId: number) => {
    return await coreApi.delete(`/steps/${stepId}`);
  },
  upsertNote: async (stepId: number, payload: StepNoteUpsertPayload) => {
    return await coreApi.put(`/steps/${stepId}/note/`, payload);
  },
};
