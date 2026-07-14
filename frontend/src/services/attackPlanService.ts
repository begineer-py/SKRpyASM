import {
  GetAttackPlansDocument,
  GetAttackPlanDocument,
  CreateAttackPlanDocument,
  UpdateAttackPlanDocument,
  GetPlanActionsDocument,
  GetActionDocument,
  UpdateActionDocument,
  GetAttackVectorsDocument,
  GetAttackVectorDocument,
  UpdateAttackVectorDocument,
} from '../gql/graphql';
import type {
  GetAttackPlansQuery,
  GetAttackPlanQuery,
  CreateAttackPlanMutation,
  UpdateAttackPlanMutation,
  GetPlanActionsQuery,
  GetActionQuery,
  UpdateActionMutation,
  GetAttackVectorsQuery,
  GetAttackVectorQuery,
  UpdateAttackVectorMutation,
} from '../gql/graphql';
import { executeGraphQL } from './gqlClient';

// ===== Re-export types for backward compatibility =====

export type AttackPlanOut = GetAttackPlansQuery['core_attackplan'][number];
export type ActionOut = GetPlanActionsQuery['core_action'][number];
export type AttackVectorOut = GetAttackVectorsQuery['core_attackvector'][number];

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

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
    const where: Record<string, unknown> = {};
    if (targetId !== undefined) {
      where.target_id = { _eq: targetId };
    }
    const data = await executeGraphQL<GetAttackPlansQuery, {
      where?: Record<string, unknown>;
      orderBy?: Record<string, string>[];
    }>(GetAttackPlansDocument, {
      where: Object.keys(where).length > 0 ? where : undefined,
      orderBy: [{ created_at: 'desc' }],
    });
    return {
      items: data.core_attackplan ?? [],
      total: data.core_attackplan_aggregate?.aggregate?.count ?? 0,
    };
  },

  getPlan: async (id: number): Promise<GetAttackPlanQuery['core_attackplan_by_pk']> => {
    const data = await executeGraphQL<GetAttackPlanQuery, { id: number }>(
      GetAttackPlanDocument,
      { id },
    );
    return data.core_attackplan_by_pk;
  },

  createPlan: async (payload: AttackPlanCreatePayload): Promise<CreateAttackPlanMutation['insert_core_attackplan_one']> => {
    const data = await executeGraphQL<CreateAttackPlanMutation, { object: typeof payload }>(
      CreateAttackPlanDocument,
      { object: payload },
    );
    return data.insert_core_attackplan_one;
  },

  updatePlan: async (id: number, payload: AttackPlanUpdatePayload): Promise<UpdateAttackPlanMutation['update_core_attackplan_by_pk']> => {
    const data = await executeGraphQL<UpdateAttackPlanMutation, { id: number; updates: typeof payload }>(
      UpdateAttackPlanDocument,
      { id, updates: payload },
    );
    return data.update_core_attackplan_by_pk;
  },

  getPlanActions: async (planId: number): Promise<PaginatedResponse<ActionOut>> => {
    const data = await executeGraphQL<GetPlanActionsQuery, { where: { plan_id: { _eq: number } } }>(
      GetPlanActionsDocument,
      { where: { plan_id: { _eq: planId } } },
    );
    return {
      items: data.core_action ?? [],
      total: data.core_action_aggregate?.aggregate?.count ?? 0,
    };
  },

  getAction: async (id: number): Promise<GetActionQuery['core_action_by_pk']> => {
    const data = await executeGraphQL<GetActionQuery, { id: number }>(
      GetActionDocument,
      { id },
    );
    return data.core_action_by_pk;
  },

  updateAction: async (id: number, payload: ActionUpdatePayload): Promise<UpdateActionMutation['update_core_action_by_pk']> => {
    const data = await executeGraphQL<UpdateActionMutation, { id: number; updates: typeof payload }>(
      UpdateActionDocument,
      { id, updates: payload },
    );
    return data.update_core_action_by_pk;
  },

  listVectors: async (overviewId?: number): Promise<PaginatedResponse<AttackVectorOut>> => {
    const where: Record<string, unknown> = {};
    if (overviewId !== undefined) {
      where.overview_id = { _eq: overviewId };
    }
    const data = await executeGraphQL<GetAttackVectorsQuery, { where?: Record<string, unknown> }>(
      GetAttackVectorsDocument,
      { where: Object.keys(where).length > 0 ? where : undefined },
    );
    return {
      items: data.core_attackvector ?? [],
      total: data.core_attackvector_aggregate?.aggregate?.count ?? 0,
    };
  },

  getVector: async (id: number): Promise<GetAttackVectorQuery['core_attackvector_by_pk']> => {
    const data = await executeGraphQL<GetAttackVectorQuery, { id: number }>(
      GetAttackVectorDocument,
      { id },
    );
    return data.core_attackvector_by_pk;
  },

  updateVector: async (id: number, payload: AttackVectorUpdatePayload): Promise<UpdateAttackVectorMutation['update_core_attackvector_by_pk']> => {
    const data = await executeGraphQL<UpdateAttackVectorMutation, { id: number; updates: typeof payload }>(
      UpdateAttackVectorDocument,
      { id, updates: payload },
    );
    return data.update_core_attackvector_by_pk;
  },
};
