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
      <div style={{ padding: 20, color: 'var(--text-muted)', textAlign: 'center' }}>
        Loading CVE report...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 20 }}>
        <div style={{ color: 'var(--red)', marginBottom: 12 }}>Error: {error}</div>
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h3 style={{ fontFamily: 'var(--font-mono)', fontSize: '1rem', color: 'var(--text-green)' }}>
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
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 12, marginBottom: 20 }}>
        <div className="c2-stat">
          <div className="c2-stat__value">{report.total_cves}</div>
          <div className="c2-stat__label">Total CVEs</div>
        </div>
        <div className="c2-stat">
          <div className="c2-stat__value" style={{ color: 'var(--red)' }}>{report.critical_count}</div>
          <div className="c2-stat__label">Critical</div>
        </div>
        <div className="c2-stat">
          <div className="c2-stat__value" style={{ color: 'var(--amber)' }}>{report.high_count}</div>
          <div className="c2-stat__label">High</div>
        </div>
        <div className="c2-stat">
          <div className="c2-stat__value" style={{ color: 'var(--red)' }}>{report.kev_count}</div>
          <div className="c2-stat__label">CISA KEV</div>
        </div>
      </div>

      {/* Top CVEs */}
      {report.top_cves.length === 0 ? (
        <div className="c2-card" style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>
          No CVEs found for this target's tech stack.
          <br />
          <small>Run technology detection scans first.</small>
        </div>
      ) : (
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 12 }}>
            TOP HIGH-RISK CVEs:
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {report.top_cves.map((mapping, idx) => (
              <div
                key={idx}
                className="c2-card"
                style={{ padding: 12 }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-cyan)' }}>
                        {mapping.cve_id}
                      </span>
                      <CVESeverityBadge
                        severity={mapping.severity as 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'}
                        cisaKev={mapping.cisa_kev}
                        exploitAvailable={mapping.exploit_available}
                      />
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      Tech: <strong>{mapping.techstack_name}</strong> {mapping.techstack_version || ''}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    {mapping.cvss_score && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        CVSS: <strong style={{ color: 'var(--text-primary)' }}>{mapping.cvss_score.toFixed(1)}</strong>
                      </div>
                    )}
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
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
