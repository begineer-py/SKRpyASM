// src/pages/UrlDetailPage/UrlDetailPage.tsx
import { useState, useEffect, useCallback } from "react";
import { useParams, Link, useSearchParams } from "react-router-dom";
import { GET_URL_DETAIL_QUERY, gqlFetcher } from "../services/targetApi";
import { cn } from '@/lib/utils';

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
  parameters?: Record<string, unknown> | null;
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

// ─── Badge helpers ────────────────────────────────────────────────────────────
const badgeBase = "inline-flex items-center gap-1 px-2.5 py-[3px] rounded-full text-[0.72rem] font-bold tracking-wide uppercase border";

const statusBadgeCls = (code?: number) => {
  if (!code) return `${badgeBase} bg-[rgba(110,118,129,0.15)] text-[#8b949e] border-[rgba(110,118,129,0.3)]`;
  if (code >= 500) return `${badgeBase} bg-[rgba(248,81,73,0.2)] text-[#ff7b72] border-[rgba(248,81,73,0.4)]`;
  if (code >= 400) return `${badgeBase} bg-[rgba(248,81,73,0.15)] text-[#f85149] border-[rgba(248,81,73,0.3)]`;
  if (code >= 300) return `${badgeBase} bg-[rgba(210,153,34,0.15)] text-[#d29922] border-[rgba(210,153,34,0.3)]`;
  if (code >= 200) return `${badgeBase} bg-[rgba(35,134,54,0.15)] text-[#3fb950] border-[rgba(63,185,80,0.3)]`;
  return `${badgeBase} bg-[rgba(110,118,129,0.15)] text-[#8b949e] border-[rgba(110,118,129,0.3)]`;
};

const methodBadgeCls = (method?: string) => {
  if (!method) return '';
  if (method === "GET") return `${badgeBase} bg-[rgba(88,166,255,0.1)] text-[#58a6ff] border-[rgba(88,166,255,0.3)]`;
  if (method === "POST") return `${badgeBase} bg-[rgba(63,185,80,0.1)] text-[#3fb950] border-[rgba(63,185,80,0.3)]`;
  return `${badgeBase} bg-[rgba(210,153,34,0.1)] text-[#d29922] border-[rgba(210,153,34,0.3)]`;
};

const vulnBadgeCls = (severity: string) => {
  const s = severity.toLowerCase();
  if (s === "critical") return `${badgeBase} bg-[rgba(188,10,10,0.25)] text-[#ff7b72] border-[rgba(188,10,10,0.5)]`;
  if (s === "high") return `${badgeBase} bg-[rgba(248,81,73,0.15)] text-[#f85149] border-[rgba(248,81,73,0.3)]`;
  if (s === "medium") return `${badgeBase} bg-[rgba(210,153,34,0.15)] text-[#d29922] border-[rgba(210,153,34,0.3)]`;
  if (s === "low") return `${badgeBase} bg-[rgba(88,166,255,0.1)] text-[#58a6ff] border-[rgba(88,166,255,0.3)]`;
  return `${badgeBase} bg-[rgba(110,118,129,0.15)] text-[#8b949e] border-[rgba(110,118,129,0.3)]`;
};

const badgeInfo = `${badgeBase} bg-[rgba(110,118,129,0.12)] text-[#8b949e] border-[rgba(110,118,129,0.2)]`;
const badgeImportant = `${badgeBase} bg-[rgba(255,166,0,0.15)] text-[#e3b341] border-[rgba(255,166,0,0.3)]`;

function StatusBadge({ code }: { code?: number }) {
  if (!code) return <span className={statusBadgeCls()}>N/A</span>;
  return <span className={statusBadgeCls(code)}>{code}</span>;
}

function MethodBadge({ method }: { method?: string }) {
  if (!method) return null;
  return <span className={methodBadgeCls(method)}>{method}</span>;
}

function VulnBadge({ severity }: { severity: string }) {
  return <span className={vulnBadgeCls(severity)}>{severity}</span>;
}

function Collapsible({ title, icon, count, children }: { title: string; icon: string; count?: number; children: React.ReactNode }) {
  const [open, setOpen] = useState(true);
  return (
    <div className="bg-[#0d1117] border border-[#21262d] rounded-[10px] mb-[18px] overflow-hidden">
      <div className="flex justify-between items-center px-[18px] py-3 bg-[#161b22] border-b border-[#21262d] cursor-pointer select-none" onClick={() => setOpen(!open)}>
        <span className="text-[0.75rem] font-bold uppercase tracking-[0.1em] text-[#8b949e]"><span className="text-[#58a6ff] mr-1.5">{icon}</span>{title}</span>
        <div className="flex gap-2 items-center">
          {count !== undefined && <span className="text-[0.7rem] text-[#484f58] bg-[#21262d] px-2 py-0.5 rounded-full">{count}</span>}
          <span className={cn("text-[#484f58] text-[0.75rem] transition-transform duration-200", open && "rotate-180")}>▾</span>
        </div>
      </div>
      {open && <div className="px-[18px] py-4">{children}</div>}
    </div>
  );
}

// ─── Main Page ─────────────────────────────────────────────────────────────────

export default function UrlDetailPage() {
  const { targetId, urlId } = useParams();
  const [searchParams] = useSearchParams();
  const nUrlId = Number(urlId);

  const [data, setData] = useState<UrlDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showScanPanel, setShowScanPanel] = useState(false);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [isScanning, setIsScanning] = useState(false);

  const handleRunScan = async () => {
    setIsScanning(true);
    try {
      const { GLOBAL_CONFIG } = await import("../../../config");
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
    } catch (err: unknown) {
      alert("Error: " + (err instanceof Error ? err.message : "Unknown error"));
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
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load URL data.");
    } finally {
      setLoading(false);
    }
  }, [nUrlId]);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) return (
    <div className="c2-page text-center"><div className="c2-loading justify-center">正在載入 URL 詳情…</div>
    </div>
  );
  if (error || !data) return (
    <div className="c2-page text-center">
      {error || "URL not found."}
    </div>
  );

  const d = data;
  const subdomains = d.core_urlresult_related_subdomains.map(r => r.core_subdomain);
  const parsedHeaders: Record<string, string> = d.headers
    ? (typeof d.headers === "string" ? JSON.parse(d.headers) : d.headers)
    : {};

  return (
    <div className="c2-page font-body text-text-primary">
      {/* ── Hero Header ── */}
      <div className="bg-[linear-gradient(135deg,#0d1117_0%,#161b22_100%)] border border-[#21262d] rounded-xl px-7 py-6 mb-6 relative overflow-hidden before:content-[''] before:absolute before:inset-0 before:bg-[linear-gradient(90deg,rgba(0,255,180,0.04)_0%,transparent_50%)] before:pointer-events-none">
        <div className="text-[0.72rem] text-[#484f58] mb-2.5 uppercase tracking-[0.08em]">
          <Link to={searchParams.get('returnTo') || `/target/${targetId}?tab=assets`} className="text-[#58a6ff] no-underline hover:underline">目標</Link>
          {" / "}
          URL 詳情
        </div>

        <div className="text-[1.15rem] font-semibold text-[#e6edf3] break-all mb-3 leading-snug">
          <a href={d.url} target="_blank" rel="noopener noreferrer" className="text-[#58a6ff] no-underline hover:underline">{d.url}</a>
        </div>

        <div className="flex flex-wrap gap-2.5 items-center">
          <StatusBadge code={d.status_code ?? undefined} />
          <MethodBadge method={d.method ?? undefined} />
          {d.is_important && <span className={badgeImportant}>⭐ IMPORTANT</span>}
          {d.used_flaresolverr && <span className={badgeInfo}>FlareSolverr</span>}
          {d.is_external_redirect && <span className={`${badgeBase} bg-[rgba(210,153,34,0.15)] text-[#d29922] border-[rgba(210,153,34,0.3)]`}>→ Redirect</span>}
          {d.discovery_source && <span className={badgeInfo}>{d.discovery_source}</span>}
          {d.content_length !== undefined && d.content_length !== null && (
            <span className={badgeInfo}>{(d.content_length / 1024).toFixed(1)} KB</span>
          )}
          <span className={`${badgeInfo} ml-auto`}>
            {new Date(d.created_at).toLocaleString()}
          </span>
          <button
            className="shrink-0 px-3 py-1 bg-[#f85149] text-white border-none cursor-pointer ml-2.5 font-bold rounded text-[0.68rem]"
            onClick={() => setShowScanPanel(!showScanPanel)}
          >
            {showScanPanel ? "CANCEL" : "LAUNCH NUCLEI"}
          </button>
        </div>
      </div>

      {/* ── Scan Panel ── */}
      {showScanPanel && (
        <div className="bg-[#161b22] border border-[#f85149] rounded-lg p-4 mb-5">
          <div className="text-[#f85149] font-bold mb-2.5">Configure Nuclei Scan</div>
          <div className="mb-2.5 text-[#8b949e] text-[0.85rem]">
            Select specific templates to run. If none selected, default active templates run.
          </div>
          <div className="flex gap-2.5 flex-wrap mb-4">
            {["cves", "sqli", "xss", "lfi", "rce", "misconfiguration", "auth-bypass", "exposure"].map(tag => (
              <label key={tag} className="flex items-center gap-1 cursor-pointer text-[#c9d1d9] text-[0.85rem]">
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
            className="px-4 py-1.5 bg-[#f85149] text-white border-none rounded cursor-pointer font-bold tracking-wide disabled:cursor-not-allowed"
            disabled={isScanning}
            onClick={handleRunScan}
          >
            {isScanning ? "INITIATING..." : "FIRE NUCLEI SCAN 🚀"}
          </button>
        </div>
      )}

      {/* ── Two-column layout ── */}
      <div className="grid grid-cols-[1fr_340px] gap-5 items-start max-[900px]:grid-cols-1">
        {/* LEFT column */}
        <div>

          {/* Basic Info */}
          <Collapsible title="Basic Information" icon="🔍">
            <div className="grid grid-cols-[max-content_1fr] gap-x-5 gap-y-2.5 items-center">
              <span className="text-[0.68rem] font-bold uppercase tracking-wide text-[#484f58] whitespace-nowrap">Title</span>
              <span className="text-sm text-[#c9d1d9] break-all">{d.title || <em className="text-[#484f58] italic text-[0.78rem]">No title</em>}</span>

              {d.final_url && d.final_url !== d.url && (
                <>
                  <span className="text-[0.68rem] font-bold uppercase tracking-wide text-[#484f58] whitespace-nowrap">Final URL</span>
                  <span className="text-sm text-[#c9d1d9] break-all">
                    <a href={d.final_url} target="_blank" rel="noopener noreferrer" className="text-[#58a6ff] no-underline hover:underline">{d.final_url}</a>
                  </span>
                </>
              )}

              <span className="text-[0.68rem] font-bold uppercase tracking-wide text-[#484f58] whitespace-nowrap">Fetch Status</span>
              <span className="text-sm text-[#c9d1d9] break-all">{d.content_fetch_status || <em className="text-[#484f58] italic text-[0.78rem]">Unknown</em>}</span>

              <span className="text-[0.68rem] font-bold uppercase tracking-wide text-[#484f58] whitespace-nowrap">Tech Analyzed</span>
              <span className="text-sm text-[#c9d1d9] break-all">{d.is_tech_analyzed ? "✅ Yes" : "❌ No"}</span>

              {subdomains.length > 0 && (
                <>
                  <span className="text-[0.68rem] font-bold uppercase tracking-wide text-[#484f58] whitespace-nowrap">Subdomains</span>
                  <span className="text-sm text-[#c9d1d9] break-all">
                    {subdomains.map(sub => (
                      <Link
                        key={sub.id}
                        to={`/target/${targetId}/subdomain/${sub.id}?returnTo=${encodeURIComponent(`/target/${targetId}?tab=assets`)}`}
                        className="inline-block mr-2 text-[#58a6ff]"
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
                    {t.categories && <span className="text-[0.6rem] uppercase tracking-[0.06em] text-[#58a6ff] mt-0.5">{t.categories}</span>}
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
                  <div key={k} className="flex gap-3 py-1 border-b border-[#21262d] last:border-b-0 text-[0.75rem]">
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
                    <th className="text-left text-[0.65rem] font-bold uppercase tracking-[0.08em] text-[#484f58] px-2 py-1.5 border-b border-[#21262d]">Attribute</th>
                    <th className="text-left text-[0.65rem] font-bold uppercase tracking-[0.08em] text-[#484f58] px-2 py-1.5 border-b border-[#21262d]">Value</th>
                  </tr>
                </thead>
                <tbody>
                  {d.core_metatags.map(m => (
                    Object.entries(m.attributes || {}).map(([k, v], i) => (
                      <tr key={`${m.id}-${i}`}>
                        <td className="px-2 py-2 border-b border-[#161b22] text-[#c9d1d9] align-top break-all" style={{ color: "#d2a8ff", minWidth: 120 }}>{k}</td>
                        <td className="px-2 py-2 border-b border-[#161b22] text-[#c9d1d9] align-top break-all">{String(v)}</td>
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
                <div key={s.id} className="py-2 border-b border-[#21262d] last:border-b-0">
                  <div className="flex gap-2 items-center mb-1">
                    <span className={badgeInfo}>#{s.id}</span>
                    <StatusBadge code={s.status === "COMPLETED" ? 200 : s.status === "FAILED" ? 500 : undefined} />
                    <span className="text-[0.72rem] text-[#8b949e]">{s.status}</span>
                  </div>
                  <span className="text-[0.68rem] text-[#484f58]">
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
                      <th className="text-left text-[0.65rem] font-bold uppercase tracking-[0.08em] text-[#484f58] px-2 py-1.5 border-b border-[#21262d]">Href</th>
                      <th className="text-left text-[0.65rem] font-bold uppercase tracking-[0.08em] text-[#484f58] px-2 py-1.5 border-b border-[#21262d]">Text</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.core_links.map(link => (
                      <tr key={link.id}>
                        <td className="px-2 py-2 border-b border-[#161b22] text-[#c9d1d9] align-top break-all">
                          <a href={link.href} target="_blank" rel="noopener noreferrer"
                            className="text-[#58a6ff] text-[0.72rem]">
                            {link.href.length > 50 ? link.href.slice(0, 50) + "…" : link.href}
                          </a>
                        </td>
                        <td className="px-2 py-2 border-b border-[#161b22] text-[#8b949e] text-[0.72rem] align-top">{link.text || "—"}</td>
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
                <div key={f.id} className="py-2.5 border-b border-[#21262d] last:border-b-0">
                  <div className="grid grid-cols-[max-content_1fr] gap-x-5 gap-y-2.5 items-center">
                    <span className="text-[0.68rem] font-bold uppercase tracking-wide text-[#484f58] whitespace-nowrap">Action</span>
                    <span className="text-sm text-[#c9d1d9] break-all">{f.action || "—"}</span>
                    <span className="text-[0.68rem] font-bold uppercase tracking-wide text-[#484f58] whitespace-nowrap">Method</span>
                    <span className="text-sm text-[#c9d1d9] break-all">{f.method || "GET"}</span>
                  </div>
                  {f.parameters && (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-[0.72rem] text-[#58a6ff]">
                        View parameters
                      </summary>
                      <pre className="bg-[#161b22] p-2.5 rounded-md text-[0.72rem] text-[#a5d6ff] mt-2 overflow-x-auto">
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
