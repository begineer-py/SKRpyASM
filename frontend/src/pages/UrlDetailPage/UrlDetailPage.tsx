// src/pages/UrlDetailPage/UrlDetailPage.tsx
import { useState, useEffect, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { gqlFetcher } from "../../services/api";
import { GET_URL_DETAIL_QUERY } from "../../services/url_detail";
import { cn } from "@/lib/utils";

// ─── Constants ─────────────────────────────────────────────────────────────────
const badgeBase = "inline-flex items-center gap-1 px-2.5 py-[3px] rounded-full text-[0.72rem] font-bold tracking-wide uppercase border";

const badgeStatus: Record<string, string> = {
  "2xx": "bg-[rgba(35,134,54,0.15)] text-[#3fb950] border-[rgba(63,185,80,0.3)]",
  "3xx": "bg-[rgba(210,153,34,0.15)] text-[#d29922] border-[rgba(210,153,34,0.3)]",
  "4xx": "bg-[rgba(248,81,73,0.15)] text-[#f85149] border-[rgba(248,81,73,0.3)]",
  "5xx": "bg-[rgba(248,81,73,0.2)] text-[#ff7b72] border-[rgba(248,81,73,0.4)]",
  unknown: "bg-[rgba(110,118,129,0.15)] text-[#8b949e] border-[rgba(110,118,129,0.3)]",
};

const badgeMethod: Record<string, string> = {
  GET: "bg-[rgba(88,166,255,0.1)] text-[#58a6ff] border-[rgba(88,166,255,0.3)]",
  POST: "bg-[rgba(63,185,80,0.1)] text-[#3fb950] border-[rgba(63,185,80,0.3)]",
  other: "bg-[rgba(210,153,34,0.1)] text-[#d29922] border-[rgba(210,153,34,0.3)]",
};

const badgeVuln: Record<string, string> = {
  critical: "bg-[rgba(188,10,10,0.25)] text-[#ff7b72] border-[rgba(188,10,10,0.5)]",
  high: "bg-[rgba(248,81,73,0.15)] text-[#f85149] border-[rgba(248,81,73,0.3)]",
  medium: "bg-[rgba(210,153,34,0.15)] text-[#d29922] border-[rgba(210,153,34,0.3)]",
  low: "bg-[rgba(88,166,255,0.1)] text-[#58a6ff] border-[rgba(88,166,255,0.3)]",
  info: "bg-[rgba(110,118,129,0.15)] text-[#8b949e] border-[rgba(110,118,129,0.3)]",
};

const badgeInfo = "bg-[rgba(110,118,129,0.12)] text-[#8b949e] border-[rgba(110,118,129,0.2)]";
const badgeImportant = "bg-[rgba(255,166,0,0.15)] text-[#e3b341] border-[rgba(255,166,0,0.3)]";

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
  if (!code) return <span className={cn(badgeBase, badgeStatus.unknown)}>N/A</span>;
  const style =
    code >= 500 ? badgeStatus["5xx"]
    : code >= 400 ? badgeStatus["4xx"]
    : code >= 300 ? badgeStatus["3xx"]
    : code >= 200 ? badgeStatus["2xx"]
    : badgeStatus.unknown;
  return <span className={cn(badgeBase, style)}>{code}</span>;
}

function MethodBadge({ method }: { method?: string }) {
  if (!method) return null;
  const style = method === "GET" ? badgeMethod.GET : method === "POST" ? badgeMethod.POST : badgeMethod.other;
  return <span className={cn(badgeBase, style)}>{method}</span>;
}

function VulnBadge({ severity }: { severity: string }) {
  const s = severity.toLowerCase();
  const style = badgeVuln[s] || badgeVuln.info;
  return <span className={cn(badgeBase, style)}>{severity}</span>;
}

function Collapsible({ title, icon, count, children }: { title: string; icon: string; count?: number; children: React.ReactNode }) {
  const [open, setOpen] = useState(true);
  return (
    <div className="bg-[#0d1117] border border-[#21262d] rounded-lg mb-4 overflow-hidden">
      <div className="flex justify-between items-center px-4 py-3 bg-[#161b22] border-b border-[#21262d] cursor-pointer select-none" onClick={() => setOpen(!open)}>
        <span className="text-[0.75rem] font-bold uppercase tracking-widest text-[#8b949e]"><span className="text-[#58a6ff] mr-1.5">{icon}</span>{title}</span>
        <div className="flex items-center gap-2">
          {count !== undefined && <span className="text-[0.7rem] text-[#484f58] bg-[#21262d] px-2 py-0.5 rounded-full">{count}</span>}
          <span className={cn("text-[#484f58] text-[0.75rem] transition-transform duration-200", open && "rotate-180")}>▾</span>
        </div>
      </div>
      {open && <div className="px-4 py-4">{children}</div>}
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
    <div className="max-w-[1280px] mx-auto px-6 pt-[60px] pb-7 font-mono text-text-muted text-center">
      Loading URL intel...
    </div>
  );
  if (error || !data) return (
    <div className="max-w-[1280px] mx-auto px-6 pt-[60px] pb-7 font-mono text-red text-center">
      {error || "URL not found."}
    </div>
  );

  const d = data;
  const subdomains = d.core_urlresult_related_subdomains.map(r => r.core_subdomain);
  const parsedHeaders: Record<string, string> = d.headers
    ? (typeof d.headers === "string" ? JSON.parse(d.headers) : d.headers)
    : {};

  return (
    <div className="max-w-[1280px] mx-auto px-6 py-7 font-mono">
      {/* ── Hero Header ── */}
      <div className="relative overflow-hidden bg-gradient-to-br from-[#0d1117] to-[#161b22] border border-[#21262d] rounded-xl px-7 py-6 mb-6 before:content-[''] before:absolute before:inset-0 before:bg-gradient-to-r before:from-[rgba(0,255,180,0.04)] before:to-transparent before:pointer-events-none">
        <div className="text-[0.72rem] text-[#484f58] mb-2.5 uppercase tracking-wider">
          <Link to={`/target/${targetId}`} className="text-[#58a6ff] no-underline hover:underline">Target</Link>
          {" / "}
          URL Detail
        </div>

        <div className="text-[1.15rem] font-semibold text-[#e6edf3] break-all mb-3 leading-normal">
          <a href={d.url} target="_blank" rel="noopener noreferrer" className="text-[#58a6ff] no-underline hover:underline">{d.url}</a>
        </div>

        <div className="flex flex-wrap gap-2.5 items-center">
          <StatusBadge code={d.status_code ?? undefined} />
          <MethodBadge method={d.method ?? undefined} />
          {d.is_important && <span className={cn(badgeBase, badgeImportant)}>⭐ IMPORTANT</span>}
          {d.used_flaresolverr && <span className={cn(badgeBase, badgeInfo)}>FlareSolverr</span>}
          {d.is_external_redirect && <span className={cn(badgeBase, badgeStatus["3xx"])}>→ Redirect</span>}
          {d.discovery_source && <span className={cn(badgeBase, badgeInfo)}>{d.discovery_source}</span>}
          {d.content_length !== undefined && d.content_length !== null && (
            <span className={cn(badgeBase, badgeInfo)}>{(d.content_length / 1024).toFixed(1)} KB</span>
          )}
          <span className={cn(badgeBase, badgeInfo, "ml-auto")}>
            {new Date(d.created_at).toLocaleString()}
          </span>
          <button 
            className="shrink-0 text-[0.68rem] font-mono uppercase tracking-wide px-3 py-1 bg-[#f85149] text-white border-0 cursor-pointer ml-2.5 font-bold"
            onClick={() => setShowScanPanel(!showScanPanel)}
          >
            {showScanPanel ? "CANCEL" : "LAUNCH NUCLEI"}
          </button>
        </div>
      </div>

      {/* ── Scan Panel ── */}
      {showScanPanel && (
        <div className="bg-bg-surface border border-red rounded-lg p-4 mb-5">
          <div className="text-red font-bold mb-2.5">Configure Nuclei Scan</div>
          <div className="mb-2.5 text-text-muted text-[0.85rem]">
            Select specific templates to run. If none selected, default active templates run.
          </div>
          <div className="flex gap-2.5 flex-wrap mb-4">
            {["cves", "sqli", "xss", "lfi", "rce", "misconfiguration", "auth-bypass", "exposure"].map(tag => (
              <label key={tag} className="flex items-center gap-1 cursor-pointer text-text-secondary text-[0.85rem]">
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
      <div className="grid grid-cols-[1fr_340px] gap-5 items-start">
        {/* LEFT column */}
        <div>

          {/* Basic Info */}
          <Collapsible title="Basic Information" icon="🔍">
            <div className="grid grid-cols-[max-content_1fr] gap-x-5 gap-y-2.5 items-center">
              <span className="text-[0.68rem] font-bold uppercase tracking-wider text-[#484f58] whitespace-nowrap">Title</span>
              <span className="text-sm text-[#c9d1d9] break-all">{d.title || <em className="text-[#484f58] italic text-[0.78rem]">No title</em>}</span>

              {d.final_url && d.final_url !== d.url && (
                <>
                  <span className="text-[0.68rem] font-bold uppercase tracking-wider text-[#484f58] whitespace-nowrap">Final URL</span>
                  <span className="text-sm text-[#c9d1d9] break-all">
                    <a href={d.final_url} target="_blank" rel="noopener noreferrer" className="text-[#58a6ff] no-underline hover:underline">{d.final_url}</a>
                  </span>
                </>
              )}

              <span className="text-[0.68rem] font-bold uppercase tracking-wider text-[#484f58] whitespace-nowrap">Fetch Status</span>
              <span className="text-sm text-[#c9d1d9] break-all">{d.content_fetch_status || <em className="text-[#484f58] italic text-[0.78rem]">Unknown</em>}</span>

              <span className="text-[0.68rem] font-bold uppercase tracking-wider text-[#484f58] whitespace-nowrap">Tech Analyzed</span>
              <span className="text-sm text-[#c9d1d9] break-all">{d.is_tech_analyzed ? "✅ Yes" : "❌ No"}</span>

              {subdomains.length > 0 && (
                <>
                  <span className="text-[0.68rem] font-bold uppercase tracking-wider text-[#484f58] whitespace-nowrap">Subdomains</span>
                  <span className="text-sm text-[#c9d1d9] break-all">
                    {subdomains.map(sub => (
                      <Link
                        key={sub.id}
                        to={`/target/${targetId}/subdomain/${sub.id}`}
                        className="inline-block mr-2 text-blue"
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
              <p className="text-[#484f58] italic text-[0.78rem]">No technologies detected.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {d.core_techstacks.map(t => (
                  <div key={t.id} className="inline-flex flex-col px-3 py-1.5 bg-[rgba(88,166,255,0.07)] border border-[rgba(88,166,255,0.2)] rounded-md">
                    <span className="text-[0.78rem] font-semibold text-[#79c0ff]">{t.name}</span>
                    {t.version && <span className="text-[0.65rem] text-[#484f58]">v{t.version}</span>}
                    {t.categories && <span className="text-[0.6rem] uppercase tracking-wider text-[#58a6ff] mt-0.5">{t.categories}</span>}
                  </div>
                ))}
              </div>
            )}
          </Collapsible>

          {/* Vulnerabilities */}
          <Collapsible title="Vulnerabilities (Nuclei)" icon="🚨" count={d.core_vulnerabilities.length}>
            {d.core_vulnerabilities.length === 0 ? (
              <p className="text-[#484f58] italic text-[0.78rem]">No vulnerabilities found.</p>
            ) : (
              d.core_vulnerabilities.map(v => (
                <div key={v.id} className="border border-[#21262d] rounded-md px-3.5 py-3 mb-2.5 transition-colors duration-200 hover:border-[#30363d]">
                  <div className="flex items-center gap-2 mb-1.5">
                    <VulnBadge severity={v.severity} />
                    <span className="text-[0.82rem] font-semibold text-[#e6edf3]">{v.name}</span>
                  </div>
                  {v.template_id && <div className="text-[0.68rem] text-[#484f58] font-mono">{v.template_id}</div>}
                  {v.description && <p className="text-[0.76rem] text-[#8b949e] leading-normal">{v.description}</p>}
                </div>
              ))
            )}
          </Collapsible>

          {/* HTTP Headers */}
          <Collapsible title="HTTP Headers" icon="📋" count={Object.keys(parsedHeaders).length}>
            {Object.keys(parsedHeaders).length === 0 ? (
              <p className="text-[#484f58] italic text-[0.78rem]">No headers stored.</p>
            ) : (
              <div className="bg-[#161b22] rounded-md p-3.5 overflow-x-auto">
                {Object.entries(parsedHeaders).map(([k, v]) => (
                  <div key={k} className="flex gap-3 py-1 border-b border-[#21262d] text-[0.75rem] last:border-b-0">
                    <span className="text-[#d2a8ff] min-w-[160px] font-semibold">{k}</span>
                    <span className="text-[#a5d6ff] break-all">{v}</span>
                  </div>
                ))}
              </div>
            )}
          </Collapsible>

          {/* Meta Tags */}
          <Collapsible title="Meta Tags" icon="🏷️" count={d.core_metatags.length}>
            {d.core_metatags.length === 0 ? (
              <p className="text-[#484f58] italic text-[0.78rem]">No meta tags found.</p>
            ) : (
              <table className="w-full border-collapse text-[0.78rem]">
                <thead>
                  <tr>
                    <th className="text-left text-[0.65rem] font-bold uppercase tracking-wider text-[#484f58] px-2 py-1.5 border-b border-[#21262d]">Attribute</th>
                    <th className="text-left text-[0.65rem] font-bold uppercase tracking-wider text-[#484f58] px-2 py-1.5 border-b border-[#21262d]">Value</th>
                  </tr>
                </thead>
                <tbody>
                  {d.core_metatags.map(m => (
                    Object.entries(m.attributes || {}).map(([k, v], i) => (
                      <tr key={`${m.id}-${i}`} className="hover:bg-[rgba(255,255,255,0.02)]">
                        <td className="p-2 border-b border-[#161b22] text-purple align-top break-all last:border-b-0 min-w-[120px]">{k}</td>
                        <td className="p-2 border-b border-[#161b22] text-[#c9d1d9] align-top break-all last:border-b-0">{String(v)}</td>
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
              <p className="text-[#484f58] italic text-[0.78rem]">No scans run yet.</p>
            ) : (
              d.core_nucleiscans.map(s => (
                <div key={s.id} className="py-2 border-b border-border-normal">
                  <div className="flex gap-2 items-center mb-1">
                    <span className={cn(badgeBase, badgeInfo)}>#{s.id}</span>
                    <StatusBadge code={s.status === "COMPLETED" ? 200 : s.status === "FAILED" ? 500 : undefined} />
                    <span className="text-[0.72rem] text-text-muted">{s.status}</span>
                  </div>
                  <span className="text-[0.68rem] text-text-muted">
                    {new Date(s.created_at).toLocaleString()}
                  </span>
                </div>
              ))
            )}
          </Collapsible>

          {/* Links */}
          <Collapsible title="Discovered Links" icon="🔗" count={d.core_links.length}>
            {d.core_links.length === 0 ? (
              <p className="text-[#484f58] italic text-[0.78rem]">No links extracted.</p>
            ) : (
              <div className="max-h-[400px] overflow-y-auto">
                <table className="w-full border-collapse text-[0.78rem]">
                  <thead>
                    <tr>
                      <th className="text-left text-[0.65rem] font-bold uppercase tracking-wider text-[#484f58] px-2 py-1.5 border-b border-[#21262d]">Href</th>
                      <th className="text-left text-[0.65rem] font-bold uppercase tracking-wider text-[#484f58] px-2 py-1.5 border-b border-[#21262d]">Text</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.core_links.map(link => (
                      <tr key={link.id} className="hover:bg-[rgba(255,255,255,0.02)]">
                        <td className="p-2 border-b border-[#161b22] text-[#c9d1d9] align-top break-all last:border-b-0">
                          <a href={link.href} target="_blank" rel="noopener noreferrer"
                            className="text-blue text-[0.72rem]">
                            {link.href.length > 50 ? link.href.slice(0, 50) + "…" : link.href}
                          </a>
                        </td>
                        <td className="p-2 border-b border-[#161b22] text-text-muted align-top break-all last:border-b-0 text-[0.72rem]">{link.text || "—"}</td>
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
              <p className="text-[#484f58] italic text-[0.78rem]">No forms found.</p>
            ) : (
              d.core_forms.map(f => (
                <div key={f.id} className="py-[10px] border-b border-border-normal">
                  <div className="grid grid-cols-[max-content_1fr] gap-x-5 gap-y-2.5 items-center">
                    <span className="text-[0.68rem] font-bold uppercase tracking-wider text-[#484f58] whitespace-nowrap">Action</span>
                    <span className="text-sm text-[#c9d1d9] break-all">{f.action || "—"}</span>
                    <span className="text-[0.68rem] font-bold uppercase tracking-wider text-[#484f58] whitespace-nowrap">Method</span>
                    <span className="text-sm text-[#c9d1d9] break-all">{f.method || "GET"}</span>
                  </div>
                  {f.parameters && (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-[0.72rem] text-blue">
                        View parameters
                      </summary>
                      <pre className="bg-bg-surface p-[10px] rounded-md text-[0.72rem] text-cyan mt-2 overflow-x-auto">
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
