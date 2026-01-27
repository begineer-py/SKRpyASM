import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { gqlFetcher } from "../../services/api";
import {
  ReconService,
  GET_SEED_ULTIMATE_INTEL_QUERY,
} from "../../services/api_recon";
import type {
  SeedIntelligenceResponse,
  Subdomain,
  IP,
  UrlResult,
} from "../../type";
import "./SeedReconPage.css";

// 可折疊卡片組件
const AssetCard: React.FC<{
  title: string;
  count: number;
  children: React.ReactNode;
}> = ({ title, count, children }) => {
  const [isOpen, setIsOpen] = useState(true);
  return (
    <div className="assets-card">
      <div className="assets-header" onClick={() => setIsOpen(!isOpen)}>
        <div className="assets-title">{title}</div>
        <div>
          <span className="assets-count">{count}</span>
          <span className={`assets-toggle ${isOpen ? "expanded" : ""}`}>▼</span>
        </div>
      </div>
      {isOpen && <div className="assets-content">{children}</div>}
    </div>
  );
};

function SeedReconPage() {
  const { targetId, seedId } = useParams();
  const navigate = useNavigate();
  const nSeedId = Number(seedId);

  const [intel, setIntel] = useState<SeedIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);

  const fetchIntel = async () => {
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
  };

  const handleStartScan = async () => {
    if (!nSeedId) return;
    setTriggering(true);
    try {
      await ReconService.startDomainRecon(nSeedId);
      setTimeout(fetchIntel, 1000);
    } catch (err: any) {
      alert(`指令被拒絕: ${err.message}`);
    } finally {
      setTriggering(false);
    }
  };

  useEffect(() => {
    fetchIntel();
    const interval = setInterval(fetchIntel, 10000);
    return () => clearInterval(interval);
  }, [nSeedId]);

  if (loading) return <div>LOADING INTEL...</div>;

  // 1. 取得 Seed 本體 (安全取值)
  const seedData = intel?.core_seed?.[0];
  if (!seedData) return <div>SEED NOT FOUND</div>;

  // =========================================================================
  // 資料清洗區 (這裡全是地雷，但我幫你掃乾淨了)
  // =========================================================================

  // [防禦性編碼] 所有的 Array 在使用前都先 || []，確保不是 undefined

  // 2. 檢查掃描狀態
  const subfinderScans = seedData.core_subfinderscans || [];
  const isSubfinderRunning = subfinderScans.some(
    (s: any) => s.status === "PENDING" || s.status === "RUNNING"
  );
  const isRunning = isSubfinderRunning;

  // 3. 洗出 IP
  // 根據 Type: core_ip_which_seeds 是一個包裝物件的陣列，這裡你的邏輯是對的
  const allIPs = (seedData.core_ip_which_seeds || []).map(
    (item: any) => item.core_ip
  );

  // 4. 洗出 Subdomains
  // [修正重點] 根據 Type: core_subdomains 本身就是 Subdomain[]，不需要再去 map item.core_subdomain
  const allSubdomains = seedData.core_subdomains || [];

  // 5. 洗出 URLs
  // 這裡要用 optional chaining (?.) 防止 Subdomain 裡面的關聯也是空的
  const allURLs = allSubdomains.flatMap((sub: Subdomain) =>
    (sub.core_urlresult_related_subdomains || []).map(
      (rel: any) => rel.core_urlresult
    )
  );

  // =========================================================================

  return (
    <div className="recon-container">
      {/* Header */}
      <div className="recon-header-card">
        <div>
          <div className="seed-info-large">{seedData.value}</div>
          <div style={{ color: "#666" }}>ID: {seedData.id}</div>
        </div>
        <button
          className="btn-fire"
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
      <AssetCard
        title="Subdomain Scans"
        count={subfinderScans.length} // 這裡已經在上面定義時確保是陣列了，安全
      >
        {subfinderScans.length > 0 ? (
          <div className="scan-history-list">
            {subfinderScans.map((scan) => (
              <div key={scan.id} className="scan-item">
                <span style={{ fontFamily: "monospace", color: "#666" }}>
                  #{scan.id}
                </span>
                <span className={`status-badge status-${scan.status}`}>
                  {scan.status}
                </span>
                <span>New Found: {scan.added_count}</span>
                <span style={{ color: "#888", fontSize: "0.9em" }}>
                  {new Date(scan.created_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state-message">No scan records.</div>
        )}
      </AssetCard>

      <h3 style={{ marginTop: 30 }}>DISCOVERED ASSETS</h3>

      {/* 子域名資產 */}
      <AssetCard title="Subdomains" count={allSubdomains.length}>
        {allSubdomains.length > 0 ? (
          <table className="assets-table">
            <thead>
              <tr>
                <th>NAME</th>
                <th>DISCOVERED AT</th>
                <th>TO DETAIL</th>
                <th>ID</th>
              </tr>
            </thead>
            <tbody>
              {allSubdomains.map((sub: Subdomain) => (
                <tr key={sub.id}>
                  <td>{sub.name}</td>
                  <td>{new Date(sub.created_at).toLocaleString()}</td>
                  <td>
                    <a
                      href={`/target/${targetId}/subdomain/${sub.id}`}
                      className="btn btn-ghost btn-sm"
                      style={{ textDecoration: "none" }}
                    >
                      Detail
                    </a>
                  </td>
                  <td>{sub.id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state-message">No subdomains found.</div>
        )}
      </AssetCard>

      {/* IP 資產 */}
      <AssetCard title="IP Addresses" count={allIPs.length}>
        {allIPs.length > 0 ? (
          <table className="assets-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>IP ADDRESS</th>
              </tr>
            </thead>
            <tbody>
              {allIPs.map((ip: IP) => (
                <tr key={ip.id}>
                  <td>{ip.id}</td>
                  <td>
                    <a
                      href={`/target/${targetId}/ip/${ip.id}`}
                      className="asset-link ip-link"
                    >
                      {ip.ipv4 || ip.ipv6}
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state-message">No IP addresses found.</div>
        )}
      </AssetCard>

      {/* URL 資產 */}
      <AssetCard title="URLs Found" count={allURLs.length}>
        {allURLs.length > 0 ? (
          <table className="assets-table">
            <thead>
              <tr>
                <th>URL</th>
                <th>DETAILS</th>
              </tr>
            </thead>
            <tbody>
              {allURLs.map((url: UrlResult) => (
                <tr key={url.id}>
                  <td>
                    <a
                      href={url.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="asset-link url-link"
                    >
                      {url.url}
                    </a>
                  </td>
                  <td>
                    <a
                      href={`/target/${targetId}/seed/${seedData.id}/url/${url.id}`}
                      className="btn btn-ghost btn-sm"
                      style={{ textDecoration: "none" }}
                    >
                      Detail
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state-message">No URLs found.</div>
        )}
      </AssetCard>
    </div>
  );
}

export default SeedReconPage;
