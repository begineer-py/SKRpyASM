import { useState, useEffect, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { gqlFetcher } from "../services/targetApi";
import { cn } from '@/lib/utils';

const GET_URL_SEED_DATA = `
  query GetUrlSeedData($seed_id: bigint!) {
    core_seed_by_pk(id: $seed_id) {
      id
      value
      type
    }
  }
`;

const GET_URL_RESULT_BY_URL = `
  query GetUrlResultByUrl($url: String!) {
    core_urlresult(where: {url: {_eq: $url}}, limit: 1) {
      id
      status_code
      title
      core_nucleiscans(order_by: {created_at: desc}) {
        id
        status
        created_at
        completed_at
      }
    }
  }
`;

interface UrlSeedQueryResponse {
  core_seed_by_pk: { id: number; value: string; type: string } | null;
}

interface UrlReconScan {
  id: number;
  status: string;
  created_at: string;
  completed_at?: string | null;
}

interface UrlResultRecord {
  id: number;
  status_code?: number | null;
  title?: string | null;
  core_nucleiscans: UrlReconScan[];
}

interface UrlResultQueryResponse {
  core_urlresult: UrlResultRecord[];
}

function UrlReconPage() {
  const { targetId, seedId } = useParams();
  const nSeedId = Number(seedId);

  const [seedVal, setSeedVal] = useState<string | null>(null);
  const [urlId, setUrlId] = useState<number | null>(null);
  const [urlResult, setUrlResult] = useState<UrlResultRecord | null>(null);
  const [loading, setLoading] = useState(true);

  // Scanner UI States
  const [triggering, setTriggering] = useState(false);
  const [selectedTags, setSelectedTags] = useState<string[]>(["cves"]);
  const availableTags = ["cves", "sqli", "xss", "lfi", "rce", "misconfiguration", "auth-bypass", "exposure"];

  const fetchData = useCallback(async () => {
    if (!nSeedId) return;
    try {
      setLoading(true);
      // 1. Get Seed
      const seedRes = await gqlFetcher<UrlSeedQueryResponse>(GET_URL_SEED_DATA, { seed_id: nSeedId });
      const seed = seedRes.core_seed_by_pk;
      if (!seed) throw new Error("Seed not found");
      setSeedVal(seed.value);

      // 2. Map to URLResult
      const resultRes = await gqlFetcher<UrlResultQueryResponse>(GET_URL_RESULT_BY_URL, { url: seed.value });
      if (resultRes.core_urlresult && resultRes.core_urlresult.length > 0) {
        const ur = resultRes.core_urlresult[0];
        setUrlId(ur.id);
        setUrlResult(ur);
      }
    } catch (err: unknown) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [nSeedId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleRunNuclei = async () => {
    if (!urlId) {
      alert("Error: Missing internal URL ID. Wait for the background worker to parse the seed first!");
      return;
    }
    setTriggering(true);
    try {
      const { GLOBAL_CONFIG } = await import("../../../config");
      const res = await fetch(`${GLOBAL_CONFIG.DJANGO_API_BASE}/scanners/vuln/urls`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          ids: [urlId], 
          tags: selectedTags.length > 0 ? selectedTags : undefined 
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || "Failed to trigger scan");
      }
      alert("Nuclei scan dispatched successfully!");
      fetchData(); // Refresh history
    } catch (err: unknown) {
      alert("Error: " + (err instanceof Error ? err.message : "Unknown error"));
    } finally {
      setTriggering(false);
    }
  };

  const toggleTag = (tag: string) => {
    if (selectedTags.includes(tag)) {
      setSelectedTags(selectedTags.filter(t => t !== tag));
    } else {
      setSelectedTags([...selectedTags, tag]);
    }
  };

  if (loading) return <div className="c2-page"><div className="c2-loading">正在載入 URL 偵察資料…</div></div>;
  if (!seedVal) return <div className="c2-page"><div className="c2-empty">找不到 Seed 資料。</div></div>;

  return (
    <div className="c2-page font-body text-text-primary">
      {/* Target Module */}
      <div className="bg-[#1e1e1e] border border-[#333] px-[30px] py-[25px] rounded-md mb-[30px] flex justify-between items-center border-l-4 border-red">
        <div>
          <div className="text-red font-bold tracking-wider mb-2 text-[0.8rem] uppercase">TARGET URL</div>
          <div className="text-3xl font-bold text-white mb-1 tracking-[1px]">{seedVal}</div>
          <div className="text-text-muted mt-1.5 flex gap-4">
            <span>SEED ID: {nSeedId}</span>
            <span>INTERNAL URL ID: {urlId || "INITIALIZING..."}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-[2fr_1fr] gap-5 mt-5">
        {/* Left Column: Command Center */}
        <div>
          <div className="bg-[#1e1e1e] border border-[#333] rounded-md mb-5 overflow-hidden">
            <div className="flex justify-between items-center px-5 py-[15px] cursor-default bg-[#2a2a2a] transition-colors duration-200 hover:bg-[#383838]">
              <div className="text-lg font-bold uppercase tracking-[0.5px] text-blue">🚀 NUCLEI COMMAND CENTER</div>
            </div>
            <div className="max-h-[600px] overflow-y-auto border-t border-[#333]">
              <p className="text-text-secondary text-[0.9rem] mb-4">
                URL templates are unique and highly specialized for web application endpoints. Select payload tags to inject into the Nuclei engine.
              </p>
              
              <div className="mb-5">
                <div className="text-text-primary text-[0.8rem] mb-3 tracking-wider">SELECT PAYLOAD TEMPLATES (TAGS)</div>
                <div className="flex gap-2.5 flex-wrap">
                  {availableTags.map(tag => (
                    <div 
                      key={tag}
                      onClick={() => toggleTag(tag)}
                      className="px-3 py-1.5 rounded cursor-pointer text-[0.8rem] font-mono transition-all duration-200"
                      style={{
                        border: selectedTags.includes(tag) ? "1px solid #f85149" : "1px solid #30363d",
                        background: selectedTags.includes(tag) ? "rgba(248,81,73,0.15)" : "#21262d",
                        color: selectedTags.includes(tag) ? "#ff7b72" : "#8b949e",
                      }}
                    >
                      {tag.toUpperCase()}
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-3 items-center">
                <button 
                  className="bg-red text-white font-mono text-base font-bold px-6 py-3 rounded cursor-pointer transition-all duration-200 uppercase tracking-[1px] shadow-[0_0_5px_rgba(211,47,47,0.4)] hover:bg-[#b71c1c] hover:-translate-y-0.5 hover:shadow-[0_4px_20px_rgba(211,47,47,0.6)] disabled:bg-[#555] disabled:cursor-not-allowed disabled:opacity-60 disabled:shadow-none"
                  onClick={handleRunNuclei}
                  disabled={triggering || !urlId}
                >
                  {triggering ? "DISPATCHING..." : "DEPLOY NUCLEI SCAN"}
                </button>
                {!urlId && <span className="text-red text-[0.8rem]">Awaiting backend database synchronization...</span>}
              </div>
            </div>
          </div>

          <div className="bg-[#1e1e1e] border border-[#333] rounded-md mb-5 overflow-hidden opacity-60 pointer-events-none">
            <div className="flex justify-between items-center px-5 py-[15px] cursor-pointer bg-[#2a2a2a] transition-colors duration-200 hover:bg-[#383838]">
              <div className="text-lg font-bold uppercase tracking-[0.5px] text-purple">🔒 SQLMAP INTEGRATION (IN DEVELOPMENT)</div>
            </div>
            <div className="max-h-[600px] overflow-y-auto border-t border-[#333]">
              Module unmounted. Specialized SQL injection automation will be deployed here.
            </div>
          </div>
        </div>

        {/* Right Column: Execution History */}
        <div>
          <div className="bg-[#1e1e1e] border border-[#333] rounded-md mb-5 overflow-hidden">
            <div className="flex justify-between items-center px-5 py-[15px] cursor-default bg-[#2a2a2a] transition-colors duration-200 hover:bg-[#383838]">
              <div className="text-lg font-bold uppercase tracking-[0.5px]">EXECUTION HISTORY</div>
              <span className="bg-[#2196f3] text-white px-2.5 py-1 rounded-full text-sm font-bold mr-[15px]">{urlResult?.core_nucleiscans?.length || 0}</span>
            </div>
            <div className="max-h-[600px] overflow-y-auto border-t border-[#333] p-0">
              {(!urlResult?.core_nucleiscans || urlResult.core_nucleiscans.length === 0) ? (
                <div className="p-10 text-center text-[#a0a0a0]">No scan deployments recorded.</div>
              ) : (
                <div className="flex flex-col">
                  {urlResult.core_nucleiscans.map((scan) => (
                    <div key={scan.id} className="px-5 py-4 border-b border-border-subtle">
                      <div className="flex justify-between mb-1.5">
                        <span className="text-blue font-mono text-[0.85rem]">#SCAN-{scan.id}</span>
                        <span className={cn(
                          "px-2.5 py-1 rounded text-sm font-bold text-center min-w-[90px] inline-block",
                          scan.status === 'PENDING' && "bg-[#ffab00] text-black",
                          scan.status === 'RUNNING' && "bg-[#2196f3] text-white animate-pulse",
                          scan.status === 'COMPLETED' && "bg-[#00c853] text-black",
                          scan.status === 'FAILED' && "bg-[#d32f2f] text-white",
                        )}>{scan.status}</span>
                      </div>
                      <div className="text-text-secondary text-[0.75rem]">
                        DISPATCHED: {new Date(scan.created_at).toLocaleString()}
                      </div>
                    </div>
                  ))}
                  
                  {urlId && (
                    <div className="p-4 text-center">
                      <Link to={`/target/${targetId}/url/${urlId}`} className="btn btn-ghost text-[0.75rem] w-full text-center">
                        VIEW DETAILED FINDINGS →
                      </Link>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default UrlReconPage;
