import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import { executionApi, type AssetPentestRecords, type TopologyNode } from '../services/executionApi';

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
    <aside
      className="bg-[#0f172a] border border-[#1e293b] rounded-[10px] p-3 flex flex-col gap-2.5 max-h-[480px] overflow-auto"
      data-testid="asset-detail-panel"
    >
      <div className="flex justify-between items-start gap-2">
        <div>
          <div className="text-[0.65rem] uppercase tracking-[0.06em] text-[#a78bfa]">{node.type}</div>
          <h3 className="mt-0.5 text-[0.9rem] text-[#f1f5f9] break-all">{node.label}</h3>
        </div>
        {onClose && (
          <button type="button" className="bg-transparent border-none text-[#64748b] cursor-pointer text-[0.9rem]" onClick={onClose}>
            ✕
          </button>
        )}
      </div>

      {node.is_active_attack && (
        <div className="bg-[rgba(244,114,182,0.12)] border border-[rgba(244,114,182,0.4)] text-[#f9a8d4] rounded-lg px-2.5 py-1.5 text-[0.72rem]">
          🤖 AI is currently attacking this asset
        </div>
      )}

      {loading && <div className="text-[0.72rem] text-[#64748b]">Loading pentest records…</div>}
      {error && <div className="text-[0.72rem] text-[#f87171]">{error}</div>}

      {data && (
        <>
          <section className="[&_h4]:mb-1.5 [&_h4]:text-[0.72rem] [&_h4]:text-[#94a3b8] [&_h4]:uppercase [&_h4]:tracking-[0.04em]">
            <h4>滲透記錄 ({data.records.length})</h4>
            {data.records.length === 0 && <div className="text-[0.72rem] text-[#64748b]">No actions linked</div>}
            {data.records.map((r) => {
              const s = r.status.toLowerCase();
              const statusCls =
                s.includes('completed') || s.includes('succeeded') ? 'text-[#4ade80]' :
                s.includes('failed') ? 'text-[#f87171]' :
                s.includes('in_progress') || s === 'running' ? 'text-[#38bdf8]' :
                '';
              return (
                <div key={r.action_id} className="bg-[#0b1220] border border-[#1e293b] rounded-lg p-2 mb-1.5">
                  <div className="flex justify-between text-[0.72rem] text-[#cbd5e1] mb-1">
                    <span>Action #{r.action_id}</span>
                    <span className={cn('text-[0.65rem] px-1.5 py-px rounded-full bg-[#1e293b] text-[#94a3b8]', statusCls)}>
                      {r.status}
                    </span>
                  </div>
                  <div className="text-[0.75rem] text-[#e2e8f0] whitespace-pre-wrap break-words">
                    {r.purpose_text || r.purpose || '(no purpose)'}
                  </div>
                  {r.result_summary && (
                    <div className="mt-1 text-[0.7rem] text-[#86efac]">{r.result_summary.slice(0, 240)}</div>
                  )}
                  {r.execution_graph_id && onOpenGraph && (
                    <button
                      type="button"
                      className="mt-1.5 bg-[#1e293b] border border-[#334155] text-[#cbd5e1] rounded-md px-2 py-0.5 text-[0.68rem] cursor-pointer"
                      onClick={() => onOpenGraph(r.execution_graph_id!)}
                    >
                      Graph #{r.execution_graph_id}
                    </button>
                  )}
                </div>
              );
            })}
          </section>

          <section className="[&_h4]:mb-1.5 [&_h4]:text-[0.72rem] [&_h4]:text-[#94a3b8] [&_h4]:uppercase [&_h4]:tracking-[0.04em]">
            <h4>漏洞 ({data.vulnerabilities.length})</h4>
            {data.vulnerabilities.length === 0 && <div className="text-[0.72rem] text-[#64748b]">None</div>}
            {data.vulnerabilities.map((v) => (
              <div key={String(v.id)} className="inline-block bg-[#1e293b] border border-[#334155] rounded-md px-2 py-0.5 mr-1.5 mb-1.5 text-[0.7rem] text-[#e2e8f0]">
                #{String(v.id)} {String(v.name || '')}{' '}
                {v.severity ? `[${String(v.severity)}]` : ''}
              </div>
            ))}
          </section>

          <section className="[&_h4]:mb-1.5 [&_h4]:text-[0.72rem] [&_h4]:text-[#94a3b8] [&_h4]:uppercase [&_h4]:tracking-[0.04em]">
            <h4>CVE ({data.cves.length})</h4>
            {data.cves.length === 0 && <div className="text-[0.72rem] text-[#64748b]">None</div>}
            {data.cves.map((c) => (
              <div key={String(c.id)} className="inline-block bg-[#1e293b] border border-[#7f1d1d] rounded-md px-2 py-0.5 mr-1.5 mb-1.5 text-[0.7rem] text-[#fca5a5]">
                {String(c.cve_id || c.id)}
                {c.cvss_score != null ? ` · CVSS ${String(c.cvss_score)}` : ''}
              </div>
            ))}
          </section>
        </>
      )}

      {(node.type === 'target' || node.type === 'seed') && (
        <div className="text-[0.72rem] text-[#64748b]">Select a concrete asset (subdomain/IP/URL/…) for pentest records.</div>
      )}
    </aside>
  );
}

export default AssetDetailPanel;
