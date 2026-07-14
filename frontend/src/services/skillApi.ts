import { createApiClient } from './apiClient';
import type { components } from '../types/api';

const api = createApiClient('skills');

type SkillTemplate = components['schemas']['SkillOut'];
type SkillCreatePayload = components['schemas']['SkillCreate'];
type SkillUpdatePayload = components['schemas']['SkillUpdate'];
type SkillTestRequest = components['schemas']['SkillTestRequest'];
type SkillTestResult = components['schemas']['SkillTestOut'];

export type { SkillTemplate, SkillCreatePayload, SkillUpdatePayload, SkillTestRequest, SkillTestResult };

export const skillApi = {
  list: async (params?: { q?: string; language?: string; deprecated?: boolean }): Promise<SkillTemplate[]> => {
    const response = await api.get<SkillTemplate[]>('/', { params });
    return Array.isArray(response.data) ? response.data : [];
  },

  get: async (id: number): Promise<SkillTemplate> => {
    const response = await api.get<SkillTemplate>(`/${id}`);
    return response.data;
  },

  create: async (payload: SkillCreatePayload): Promise<SkillTemplate> => {
    const response = await api.post<SkillTemplate>('/', payload);
    return response.data;
  },

  update: async (id: number, payload: SkillUpdatePayload): Promise<SkillTemplate> => {
    const response = await api.patch<SkillTemplate>(`/${id}`, payload);
    return response.data;
  },

  delete: async (id: number): Promise<{ success: boolean; message: string }> => {
    const response = await api.delete<{ success: boolean; message: string }>(`/${id}`);
    return response.data;
  },

  test: async (id: number, payload?: SkillTestRequest): Promise<SkillTestResult> => {
    const response = await api.post<SkillTestResult>(`/${id}/test`, payload || {});
    return response.data;
  },
};
