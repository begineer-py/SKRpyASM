import {
  AddSeedDocument,
  DeleteSeedDocument,
} from '../gql/graphql';
import type {
  AddSeedMutation,
  DeleteSeedMutation,
} from '../gql/graphql';
import { executeGraphQL } from './gqlClient';
import type { Seed, AddSeedPayload } from '../type';

export const SeedService = {
  /**
   * 為指定目標新增種子
   */
  add: async (targetId: number, payload: AddSeedPayload): Promise<Seed> => {
    try {
      const object = {
        target_id: targetId,
        value: payload.value,
        type: payload.type ?? 'DOMAIN',
        is_active: true,
      };
      const data = await executeGraphQL<AddSeedMutation, { object: typeof object }>(
        AddSeedDocument,
        { object },
      );
      return data.insert_core_seed_one as unknown as Seed;
    } catch (error: any) {
      console.error('API Error: Failed to add seed', error);
      throw new Error(error.message || '添加種子失敗');
    }
  },

  /**
   * 刪除指定種子
   */
  delete: async (seedId: number): Promise<void> => {
    try {
      await executeGraphQL<DeleteSeedMutation, { id: number }>(
        DeleteSeedDocument,
        { id: seedId },
      );
    } catch (error: any) {
      console.error('API Error: Failed to delete seed', error);
      throw new Error(error.message || '刪除種子失敗');
    }
  },

  /**
   * 獲取指定目標的所有種子 (read via GraphQL; backward compat)
   */
  listByTarget: async (targetId: number): Promise<Seed[]> => {
    // Seeds are typically loaded via the existing GraphQL query in api.ts (GET_TARGET_DETAIL_QUERY)
    // This method kept for backward compatibility
    const { gqlFetcher, GET_TARGET_DETAIL_QUERY } = await import('./api');
    const data = await gqlFetcher<{ core_target_by_pk: { core_seeds: Seed[] } }>(
      GET_TARGET_DETAIL_QUERY,
      { id: targetId },
    );
    return data.core_target_by_pk?.core_seeds ?? [];
  },
};
