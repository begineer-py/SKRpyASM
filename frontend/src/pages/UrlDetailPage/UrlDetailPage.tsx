// src/pages/UrlDetailPage/UrlDetailPage.tsx
import { useState, useEffect, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { gqlFetcher } from "../../services/api";
import { GET_URL_DETAIL_QUERY } from "../../services/url_detail";
import "./UrlDetailPage.css";

// ─── Types ────────────────────────────────────────────────────────────────────
interface TechStack {
  id: number;
  name: string;
  version?: string;
  categories?: string;
}

interface Vulnerability {
  id: number;
  severity: string;
  name: string;
  description?: string;
  template_id?: string;
}

interface NucleiScan {
  id: number;
  status: string;
  created_at: string;
  completed_at?: string;
}

interface MetaTag {
  id: number;
  attributes: Record<string, string>;
}

interface Link_ {
  id: number;
  href: string;
  text?: string;
}

interface Form {
  id: number;
  action?: string;
  method?: string;
  parameters?: any;
}

interface UrlDetail {
  id: number;
  url: string;
  final_url?: string;
  status_code?: number;
  title?: string;
  method?: string;
  content_length?: number;
  content_fetch_status?: string;
  is_external_redirect?: boolean;
  is_important?: boolean;
  is_tech_analyzed?: boolean;
  discovery_source?: string;
  used_flaresolverr?: boolean;
  created_at: string;
  headers?: Record<string, string>;
  core_urlresult_related_subdomains: { core_subdomain: { id: number; name: string } }[];
  core_techstacks: TechStack[];
  core_nucleiscans: NucleiScan[];
  core_vulnerabilities: Vulnerability[];
  core_metatags: MetaTag[];
  core_links: Link_[];
  core_forms: Form[];
}

interface UrlDetailResponse {
  core_urlresult_by_pk: UrlDetail | null;
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatusBadge({ code }: { code?: number }) {
  if (!code) return <span className="badge badge-status-unknown">N/A</span>;
  const cls =
    code >= 500 ? "badge-status-5xx"
    : code >= 400 ? "badge-status-4xx"
    : code >= 300 ? "badge-status-3xx"
    : code >= 200 ? "badge-status-2xx"
    : "badge-status-unknown";
  return <span className={`badge ${cls}`}>{code}</span>;
}

function MethodBadge({ method }: { method?: string }) {
  if (!method) return null;
  const cls = method === "GET" ? "badge-method-get" : method === "POST" ? "badge-method-post" : "badge-method-other";
  return <span className={`badge ${cls}`}>{method}</span>;
}

function VulnBadge({ severity }: { severity: string }) {
  const s = severity.toLowerCase();
  const cls =
    s === "critical" ? "badge-vuln-critical"
    : s === "high" ? "badge-vuln-high"
    : s === "medium" ? "badge-vuln-medium"
    : s === "low" ? "badge-vuln-low"
    : "badge-vuln-info";
  return <span className={`badge ${cls}`}>{severity}</span>;
}

function CopyText({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };
  return (
    <div className="cmd-block">
      <span className="cmd-text">{text}</span>
      <button className="btn-copy-sm" onClick={copy}>{copied ? "✓ COPIED" : "COPY"}</button>
    </div>
  );
}

function Collapsible({ title, icon, count, children }: { title: string; icon: string; count?: number; children: React.ReactNode }) {
  const [open, setOpen] = useState(true);
  return (
    <div className="url-section">
      <div className="url-section-header" onClick={() => setOpen(!open)}>
        <span className="url-section-title"><span>{icon}</span>{title}</span>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {count !== undefined && <span className="url-section-count">{count}</span>}
          <span className={`url-section-toggle ${open ? "open" : ""}`}>▾</span>
        </div>
      </div>
      {open && <div className="url-section-body">{children}</div>}
    </div>
  );
}

// ─── Main Page ─────────────────────────────────────────────────────────────────

export default function UrlDetailPage() {
  const { targetId, urlId } = useParams();
  const nUrlId = Number(urlId);

  const [data, setData] = useState<UrlDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Scan Panel State
  const [showScanPanel, setShowScanPanel] = useState(false);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [isScanning, setIsScanning] = useState(false);

  const handleRunScan = async () => {
    setIsScanning(true);
    try {
      const { GLOBAL_CONFIG } = await import("../../config");
      const res = await fetch(`${GLOBAL_CONFIG.DJANGO_API_BASE}/scanners/vuln/urls`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          ids: [nUrlId], 
          tags: selectedTags.length > 0 ? selectedTags : undefined 
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || 'Scan failed');
      }
      alert("Scan triggered successfully! Wait a few minutes for results.");
      setShowScanPanel(false);
    } catch (err: any) {
      alert("Error: " + err.message);
    } finally {
      setIsScanning(false);
    }
  };

  const fetchData = useCallback(async () => {
    if (!nUrlId) return;
    try {
      const res = await gqlFetcher<UrlDetailResponse>(GET_URL_DETAIL_QUERY, { url_id: nUrlId });
      if (res.core_urlresult_by_pk) {
        setData(res.core_urlresult_by_pk);
      } else {
        setError("URL not found.");
      }
    } catch (e: any) {
      setError(e.message || "Failed to load URL data.");
    } finally {
      setLoading(false);
    }
  }, [nUrlId]);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) return (
    <div className="url-detail-container" style={{ color: "#8b949e", paddingTop: 60, textAlign: "center" }}>
      Loading URL intel...
    </div>
  );
  if (error || !data) return (
    <div className="url-detail-container" style={{ color: "#f85149", paddingTop: 60, textAlign: "center" }}>
      {error || "URL not found."}
    </div>
  );

  const d = data;
  const subdomains = d.core_urlresult_related_subdomains.map(r => r.core_subdomain);
  const parsedHeaders: Record<string, string> = d.headers
    ? (typeof d.headers === "string" ? JSON.parse(d.headers) : d.headers)
    : {};

  return (
    <div className="url-detail-container">
      {/* ── Hero Header ── */}
      <div className="url-detail-hero">
        <div className="url-detail-breadcrumb">
          <Link to={`/target/${targetId}`}>Target</Link>
          {" / "}
          URL Detail
        </div>

        <div className="url-detail-title">
          <a href={d.url} target="_blank" rel="noopener noreferrer">{d.url}</a>
        </div>

        <div className="url-meta-bar">
          <StatusBadge code={d.status_code ?? undefined} />
          <MethodBadge method={d.method ?? undefined} />
          {d.is_important && <span className="badge badge-important">⭐ IMPORTANT</span>}
          {d.used_flaresolverr && <span className="badge badge-info">FlareSolverr</span>}
          {d.is_external_redirect && <span className="badge badge-status-3xx">→ Redirect</span>}
          {d.discovery_source && <span className="badge badge-info">{d.discovery_source}</span>}
          {d.content_length !== undefined && d.content_length !== null && (
            <span className="badge badge-info">{(d.content_length / 1024).toFixed(1)} KB</span>
          )}
          <span className="badge badge-info" style={{ marginLeft: "auto" }}>
            {new Date(d.created_at).toLocaleString()}
          </span>
          <button 
            className="btn-copy-sm" 
            style={{ padding: "4px 12px", background: "#f85149", color: "white", border: "none", cursor: "pointer", marginLeft: 10, fontWeight: "bold" }}
            onClick={() => setShowScanPanel(!showScanPanel)}
          >
            {showScanPanel ? "CANCEL" : "LAUNCH NUCLEI"}
          </button>
        </div>
      </div>

      {/* ── Scan Panel ── */}
      {showScanPanel && (
        <div style={{ background: "#161b22", border: "1px solid #f85149", borderRadius: 8, padding: 16, marginBottom: 20 }}>
          <div style={{ color: "#f85149", fontWeight: "bold", marginBottom: 10 }}>Configure Nuclei Scan</div>
          <div style={{ marginBottom: 10, color: "#8b949e", fontSize: "0.85rem" }}>
            Select specific templates to run. If none selected, default active templates run.
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 16 }}>
            {["cves", "sqli", "xss", "lfi", "rce", "misconfiguration", "auth-bypass", "exposure"].map(tag => (
              <label key={tag} style={{ display: "flex", alignItems: "center", gap: 4, cursor: "pointer", color: "#c9d1d9", fontSize: "0.85rem" }}>
                <input 
                  type="checkbox" 
                  checked={selectedTags.includes(tag)}
                  onChange={(e) => {
                    if (e.target.checked) setSelectedTags([...selectedTags, tag]);
                    else setSelectedTags(selectedTags.filter(t => t !== tag));
                  }} 
                />
                {tag.toUpperCase()}
              </label>
            ))}
          </div>
          <button 
            style={{ padding: "6px 16px", background: "#f85149", color: "white", border: "none", borderRadius: 4, cursor: isScanning ? "not-allowed" : "pointer", fontWeight: "bold", letterSpacing: 1 }}
            disabled={isScanning}
            onClick={handleRunScan}
          >
            {isScanning ? "INITIATING..." : "FIRE NUCLEI SCAN 🚀"}
          </button>
        </div>
      )}

      {/* ── Two-column layout ── */}
      <div className="url-detail-layout">
        {/* LEFT column */}
        <div>

          {/* Basic Info */}
          <Collapsible title="Basic Information" icon="🔍">
            <div className="info-grid">
              <span className="info-label">Title</span>
              <span className="info-value">{d.title || <em className="muted">No title</em>}</span>

              {d.final_url && d.final_url !== d.url && (
                <>
                  <span className="info-label">Final URL</span>
                  <span className="info-value">
                    <a href={d.final_url} target="_blank" rel="noopener noreferrer">{d.final_url}</a>
                  </span>
                </>
              )}

              <span className="info-label">Fetch Status</span>
              <span className="info-value">{d.content_fetch_status || <em className="muted">Unknown</em>}</span>

              <span className="info-label">Tech Analyzed</span>
              <span className="info-value">{d.is_tech_analyzed ? "✅ Yes" : "❌ No"}</span>

              {subdomains.length > 0 && (
                <>
                  <span className="info-label">Subdomains</span>
                  <span className="info-value">
                    {subdomains.map(sub => (
                      <Link
                        key={sub.id}
                        to={`/target/${targetId}/subdomain/${sub.id}`}
                        style={{ display: "inline-block", marginRight: 8, color: "#58a6ff" }}
                      >
                        {sub.name}
                      </Link>
                    ))}
                  </span>
                </>
              )}
            </div>
          </Collapsible>

          {/* Tech Stack */}
          <Collapsible title="Technology Stack" icon="⚙️" count={d.core_techstacks.length}>
            {d.core_techstacks.length === 0 ? (
              <p className="muted">No technologies detected.</p>
            ) : (
              <div className="tech-grid">
                {d.core_techstacks.map(t => (
                  <div key={t.id} className="tech-pill">
                    <span className="tech-name">{t.name}</span>
                    {t.version && <span className="tech-ver">v{t.version}</span>}
                    {t.categories && <span className="tech-cat">{t.categories}</span>}
                  </div>
                ))}
              </div>
            )}
          </Collapsible>

          {/* Vulnerabilities */}
          <Collapsible title="Vulnerabilities (Nuclei)" icon="🚨" count={d.core_vulnerabilities.length}>
            {d.core_vulnerabilities.length === 0 ? (
              <p className="muted">No vulnerabilities found.</p>
            ) : (
              d.core_vulnerabilities.map(v => (
                <div key={v.id} className="vuln-card">
                  <div className="vuln-card-header">
                    <VulnBadge severity={v.severity} />
                    <span className="vuln-name">{v.name}</span>
                  </div>
                  {v.template_id && <div className="vuln-template">{v.template_id}</div>}
                  {v.description && <p className="vuln-desc">{v.description}</p>}
                </div>
              ))
            )}
          </Collapsible>

          {/* HTTP Headers */}
          <Collapsible title="HTTP Headers" icon="📋" count={Object.keys(parsedHeaders).length}>
            {Object.keys(parsedHeaders).length === 0 ? (
              <p className="muted">No headers stored.</p>
            ) : (
              <div className="headers-block">
                {Object.entries(parsedHeaders).map(([k, v]) => (
                  <div key={k} className="header-row">
                    <span className="header-key">{k}</span>
                    <span className="header-val">{v}</span>
                  </div>
                ))}
              </div>
            )}
          </Collapsible>

          {/* Meta Tags */}
          <Collapsible title="Meta Tags" icon="🏷️" count={d.core_metatags.length}>
            {d.core_metatags.length === 0 ? (
              <p className="muted">No meta tags found.</p>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Attribute</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  {d.core_metatags.map(m => (
                    Object.entries(m.attributes || {}).map(([k, v], i) => (
                      <tr key={`${m.id}-${i}`}>
                        <td style={{ color: "#d2a8ff", minWidth: 120 }}>{k}</td>
                        <td>{String(v)}</td>
                      </tr>
                    ))
                  ))}
                </tbody>
              </table>
            )}
          </Collapsible>

        </div>

        {/* RIGHT column */}
        <div>

          {/* Nuclei Scans */}
          <Collapsible title="Nuclei Scans" icon="🔬" count={d.core_nucleiscans.length}>
            {d.core_nucleiscans.length === 0 ? (
              <p className="muted">No scans run yet.</p>
            ) : (
              d.core_nucleiscans.map(s => (
                <div key={s.id} style={{ padding: "8px 0", borderBottom: "1px solid #21262d" }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
                    <span className="badge badge-info">#{s.id}</span>
                    <StatusBadge code={s.status === "COMPLETED" ? 200 : s.status === "FAILED" ? 500 : undefined} />
                    <span style={{ fontSize: "0.72rem", color: "#8b949e" }}>{s.status}</span>
                  </div>
                  <span style={{ fontSize: "0.68rem", color: "#484f58" }}>
                    {new Date(s.created_at).toLocaleString()}
                  </span>
                </div>
              ))
            )}
          </Collapsible>

          {/* Links */}
          <Collapsible title="Discovered Links" icon="🔗" count={d.core_links.length}>
            {d.core_links.length === 0 ? (
              <p className="muted">No links extracted.</p>
            ) : (
              <div style={{ maxHeight: 400, overflowY: "auto" }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Href</th>
                      <th>Text</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.core_links.map(link => (
                      <tr key={link.id}>
                        <td>
                          <a href={link.href} target="_blank" rel="noopener noreferrer"
                            style={{ color: "#58a6ff", fontSize: "0.72rem" }}>
                            {link.href.length > 50 ? link.href.slice(0, 50) + "…" : link.href}
                          </a>
                        </td>
                        <td style={{ fontSize: "0.72rem", color: "#8b949e" }}>{link.text || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Collapsible>

          {/* Forms */}
          <Collapsible title="Forms" icon="📝" count={d.core_forms.length}>
            {d.core_forms.length === 0 ? (
              <p className="muted">No forms found.</p>
            ) : (
              d.core_forms.map(f => (
                <div key={f.id} style={{ padding: "10px 0", borderBottom: "1px solid #21262d" }}>
                  <div className="info-grid">
                    <span className="info-label">Action</span>
                    <span className="info-value">{f.action || "—"}</span>
                    <span className="info-label">Method</span>
                    <span className="info-value">{f.method || "GET"}</span>
                  </div>
                  {f.parameters && (
                    <details style={{ marginTop: 8 }}>
                      <summary style={{ cursor: "pointer", fontSize: "0.72rem", color: "#58a6ff" }}>
                        View parameters
                      </summary>
                      <pre style={{
                        background: "#161b22", padding: "10px", borderRadius: 6,
                        fontSize: "0.72rem", color: "#a5d6ff", marginTop: 8, overflowX: "auto"
                      }}>
                        {JSON.stringify(f.parameters, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              ))
            )}
          </Collapsible>

        </div>
      </div>
    </div>
  );
}
