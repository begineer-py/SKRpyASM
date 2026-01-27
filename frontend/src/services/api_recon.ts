import axios from 'axios';
import { GLOBAL_CONFIG } from '../config';
import type { SubfinderScan, DomainReconTriggerPayload } from '../type';

// 專門用於偵察的 Axios 實例
const reconApi = axios.create({
  baseURL: `${GLOBAL_CONFIG.DJANGO_API_BASE}/subfinder`, // 假設掛載路徑
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000, 
});

export const ReconService = {
  /**
   * 觸發 Subfinder / 全域名偵察鏈
   * POST /start_subfinder
   */
  startDomainRecon: async (seedId: number): Promise<SubfinderScan> => {
    try {
      const payload: DomainReconTriggerPayload = { seed_id: seedId };
      const response = await reconApi.post<SubfinderScan>('/start_subfinder', payload);
      return response.data;
    } catch (error: any) {
      // 處理 409 (衝突/任務已在運行)
      if (error.response?.status === 409) {
        throw new Error('任務已在運行中，請勿重複觸發');
      }
      throw new Error(error.response?.data?.message || '啟動偵察失敗');
    }
  }
};

export const GET_SEED_INFO = `
  query GetSeedInfo($seed_id: bigint!) {
    core_seed_by_pk(id: $seed_id) {
      id
      value
      type
      target_id
    }
  }
`;

// src/services/api_recon.ts

// ... (保留 ReconService) ...

// [替換] 使用你的終極查詢
export const GET_SEED_ULTIMATE_INTEL_QUERY = `
query GetSeedUltimateIntel($seed_id: bigint!) {
  core_seed(where: {id: {_eq: $seed_id}}) {
    id
    target_id
    type
    value
    is_active
    created_at

    # 1. NmapScans (透過 M2M 中間表)
    core_nmapscan_which_seeds(order_by: {core_nmapscan: {completed_at: desc}}) {
      core_nmapscan {
        completed_at
        status
        id
      }
    }

    # 2. SubfinderScans (這應該還是外鍵，直接拿)
    core_subfinderscans(order_by: {created_at: desc}) {
      completed_at
      added_count
      id
      created_at
      status
      started_at
    }

    # 3. IP 資產 (透過 M2M 中間表)
    core_ip_which_seeds {
      core_ip {
        id
        ipv4
        ipv6
      }
    }

    # 4. 子域名 & URL (重點！透過 SubdomainSeed 中間表)
    core_subdomainseeds {
      core_subdomain {  # 注意：Hasura 這裡通常是單數，代表中間表連到該子域名的一條線
        id
        name
        created_at
        # URL 又是另一層 M2M... 繼續鑽
        core_urlresult_related_subdomains {
          core_urlresult {
            id
            url
            status_code
            content_fetch_status
          }
        }
      }
    }
  }
}


`;