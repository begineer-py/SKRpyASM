import { useEffect, useState } from 'react';
import { executionApi, type AssetPentestRecords, type TopologyNode } from '../services/executionApi';
import './AssetDetailPanel.css';

interface AssetDetailPanelProps {
  node: TopologyNode | null;
  onClose?: () => void;
  onOpenGraph?: (graphId: number) => void;
}

export function AssetDetailPanel({ node, onClose, onOpenGraph }: AssetDetailPanelProps) {
  const [data, setData] = useState<AssetPentestRecords | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!node || !node.asset_id || node.type === 'target' || node.type === 'seed') {
      setData(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    executionApi
      .getAssetPentestRecords(node.type, node.asset_id)
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setData(null);
          setError(err instanceof Error ? err.message : 'Failed to load');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [node]);

  if (!node) return null;

  return (
    <aside className="asset-detail-panel" data-testid="asset-detail-panel">
      <div className="adp-header">
        <div>
          <div className="adp-type">{node.type}</div>
          <h3 className="adp-title">{node.label}</h3>
        </div>
        {onClose && (
          <button type="button" className="adp-close" onClick={onClose}>
            ✕
          </button>
        )}
      </div>

      {node.is_active_attack && (
        <div className="adp-attack-banner">🤖 AI is currently attacking this asset</div>
      )}

      {loading && <div className="adp-muted">Loading pentest records…</div>}
      {error && <div className="adp-error">{error}</div>}

      {data && (
        <>
          <section className="adp-section">
            <h4>滲透記錄 ({data.records.length})</h4>
            {data.records.length === 0 && <div className="adp-muted">No actions linked</div>}
            {data.records.map((r) => (
              <div key={r.action_id} className="adp-record">
                <div className="adp-record-top">
                  <span>Action #{r.action_id}</span>
                  <span className={`adp-status adp-status--${r.status.toLowerCase()}`}>
                    {r.status}
                  </span>
                </div>
                <div className="adp-record-body">
                  {r.purpose_text || r.purpose || '(no purpose)'}
                </div>
                {r.result_summary && (
                  <div className="adp-record-summary">{r.result_summary.slice(0, 240)}</div>
                )}
                {r.execution_graph_id && onOpenGraph && (
                  <button
                    type="button"
                    className="adp-link-btn"
                    onClick={() => onOpenGraph(r.execution_graph_id!)}
                  >
                    Graph #{r.execution_graph_id}
                  </button>
                )}
              </div>
            ))}
          </section>

          <section className="adp-section">
            <h4>漏洞 ({data.vulnerabilities.length})</h4>
            {data.vulnerabilities.length === 0 && <div className="adp-muted">None</div>}
            {data.vulnerabilities.map((v) => (
              <div key={String(v.id)} className="adp-chip">
                #{String(v.id)} {String(v.name || '')}{' '}
                {v.severity ? `[${String(v.severity)}]` : ''}
              </div>
            ))}
          </section>

          <section className="adp-section">
            <h4>CVE ({data.cves.length})</h4>
            {data.cves.length === 0 && <div className="adp-muted">None</div>}
            {data.cves.map((c) => (
              <div key={String(c.id)} className="adp-chip adp-chip--cve">
                {String(c.cve_id || c.id)}
                {c.cvss_score != null ? ` · CVSS ${String(c.cvss_score)}` : ''}
              </div>
            ))}
          </section>
        </>
      )}

      {(node.type === 'target' || node.type === 'seed') && (
        <div className="adp-muted">Select a concrete asset (subdomain/IP/URL/…) for pentest records.</div>
      )}
    </aside>
  );
}

export default AssetDetailPanel;
