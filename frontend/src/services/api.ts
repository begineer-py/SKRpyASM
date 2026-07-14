import {
  CreateTargetDocument,
  UpdateTargetDocument,
  DeleteTargetDocument,
} from '../gql/graphql';
import type {
  CreateTargetMutation,
  UpdateTargetMutation,
  DeleteTargetMutation,
} from '../gql/graphql';
import { executeGraphQL } from './gqlClient';
import type { Target, CreateTargetPayload, UpdateTargetPayload } from '../type';

// ==========================================
// 1. Target CRUD via Hasura GraphQL
// ==========================================

export const TargetService = {
  create: async (payload: CreateTargetPayload) => {
    const data = await executeGraphQL<CreateTargetMutation, { object: CreateTargetPayload }>(
      CreateTargetDocument,
      { object: payload },
    );
    return data.insert_core_target_one as unknown as Target;
  },
  update: async (id: number, payload: UpdateTargetPayload) => {
    const data = await executeGraphQL<UpdateTargetMutation, { id: number; updates: UpdateTargetPayload }>(
      UpdateTargetDocument,
      { id, updates: payload },
    );
    return data.update_core_target_by_pk as unknown as Target;
  },
  delete: async (id: number) => {
    const data = await executeGraphQL<DeleteTargetMutation, { id: number }>(
      DeleteTargetDocument,
      { id },
    );
    return data.delete_core_target_by_pk as unknown as Target;
  },
};

// ==========================================
// 2. Hasura GraphQL (Fetch) - 負責讀取 (Read)
// ==========================================

export const gqlFetcher = async <T>(query: string, variables: Record<string, unknown> = {}): Promise<T> => {
  const { GLOBAL_CONFIG } = await import('../config');
  try {
    const response = await fetch(GLOBAL_CONFIG.HASURA_GRAPHQL_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-hasura-admin-secret': GLOBAL_CONFIG.HASURA_ADMIN_SECRET,
      },
      body: JSON.stringify({ query, variables }),
    });

    const result = await response.json();

    if (result.errors) {
      const msg = result.errors[0]?.message || 'GraphQL Error';
      throw new Error(msg);
    }

    return result.data;
  } catch (error) {
    console.error("GraphQL Request Failed:", error);
    throw error;
  }
};

// === Query Definitions (kept for gqlFetcher usage) ===

// 用於首頁列表
export const GET_TARGETS_QUERY = `
  query GetTargets {
    core_target(order_by: {created_at: desc}) {
      id
      name
      description
      created_at
    }
  }
`;

// [關鍵修正] 用於詳情頁，包含 seeds 關聯
export const GET_TARGET_DETAIL_QUERY = `
  query GetTargetDetail($id: bigint!) {
    core_target_by_pk(id: $id) {
      id
      name
      description
      created_at
      core_seeds(order_by: {created_at: desc}) {
        id
        value
        type
        is_active
        created_at
      }
    }
  }
`;

// 查詢目標的子域名 (含IP關聯和狀態)，支援動態 where/orderBy/分頁
export const GET_TARGET_SUBDOMAINS_QUERY = `
  query GetTargetSubdomains($where: core_subdomain_bool_exp!, $orderBy: [core_subdomain_order_by!]!, $limit: Int!, $offset: Int!) {
    core_subdomain(
      where: $where
      order_by: $orderBy
      limit: $limit
      offset: $offset
    ) {
      id
      name
      is_active
      is_resolvable
      is_cdn
      is_waf
      created_at
      core_subdomain_ips(limit: 3) {
        core_ip {
          id
          address
        }
      }
    }
    core_subdomain_aggregate(where: $where) {
      aggregate { count }
    }
  }
`;

// 查詢目標的 IP 資產 (含埠號詳情)，支援動態 where/orderBy/分頁
export const GET_TARGET_IPS_QUERY = `
  query GetTargetIPs($where: core_ip_bool_exp!, $orderBy: [core_ip_order_by!]!, $limit: Int!, $offset: Int!) {
    core_ip(
      where: $where
      order_by: $orderBy
      limit: $limit
      offset: $offset
    ) {
      id
      address
      version
      core_ports {
        id
        port_number
        protocol
        service_name
        service_version
        state
        first_seen
      }
    }
    core_ip_aggregate(where: $where) {
      aggregate { count }
    }
  }
`;

// 查詢目標 AI Overview (戰略概覽)
// 注意：後端 Target ↔ Overview 已改為 OneToOneField (1:1)，每個 target 最多僅有一筆 overview。
// 此 query 仍回傳 list 形式以相容 Hasura GraphQL schema 與 null 情況，前端取 core_overview[0] 使用。
export const GET_TARGET_OVERVIEWS_QUERY = `
  query GetTargetOverviews($targetId: bigint!) {
    core_overview(
      where: { target_id: { _eq: $targetId } }
      order_by: { updated_at: desc }
      limit: 1
    ) {
      id
      status
      summary
      plan
      knowledge
      risk_score
      business_impact
      thread_id
      parent_thread_id
      created_at
      updated_at
    }
  }
`;

// 查詢目標的 URL 資產 (支持分頁、排序、動態篩選、初步分析分數)
export const GET_TARGET_URLS_QUERY = `
  query GetTargetURLs($where: core_urlresult_bool_exp!, $limit: Int = 50, $offset: Int = 0, $orderBy: [core_urlresult_order_by!] = {created_at: desc}) {
    core_urlresult(
      where: $where
      order_by: $orderBy
      limit: $limit
      offset: $offset
    ) {
      id
      url
      status_code
      title
      content_length
      discovery_source
      content_fetch_status
      created_at
      # 初步分析分數 (最新一筆)
      core_initialaianalyses(
        order_by: { created_at: desc }
        limit: 1
      ) {
        id
        risk_score
        summary
        worth_deep_analysis
        status
      }
    }
    # 統計總數，用於前端判斷是否還有更多資料
    core_urlresult_aggregate(where: $where) {
      aggregate {
        count
      }
    }
  }
`;
