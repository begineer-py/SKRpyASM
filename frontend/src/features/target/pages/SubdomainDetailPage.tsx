import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import {
  AiAnalysisService,
  GET_SUBDOMAIN_DETAIL_QUERY,
  gqlFetcher,
} from "../services/targetApi";
import type { SubdomainIntelResponse } from "../types";
import { cn } from '@/lib/utils';

const BooleanDisplay: React.FC<{ value: boolean }> = ({ value }) => (
  <span className={cn("text-lg text-[#e0e0e0] font-bold", value ? "text-[#00c853]" : "text-[#d32f2f]")}>
    {value ? "TRUE" : "FALSE"}
  </span>
);

function SubdomainDetailPage() {
  const { targetId, subdomainId } = useParams();
  const nSubdomainId = Number(subdomainId);

  const [intel, setIntel] = useState<SubdomainIntelResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const fetchData = () => {
    if (!nSubdomainId) return;
    setLoading(true);
    gqlFetcher<SubdomainIntelResponse>(GET_SUBDOMAIN_DETAIL_QUERY, {
      subdomain_id: nSubdomainId,
    })
      .then((data) => setIntel(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const handleRequestAiAnalysis = async () => {
    if (!intel?.core_subdomain_by_pk) return;

    setIsAnalyzing(true);
    try {
      const response = await AiAnalysisService.analyzeSubdomains([
        intel.core_subdomain_by_pk.name,
      ]);
      alert(`AI 分析任務已提交: ${response.detail}`);
      setTimeout(fetchData, 5000);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [nSubdomainId]);

  if (loading) return <div>Loading Subdomain Intel...</div>;
  if (!intel || !intel.core_subdomain_by_pk)
    return <div>Subdomain not found.</div>;

  const subdomain = intel.core_subdomain_by_pk;
  const aiAnalysis = subdomain.core_initialaianalyses?.[0];
  const relatedUrls = intel.core_urlresult.filter((url) =>
    url.url.includes(subdomain.name)
  );

  return (
    <div className="max-w-[1600px] mx-auto p-5 pt-[calc(var(--navbar-height)+24px)] font-mono">
      {/* 標頭 */}
      <div className="mb-5">
        <h1 className="m-0">{subdomain.name}</h1>
        <div className="text-[#888]">Subdomain Deep-Dive Analysis</div>
      </div>

      <div className="grid grid-cols-[2fr_1fr] gap-[25px] items-start">
        {/* 左側主情報區 */}
        <main className="sdd-main [&_.info-item]:mb-4 [&_.info-item:last-child]:mb-0">
          {/* 基礎情報 */}
          <div className="bg-[#1e1e1e] border border-[#333] rounded-md mb-[25px] overflow-hidden">
            <div className="bg-[#2a2a2a] px-5 py-3 font-bold text-base uppercase tracking-[0.5px] border-b border-[#333]">Basic Information</div>
            <div className="p-5 grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-5 [&_.info-item]:mb-0">
              <div className="info-item">
                <span className="block text-sm text-[#a0a0a0] mb-1">ID</span>{" "}
                <span className="text-lg text-[#e0e0e0] font-bold">{subdomain.id}</span>
              </div>
              <div className="info-item">
                <span className="block text-sm text-[#a0a0a0] mb-1">Active</span>{" "}
                <BooleanDisplay value={subdomain.is_active} />
              </div>
              <div className="info-item">
                <span className="block text-sm text-[#a0a0a0] mb-1">Resolvable</span>{" "}
                <BooleanDisplay value={subdomain.is_resolvable} />
              </div>
              <div className="info-item">
                <span className="block text-sm text-[#a0a0a0] mb-1">Created At</span>{" "}
                <span className="text-lg text-[#e0e0e0] font-bold">{new Date(subdomain.created_at).toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* 安全情報 */}
          <div className="bg-[#1e1e1e] border border-[#333] rounded-md mb-[25px] overflow-hidden">
            <div className="bg-[#2a2a2a] px-5 py-3 font-bold text-base uppercase tracking-[0.5px] border-b border-[#333]">Security Posture</div>
            <div className="p-5 grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-5 [&_.info-item]:mb-0">
              <div className="info-item">
                <span className="block text-sm text-[#a0a0a0] mb-1">Behind CDN</span>{" "}
                <BooleanDisplay value={subdomain.is_cdn} />
              </div>
              <div className="info-item">
                <span className="block text-sm text-[#a0a0a0] mb-1">CDN Name</span>{" "}
                <span className="text-lg text-[#e0e0e0] font-bold">
                  {subdomain.cdn_name || "N/A"}
                </span>
              </div>
              <div className="info-item">
                <span className="block text-sm text-[#a0a0a0] mb-1">Behind WAF</span>{" "}
                <BooleanDisplay value={subdomain.is_waf} />
              </div>
              <div className="info-item">
                <span className="block text-sm text-[#a0a0a0] mb-1">WAF Name</span>{" "}
                <span className="text-lg text-[#e0e0e0] font-bold">
                  {subdomain.waf_name || "N/A"}
                </span>
              </div>
            </div>
          </div>

          {/* 關聯資產 */}
          <div className="bg-[#1e1e1e] border border-[#333] rounded-md mb-[25px] overflow-hidden">
            <div className="bg-[#2a2a2a] px-5 py-3 font-bold text-base uppercase tracking-[0.5px] border-b border-[#333]">Associated Assets</div>
            <div className="p-5">
              <div className="info-item mb-4">
                <span className="block text-sm text-[#a0a0a0] mb-1">Resolved IPs</span>
                <div className="flex flex-col gap-2">
                  {subdomain.core_subdomain_ips.length > 0 ? (
                    subdomain.core_subdomain_ips.map(({ core_ip }) => (
                      <div key={core_ip.id} className="flex items-center gap-2">
                        <span>🌐</span>
                        <a
                          href={`/target/${targetId}/ip/${core_ip.id}`}
                          className="asset-link ip-link"
                        >
                          {core_ip.address}
                        </a>
                      </div>
                    ))
                  ) : (
                    <span className="text-text-muted">None</span>
                  )}
                </div>
              </div>
              <div className="info-item">
                <span className="block text-sm text-[#a0a0a0] mb-1">Related URLs</span>
                <div className="flex flex-col gap-2">
                  {relatedUrls.length > 0 ? (
                    relatedUrls.map((u) => (
                      <div key={u.id} className="flex items-center gap-2">
                        <span>🔗</span>
                        <a
                          href={`/target/${targetId}/url/${u.id}`}
                          className="asset-link url-link"
                        >
                          {u.url}
                        </a>
                      </div>
                    ))
                  ) : (
                    <span className="text-text-muted">None</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </main>
        {/* 右側 AI 分析 */}
        <aside className="sticky top-5">
          <div className="bg-[#1e1e1e] border border-[#2196f3] rounded-md mb-[25px] overflow-hidden">
            <div className="bg-[rgba(33,150,243,0.2)] px-5 py-3 font-bold text-base uppercase tracking-[0.5px] border-b border-[#333] text-[#2196f3]">AI-Powered Tactical Briefing</div>

            {aiAnalysis ? (
              <div className="p-5 [&_.info-item]:mb-6">
                <div className="info-item">
                  <span className="block text-sm text-[#2196f3] font-bold mb-2">Risk Score</span>
                  <span className="text-lg text-[#e0e0e0] font-bold">{aiAnalysis.risk_score}</span>
                </div>

                <div className="info-item">
                  <span className="block text-sm text-[#2196f3] font-bold mb-2">Worth Deep Analysis</span>
                  <BooleanDisplay value={aiAnalysis.worth_deep_analysis} />
                </div>

                <div className="info-item">
                  <span className="block text-sm text-[#2196f3] font-bold mb-2">Summary</span>
                  <p className="text-base leading-relaxed text-[#e0e0e0] m-0">{aiAnalysis.summary}</p>
                </div>

                <div className="info-item">
                  <span className="block text-sm text-[#2196f3] font-bold mb-2">Inferred Purpose</span>
                  <p className="text-base leading-relaxed text-[#e0e0e0] m-0">{aiAnalysis.inferred_purpose}</p>
                </div>
              </div>
            ) : (
              <div className="p-5 text-center px-5 py-10 text-[#a0a0a0]">
                <p>No analysis data available for this subdomain.</p>
                <button
                  className="bg-[#2196f3] text-white px-5 py-2.5 cursor-pointer"
                  onClick={handleRequestAiAnalysis}
                  disabled={isAnalyzing}
                >
                  {isAnalyzing ? "SUBMITTING..." : "REQUEST AI ANALYSIS"}
                </button>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}

export default SubdomainDetailPage;
