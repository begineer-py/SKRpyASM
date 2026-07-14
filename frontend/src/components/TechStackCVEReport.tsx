import { useState, useEffect, useCallback } from 'react';
import { CVEService, type TechStackCVEReport } from '../services/api_cve';
import CVESeverityBadge from './CVESeverityBadge';

interface TechStackCVEReportProps {
  targetId: number;
}

export default function TechStackCVEReport({ targetId }: TechStackCVEReportProps) {
  const [report, setReport] = useState<TechStackCVEReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

  const fetchReport = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await CVEService.getTechStackReport(targetId);
      setReport(data);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to load CVE report';
      const axiosError = e as { response?: { data?: { message?: string } } };
      setError(axiosError.response?.data?.message || msg);
    } finally {
      setLoading(false);
    }
  }, [targetId]);

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await CVEService.syncTechStack(targetId);
      alert('CVE sync task dispatched. Refresh in a few moments.');
      setTimeout(fetchReport, 3000);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Sync failed';
      alert(`Sync failed: ${msg}`);
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="p-5 text-text-muted text-center">
        Loading CVE report...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-5">
        <div className="text-red mb-3">Error: {error}</div>
        <button className="c2-btn c2-btn--sm" onClick={fetchReport}>
          Retry
        </button>
      </div>
    );
  }

  if (!report) return null;

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-5">
        <h3 className="font-mono text-base text-green">
          TECHSTACK CVE REPORT
        </h3>
        <button
          className="c2-btn c2-btn--sm"
          onClick={handleSync}
          disabled={syncing}
        >
          {syncing ? 'SYNCING...' : '🔄 SYNC CVEs'}
        </button>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-[repeat(auto-fit,minmax(120px,1fr))] gap-3 mb-5">
        <div className="c2-stat">
          <div className="c2-stat__value">{report.total_cves}</div>
          <div className="c2-stat__label">Total CVEs</div>
        </div>
        <div className="c2-stat">
          <div className="c2-stat__value text-red">{report.critical_count}</div>
          <div className="c2-stat__label">Critical</div>
        </div>
        <div className="c2-stat">
          <div className="c2-stat__value text-amber">{report.high_count}</div>
          <div className="c2-stat__label">High</div>
        </div>
        <div className="c2-stat">
          <div className="c2-stat__value text-red">{report.kev_count}</div>
          <div className="c2-stat__label">CISA KEV</div>
        </div>
      </div>

      {/* Top CVEs */}
      {report.top_cves.length === 0 ? (
        <div className="c2-card p-5 text-center text-text-muted">
          No CVEs found for this target's tech stack.
          <br />
          <small>Run technology detection scans first.</small>
        </div>
      ) : (
        <div>
          <div className="text-xs text-text-muted mb-3">
            TOP HIGH-RISK CVEs:
          </div>
          <div className="flex flex-col gap-2">
            {report.top_cves.map((mapping, idx) => (
              <div
                key={idx}
                className="c2-card p-3"
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <div className="flex gap-2 items-center mb-1">
                      <span className="font-mono text-[0.85rem] font-semibold text-text-cyan">
                        {mapping.cve_id}
                      </span>
                      <CVESeverityBadge
                        severity={mapping.severity as 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'}
                        cisaKev={mapping.cisa_kev}
                        exploitAvailable={mapping.exploit_available}
                      />
                    </div>
                    <div className="text-xs text-text-secondary">
                      Tech: <strong>{mapping.techstack_name}</strong> {mapping.techstack_version || ''}
                    </div>
                  </div>
                  <div className="text-right">
                    {mapping.cvss_score && (
                      <div className="text-xs text-text-muted">
                        CVSS: <strong className="text-text-primary">{mapping.cvss_score.toFixed(1)}</strong>
                      </div>
                    )}
                    <div className="text-[0.7rem] text-text-muted">
                      Match: {(mapping.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
