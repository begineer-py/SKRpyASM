import axios from 'axios';
import { GLOBAL_CONFIG } from '../config';

const api = axios.create({
  baseURL: `${GLOBAL_CONFIG.DJANGO_API_BASE}/skills`,
});

export interface SkillTemplate {
  id: number;
  name: string;
  description: string;
  instructions: string;
  script_content: string | null;
  script_body: string | null;
  language: string;
  tags: string[];
  usage_count: number;
  input_schema: Record<string, unknown> | null;
  output_schema: Record<string, unknown> | null;
  is_robust: boolean;
  is_deprecated: boolean;
  has_io_contract: boolean;
  version: number;
  last_verified_at: string | null;
  last_failure_reason: string | null;
  test_input_example: Record<string, unknown> | null;
  merged_from: number[] | null;
  created_at: string;
  updated_at: string;
}

export interface SkillCreatePayload {
  name: string;
  description: string;
  instructions: string;
  language?: string;
  tags?: string[];
  input_schema?: Record<string, unknown> | null;
  output_schema?: Record<string, unknown> | null;
  script_body?: string | null;
  script_content?: string | null;
}

export interface SkillUpdatePayload {
  name?: string;
  description?: string;
  instructions?: string;
  language?: string;
  tags?: string[];
  input_schema?: Record<string, unknown> | null;
  output_schema?: Record<string, unknown> | null;
  script_body?: string | null;
  script_content?: string | null;
  is_deprecated?: boolean;
}

export interface SkillTestRequest {
  test_input?: Record<string, unknown> | null;
}

export interface SkillTestResult {
  ok: boolean;
  verification_id: number | null;
  verdict: string | null;
  confidence: number | null;
  error: string | null;
  exit_code: number | null;
  duration_ms: number | null;
  raw_output: string | null;
  agent_notes: string | null;
}

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
