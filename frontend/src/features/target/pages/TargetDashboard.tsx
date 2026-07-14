import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  gqlFetcher,
  GET_TARGET_DETAIL_QUERY,
  GET_TARGET_SUBDOMAINS_QUERY,
  GET_TARGET_IPS_QUERY,
  GET_TARGET_OVERVIEWS_QUERY,
  GET_TARGET_URLS_QUERY,
} from "../../../services/api";
import { GLOBAL_CONFIG } from "../../../config";
import { createCoreClient } from "../../../services/apiClient";
import { useApiQuery } from "../../../hooks/useApiQuery";
import TargetActivityMonitor from "../../../components/TargetActivityMonitor";
import TechStackCVEReport from "../../../components/TechStackCVEReport";
import type { Target, Seed } from "../../../type";
import TargetHeader from '../components/TargetHeader';
import SeedsTabContent from '../components/SeedsTabContent';
import SubdomainsTabContent from '../components/SubdomainsTabContent';
import IPsTabContent from '../components/IPsTabContent';
import URLsTabContent from '../components/URLsTabContent';
import AIOverviewTabContent from '../components/AIOverviewTabContent';

// ─── Type Definitions ─────────────────────────────────────────
interface Port {
  id: number;
  port_number: number;
  protocol: string;
  service_name: string;
  service_version: string;
  state: string;
  first_seen?: string;
}

interface IPAsset {
  id: number;
  address: string;
  version: number | null;
  ports: Port[];
}

interface SubdomainAsset {
  id: number;
  name: string;
  is_active: boolean;
  is_resolvable: boolean;
  is_cdn: boolean;
  is_waf: boolean;
  created_at: string;
  ips: { id: number; address: string }[];
}

interface URLAsset {
  id: number;
  url: string;
  status_code: number;
  title: string;
  content_length: number | null;
  discovery_source: string;
  content_fetch_status: string;
  created_at: string;
  core_initialaianalysis_set?: { id: number; risk_score: number; summary: string; worth_deep_analysis: boolean; status: string }[];
}

interface AIOverview {
  id: number;
  status: string;
  summary?: string;
  plan?: {
    reasoning?: string;
    objectives?: {
      id: string | number;
      description: string;
      status?: string;
      priority?: string;
    }[];
  };
  knowledge?: Record<string, unknown>;
  risk_score: number;
  business_impact?: string;
  thread_id?: number | null;
  parent_thread_id?: number | null;
  created_at: string;
  updated_at: string;
}

interface SubdomainRaw {
  id: number;
  name: string;
  is_active: boolean;
  is_resolvable: boolean;
  is_cdn: boolean;
  is_waf: boolean;
  created_at: string;
  core_subdomain_ips?: { core_ip: { id: number; address: string } }[];
}

interface IPRaw {
  id: number;
  address: string;
  version: number | null;
  core_ports?: Port[];
}

type TabId = "seeds" | "activity" | "subdomains" | "ips" | "urls" | "cve" | "ai" | "requestConfig";
type SubSortKey = "created_at_desc" | "created_at_asc" | "name_asc" | "name_desc";
type IPSortKey = "id_desc" | "address_asc" | "address_desc";
type URLSortKey = "created_at_desc" | "created_at_asc" | "status_code_asc" | "preliminary_score_desc" | "preliminary_score_asc";

const SUB_PAGE_SIZE = 100;
const IP_PAGE_SIZE = 50;
const URLS_PAGE_SIZE = 50;

const coreApi = createCoreClient();

interface ReqConfig {
  header_enabled: boolean | null;
  header_username: string | null;
  header_prefix: string | null;
  custom_headers: Record<string, string>;
  rps: number | null;
  max_concurrency: number | null;
  timeout: number | null;
}

const DEFAULT_REQ_CONFIG: ReqConfig = { header_enabled: null, header_username: null, header_prefix: null, custom_headers: {}, rps: null, max_concurrency: null, timeout: null };

// ─── MAIN COMPONENT ────────────────────────────────────────────
function TargetDashboard() {
  const navigate = useNavigate();
  const { targetId } = useParams<{ targetId: string }>();
  const numericId = Number(targetId);

  const [target, setTarget] = useState<Target | null>(null);
  const [seeds, setSeeds] = useState<Seed[]>([]);
  const [subdomains, setSubdomains] = useState<SubdomainAsset[]>([]);
  const [ips, setIps] = useState<IPAsset[]>([]);
  const [urls, setUrls] = useState<URLAsset[]>([]);
  const [overview, setOverview] = useState<AIOverview | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>("seeds");
  const [loading, setLoading] = useState(true);
  const [tabLoading, setTabLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Subdomains sort / filter / pagination
  const [subSortBy, setSubSortBy] = useState<SubSortKey>("created_at_desc");
  const [subSearch, setSubSearch] = useState("");
  const [subFilterCdn, setSubFilterCdn] = useState<boolean | null>(null);
  const [subFilterWaf, setSubFilterWaf] = useState<boolean | null>(null);
  const [subPage, setSubPage] = useState(0);
  const [subTotalCount, setSubTotalCount] = useState(0);

  // IPs sort / filter / pagination
  const [ipSortBy, setIpSortBy] = useState<IPSortKey>("id_desc");
  const [ipPortFilter, setIpPortFilter] = useState("");
  const [ipPage, setIpPage] = useState(0);
  const [ipTotalCount, setIpTotalCount] = useState(0);

  // URL sort / filter / pagination
  const [urlsOffset, setUrlsOffset] = useState(0);
  const [urlsTotalCount, setUrlsTotalCount] = useState(0);
  const [urlsSortBy, setUrlsSortBy] = useState<URLSortKey>("created_at_desc");
  const [urlSearch, setUrlSearch] = useState("");
  const [urlStatusFilter, setUrlStatusFilter] = useState("");

  // Per-target request config
  const {
    data: reqConfigFetched,
    loading: reqConfigFetching,
    refetch: refetchReqConfig,
  } = useApiQuery<ReqConfig>(
    () => coreApi.get<ReqConfig>(`/target-request-config/${numericId}`).then(r => r.data),
    [numericId],
    { immediate: false },
  );
  const [reqConfig, setReqConfig] = useState<ReqConfig>(DEFAULT_REQ_CONFIG);
  const [reqConfigSaving, setReqConfigSaving] = useState(false);
  const [reqConfigMsg, setReqConfigMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);

  useEffect(() => {
    if (reqConfigFetched) setReqConfig(reqConfigFetched);
  }, [reqConfigFetched]);

  // ── Fetch base target data ──
  const fetchBase = useCallback(async () => {
    if (!numericId || isNaN(numericId)) return;
    setLoading(true);
    try {
      const data = await gqlFetcher<{ core_target_by_pk: Target }>(
        GET_TARGET_DETAIL_QUERY, { id: numericId }
      );
      if (!data.core_target_by_pk) { setError("Target not found"); return; }
      setTarget(data.core_target_by_pk);
      setSeeds(data.core_target_by_pk.core_seeds || []);
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Failed to load target"); }
    finally { setLoading(false); }
  }, [numericId]);

  // ── Fetch Subdomains ──
  const fetchSubdomains = useCallback(async (
    page: number,
    sortBy: SubSortKey,
    search: string,
    filterCdn: boolean | null,
    filterWaf: boolean | null,
  ) => {
    if (!numericId || isNaN(numericId)) return;
    setTabLoading(true);
    try {
      const where: Record<string, unknown> = { target_id: { _eq: numericId } };
      if (search.trim()) where.name = { _ilike: `%${search.trim()}%` };
      if (filterCdn !== null) where.is_cdn = { _eq: filterCdn };
      if (filterWaf !== null) where.is_waf = { _eq: filterWaf };

      const sortMap: Record<SubSortKey, Record<string, string>> = {
        created_at_desc: { created_at: "desc" },
        created_at_asc:  { created_at: "asc" },
        name_asc:        { name: "asc" },
        name_desc:       { name: "desc" },
      };

      const d = await gqlFetcher<{
        core_subdomain: SubdomainRaw[];
        core_subdomain_aggregate: { aggregate: { count: number } };
      }>(GET_TARGET_SUBDOMAINS_QUERY, {
        where,
        orderBy: sortMap[sortBy],
        limit: SUB_PAGE_SIZE,
        offset: page * SUB_PAGE_SIZE,
      });

      setSubdomains((d.core_subdomain || []).map(sub => ({
        ...sub,
        ips: (sub.core_subdomain_ips || []).map(item => item.core_ip),
      })));
      setSubTotalCount(d.core_subdomain_aggregate?.aggregate?.count ?? 0);
      setSubPage(page);
    } catch (e) { console.error("Subdomain fetch error:", e); }
    finally { setTabLoading(false); }
  }, [numericId]);

  // ── Fetch IPs ──
  const fetchIPs = useCallback(async (
    page: number,
    sortBy: IPSortKey,
    portFilter: string,
  ) => {
    if (!numericId || isNaN(numericId)) return;
    setTabLoading(true);
    try {
      const where: Record<string, unknown> = { target_id: { _eq: numericId } };
      const portNum = parseInt(portFilter);
      if (portFilter && !isNaN(portNum)) {
        where.core_ports = { port_number: { _eq: portNum } };
      }

      const sortMap: Record<IPSortKey, Record<string, string>> = {
        id_desc:      { id: "desc" },
        address_asc:  { address: "asc" },
        address_desc: { address: "desc" },
      };

      const d = await gqlFetcher<{
        core_ip: IPRaw[];
        core_ip_aggregate: { aggregate: { count: number } };
      }>(GET_TARGET_IPS_QUERY, {
        where,
        orderBy: sortMap[sortBy],
        limit: IP_PAGE_SIZE,
        offset: page * IP_PAGE_SIZE,
      });

      setIps((d.core_ip || []).map(ip => ({
        id: ip.id,
        address: ip.address,
        version: ip.version,
        ports: ip.core_ports || [],
      })));
      setIpTotalCount(d.core_ip_aggregate?.aggregate?.count ?? 0);
      setIpPage(page);
    } catch (e) { console.error("IP fetch error:", e); }
    finally { setTabLoading(false); }
  }, [numericId]);

  // ── Fetch URLs ──
  const fetchURLs = useCallback(async (
    offset: number,
    sortBy: URLSortKey,
    search: string,
    statusFilter: string,
  ) => {
    if (!numericId || isNaN(numericId)) return;
    setTabLoading(true);
    try {
      const where: Record<string, unknown> = { target_id: { _eq: numericId } };
      if (search.trim()) where.url = { _ilike: `%${search.trim()}%` };
      const statusNum = parseInt(statusFilter);
      if (statusFilter && !isNaN(statusNum)) where.status_code = { _eq: statusNum };

      const orderByMap: Record<string, Record<string, string>> = {
        created_at_desc: { created_at: "desc" },
        created_at_asc:  { created_at: "asc" },
        status_code_asc: { status_code: "asc" },
      };
      const orderBy = orderByMap[sortBy] ?? { created_at: "desc" };

      const d = await gqlFetcher<{
        core_urlresult: URLAsset[];
        core_urlresult_aggregate: { aggregate: { count: number } };
      }>(GET_TARGET_URLS_QUERY, {
        where,
        limit: URLS_PAGE_SIZE,
        offset,
        orderBy,
      });

      let fetched = d.core_urlresult || [];
      if (sortBy === "preliminary_score_desc" || sortBy === "preliminary_score_asc") {
        fetched = [...fetched].sort((a, b) => {
          const sA = a.core_initialaianalysis_set?.[0]?.risk_score ?? -1;
          const sB = b.core_initialaianalysis_set?.[0]?.risk_score ?? -1;
          return sortBy === "preliminary_score_desc" ? sB - sA : sA - sB;
        });
      }

      setUrls(fetched);
      setUrlsOffset(offset);
      setUrlsTotalCount(d.core_urlresult_aggregate?.aggregate?.count ?? 0);
    } catch (e) { console.error("URL fetch error:", e); }
    finally { setTabLoading(false); }
  }, [numericId]);

  // ── Fetch AI Overview (1:1 — target 最多僅一筆) ──
  const fetchOverviews = useCallback(async () => {
    if (!numericId || isNaN(numericId)) return;
    setTabLoading(true);
    try {
      const d = await gqlFetcher<{ core_overview: AIOverview[] }>(
        GET_TARGET_OVERVIEWS_QUERY, { targetId: numericId }
      );
      const list = d.core_overview || [];
      setOverview(list.length > 0 ? list[0] : null);
    } catch (e) { console.error("Overview fetch error:", e); }
    finally { setTabLoading(false); }
  }, [numericId]);

  const apiBase = GLOBAL_CONFIG.DJANGO_API_BASE;

  const saveReqConfig = async () => {
    if (!numericId) return;
    setReqConfigSaving(true);
    setReqConfigMsg(null);
    try {
      const res = await fetch(`${apiBase}/core/target-request-config/${numericId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reqConfig),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setReqConfigMsg({ type: 'ok', text: 'Saved' });
      setTimeout(() => setReqConfigMsg(null), 3000);
    } catch (e) {
      setReqConfigMsg({ type: 'err', text: e instanceof Error ? e.message : 'Unknown error' });
    } finally { setReqConfigSaving(false); }
  };

  const resetReqConfig = async () => {
    if (!numericId) return;
    try {
      const res = await fetch(`${apiBase}/core/target-request-config/${numericId}`, { method: 'DELETE' });
      if (!res.ok && res.status !== 404) throw new Error(`HTTP ${res.status}`);
      setReqConfig({ header_enabled: null, header_username: null, header_prefix: null, custom_headers: {}, rps: null, max_concurrency: null, timeout: null });
      setReqConfigMsg({ type: 'ok', text: 'Reset to global defaults' });
      setTimeout(() => setReqConfigMsg(null), 3000);
    } catch (e) {
      setReqConfigMsg({ type: 'err', text: e instanceof Error ? e.message : 'Unknown error' });
    }
  };

  useEffect(() => { fetchBase(); }, [fetchBase]);

  const handleTabChange = (tab: TabId) => {
    setActiveTab(tab);
    if (tab === "subdomains") {
      setSubPage(0);
      fetchSubdomains(0, subSortBy, subSearch, subFilterCdn, subFilterWaf);
    } else if (tab === "ips") {
      setIpPage(0);
      fetchIPs(0, ipSortBy, ipPortFilter);
    } else if (tab === "urls") {
      setUrlsOffset(0);
      fetchURLs(0, urlsSortBy, urlSearch, urlStatusFilter);
    } else if (tab === "ai") {
      fetchOverviews();
    } else if (tab === "requestConfig") {
      refetchReqConfig();
    }
  };

  if (isNaN(numericId)) return <div className="c2-loading">INVALID TARGET ID</div>;
  if (loading && !target) return <div className="c2-loading">INITIALIZING DASHBOARD...</div>;
  if (error) return <div className="c2-loading text-red">ERROR: {error}</div>;
  if (!target) return null;

  const TABS: { id: TabId; label: string; count?: number }[] = [
    { id: "seeds",      label: "Seeds",         count: seeds.length },
    { id: "activity",   label: "AI Activity" },
    { id: "subdomains", label: "Subdomains",    count: subTotalCount || undefined },
    { id: "ips",        label: "IPs / Ports",   count: ipTotalCount || undefined },
    { id: "urls",       label: "URLs",          count: urlsTotalCount || undefined },
    { id: "cve",        label: "CVE Report" },
    { id: "ai",         label: "AI Overview",   count: overview ? 1 : undefined },
    { id: "requestConfig", label: "Req Config" },
  ];

  return (
    <div className="c2-page min-h-[calc(100vh-var(--spacing-navbar))]">
      {/* ── Header ── */}
      <TargetHeader target={target} seeds={seeds} onBack={() => navigate("/")} />

      {/* ── Tabs ── */}
      <div className="c2-tabs">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`c2-tab ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => handleTabChange(tab.id)}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span className="inline-flex min-w-[22px] justify-center bg-[rgba(6,182,212,0.12)] border border-[rgba(6,182,212,0.22)] text-cyan text-[0.6rem] px-1.5 py-px rounded-[10px] ml-1.5 font-mono">{tab.count}</span>
            )}
          </button>
        ))}
      </div>

      {/* ── Tab Content ── */}
      <div className="min-h-[300px] border border-[rgba(148,163,184,0.08)] rounded-[20px] bg-[rgba(5,8,20,0.22)] p-3.5">

        {/* SEEDS TAB */}
        {activeTab === "seeds" && (
          <SeedsTabContent targetId={numericId} seeds={seeds} onRefresh={fetchBase} />
        )}

        {/* ACTIVITY TAB */}
        {activeTab === "activity" && (
          <div className="flex flex-col h-full gap-3">
            <div className="c2-section-header">
              <span className="c2-section-title">AI ACTIVITY MONITOR</span>
              <span className="td-muted text-xs">
                Real-time tracking of AI operations on this target
              </span>
            </div>
            <div className="flex-1 min-h-0 px-4">
              <TargetActivityMonitor targetId={numericId} compact={false} maxSteps={50} />
            </div>
          </div>
        )}

        {/* SUBDOMAINS TAB */}
        {activeTab === "subdomains" && (
          <SubdomainsTabContent
            targetId={numericId}
            subdomains={subdomains as any}
            tabLoading={tabLoading}
            subTotalCount={subTotalCount}
            subSortBy={subSortBy}
            subSearch={subSearch}
            subFilterCdn={subFilterCdn}
            subFilterWaf={subFilterWaf}
            subPage={subPage}
            pageSize={SUB_PAGE_SIZE}
            onFetch={fetchSubdomains as any}
            onSortChange={setSubSortBy}
            onSearchChange={setSubSearch}
            onFilterCdnChange={setSubFilterCdn}
            onFilterWafChange={setSubFilterWaf}
          />
        )}

        {/* IPs / PORTS TAB */}
        {activeTab === "ips" && (
          <IPsTabContent
            ips={ips as any}
            tabLoading={tabLoading}
            ipTotalCount={ipTotalCount}
            ipSortBy={ipSortBy}
            ipPortFilter={ipPortFilter}
            ipPage={ipPage}
            pageSize={IP_PAGE_SIZE}
            onFetch={fetchIPs as any}
            onSortChange={setIpSortBy}
            onPortFilterChange={setIpPortFilter}
          />
        )}

        {/* URLs TAB */}
        {activeTab === "urls" && (
          <URLsTabContent
            urls={urls as any}
            tabLoading={tabLoading}
            urlsTotalCount={urlsTotalCount}
            urlsSortBy={urlsSortBy}
            urlSearch={urlSearch}
            urlStatusFilter={urlStatusFilter}
            urlsOffset={urlsOffset}
            pageSize={URLS_PAGE_SIZE}
            onFetch={fetchURLs as any}
            onSortChange={setUrlsSortBy}
            onSearchChange={setUrlSearch}
            onStatusFilterChange={setUrlStatusFilter}
          />
        )}

        {/* CVE REPORT TAB */}
        {activeTab === "cve" && (
          <div className="p-5">
            <TechStackCVEReport targetId={numericId} />
          </div>
        )}

        {/* AI OVERVIEW TAB */}
        {activeTab === "ai" && (
          <AIOverviewTabContent
            overview={overview}
            tabLoading={tabLoading}
            onRefresh={fetchOverviews}
          />
        )}

        {/* REQUEST CONFIG TAB */}
        {activeTab === "requestConfig" && (
          <div className="p-5 max-w-[700px]">
            <div className="c2-section-header">
              <span className="c2-section-title">REQUEST CONFIG OVERRIDE</span>
              <div className="flex gap-2">
                <button className="c2-btn c2-btn--ghost text-[0.7rem]" onClick={() => void refetchReqConfig()}>↻ REFRESH</button>
              </div>
            </div>
            <p className="text-xs text-text-muted mb-4">
              留空的欄位會自動繼承全域設定（Pentest Config 頁面）。設定值會覆蓋全域預設。
            </p>

            <div className="bg-[rgba(15,23,42,0.6)] border border-border-subtle rounded-md p-5 mb-4">
              <div className="text-[0.72rem] text-green uppercase tracking-[1px] mb-3">Header Injection</div>
              <div className="flex gap-4 mb-3">
                <div className="flex-1">
                  <label className="block text-[0.65rem] text-text-muted mb-1 uppercase">Enabled</label>
                  <select
                    value={reqConfig.header_enabled === null ? 'inherit' : reqConfig.header_enabled ? 'true' : 'false'}
                    onChange={(e) => setReqConfig({ ...reqConfig, header_enabled: e.target.value === 'inherit' ? null : e.target.value === 'true' })}
                    className="w-full px-2.5 py-2 bg-bg-card border border-border-subtle rounded text-text-primary text-[0.78rem] font-mono"
                  >
                    <option value="inherit">繼承全域</option>
                    <option value="true">啟用</option>
                    <option value="false">停用</option>
                  </select>
                </div>
              </div>
              <div className="flex gap-4 mb-3">
                <div className="flex-1">
                  <label className="block text-[0.65rem] text-text-muted mb-1 uppercase">Username</label>
                  <input
                    className="pentest-config-input w-full px-2.5 py-2 bg-bg-card border border-border-subtle rounded text-text-primary text-[0.78rem] font-mono"
                    type="text"
                    value={reqConfig.header_username || ''}
                    onChange={(e) => setReqConfig({ ...reqConfig, header_username: e.target.value || null })}
                    placeholder="繼承全域設定"
                  />
                </div>
                <div className="flex-1">
                  <label className="block text-[0.65rem] text-text-muted mb-1 uppercase">Header Prefix</label>
                  <input
                    type="text"
                    value={reqConfig.header_prefix || ''}
                    onChange={(e) => setReqConfig({ ...reqConfig, header_prefix: e.target.value || null })}
                    placeholder="繼承全域設定"
                    className="w-full px-2.5 py-2 bg-bg-card border border-border-subtle rounded text-text-primary text-[0.78rem] font-mono"
                  />
                </div>
              </div>
              <div>
                <label className="block text-[0.65rem] text-text-muted mb-1 uppercase">Custom Headers (JSON)</label>
                <textarea
                  value={JSON.stringify(reqConfig.custom_headers, null, 2)}
                  onChange={(e) => {
                    try { setReqConfig({ ...reqConfig, custom_headers: JSON.parse(e.target.value) }); } catch { /* ignore invalid JSON while typing */ }
                  }}
                  placeholder='{"X-Custom": "value"}'
                  rows={3}
                  className="w-full px-2.5 py-2 bg-bg-card border border-border-subtle rounded text-text-primary text-[0.78rem] font-mono resize-y box-border"
                />
              </div>
            </div>

            <div className="bg-[rgba(15,23,42,0.6)] border border-border-subtle rounded-md p-5 mb-4">
              <div className="text-[0.72rem] text-green uppercase tracking-[1px] mb-3">Rate Limiting</div>
              <div className="flex gap-4 mb-3">
                <div className="flex-1">
                  <label className="block text-[0.65rem] text-text-muted mb-1 uppercase">RPS (Requests/sec)</label>
                  <input
                    type="number"
                    min={1}
                    value={reqConfig.rps ?? ''}
                    onChange={(e) => setReqConfig({ ...reqConfig, rps: e.target.value ? Number(e.target.value) : null })}
                    placeholder="繼承全域設定"
                    className="w-full px-2.5 py-2 bg-bg-card border border-border-subtle rounded text-text-primary text-[0.78rem] font-mono"
                  />
                </div>
                <div className="flex-1">
                  <label className="block text-[0.65rem] text-text-muted mb-1 uppercase">Max Concurrency</label>
                  <input
                    type="number"
                    min={1}
                    value={reqConfig.max_concurrency ?? ''}
                    onChange={(e) => setReqConfig({ ...reqConfig, max_concurrency: e.target.value ? Number(e.target.value) : null })}
                    placeholder="繼承全域設定"
                    className="w-full px-2.5 py-2 bg-bg-card border border-border-subtle rounded text-text-primary text-[0.78rem] font-mono"
                  />
                </div>
                <div className="flex-1">
                  <label className="block text-[0.65rem] text-text-muted mb-1 uppercase">Timeout (sec)</label>
                  <input
                    type="number"
                    min={1}
                    value={reqConfig.timeout ?? ''}
                    onChange={(e) => setReqConfig({ ...reqConfig, timeout: e.target.value ? Number(e.target.value) : null })}
                    placeholder="繼承全域設定"
                    className="w-full px-2.5 py-2 bg-bg-card border border-border-subtle rounded text-text-primary text-[0.78rem] font-mono"
                  />
                </div>
              </div>
            </div>

            <div className="flex gap-2 items-center">
              <button className="c2-btn c2-btn--ghost text-[0.72rem] px-4 py-2" onClick={saveReqConfig} disabled={reqConfigSaving}>
                {reqConfigSaving ? 'Saving...' : 'Save'}
              </button>
              <button className="c2-btn c2-btn--ghost text-[0.72rem] px-4 py-2" onClick={resetReqConfig}>
                Reset to Global
              </button>
              {reqConfigMsg && (
                <span className="text-[0.72rem]" style={{ color: reqConfigMsg.type === 'ok' ? 'var(--green)' : 'var(--red)' }}>
                  {reqConfigMsg.text}
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default TargetDashboard;
