import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { gqlFetcher } from "../../services/api";
import "../SeedReconPageSub/SeedReconPage.css"; // Reuse styling variables

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

function UrlReconPage() {
  const { targetId, seedId } = useParams();
  const nSeedId = Number(seedId);

  const [seedVal, setSeedVal] = useState<string | null>(null);
  const [urlId, setUrlId] = useState<number | null>(null);
  const [urlResult, setUrlResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Scanner UI States
  const [triggering, setTriggering] = useState(false);
  const [selectedTags, setSelectedTags] = useState<string[]>(["cves"]);
  const availableTags = ["cves", "sqli", "xss", "lfi", "rce", "misconfiguration", "auth-bypass", "exposure"];

  const fetchData = async () => {
    if (!nSeedId) return;
    try {
      setLoading(true);
      // 1. Get Seed
      const seedRes = await gqlFetcher<any>(GET_URL_SEED_DATA, { seed_id: nSeedId });
      const seed = seedRes.core_seed_by_pk;
      if (!seed) throw new Error("Seed not found");
      setSeedVal(seed.value);

      // 2. Map to URLResult
      const resultRes = await gqlFetcher<any>(GET_URL_RESULT_BY_URL, { url: seed.value });
      if (resultRes.core_urlresult && resultRes.core_urlresult.length > 0) {
        const ur = resultRes.core_urlresult[0];
        setUrlId(ur.id);
        setUrlResult(ur);
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [nSeedId]);

  const handleRunNuclei = async () => {
    if (!urlId) {
      alert("Error: Missing internal URL ID. Wait for the background worker to parse the seed first!");
      return;
    }
    setTriggering(true);
    try {
      const { GLOBAL_CONFIG } = await import("../../config");
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
    } catch (err: any) {
      alert("Error: " + err.message);
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

  if (loading) return <div className="recon-container">INITIALIZING URL RECON ENVIRONMENT...</div>;
  if (!seedVal) return <div className="recon-container">ERROR: SEED DATA NOT FOUND.</div>;

  return (
    <div className="recon-container">
      {/* Target Module */}
      <div className="recon-header-card border-l-4 border-red">
        <div>
          <div className="text-red font-bold tracking-wider mb-2 text-[0.8rem] uppercase">TARGET URL</div>
          <div className="seed-info-large">{seedVal}</div>
          <div className="text-text-muted mt-1.5 flex gap-4">
            <span>SEED ID: {nSeedId}</span>
            <span>INTERNAL URL ID: {urlId || "INITIALIZING..."}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-[2fr_1fr] gap-5 mt-5">
        {/* Left Column: Command Center */}
        <div>
          <div className="assets-card">
            <div className="assets-header cursor-default">
              <div className="assets-title text-blue">🚀 NUCLEI COMMAND CENTER</div>
            </div>
            <div className="assets-content">
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
                  className="btn-fire bg-red border-red"
                  onClick={handleRunNuclei}
                  disabled={triggering || !urlId}
                >
                  {triggering ? "DISPATCHING..." : "DEPLOY NUCLEI SCAN"}
                </button>
                {!urlId && <span className="text-red text-[0.8rem]">Awaiting backend database synchronization...</span>}
              </div>
            </div>
          </div>

          <div className="assets-card opacity-60 pointer-events-none">
            <div className="assets-header">
              <div className="assets-title text-purple">🔒 SQLMAP INTEGRATION (IN DEVELOPMENT)</div>
            </div>
            <div className="assets-content">
              Module unmounted. Specialized SQL injection automation will be deployed here.
            </div>
          </div>
        </div>

        {/* Right Column: Execution History */}
        <div>
          <div className="assets-card">
            <div className="assets-header cursor-default">
              <div className="assets-title">EXECUTION HISTORY</div>
              <span className="assets-count">{urlResult?.core_nucleiscans?.length || 0}</span>
            </div>
            <div className="assets-content p-0">
              {(!urlResult?.core_nucleiscans || urlResult.core_nucleiscans.length === 0) ? (
                <div className="empty-state-message">No scan deployments recorded.</div>
              ) : (
                <div className="flex flex-col">
                  {urlResult.core_nucleiscans.map((scan: any) => (
                    <div key={scan.id} className="px-5 py-4 border-b border-border-subtle">
                      <div className="flex justify-between mb-1.5">
                        <span className="text-blue font-mono text-[0.85rem]">#SCAN-{scan.id}</span>
                        <span className={`status-badge status-${scan.status}`}>{scan.status}</span>
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
