// src/type.ts

// ==================================================================
// 1. 基础枚举和 API Payloads
// ==================================================================

export type ScanStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
export type ScanMode = 'DOMAIN' | 'IP' | 'URL';

export interface CreateTargetPayload {
  name: string;
  description?: string;
}

export interface UpdateTargetPayload {
  name?: string;
  description?: string;
}

export interface AddSeedPayload {
  value: string;
  type?: string;
}
export interface DomainReconTriggerPayload {
  seed_id: number;
}

// ==================================================================
// 2. 核心资产模型 (Assets)
// ==================================================================

export interface Target {
  id: number;
  name: string;
  description?: string | null;
  created_at: string;
  core_seeds?: Seed[];
}

export interface Seed {
  id: number;
  target_id: number;
  value: string;
  type: string;
  is_active: boolean;
  created_at: string;
}

export interface IP {
  id: number;
  ipv4?: string | null;
  ipv6?: string | null;
}

export interface UrlResult {
  id: number;
  url: string;
  content_length?: number;
  content_fetch_status?: string;
}

export interface Subdomain {
  id: number;
  name: string;
  created_at: string;
  core_urlscans: UrlScan[];
  core_urlresult_related_subdomains: {
    core_urlresult: UrlResult;
  }[];
}


// ==================================================================
// 3. 扫描记录模型 (Scan Records)
// ==================================================================

export interface SubfinderScan {
  id: number;
  status: ScanStatus;
  created_at: string;
  completed_at?: string | null;
  added_count: number;
}

export interface NmapScan {
  id: number;
  status: ScanStatus;
  completed_at?: string | null;
}

export interface UrlScan {
  id: number;
  status: ScanStatus;
  created_at: string;
  completed_at?: string | null;
  added_count: number;
}


// ==================================================================
// 4. AI 分析模型
// ==================================================================

export interface SubdomainAIAnalysis {
  risk_score: number;
  summary: string;
  business_impact: string;
  inferred_purpose: string;
  tech_stack_summary: string;
  potential_vulnerabilities: string[];
  recommended_actions: string[];
  command_actions: string[];
  status: ScanStatus;
  created_at: string;
  completed_at?: string | null;
  error_message?: string | null;
  raw_response?: any;
}


// ==================================================================
// 5. GraphQL 聚合响应模型 (最重要的部分)
// ==================================================================

/**
 * [修正] Seed 及其关联资产的层级结构，现在是一个独立的、可导出的类型。
 */
export interface SeedIntelligenceData {
  id: number;
  value: string;
  type: string;
  is_active: boolean;
  created_at: string;
  core_nmapscans: NmapScan[];
  core_subfinderscans: SubfinderScan[];
  core_subdomains: Subdomain[];
  core_ip_which_seeds: {
    core_ip: IP;
  }[];
}

/**
 * @description 用于 SeedReconPage 的终极情报聚合体
 */
export interface SeedIntelligenceResponse {
  core_seed: SeedIntelligenceData[];
}

/**
 * @description 用于 SubdomainDetailPage 的深度情报聚合体
 */
export interface SubdomainIntelResponse {
  core_subdomain_by_pk: {
    id: number;
    name: string;
    created_at: string;
    is_active: boolean;
    is_resolvable: boolean;
    is_cdn: boolean;
    is_waf: boolean;
    cname?: string | null;
    cdn_name?: string | null;
    waf_name?: string | null;
    core_subdomain_ips: {
      core_ip: IP;
    }[];
    core_subdomainaianalysis: SubdomainAIAnalysis | null;
  };
  core_urlresult: UrlResult[];
}

/**
 * @description 用于 UrlReconPage 的情报聚合体
 */
export interface UrlSeedIntelligenceResponse {
  core_seed_by_pk: {
    id: number;
    value: string;
    type: string;
    core_gauscans: UrlScan[];
    core_urlresults: UrlResult[];
  };
}