import axios from 'axios';
import { GLOBAL_CONFIG } from '../config';

const cveApi = axios.create({
  baseURL: `${GLOBAL_CONFIG.DJANGO_API_BASE}/scanners/cve`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

// ===== 类型定义 =====
export interface CVEIntelligence {
  id: number;
  cve_id: string;
  description: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  cvss_score: number | null;
  cvss_vector: string | null;
  affected_products: Array<{
    vendor: string;
    product: string;
    version?: string;
  }>;
  exploit_available: boolean;
  exploited_in_wild: boolean;
  cisa_kev: boolean;
  epss_score: number | null;
  references: Array<{
    url: string;
    tags?: string[];
  }>;
  cwe_ids?: string[];
  published_date: string | null;
  created_at: string;
  updated_at: string;
  risk_score?: number;
}

export interface TechStackCVEMapping {
  cve_id: string;
  severity: string;
  cvss_score: number | null;
  cisa_kev: boolean;
  exploit_available: boolean;
  techstack_name: string;
  techstack_version: string | null;
  confidence: number;
}

export interface TechStackCVEReport {
  target_id: number;
  total_cves: number;
  critical_count: number;
  high_count: number;
  kev_count: number;
  top_cves: TechStackCVEMapping[];
}

// ===== API 方法 =====
export const CVEService = {
  /**
   * 获取目标的技术栈 CVE 报告
   */
  getTechStackReport: async (targetId: number): Promise<TechStackCVEReport> => {
    const response = await cveApi.get<TechStackCVEReport>(`/techstack_report/${targetId}`);
    return response.data;
  },

  /**
   * 同步目标技术栈 CVE（异步任务）
   */
  syncTechStack: async (targetId: number): Promise<{ detail: string }> => {
    const response = await cveApi.post<{ detail: string }>('/sync_techstack', { target_id: targetId });
    return response.data;
  },

  /**
   * 查询单个 CVE 详情（P1）
   * use_nvd: 若本地 DB 沒有，是否嘗試從 NVD 拉取（預設 true）
   */
  queryCVE: async (cveId: string, useNvd = true): Promise<CVEIntelligence> => {
    const response = await cveApi.post<CVEIntelligence>('/query', {
      cve_id: cveId,
      use_nvd: useNvd,
    });
    return response.data;
  },

  /**
   * 搜索 CVE（按技术名称和版本）（P1）
   */
  searchCVEs: async (params: {
    tech_name: string;
    version?: string;
    severity_min?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
    exploited_only?: boolean;
    limit?: number;
    pub_start_date?: string;
    pub_end_date?: string;
    min_cvss?: number;
    min_epss?: number;
  }): Promise<{ total: number; cves: CVEIntelligence[] }> => {
    const response = await cveApi.post<{ total: number; cves: CVEIntelligence[] }>('/search', params);
    return response.data;
  },

  /**
   * 批量丰富化漏洞（异步任务）（P2）
   */
  enrichVulnerabilities: async (vulnerabilityIds: number[]): Promise<{ detail: string }> => {
    const response = await cveApi.post<{ detail: string }>('/enrich_vulnerabilities', {
      vulnerability_ids: vulnerabilityIds,
    });
    return response.data;
  },

  /**
   * 同步 CISA KEV 数据库（异步任务）（P2）
   */
  syncKEV: async (): Promise<{ detail: string }> => {
    const response = await cveApi.post<{ detail: string }>('/sync_kev', {});
    return response.data;
  },
};
