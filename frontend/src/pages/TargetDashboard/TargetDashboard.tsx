import { useState, useEffect, useCallback } from "react";
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
import TargetActivityMonitor from "../../components/TargetActivityMonitor";
import TechStackCVEReport from "../../components/TechStackCVEReport";
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
  created_at: string;
  core_subdomain_ips?: { core_ip: { id: number; address: string } }[];
}

interface IPRaw {
  id: number;
  address: string;
  version: number | null;
  core_ports?: Port[];
}

type TabId = "seeds" | "activity" | "subdomains" | "ips" | "urls" | "cve" | "ai";

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

  // URL pagination & sorting
  const [urlsOffset, setUrlsOffset] = useState(0);
  const [urlsTotalCount, setUrlsTotalCount] = useState(0);
  const [urlsSortBy, setUrlsSortBy] = useState<"created_at_desc" | "created_at_asc" | "status_code_asc" | "preliminary_score_desc" | "preliminary_score_asc">("created_at_desc");
  const URLS_PAGE_SIZE = 50;

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

  // ── Fetch tab data ──
  const fetchTabData = useCallback(async (tab: TabId, offset: number = 0) => {
    if (!numericId || isNaN(numericId)) return;
    setTabLoading(true);
    try {
      if (tab === "subdomains") {
        const d = await gqlFetcher<{ core_subdomain: SubdomainRaw[] }>(
          GET_TARGET_SUBDOMAINS_QUERY, { targetId: numericId }
        );
        const mapped: SubdomainAsset[] = (d.core_subdomain || []).map(sub => ({
          ...sub,
          ips: (sub.core_subdomain_ips || []).map(item => item.core_ip)
        }));
        setSubdomains(mapped);
      } else if (tab === "ips") {
        const d = await gqlFetcher<{ core_ip: IPRaw[] }>(
          GET_TARGET_IPS_QUERY, { targetId: numericId }
        );
        const mapped: IPAsset[] = (d.core_ip || []).map(ip => ({
          id: ip.id,
          address: ip.address,
          version: ip.version,
          ports: ip.core_ports || [],
        }));
        setIps(mapped);
      } else if (tab === "urls") {
        // 構建排序參數
        const orderByMap: Record<string, any> = {
          "created_at_desc": { created_at: "desc" },
          "created_at_asc": { created_at: "asc" },
          "status_code_asc": { status_code: "asc" }
        };
        const orderBy = orderByMap[urlsSortBy] || { created_at: "desc" };
        
        const d = await gqlFetcher<{ 
          core_urlresult: URLAsset[],
          core_urlresult_aggregate: { aggregate: { count: number } }
        }>(
          GET_TARGET_URLS_QUERY, 
          { 
            targetId: numericId,
            limit: URLS_PAGE_SIZE,
            offset: offset,
            orderBy: orderBy
          }
        );
        
        let urls = d.core_urlresult || [];
        
        // 前端排序（用於初步分析分數排序）
        if (urlsSortBy === "preliminary_score_desc" || urlsSortBy === "preliminary_score_asc") {
          urls.sort((a, b) => {
            const scoreA = a.core_initialaianalysis_set?.[0]?.risk_score ?? -1;
            const scoreB = b.core_initialaianalysis_set?.[0]?.risk_score ?? -1;
            return urlsSortBy === "preliminary_score_desc" ? scoreB - scoreA : scoreA - scoreB;
          });
        }
        
        setUrls(urls);
        setUrlsOffset(offset);
        setUrlsTotalCount(d.core_urlresult_aggregate?.aggregate?.count || 0);
      } else if (tab === "ai") {
        const d = await gqlFetcher<{ core_overview: AIOverview[] }>(
          GET_TARGET_OVERVIEWS_QUERY, { targetId: numericId }
        );
        setOverviews(d.core_overview || []);
      }
    } catch (e: unknown) { console.error("Tab fetch error:", e); }
    finally { setTabLoading(false); }
  }, [numericId, urlsSortBy]);

  useEffect(() => { fetchBase(); }, [fetchBase]);

  const handleTabChange = (tab: TabId) => {
    setActiveTab(tab);
    if (tab === "urls") {
      // 重置 URL 分頁狀態
      setUrlsOffset(0);
      fetchTabData(tab, 0);
    } else if (tab !== "seeds") {
      fetchTabData(tab);
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
    { id: "seeds",      label: "Seeds",      count: seeds.length },
    { id: "activity",   label: "🤖 AI Activity", count: undefined },
    { id: "subdomains", label: "Subdomains", count: subdomains.length || undefined },
    { id: "ips",        label: "IPs / Ports", count: ips.length || undefined },
    { id: "urls",       label: "URLs",       count: urlsTotalCount || undefined },
    { id: "cve",        label: "CVE Report", count: undefined },
    { id: "ai",         label: "AI Overview",count: overviews.length || undefined },
  ];

  return (
    <div className="td-outer c2-page">
      {/* ── Header ── */}
      <header className="td-header">
        <div className="td-header__left">
          <button onClick={() => navigate("/")} className="c2-btn c2-btn--ghost td-back-btn">
            ← BACK
          </button>
          <div>
            <h1 className="td-title">
              <span className="c2-pulse" style={{ marginRight: 10 }} />
              {target.name}
              <span className="td-title__sub">// OPERATION DASHBOARD</span>
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
        {tabLoading && activeTab !== "seeds" && (
          <div className="c2-loading">LOADING DATA...</div>
        )}

        {/* SEEDS TAB */}
        {activeTab === "seeds" && (
          <div className="td-seeds-layout">
            <div className="td-seeds-main c2-card" style={{ padding: 16 }}>
              <div className="c2-section-header">
                <span className="c2-section-title">SEEDS <span>({seeds.length})</span></span>
                <button className="c2-btn c2-btn--ghost" onClick={fetchBase} style={{ fontSize: "0.7rem" }}>
                  ↻ REFRESH
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
              <h3 style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem", marginBottom: 16, color: "var(--green)", textTransform: "uppercase" }}>+ ADD SEED</h3>
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
                {isAdding ? "ADDING..." : "ADD SEED +"}
              </button>
              <div style={{ marginTop: 16, fontSize: "0.72rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                <div style={{ marginBottom: 8, color: "var(--text-secondary)" }}>AUTO TRIGGERS:</div>
                <div>→ Subdomain Enumeration</div>
                <div>→ Port Scanning</div>
                <div>→ AI Initial Analysis</div>
              </div>
            </div>
          </div>
        )}

        {/* ACTIVITY TAB */}
        {activeTab === "activity" && (
          <div style={{ display: "flex", flexDirection: "column", height: "100%", gap: 12 }}>
            <div className="c2-section-header">
              <span className="c2-section-title">🤖 AI ACTIVITY MONITOR</span>
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
        {activeTab === "subdomains" && !tabLoading && (
          <>
            <div className="c2-section-header">
              <span className="c2-section-title">SUBDOMAINS <span>({subdomains.length})</span></span>
              <button className="c2-btn c2-btn--ghost" onClick={() => fetchTabData("subdomains")} style={{ fontSize: "0.7rem" }}>↻ REFRESH</button>
            </div>
            {subdomains.length === 0 ? (
              <div className="c2-empty">No subdomains found.<br />Run Subfinder on a DOMAIN seed to discover subdomains.</div>
            ) : (
              <div className="c2-card" style={{ overflow: "hidden" }}>
                <table className="c2-table">
                  <thead><tr>
                    <th>#ID</th><th>SUBDOMAIN</th><th>RESOLVABLE</th><th>STATUS</th>
                    <th>LINKED IPs</th><th>URLs</th><th>DISCOVERED</th><th></th>
                  </tr></thead>
                  <tbody>
                    {subdomains.map(sub => (
                      <tr key={sub.id} onClick={() => navigate(`/target/${numericId}/subdomain/${sub.id}`)}>
                        <td className="td-mono">#{sub.id}</td>
                        <td className="td-mono" style={{ color: "var(--cyan)" }}>{sub.name}</td>
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
                        <td>
                          <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>→</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        {/* IPs / PORTS TAB */}
        {activeTab === "ips" && !tabLoading && (
          <>
            <div className="c2-section-header">
              <span className="c2-section-title">IP ASSETS <span>({ips.length})</span></span>
              <button className="c2-btn c2-btn--ghost" onClick={() => fetchTabData("ips")} style={{ fontSize: "0.7rem" }}>↻ REFRESH</button>
            </div>
            {ips.length === 0 ? (
              <div className="c2-empty">No IP assets found.<br />Run Nmap on seeds to discover IP addresses and open ports.</div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {ips.map(ip => (
                  <div key={ip.id} className="c2-card" style={{ overflow: "hidden" }}>
                    {/* IP Header Row */}
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
                    {/* Ports Table (expanded) */}
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
          </>
        )}

        {/* URLs TAB */}
        {activeTab === "urls" && !tabLoading && (
          <>
            <div className="c2-section-header">
              <div style={{ display: "flex", alignItems: "center", gap: 16, flex: 1 }}>
                <span className="c2-section-title">URL ASSETS <span>({urlsTotalCount})</span></span>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <label style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>SORT BY:</label>
                  <select 
                    value={urlsSortBy} 
                    onChange={(e) => {
                      setUrlsSortBy(e.target.value as any);
                      setUrlsOffset(0);
                      fetchTabData("urls", 0);
                    }}
                    style={{ 
                      fontSize: "0.75rem", 
                      padding: "4px 8px", 
                      borderRadius: 4, 
                      border: "1px solid var(--border-subtle)",
                      background: "var(--bg-secondary)",
                      color: "var(--text-primary)",
                      fontFamily: "var(--font-mono)",
                      cursor: "pointer"
                    }}
                  >
                    <option value="created_at_desc">最新優先 (newest)</option>
                    <option value="created_at_asc">最舊優先 (oldest)</option>
                    <option value="status_code_asc">狀態碼 (asc)</option>
                    <option value="preliminary_score_desc">初步分數 (high→low)</option>
                    <option value="preliminary_score_asc">初步分數 (low→high)</option>
                  </select>
                </div>
              </div>
              <button className="c2-btn c2-btn--ghost" onClick={() => fetchTabData("urls", urlsOffset)} style={{ fontSize: "0.7rem" }}>↻ REFRESH</button>
            </div>
            {urlsTotalCount === 0 ? (
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
                                <span style={{ 
                                  color: preliminaryScore >= 70 ? "#ef4444" : preliminaryScore >= 40 ? "#f59e0b" : "#22C55E"
                                }}>
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
                              <a
                                href={`/target/${numericId}/url/${url.id}`}
                                style={{ color: "var(--cyan)", fontSize: "0.72rem", textDecoration: "none", fontFamily: "var(--font-mono)" }}
                              >
                                DETAIL →
                              </a>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                
                {/* 分頁控制 */}
                <div style={{ display: "flex", justifyContent: "center", gap: 8, padding: "12px 0" }}>
                  <button 
                    className="c2-btn c2-btn--ghost"
                    onClick={() => fetchTabData("urls", Math.max(0, urlsOffset - URLS_PAGE_SIZE))}
                    disabled={urlsOffset === 0}
                    style={{ fontSize: "0.75rem" }}
                  >
                    ← PREVIOUS
                  </button>
                  <span style={{ 
                    fontSize: "0.75rem", 
                    color: "var(--text-muted)", 
                    fontFamily: "var(--font-mono)",
                    display: "flex",
                    alignItems: "center"
                  }}>
                    {urlsOffset + 1} — {Math.min(urlsOffset + URLS_PAGE_SIZE, urlsTotalCount)} / {urlsTotalCount}
                  </span>
                  <button 
                    className="c2-btn c2-btn--ghost"
                    onClick={() => fetchTabData("urls", urlsOffset + URLS_PAGE_SIZE)}
                    disabled={urlsOffset + URLS_PAGE_SIZE >= urlsTotalCount}
                    style={{ fontSize: "0.75rem" }}
                  >
                    NEXT →
                  </button>
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
        {activeTab === "ai" && !tabLoading && (
          <>
            <div className="c2-section-header">
              <span className="c2-section-title">AI STRATEGIC OVERVIEW <span>({overviews.length})</span></span>
              <button className="c2-btn c2-btn--ghost" onClick={() => fetchTabData("ai")} style={{ fontSize: "0.7rem" }}>↻ REFRESH</button>
            </div>
            {overviews.length === 0 ? (
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
                      <div style={{ textAlign: "right" }}>
                        <div style={{ marginBottom: 6, width: 140 }}>
                          <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", marginBottom: 4, fontFamily: "var(--font-mono)" }}>RISK SCORE</div>
                          <RiskBar score={ov.risk_score} />
                        </div>
                        <div className="td-muted">{new Date(ov.updated_at).toLocaleString()}</div>
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
                            {ov.plan.objectives.map((obj) => (
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
      </div>
    </div>
  );
}

export default TargetDashboard;
