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
  address?: string | null;  // GenericIPAddressField (IPv4 or IPv6)
  version?: number | null;
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
// 3.1 Nmap Scan Result Page (legacy page)
// ==================================================================

export interface PortSchema {
  port_number: number;
  protocol: string;
  state: string;
  service_name?: string | null;
  service_version?: string | null;
}

export interface NmapScanSchema {
  id: number;
  target_id: number;
  scan_type: string;
  status: ScanStatus | string;
  started_at: string;
  completed_at?: string | null;
  error_message?: string | null;
  ports: PortSchema[];
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
  raw_response?: unknown;
}

export interface InitialAIAnalysis {
  summary: string;
  inferred_purpose: string;
  risk_score: number;
  worth_deep_analysis: boolean;
  status: ScanStatus;
  created_at: string;
  completed_at?: string | null;
  error_message?: string | null;
  raw_response?: unknown;
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
  core_subdomainseeds: {
    core_subdomain: Subdomain;
  }[];
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
    cdn_name?: string | null;

    waf_name?: string | null;
    core_subdomain_ips: {
      core_ip: IP;
    }[];
    core_initialaianalyses: InitialAIAnalysis[];
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

// ==================================================================
// CVE Intelligence Types
// ==================================================================

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
