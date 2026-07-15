import { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import {
  GET_SEED_ULTIMATE_INTEL_QUERY,
  ReconService,
  gqlFetcher,
} from "../services/targetApi";
import type {
  SeedIntelligenceResponse,
  Subdomain,
  IP,
  UrlResult,
} from "../types";
import { cn } from '@/lib/utils';

const AssetCard: React.FC<{
  title: string;
  count: number;
  children: React.ReactNode;
}> = ({ title, count, children }) => {
  const [isOpen, setIsOpen] = useState(true);
  return (
    <div className="bg-[#1e1e1e] border border-[#333] rounded-md mb-5 overflow-hidden">
      <div className="flex justify-between items-center px-5 py-[15px] cursor-pointer bg-[#2a2a2a] transition-colors duration-200 hover:bg-[#383838]" onClick={() => setIsOpen(!isOpen)}>
        <div className="text-lg font-bold uppercase tracking-[0.5px]">{title}</div>
        <div>
          <span className="bg-[#2196f3] text-white px-2.5 py-1 rounded-full text-sm font-bold mr-[15px]">{count}</span>
          <span className={cn("text-2xl text-[#a0a0a0] transition-transform duration-200", isOpen && "rotate-180")}>▼</span>
        </div>
      </div>
      {isOpen && <div className="p-0 max-h-[600px] overflow-y-auto border-t border-[#333]">{children}</div>}
    </div>
  );
};

function SeedReconPage() {
  const { targetId, seedId } = useParams();
  const nSeedId = Number(seedId);

  const [intel, setIntel] = useState<SeedIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);

  const fetchIntel = useCallback(async () => {
    if (!nSeedId) return;
    try {
      const data = await gqlFetcher<SeedIntelligenceResponse>(
        GET_SEED_ULTIMATE_INTEL_QUERY,
        { seed_id: nSeedId }
      );
      setIntel(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [nSeedId]);

  const handleStartScan = async () => {
    if (!nSeedId) return;
    setTriggering(true);
    try {
      await ReconService.startDomainRecon(nSeedId);
      setTimeout(fetchIntel, 1000);
    } catch (err: unknown) {
      alert(`指令被拒絕: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setTriggering(false);
    }
  };

  useEffect(() => {
    fetchIntel();
    const interval = setInterval(fetchIntel, 10000);
    return () => clearInterval(interval);
  }, [fetchIntel]);

  if (loading) return <div>LOADING INTEL...</div>;

  const seedData = intel?.core_seed?.[0];
  if (!seedData) return <div>SEED NOT FOUND</div>;

  const subfinderScans = seedData.core_subfinderscans || [];
  const isSubfinderRunning = subfinderScans.some(
    (s) => s.status === "PENDING" || s.status === "RUNNING"
  );
  const isRunning = isSubfinderRunning;

  const allIPs = (seedData.core_ip_which_seeds || []).map(
    (item) => item.core_ip
  );

  const allSubdomains = (seedData.core_subdomainseeds || []).map(
    (item) => item.core_subdomain
  );

  const allURLs = allSubdomains.flatMap((sub: Subdomain) =>
    (sub.core_urlresult_related_subdomains || []).map(
      (rel) => rel.core_urlresult
    )
  );

  const statusBadgeCls = (status: string) => cn(
    "px-2.5 py-1 rounded text-sm font-bold text-center min-w-[90px] inline-block",
    status === 'PENDING' && "bg-[#ffab00] text-black",
    status === 'RUNNING' && "bg-[#2196f3] text-white animate-pulse",
    status === 'COMPLETED' && "bg-[#00c853] text-black",
    status === 'FAILED' && "bg-[#d32f2f] text-white",
  );

  return (
    <div className="c2-page font-body text-text-primary">
      {/* Header */}
      <div className="bg-[#1e1e1e] border border-[#333] px-[30px] py-[25px] rounded-md mb-[30px] flex justify-between items-center border-l-4 border-l-[#2196f3]">
        <div>
          <div className="text-3xl font-bold text-white mb-1 tracking-[1px]">{seedData.value}</div>
          <div className="text-[#666]">ID: {seedData.id}</div>
        </div>
        <button
          className="bg-[#d32f2f] text-white font-mono text-base font-bold px-6 py-3 rounded cursor-pointer transition-all duration-200 uppercase tracking-[1px] shadow-[0_0_5px_rgba(211,47,47,0.4)] hover:bg-[#b71c1c] hover:-translate-y-0.5 hover:shadow-[0_4px_20px_rgba(211,47,47,0.6)] disabled:bg-[#555] disabled:cursor-not-allowed disabled:opacity-60 disabled:shadow-none"
          onClick={handleStartScan}
          disabled={triggering || isRunning}
        >
          {triggering
            ? "INITIATING..."
            : isRunning
            ? "SCAN RUNNING"
            : "START RECON"}
        </button>
      </div>

      {/* 掃描記錄 */}
      <AssetCard title="Subdomain Scans" count={subfinderScans.length}>
        {subfinderScans.length > 0 ? (
          <div className="scan-history-list">
            {subfinderScans.map((scan) => (
              <div key={scan.id} className="flex justify-between items-center px-5 py-[15px] border-b border-[#333] last:border-b-0 [&>*]:basis-1/4">
                <span className="font-mono text-[#666]">
                  #{scan.id}
                </span>
                <span className={statusBadgeCls(scan.status)}>
                  {scan.status}
                </span>
                <span>New Found: {scan.added_count}</span>
                <span className="text-[#888] text-[0.9em]">
                  {new Date(scan.created_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-10 text-center text-[#a0a0a0]">No scan records.</div>
        )}
      </AssetCard>

      <h3 className="mt-[30px]">DISCOVERED ASSETS</h3>

      {/* 子域名資產 */}
      <AssetCard title="Subdomains" count={allSubdomains.length}>
        {allSubdomains.length > 0 ? (
          <table className="w-full border-collapse [&_tr:nth-child(even)]:bg-black/20 [&_tr:last-child_td]:border-b-0">
            <thead>
              <tr>
                <th className="text-left px-5 py-[14px] border-b border-[#333] text-[#a0a0a0] text-sm uppercase">NAME</th>
                <th className="text-left px-5 py-[14px] border-b border-[#333] text-[#a0a0a0] text-sm uppercase">DISCOVERED AT</th>
                <th className="text-left px-5 py-[14px] border-b border-[#333] text-[#a0a0a0] text-sm uppercase">TO DETAIL</th>
                <th className="text-left px-5 py-[14px] border-b border-[#333] text-[#a0a0a0] text-sm uppercase">ID</th>
              </tr>
            </thead>
            <tbody>
              {allSubdomains.map((sub: Subdomain) => (
                <tr key={sub.id}>
                  <td className="text-left px-5 py-[14px] border-b border-[#333]">{sub.name}</td>
                  <td className="text-left px-5 py-[14px] border-b border-[#333]">{new Date(sub.created_at).toLocaleString()}</td>
                  <td className="text-left px-5 py-[14px] border-b border-[#333]">
                    <a
                      href={`/target/${targetId}/subdomain/${sub.id}`}
                      className="btn btn-ghost btn-sm no-underline"
                    >
                      Detail
                    </a>
                  </td>
                  <td className="text-left px-5 py-[14px] border-b border-[#333]">{sub.id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-10 text-center text-[#a0a0a0]">No subdomains found.</div>
        )}
      </AssetCard>

      {/* IP 資產 */}
      <AssetCard title="IP Addresses" count={allIPs.length}>
        {allIPs.length > 0 ? (
          <table className="w-full border-collapse [&_tr:nth-child(even)]:bg-black/20 [&_tr:last-child_td]:border-b-0">
            <thead>
              <tr>
                <th className="text-left px-5 py-[14px] border-b border-[#333] text-[#a0a0a0] text-sm uppercase">ID</th>
                <th className="text-left px-5 py-[14px] border-b border-[#333] text-[#a0a0a0] text-sm uppercase">IP ADDRESS</th>
              </tr>
            </thead>
            <tbody>
              {allIPs.map((ip: IP) => (
                <tr key={ip.id}>
                  <td className="text-left px-5 py-[14px] border-b border-[#333]">{ip.id}</td>
                  <td className="text-left px-5 py-[14px] border-b border-[#333]">
                    <a
                      href={`/target/${targetId}/ip/${ip.id}`}
                      className="asset-link ip-link"
                    >
                      {ip.address || 'Unknown'}
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-10 text-center text-[#a0a0a0]">No IP addresses found.</div>
        )}
      </AssetCard>

      {/* URL 資產 */}
      <AssetCard title="URLs Found" count={allURLs.length}>
        {allURLs.length > 0 ? (
          <table className="w-full border-collapse [&_tr:nth-child(even)]:bg-black/20 [&_tr:last-child_td]:border-b-0">
            <thead>
              <tr>
                <th className="text-left px-5 py-[14px] border-b border-[#333] text-[#a0a0a0] text-sm uppercase">STATUS</th>
                <th className="text-left px-5 py-[14px] border-b border-[#333] text-[#a0a0a0] text-sm uppercase">URL</th>
                <th className="text-left px-5 py-[14px] border-b border-[#333] text-[#a0a0a0] text-sm uppercase">DETAILS</th>
              </tr>
            </thead>
            <tbody>
              {allURLs.map((url: UrlResult) => (
                <tr key={url.id}>
                  <td className="text-left px-5 py-[14px] border-b border-[#333]">
                    <span className="font-mono text-[0.78rem] opacity-80">
                      {url.status_code || "—"}
                    </span>
                  </td>
                  <td className="text-left px-5 py-[14px] border-b border-[#333]">
                    <a
                      href={url.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="asset-link url-link"
                    >
                      {url.url}
                    </a>
                  </td>
                  <td className="text-left px-5 py-[14px] border-b border-[#333]">
                    <a
                      href={`/target/${targetId}/url/${url.id}`}
                      className="btn btn-ghost btn-sm no-underline"
                    >
                      Detail
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-10 text-center text-[#a0a0a0]">No URLs found.</div>
        )}
      </AssetCard>
    </div>
  );
}

export default SeedReconPage;
