import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  gqlFetcher,
  GET_TARGET_DETAIL_QUERY,
  GET_TARGET_SUBDOMAINS_QUERY,
  GET_TARGET_IPS_QUERY,
  GET_TARGET_OVERVIEWS_QUERY,
  GET_TARGET_URLS_QUERY,
} from "../../services/api";
import { SeedService } from "../../services/api_seed";
import { GLOBAL_CONFIG } from "../../config";
import TargetActivityMonitor from "../../components/TargetActivityMonitor";
import TechStackCVEReport from "../../components/TechStackCVEReport";
import { SkeletonTable, SkeletonCards } from "../../components/SkeletonLoader";
import type { Target, Seed } from "../../type";
import "./TargetDashboard.css";

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

interface InitialAIAnalysis {
  id: number;
  risk_score: number;
  summary: string;
  worth_deep_analysis: boolean;
  status: string;
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
  core_initialaianalysis_set?: InitialAIAnalysis[];
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

// ─── Helper Components ─────────────────────────────────────────
const StatusBadge = ({ status }: { status: string }) => {
  const map: Record<string, string> = {
    PLANNING: "cyan", EXECUTING: "green", STALLED: "amber",
    COMPLETED: "green", PENDING: "muted", RUNNING: "cyan",
    FAILED: "red", OPEN: "green", CLOSED: "muted", FILTERED: "amber",
  };
  const c = map[status?.toUpperCase()] ?? "muted";
  return <span className={`c2-badge c2-badge--${c}`}>{status}</span>;
};

const RiskBar = ({ score }: { score: number }) => {
  const color = score >= 70 ? "#ef4444" : score >= 40 ? "#f59e0b" : "#22C55E";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{ flex: 1, height: 4, background: "#1e293b", borderRadius: 2, overflow: "hidden" }}>
        <div style={{ width: `${score}%`, height: "100%", background: color, borderRadius: 2, transition: "width 0.6s ease" }} />
      </div>
      <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color }}>{score}</span>
    </div>
  );
};

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
  const [overviews, setOverviews] = useState<AIOverview[]>([]);
  const [activeTab, setActiveTab] = useState<TabId>("seeds");
  const [loading, setLoading] = useState(true);
  const [tabLoading, setTabLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Add seed form
  const [newSeedVal, setNewSeedVal] = useState("");
  const [newSeedType, setNewSeedType] = useState("DOMAIN");
  const [isAdding, setIsAdding] = useState(false);

  // Expanded IP rows
  const [expandedIp, setExpandedIp] = useState<number | null>(null);

  // Subdomains sort / filter / pagination
  const [subSortBy, setSubSortBy] = useState<SubSortKey>("created_at_desc");
  const [subSearch, setSubSearch] = useState("");
  const [subFilterCdn, setSubFilterCdn] = useState<boolean | null>(null);
  const [subFilterWaf, setSubFilterWaf] = useState<boolean | null>(null);
  const [subPage, setSubPage] = useState(0);
  const [subTotalCount, setSubTotalCount] = useState(0);
  const subSearchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

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
  const urlSearchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Per-target request config
  const [reqConfig, setReqConfig] = useState<{
    header_enabled: boolean | null;
    header_username: string | null;
    header_prefix: string | null;
    custom_headers: Record<string, string>;
    rps: number | null;
    max_concurrency: number | null;
    timeout: number | null;
  }>({ header_enabled: null, header_username: null, header_prefix: null, custom_headers: {}, rps: null, max_concurrency: null, timeout: null });
  const [reqConfigSaving, setReqConfigSaving] = useState(false);
  const [reqConfigMsg, setReqConfigMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);

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

  // ── Fetch AI Overviews ──
  const fetchOverviews = useCallback(async () => {
    if (!numericId || isNaN(numericId)) return;
    setTabLoading(true);
    try {
      const d = await gqlFetcher<{ core_overview: AIOverview[] }>(
        GET_TARGET_OVERVIEWS_QUERY, { targetId: numericId }
      );
      setOverviews(d.core_overview || []);
    } catch (e) { console.error("Overview fetch error:", e); }
    finally { setTabLoading(false); }
  }, [numericId]);

  const apiBase = GLOBAL_CONFIG.DJANGO_API_BASE;

  const fetchReqConfig = useCallback(async () => {
    if (!numericId || isNaN(numericId)) return;
    setTabLoading(true);
    try {
      const res = await fetch(`${apiBase}/core/target-request-config/${numericId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setReqConfig({
        header_enabled: data.header_enabled ?? null,
        header_username: data.header_username ?? null,
        header_prefix: data.header_prefix ?? null,
        custom_headers: data.custom_headers ?? {},
        rps: data.rps ?? null,
        max_concurrency: data.max_concurrency ?? null,
        timeout: data.timeout ?? null,
      });
    } catch (e) { console.error("ReqConfig fetch error:", e); }
    finally { setTabLoading(false); }
  }, [numericId, apiBase]);

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
      fetchReqConfig();
    }
  };

  const handleAddSeed = async () => {
    if (!newSeedVal.trim() || !numericId) return;
    setIsAdding(true);
    try {
      await SeedService.add(numericId, { value: newSeedVal.trim(), type: newSeedType });
      setNewSeedVal("");
      fetchBase();
    } catch (e: unknown) { alert(`Add failed: ${e instanceof Error ? e.message : "Unknown error"}`); }
    finally { setIsAdding(false); }
  };

  const handleDeleteSeed = async (seedId: number) => {
    if (!window.confirm("Remove this seed?")) return;
    try {
      await SeedService.delete(seedId);
      setSeeds(prev => prev.filter(s => s.id !== seedId));
    } catch { alert("Delete failed"); }
  };

  if (isNaN(numericId)) return <div className="c2-loading">INVALID TARGET ID</div>;
  if (loading && !target) return <div className="c2-loading">INITIALIZING DASHBOARD...</div>;
  if (error) return <div className="c2-loading" style={{ color: "var(--red)" }}>ERROR: {error}</div>;
  if (!target) return null;

  const TABS: { id: TabId; label: string; count?: number }[] = [
    { id: "seeds",      label: "Seeds",         count: seeds.length },
    { id: "activity",   label: "AI Activity" },
    { id: "subdomains", label: "Subdomains",    count: subTotalCount || undefined },
    { id: "ips",        label: "IPs / Ports",   count: ipTotalCount || undefined },
    { id: "urls",       label: "URLs",          count: urlsTotalCount || undefined },
    { id: "cve",        label: "CVE Report" },
    { id: "ai",         label: "AI Overview",   count: overviews.length || undefined },
    { id: "requestConfig", label: "Req Config" },
  ];

  return (
    <div className="td-outer c2-page">
      {/* ── Header ── */}
      <header className="td-header">
        <div className="td-header__left">
            <button onClick={() => navigate("/")} className="c2-btn c2-btn--ghost td-back-btn">
              Back
            </button>
            <div>
              <div className="td-eyebrow">Target Mission Control</div>
              <h1 className="td-title">
                {target.name}
                <span className="td-title__sub">Authorized operation</span>
              </h1>
            <p className="td-subtitle">{target.description || "No description provided"}</p>
          </div>
        </div>
        <div className="td-header__stats">
          <div className="c2-stat">
            <div className="c2-stat__label">Seeds</div>
            <div className="c2-stat__value">{seeds.length}</div>
          </div>
          <div className="c2-stat">
            <div className="c2-stat__label">Target ID</div>
            <div className="c2-stat__value--cyan c2-stat__value">#{target.id}</div>
          </div>
          <div className="c2-stat">
            <div className="c2-stat__label">Active Seeds</div>
            <div className="c2-stat__value">{seeds.filter(s => s.is_active).length}</div>
          </div>
        </div>
      </header>

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
              <span className="td-tab-count">{tab.count}</span>
            )}
          </button>
        ))}
      </div>

      {/* ── Tab Content ── */}
      <div className="td-content">

        {/* SEEDS TAB */}
        {activeTab === "seeds" && (
          <div className="td-seeds-layout">
            <div className="td-seeds-main c2-card" style={{ padding: 16 }}>
              <div className="c2-section-header">
                <span className="c2-section-title">SEEDS <span>({seeds.length})</span></span>
                <button className="c2-btn c2-btn--ghost" onClick={fetchBase} style={{ fontSize: "0.7rem" }}>
                  Refresh
                </button>
              </div>
              {seeds.length === 0 ? (
                <div className="c2-empty">NO SEEDS CONFIGURED.<br />Add a root domain or IP range to begin reconnaissance.</div>
              ) : (
                <table className="c2-table">
                  <thead><tr>
                    <th>#ID</th><th>TYPE</th><th>VALUE</th><th>STATUS</th><th>ADDED</th><th>ACTIONS</th>
                  </tr></thead>
                  <tbody>
                    {seeds.map(seed => (
                      <tr key={seed.id}>
                        <td className="td-mono">#{seed.id}</td>
                        <td>
                          <span className={`c2-badge ${seed.type === "DOMAIN" ? "c2-badge--green" : seed.type === "URL" ? "c2-badge--cyan" : "c2-badge--amber"}`}>
                            {seed.type}
                          </span>
                        </td>
                        <td className="td-mono">{seed.value}</td>
                        <td>
                          <span className={`c2-badge ${seed.is_active ? "c2-badge--green" : "c2-badge--muted"}`}>
                            {seed.is_active ? "ACTIVE" : "INACTIVE"}
                          </span>
                        </td>
                        <td className="td-muted">{new Date(seed.created_at).toLocaleDateString()}</td>
                        <td>
                          <div style={{ display: "flex", gap: 6 }}>
                            {seed.type === "DOMAIN" && (
                              <button className="c2-btn c2-btn--ghost" style={{ padding: "4px 10px", fontSize: "0.68rem" }}
                                onClick={() => navigate(`/target/${target.id}/seed/${seed.id}/subdomain`)}>
                                RECON
                              </button>
                            )}
                            {seed.type === "URL" && (
                              <button className="c2-btn c2-btn--ghost" style={{ padding: "4px 10px", fontSize: "0.68rem" }}
                                onClick={() => navigate(`/target/${target.id}/seed/${seed.id}/url_recon`)}>
                                URL RECON
                              </button>
                            )}
                            <button className="c2-btn c2-btn--danger" style={{ padding: "4px 8px", fontSize: "0.68rem" }}
                              onClick={() => handleDeleteSeed(seed.id)}>×</button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* Add Seed Sidebar */}
            <div className="td-seeds-sidebar c2-card c2-card--green" style={{ padding: 20 }}>
              <h3 style={{ fontFamily: "var(--font-body)", fontSize: "0.95rem", marginBottom: 16, color: "var(--text-primary)", fontWeight: 800 }}>Add Seed</h3>
              <label className="c2-form-label">Seed Value</label>
              <input
                className="c2-input" type="text" placeholder="e.g. example.com"
                value={newSeedVal} onChange={e => setNewSeedVal(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleAddSeed()}
              />
              <label className="c2-form-label">Type</label>
              <select className="c2-select c2-input" value={newSeedType} onChange={e => setNewSeedType(e.target.value)}>
                <option value="DOMAIN">DOMAIN</option>
                <option value="IP_RANGE">IP RANGE</option>
                <option value="URL">URL</option>
              </select>
              <button className="c2-btn c2-btn--primary" style={{ width: "100%", justifyContent: "center" }}
                onClick={handleAddSeed} disabled={isAdding || !newSeedVal.trim()}>
                {isAdding ? "Adding..." : "Add Seed"}
              </button>
              <div style={{ marginTop: 16, fontSize: "0.72rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                <div style={{ marginBottom: 8, color: "var(--text-secondary)" }}>Auto triggers:</div>
                <div>Subdomain Enumeration</div>
                <div>Port Scanning</div>
                <div>AI Initial Analysis</div>
              </div>
            </div>
          </div>
        )}

        {/* ACTIVITY TAB */}
        {activeTab === "activity" && (
          <div style={{ display: "flex", flexDirection: "column", height: "100%", gap: 12 }}>
            <div className="c2-section-header">
              <span className="c2-section-title">AI ACTIVITY MONITOR</span>
              <span className="td-muted" style={{ fontSize: "0.75rem" }}>
                Real-time tracking of AI operations on this target
              </span>
            </div>
            <div style={{ flex: 1, minHeight: 0, padding: "0 16px" }}>
              <TargetActivityMonitor targetId={numericId} compact={false} maxSteps={50} />
            </div>
          </div>
        )}

        {/* SUBDOMAINS TAB */}
        {activeTab === "subdomains" && (
          <>
            {/* Toolbar */}
            <div className="c2-section-header" style={{ flexWrap: "wrap", gap: 8 }}>
              <span className="c2-section-title">
                SUBDOMAINS <span>({subTotalCount})</span>
              </span>
              <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
                {/* Search */}
                <input
                  className="c2-input"
                  placeholder="Search subdomain..."
                  value={subSearch}
                  onChange={e => {
                    const val = e.target.value;
                    setSubSearch(val);
                    if (subSearchTimer.current) clearTimeout(subSearchTimer.current);
                    subSearchTimer.current = setTimeout(() => {
                      fetchSubdomains(0, subSortBy, val, subFilterCdn, subFilterWaf);
                    }, 350);
                  }}
                  style={{ width: 190, fontSize: "0.78rem" }}
                />
                {/* CDN toggle */}
                <button
                  className={`c2-btn c2-btn--sm ${subFilterCdn === true ? "c2-btn--primary" : "c2-btn--ghost"}`}
                  title="Filter: CDN only"
                  onClick={() => {
                    const next = subFilterCdn === true ? null : true;
                    setSubFilterCdn(next);
                    fetchSubdomains(0, subSortBy, subSearch, next, subFilterWaf);
                  }}
                >CDN</button>
                {/* WAF toggle */}
                <button
                  className={`c2-btn c2-btn--sm ${subFilterWaf === true ? "c2-btn--primary" : "c2-btn--ghost"}`}
                  title="Filter: WAF only"
                  onClick={() => {
                    const next = subFilterWaf === true ? null : true;
                    setSubFilterWaf(next);
                    fetchSubdomains(0, subSortBy, subSearch, subFilterCdn, next);
                  }}
                >WAF</button>
                {/* Sort */}
                <select
                  className="c2-input"
                  value={subSortBy}
                  onChange={e => {
                    const val = e.target.value as SubSortKey;
                    setSubSortBy(val);
                    fetchSubdomains(0, val, subSearch, subFilterCdn, subFilterWaf);
                  }}
                  style={{ width: 155, fontSize: "0.78rem" }}
                >
                  <option value="created_at_desc">最新優先</option>
                  <option value="created_at_asc">最舊優先</option>
                  <option value="name_asc">名稱 A→Z</option>
                  <option value="name_desc">名稱 Z→A</option>
                </select>
                <button className="c2-btn c2-btn--ghost"
                  onClick={() => fetchSubdomains(subPage, subSortBy, subSearch, subFilterCdn, subFilterWaf)}
                  style={{ fontSize: "0.7rem" }}>↻</button>
              </div>
            </div>

            {/* Content */}
            {tabLoading ? (
              <SkeletonTable rows={8} cols={7} />
            ) : subdomains.length === 0 ? (
              <div className="c2-empty">No subdomains found.<br />Run Subfinder on a DOMAIN seed to discover subdomains.</div>
            ) : (
              <div className="c2-card" style={{ overflow: "hidden" }}>
                <table className="c2-table">
                  <thead><tr>
                    <th>#ID</th><th>SUBDOMAIN</th><th>CDN</th><th>WAF</th>
                    <th>RESOLVABLE</th><th>STATUS</th><th>LINKED IPs</th><th>DISCOVERED</th><th></th>
                  </tr></thead>
                  <tbody>
                    {subdomains.map(sub => (
                      <tr key={sub.id} onClick={() => navigate(`/target/${numericId}/subdomain/${sub.id}`)}>
                        <td className="td-mono">#{sub.id}</td>
                        <td className="td-mono" style={{ color: "var(--cyan)" }}>{sub.name}</td>
                        <td>
                          {sub.is_cdn
                            ? <span className="c2-badge c2-badge--amber">CDN</span>
                            : <span className="td-muted">—</span>}
                        </td>
                        <td>
                          {sub.is_waf
                            ? <span className="c2-badge c2-badge--red">WAF</span>
                            : <span className="td-muted">—</span>}
                        </td>
                        <td>
                          <span className={`c2-badge ${sub.is_resolvable ? "c2-badge--green" : "c2-badge--red"}`}>
                            {sub.is_resolvable ? "YES" : "NO"}
                          </span>
                        </td>
                        <td>
                          <span className={`c2-badge ${sub.is_active ? "c2-badge--green" : "c2-badge--muted"}`}>
                            {sub.is_active ? "ACTIVE" : "INACTIVE"}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                            {sub.ips.length ? sub.ips.map(ip => (
                              <span key={ip.id} className="c2-badge c2-badge--cyan">{ip.address}</span>
                            )) : <span className="td-muted">—</span>}
                          </div>
                        </td>
                        <td className="td-muted">{new Date(sub.created_at).toLocaleDateString()}</td>
                        <td><span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>→</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Subdomain Pagination */}
            {!tabLoading && subTotalCount > SUB_PAGE_SIZE && (
              <div style={{ display: "flex", justifyContent: "center", gap: 8, padding: "12px 0" }}>
                <button
                  className="c2-btn c2-btn--ghost"
                  onClick={() => fetchSubdomains(subPage - 1, subSortBy, subSearch, subFilterCdn, subFilterWaf)}
                  disabled={subPage === 0}
                  style={{ fontSize: "0.75rem" }}
                >← PREVIOUS</button>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)", display: "flex", alignItems: "center" }}>
                  {subPage * SUB_PAGE_SIZE + 1} — {Math.min((subPage + 1) * SUB_PAGE_SIZE, subTotalCount)} / {subTotalCount}
                </span>
                <button
                  className="c2-btn c2-btn--ghost"
                  onClick={() => fetchSubdomains(subPage + 1, subSortBy, subSearch, subFilterCdn, subFilterWaf)}
                  disabled={(subPage + 1) * SUB_PAGE_SIZE >= subTotalCount}
                  style={{ fontSize: "0.75rem" }}
                >NEXT →</button>
              </div>
            )}
          </>
        )}

        {/* IPs / PORTS TAB */}
        {activeTab === "ips" && (
          <>
            {/* Toolbar */}
            <div className="c2-section-header" style={{ flexWrap: "wrap", gap: 8 }}>
              <span className="c2-section-title">IP ASSETS <span>({ipTotalCount})</span></span>
              <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
                {/* Port filter */}
                <input
                  className="c2-input"
                  placeholder="Filter by port (e.g. 443)"
                  value={ipPortFilter}
                  onChange={e => setIpPortFilter(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === "Enter") fetchIPs(0, ipSortBy, ipPortFilter);
                  }}
                  style={{ width: 190, fontSize: "0.78rem" }}
                />
                <button
                  className="c2-btn c2-btn--ghost"
                  onClick={() => fetchIPs(0, ipSortBy, ipPortFilter)}
                  style={{ fontSize: "0.7rem" }}
                >FILTER</button>
                {ipPortFilter && (
                  <button
                    className="c2-btn c2-btn--ghost"
                    onClick={() => { setIpPortFilter(""); fetchIPs(0, ipSortBy, ""); }}
                    style={{ fontSize: "0.7rem" }}
                  >✕</button>
                )}
                {/* Sort */}
                <select
                  className="c2-input"
                  value={ipSortBy}
                  onChange={e => {
                    const val = e.target.value as IPSortKey;
                    setIpSortBy(val);
                    fetchIPs(0, val, ipPortFilter);
                  }}
                  style={{ width: 155, fontSize: "0.78rem" }}
                >
                  <option value="id_desc">最新新增</option>
                  <option value="address_asc">IP 位址 A→Z</option>
                  <option value="address_desc">IP 位址 Z→A</option>
                </select>
                <button className="c2-btn c2-btn--ghost"
                  onClick={() => fetchIPs(ipPage, ipSortBy, ipPortFilter)}
                  style={{ fontSize: "0.7rem" }}>↻</button>
              </div>
            </div>

            {/* Content */}
            {tabLoading ? (
              <SkeletonCards count={6} height={52} />
            ) : ips.length === 0 ? (
              <div className="c2-empty">No IP assets found.<br />Run Nmap on seeds to discover IP addresses and open ports.</div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {ips.map(ip => (
                  <div key={ip.id} className="c2-card" style={{ overflow: "hidden" }}>
                    <div
                      style={{ padding: "12px 16px", display: "flex", alignItems: "center", gap: 16, cursor: "pointer" }}
                      onClick={() => setExpandedIp(expandedIp === ip.id ? null : ip.id)}
                    >
                      <span className="c2-pulse" />
                      <span className="td-mono" style={{ color: "var(--cyan)", fontSize: "0.9rem", flex: 1 }}>{ip.address}</span>
                      {ip.version && <span className="c2-badge c2-badge--muted">IPv{ip.version}</span>}
                      <span className="c2-badge c2-badge--green">{ip.ports.length} PORT{ip.ports.length !== 1 ? "S" : ""}</span>
                      <span style={{ color: "var(--text-muted)", fontSize: "0.8rem", transition: "transform 0.2s", display: "inline-block", transform: expandedIp === ip.id ? "rotate(90deg)" : "none" }}>▶</span>
                    </div>
                    {expandedIp === ip.id && ip.ports.length > 0 && (
                      <div style={{ borderTop: "1px solid var(--border-subtle)" }}>
                        <table className="c2-table" style={{ fontSize: "0.75rem" }}>
                          <thead><tr>
                            <th>PORT</th><th>PROTOCOL</th><th>STATE</th><th>SERVICE</th><th>VERSION</th><th>FIRST SEEN</th>
                          </tr></thead>
                          <tbody>
                            {ip.ports.map(port => (
                              <tr key={port.id}>
                                <td className="td-mono" style={{ color: "var(--amber)" }}>{port.port_number}</td>
                                <td className="td-mono">{port.protocol?.toUpperCase()}</td>
                                <td><StatusBadge status={port.state} /></td>
                                <td className="td-mono">{port.service_name || "—"}</td>
                                <td className="td-muted">{port.service_version || "—"}</td>
                                <td className="td-muted">{port.first_seen ? new Date(port.first_seen).toLocaleDateString() : "—"}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                    {expandedIp === ip.id && ip.ports.length === 0 && (
                      <div style={{ padding: "12px 16px", color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: "0.75rem", borderTop: "1px solid var(--border-subtle)" }}>
                        No open ports recorded. Run Nmap to scan.
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* IP Pagination */}
            {!tabLoading && ipTotalCount > IP_PAGE_SIZE && (
              <div style={{ display: "flex", justifyContent: "center", gap: 8, padding: "12px 0" }}>
                <button
                  className="c2-btn c2-btn--ghost"
                  onClick={() => fetchIPs(ipPage - 1, ipSortBy, ipPortFilter)}
                  disabled={ipPage === 0}
                  style={{ fontSize: "0.75rem" }}
                >← PREVIOUS</button>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)", display: "flex", alignItems: "center" }}>
                  {ipPage * IP_PAGE_SIZE + 1} — {Math.min((ipPage + 1) * IP_PAGE_SIZE, ipTotalCount)} / {ipTotalCount}
                </span>
                <button
                  className="c2-btn c2-btn--ghost"
                  onClick={() => fetchIPs(ipPage + 1, ipSortBy, ipPortFilter)}
                  disabled={(ipPage + 1) * IP_PAGE_SIZE >= ipTotalCount}
                  style={{ fontSize: "0.75rem" }}
                >NEXT →</button>
              </div>
            )}
          </>
        )}

        {/* URLs TAB */}
        {activeTab === "urls" && (
          <>
            {/* Toolbar */}
            <div className="c2-section-header" style={{ flexWrap: "wrap", gap: 8 }}>
              <span className="c2-section-title">URL ASSETS <span>({urlsTotalCount})</span></span>
              <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
                {/* URL search */}
                <input
                  className="c2-input"
                  placeholder="Search URL..."
                  value={urlSearch}
                  onChange={e => {
                    const val = e.target.value;
                    setUrlSearch(val);
                    if (urlSearchTimer.current) clearTimeout(urlSearchTimer.current);
                    urlSearchTimer.current = setTimeout(() => {
                      fetchURLs(0, urlsSortBy, val, urlStatusFilter);
                    }, 350);
                  }}
                  style={{ width: 200, fontSize: "0.78rem" }}
                />
                {/* Status code filter */}
                <input
                  className="c2-input"
                  placeholder="Status (e.g. 200)"
                  value={urlStatusFilter}
                  onChange={e => setUrlStatusFilter(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === "Enter") fetchURLs(0, urlsSortBy, urlSearch, urlStatusFilter);
                  }}
                  style={{ width: 130, fontSize: "0.78rem" }}
                />
                {(urlSearch || urlStatusFilter) && (
                  <button
                    className="c2-btn c2-btn--ghost"
                    onClick={() => {
                      setUrlSearch("");
                      setUrlStatusFilter("");
                      fetchURLs(0, urlsSortBy, "", "");
                    }}
                    style={{ fontSize: "0.7rem" }}
                  >✕ 清除</button>
                )}
                {/* Sort */}
                <select
                  className="c2-input"
                  value={urlsSortBy}
                  onChange={e => {
                    const val = e.target.value as URLSortKey;
                    setUrlsSortBy(val);
                    fetchURLs(0, val, urlSearch, urlStatusFilter);
                  }}
                  style={{ width: 175, fontSize: "0.78rem" }}
                >
                  <option value="created_at_desc">最新優先 (newest)</option>
                  <option value="created_at_asc">最舊優先 (oldest)</option>
                  <option value="status_code_asc">狀態碼 (asc)</option>
                  <option value="preliminary_score_desc">初步分數 (high→low)</option>
                  <option value="preliminary_score_asc">初步分數 (low→high)</option>
                </select>
                <button className="c2-btn c2-btn--ghost"
                  onClick={() => fetchURLs(urlsOffset, urlsSortBy, urlSearch, urlStatusFilter)}
                  style={{ fontSize: "0.7rem" }}>↻</button>
              </div>
            </div>

            {/* Content */}
            {tabLoading ? (
              <SkeletonTable rows={10} cols={8} />
            ) : urlsTotalCount === 0 ? (
              <div className="c2-empty">No URLs found.<br />Run URL scanning on subdomains to discover endpoints.</div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <div className="c2-card" style={{ overflow: "hidden" }}>
                  <table className="c2-table">
                    <thead><tr>
                      <th>#ID</th><th>URL</th><th>STATUS</th><th>PRELIMINARY SCORE</th><th>TITLE</th><th>SOURCE</th><th>FETCH STATUS</th><th>FOUND</th><th>DETAIL</th>
                    </tr></thead>
                    <tbody>
                      {urls.map(url => {
                        const preliminaryScore = url.core_initialaianalysis_set?.[0]?.risk_score;
                        return (
                          <tr key={url.id}>
                            <td className="td-mono">#{url.id}</td>
                            <td className="td-mono" style={{ color: "var(--cyan)", maxWidth: 280, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                              <a href={url.url} target="_blank" rel="noopener noreferrer">{url.url}</a>
                            </td>
                            <td>
                              <span className={`c2-badge ${url.status_code >= 200 && url.status_code < 300 ? "c2-badge--green" : url.status_code >= 300 && url.status_code < 400 ? "c2-badge--amber" : url.status_code >= 400 ? "c2-badge--red" : "c2-badge--muted"}`}>
                                {url.status_code || "—"}
                              </span>
                            </td>
                            <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem", textAlign: "center" }}>
                              {preliminaryScore !== undefined ? (
                                <span style={{ color: preliminaryScore >= 70 ? "#ef4444" : preliminaryScore >= 40 ? "#f59e0b" : "#22C55E" }}>
                                  {preliminaryScore.toFixed(1)}
                                </span>
                              ) : (
                                <span style={{ color: "var(--text-muted)" }}>—</span>
                              )}
                            </td>
                            <td style={{ maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontSize: "0.78rem" }}>{url.title || "—"}</td>
                            <td className="td-muted">{url.discovery_source}</td>
                            <td><StatusBadge status={url.content_fetch_status} /></td>
                            <td className="td-muted">{new Date(url.created_at).toLocaleDateString()}</td>
                            <td>
                              <a href={`/target/${numericId}/url/${url.id}`} style={{ color: "var(--cyan)", fontSize: "0.72rem", textDecoration: "none", fontFamily: "var(--font-mono)" }}>
                                DETAIL →
                              </a>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* URL Pagination */}
                <div style={{ display: "flex", justifyContent: "center", gap: 8, padding: "12px 0" }}>
                  <button
                    className="c2-btn c2-btn--ghost"
                    onClick={() => fetchURLs(Math.max(0, urlsOffset - URLS_PAGE_SIZE), urlsSortBy, urlSearch, urlStatusFilter)}
                    disabled={urlsOffset === 0}
                    style={{ fontSize: "0.75rem" }}
                  >← PREVIOUS</button>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)", display: "flex", alignItems: "center" }}>
                    {urlsOffset + 1} — {Math.min(urlsOffset + URLS_PAGE_SIZE, urlsTotalCount)} / {urlsTotalCount}
                  </span>
                  <button
                    className="c2-btn c2-btn--ghost"
                    onClick={() => fetchURLs(urlsOffset + URLS_PAGE_SIZE, urlsSortBy, urlSearch, urlStatusFilter)}
                    disabled={urlsOffset + URLS_PAGE_SIZE >= urlsTotalCount}
                    style={{ fontSize: "0.75rem" }}
                  >NEXT →</button>
                </div>
              </div>
            )}
          </>
        )}

        {/* CVE REPORT TAB */}
        {activeTab === "cve" && (
          <div style={{ padding: 20 }}>
            <TechStackCVEReport targetId={numericId} />
          </div>
        )}

        {/* AI OVERVIEW TAB */}
        {activeTab === "ai" && (
          <>
            <div className="c2-section-header">
              <span className="c2-section-title">AI STRATEGIC OVERVIEW <span>({overviews.length})</span></span>
              <button className="c2-btn c2-btn--ghost" onClick={fetchOverviews} style={{ fontSize: "0.7rem" }}>↻ REFRESH</button>
            </div>
            {tabLoading ? (
              <SkeletonCards count={3} height={120} />
            ) : overviews.length === 0 ? (
              <div className="c2-empty">No AI analysis found.<br />The Celery beat task will generate overviews automatically. Check back after 30 minutes.</div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {overviews.map(ov => (
                  <div key={ov.id} className="c2-card c2-card--cyan" style={{ padding: 20 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                        <StatusBadge status={ov.status} />
                        {ov.business_impact && <span className="c2-badge c2-badge--amber">{ov.business_impact}</span>}
                        <span className="td-mono" style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>ID #{ov.id}</span>
                        {ov.thread_id && <span className="td-mono" style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginLeft: 8 }}>Thread #{ov.thread_id}</span>}
                      </div>
                      <div style={{ textAlign: "right", display: "flex", flexDirection: "column", gap: 6 }}>
                        <div style={{ marginBottom: 0, width: 140 }}>
                          <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", marginBottom: 4, fontFamily: "var(--font-mono)" }}>RISK SCORE</div>
                          <RiskBar score={ov.risk_score} />
                        </div>
                        <div className="td-muted">{new Date(ov.updated_at).toLocaleString()}</div>
                        <button
                          className="c2-btn c2-btn--ghost"
                          onClick={() => navigate(`/overviews/${ov.id}`)}
                          style={{ fontSize: "0.7rem", marginTop: 4 }}
                        >
                          EDIT DETAILS →
                        </button>
                      </div>
                    </div>

                    {ov.summary && (
                      <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: 12 }}>{ov.summary}</p>
                    )}

                    {ov.plan && (
                      <div style={{ marginBottom: 12 }}>
                        <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.7rem", color: "var(--text-muted)", marginBottom: 8, textTransform: "uppercase" }}>ATTACK PLAN:</div>
                        {ov.plan.reasoning && (
                          <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", marginBottom: 8, fontStyle: "italic" }}>{ov.plan.reasoning}</p>
                        )}
                        {ov.plan.objectives && Array.isArray(ov.plan.objectives) && (
                          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                            {ov.plan.objectives.map(obj => (
                              <div key={obj.id} style={{ display: "flex", gap: 10, alignItems: "center", padding: "6px 10px", background: "rgba(15,23,42,0.6)", borderRadius: 4, border: "1px solid var(--border-subtle)" }}>
                                <StatusBadge status={obj.status || "PENDING"} />
                                {obj.priority && <span className="c2-badge c2-badge--amber">{obj.priority}</span>}
                                <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.78rem", flex: 1 }}>{obj.description}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {ov.knowledge && (
                      <details style={{ marginTop: 8 }}>
                        <summary style={{ cursor: "pointer", fontFamily: "var(--font-mono)", fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase" }}>VIEW KNOWLEDGE SNAPSHOT</summary>
                        <pre style={{ marginTop: 8, padding: 12, background: "rgba(2,6,23,0.8)", borderRadius: 4, border: "1px solid var(--border-subtle)", fontSize: "0.72rem", color: "var(--text-secondary)", overflow: "auto", maxHeight: 200 }}>
                          {JSON.stringify(ov.knowledge, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* REQUEST CONFIG TAB */}
        {activeTab === "requestConfig" && (
          <div style={{ padding: 20, maxWidth: 700 }}>
            <div className="c2-section-header">
              <span className="c2-section-title">REQUEST CONFIG OVERRIDE</span>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="c2-btn c2-btn--ghost" onClick={() => fetchReqConfig()} style={{ fontSize: "0.7rem" }}>↻ REFRESH</button>
              </div>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 16 }}>
              留空的欄位會自動繼承全域設定（Pentest Config 頁面）。設定值會覆蓋全域預設。
            </p>

            <div style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid var(--border-subtle)', borderRadius: 6, padding: 20, marginBottom: 16 }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--green)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>Header Injection</div>
              <div style={{ display: 'flex', gap: 16, marginBottom: 12 }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.65rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>Enabled</label>
                  <select
                    value={reqConfig.header_enabled === null ? 'inherit' : reqConfig.header_enabled ? 'true' : 'false'}
                    onChange={(e) => setReqConfig({ ...reqConfig, header_enabled: e.target.value === 'inherit' ? null : e.target.value === 'true' })}
                    style={{ width: '100%', padding: '8px 10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 4, color: 'var(--text-primary)', fontSize: '0.78rem', fontFamily: 'var(--font-mono)' }}
                  >
                    <option value="inherit">繼承全域</option>
                    <option value="true">啟用</option>
                    <option value="false">停用</option>
                  </select>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 16, marginBottom: 12 }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.65rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>Username</label>
                  <input
                    className="pentest-config-input"
                    type="text"
                    value={reqConfig.header_username || ''}
                    onChange={(e) => setReqConfig({ ...reqConfig, header_username: e.target.value || null })}
                    placeholder="繼承全域設定"
                    style={{ width: '100%', padding: '8px 10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 4, color: 'var(--text-primary)', fontSize: '0.78rem', fontFamily: 'var(--font-mono)' }}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.65rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>Header Prefix</label>
                  <input
                    type="text"
                    value={reqConfig.header_prefix || ''}
                    onChange={(e) => setReqConfig({ ...reqConfig, header_prefix: e.target.value || null })}
                    placeholder="繼承全域設定"
                    style={{ width: '100%', padding: '8px 10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 4, color: 'var(--text-primary)', fontSize: '0.78rem', fontFamily: 'var(--font-mono)' }}
                  />
                </div>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.65rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>Custom Headers (JSON)</label>
                <textarea
                  value={JSON.stringify(reqConfig.custom_headers, null, 2)}
                  onChange={(e) => {
                    try { setReqConfig({ ...reqConfig, custom_headers: JSON.parse(e.target.value) }); } catch { /* ignore invalid JSON while typing */ }
                  }}
                  placeholder='{"X-Custom": "value"}'
                  rows={3}
                  style={{ width: '100%', padding: '8px 10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 4, color: 'var(--text-primary)', fontSize: '0.78rem', fontFamily: 'var(--font-mono)', resize: 'vertical', boxSizing: 'border-box' }}
                />
              </div>
            </div>

            <div style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid var(--border-subtle)', borderRadius: 6, padding: 20, marginBottom: 16 }}>
              <div style={{ fontSize: '0.72rem', color: 'var(--green)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>Rate Limiting</div>
              <div style={{ display: 'flex', gap: 16, marginBottom: 12 }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.65rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>RPS (Requests/sec)</label>
                  <input
                    type="number"
                    min={1}
                    value={reqConfig.rps ?? ''}
                    onChange={(e) => setReqConfig({ ...reqConfig, rps: e.target.value ? Number(e.target.value) : null })}
                    placeholder="繼承全域設定"
                    style={{ width: '100%', padding: '8px 10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 4, color: 'var(--text-primary)', fontSize: '0.78rem', fontFamily: 'var(--font-mono)' }}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.65rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>Max Concurrency</label>
                  <input
                    type="number"
                    min={1}
                    value={reqConfig.max_concurrency ?? ''}
                    onChange={(e) => setReqConfig({ ...reqConfig, max_concurrency: e.target.value ? Number(e.target.value) : null })}
                    placeholder="繼承全域設定"
                    style={{ width: '100%', padding: '8px 10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 4, color: 'var(--text-primary)', fontSize: '0.78rem', fontFamily: 'var(--font-mono)' }}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.65rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>Timeout (sec)</label>
                  <input
                    type="number"
                    min={1}
                    value={reqConfig.timeout ?? ''}
                    onChange={(e) => setReqConfig({ ...reqConfig, timeout: e.target.value ? Number(e.target.value) : null })}
                    placeholder="繼承全域設定"
                    style={{ width: '100%', padding: '8px 10px', background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 4, color: 'var(--text-primary)', fontSize: '0.78rem', fontFamily: 'var(--font-mono)' }}
                  />
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <button className="c2-btn c2-btn--ghost" onClick={saveReqConfig} disabled={reqConfigSaving} style={{ fontSize: "0.72rem", padding: "8px 16px" }}>
                {reqConfigSaving ? 'Saving...' : 'Save'}
              </button>
              <button className="c2-btn c2-btn--ghost" onClick={resetReqConfig} style={{ fontSize: "0.72rem", padding: "8px 16px" }}>
                Reset to Global
              </button>
              {reqConfigMsg && (
                <span style={{ fontSize: '0.72rem', color: reqConfigMsg.type === 'ok' ? 'var(--green)' : 'var(--red)' }}>
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
