import axios from 'axios';
import { GLOBAL_CONFIG } from '../config';
import type { Target, CreateTargetPayload, UpdateTargetPayload } from '../type';

// ==========================================
// 1. Django API (Axios) - 負責 Target 寫入 (CUD)
// ==========================================

const djangoApi = axios.create({
  baseURL: `${GLOBAL_CONFIG.DJANGO_API_BASE}/targets`, 
  headers: {
    'Content-Type': 'application/json',
  },
});

export const TargetService = {
  create: async (payload: CreateTargetPayload) => {
    return await djangoApi.post<Target>('/', payload);
  },
  update: async (id: number, payload: UpdateTargetPayload) => {
    return await djangoApi.put<Target>(`/${id}`, payload);
  },
  delete: async (id: number) => {
    return await djangoApi.delete(`/${id}`);
  },
};

// ==========================================
// 2. Hasura GraphQL (Fetch) - 負責讀取 (Read)
// ==========================================

export const gqlFetcher = async <T>(query: string, variables: any = {}): Promise<T> => {
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

// === Query Definitions ===

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

// 查詢目標的子域名 (含IP關聯和狀態)
// NOTE: Subdomain has direct target FK, so filter by target_id directly
export const GET_TARGET_SUBDOMAINS_QUERY = `
  query GetTargetSubdomains($targetId: bigint!) {
    core_subdomain(
      where: { target_id: { _eq: $targetId } }
      order_by: { created_at: desc }
      limit: 200
    ) {
      id
      name
      is_active
      is_resolvable
      created_at
      core_subdomain_ips(limit: 3) {
        core_ip {
          id
          address
        }
      }
    }
  }
`;


// 查詢目標的 IP 資產 (含埠號詳情)
// NOTE: IP model has no `created_at`, sort by id. Ports related_name is 'ports'
export const GET_TARGET_IPS_QUERY = `
  query GetTargetIPs($targetId: bigint!) {
    core_ip(
      where: { target_id: { _eq: $targetId } }
      order_by: { id: desc }
      limit: 200
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
  }
`;

// 查詢目標 AI Overview (戰略概覽)
export const GET_TARGET_OVERVIEWS_QUERY = `
  query GetTargetOverviews($targetId: bigint!) {
    core_overview(
      where: { target_id: { _eq: $targetId } }
      order_by: { updated_at: desc }
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

// 查詢目標的 URL 資產 (支持分頁、排序、初步分析分數)
// NOTE: URLResult has no `content_type` field. Use title, status_code, created_at
// 新增: core_initialaianalysis_set relationship 取得初步分析分數
export const GET_TARGET_URLS_QUERY = `
  query GetTargetURLs($targetId: bigint!, $limit: Int = 50, $offset: Int = 0, $orderBy: [core_urlresult_order_by!] = {created_at: desc}) {
    core_urlresult(
      where: { target_id: { _eq: $targetId } }
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
      core_initialaianalysis_set(
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
    # 新增: 統計總數，用於前端判斷是否還有更多資料
    core_urlresult_aggregate(
      where: { target_id: { _eq: $targetId } }
    ) {
      aggregate {
        count
      }
    }
  }
`;