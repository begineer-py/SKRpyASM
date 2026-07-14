import { useNavigate } from 'react-router-dom';
import type { ActionOut, AssetVectorLinkOut, AssetLinkStatus } from '../../../types/attackPlan';
import AttackVectorDisplay from './AttackVectorDisplay';

// ─── Color Mappings ─────────────────────────────────────────────────────────

const ASSET_LINK_STATUS_STYLE: Record<AssetLinkStatus, React.CSSProperties> = {
  TARGETED:    { color: '#94a3b8', background: 'rgba(148,163,184,0.1)', border: '1px solid rgba(148,163,184,0.2)' },
  IN_PROGRESS: { color: '#60a5fa', background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.25)' },
  COMPLETED:   { color: '#00ff00', background: 'rgba(0,255,0,0.08)', border: '1px solid rgba(0,255,0,0.2)' },
  FAILED:      { color: '#ef4444', background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.25)' },
};

// ─── Helpers ────────────────────────────────────────────────────────────────

const pillBase: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  padding: '2px 8px',
  fontSize: '0.65rem',
  fontWeight: 700,
  letterSpacing: '0.08em',
  borderRadius: 3,
  whiteSpace: 'nowrap',
};

function assetIdForLink(link: AssetVectorLinkOut): number | null {
  switch (link.asset_type) {
    case 'IP': return link.ip_asset_id;
    case 'SUBDOMAIN': return link.subdomain_asset_id;
    case 'URL': return link.url_asset_id;
    case 'ENDPOINT': return link.endpoint_asset_id;
    case 'PORT': return link.port_asset_id;
    default: return null;
  }
}

function formatTimestamp(ts: string | null): string {
  if (!ts) return '—';
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return ts;
  }
}

function formatPurpose(purpose: Record<string, unknown>): string {
  if (Object.keys(purpose).length === 0) return '';
  return JSON.stringify(purpose, null, 2);
}

// ─── Styles ─────────────────────────────────────────────────────────────────

const panelClass = "flex flex-col gap-3 p-3.5 bg-white/[0.015] border border-white/[0.06] rounded-md mt-1.5";

const sectionLabelClass = "text-[0.65rem] font-bold tracking-[0.1em] text-[#64748b] uppercase mb-1";

const preClass = "m-0 p-2 px-3 bg-black/40 text-[#e2e8f0] rounded text-[0.72rem] font-mono overflow-auto max-h-[200px] whitespace-pre-wrap break-words leading-[1.5]";

const resultBoxClass = "p-2 px-3 bg-[rgba(15,23,42,0.6)] border border-border-subtle rounded text-[#cbd5e1] text-[0.78rem] leading-[1.5] whitespace-pre-wrap";

const timestampRowClass = "flex gap-4 text-[0.7rem] text-[#475569] flex-wrap";

// ─── Component ──────────────────────────────────────────────────────────────

interface ActionDetailProps {
  action: ActionOut;
  onExpand?: () => void;
}

/**
 * Expandable detail panel for a single Action.
 * Shows full purpose JSON, asset_links, attack_vectors, result_summary,
 * execution_graph_id link, and timestamps.
 */
export default function ActionDetail({ action }: ActionDetailProps) {
  const navigate = useNavigate();
  const purposeStr = formatPurpose(action.purpose);

  return (
    <div className={panelClass}>
      {/* Purpose JSON */}
      {purposeStr && (
        <div>
          <div className={sectionLabelClass}>PURPOSE</div>
          <pre className={preClass}>{purposeStr}</pre>
        </div>
      )}

      {/* Result summary */}
      {action.result_summary && (
        <div>
          <div className={sectionLabelClass}>RESULT</div>
          <div className={resultBoxClass}>{action.result_summary}</div>
        </div>
      )}

      {/* Asset links */}
      {action.asset_links.length > 0 && (
        <div>
          <div className={sectionLabelClass}>ASSET LINKS ({action.asset_links.length})</div>
          <div className="flex flex-col gap-1">
            {action.asset_links.map((link) => {
              const assetId = assetIdForLink(link);
              return (
                <div
                  key={link.id}
                  className="flex items-center gap-2 text-xs"
                >
                  <span style={{ ...pillBase, ...ASSET_LINK_STATUS_STYLE[link.status] }}>
                    {link.status}
                  </span>
                  <code className="text-[#a5f3fc] bg-black/40 px-1.5 py-px rounded text-[0.7rem]">
                    {link.asset_type}#{assetId ?? '?'}
                  </code>
                  {link.agent_role && (
                    <span style={{ ...pillBase, color: '#8b5cf6', background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.2)' }}>
                      {link.agent_role}
                    </span>
                  )}
                  {link.last_result && (
                    <span className="text-[#475569] text-[0.7rem] overflow-hidden text-ellipsis max-w-[200px] whitespace-nowrap">
                      {link.last_result}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Attack vectors */}
      {action.attack_vectors.length > 0 && (
        <div>
          <div className={sectionLabelClass}>ATTACK VECTORS ({action.attack_vectors.length})</div>
          <div className="flex flex-col gap-0.5">
            {action.attack_vectors.map((v) => (
              <AttackVectorDisplay key={v.id} vector={v} />
            ))}
          </div>
        </div>
      )}

      {/* Execution graph link */}
      {action.execution_graph_id && (
        <div className="flex items-center gap-2">
          <span className={sectionLabelClass}>EXECUTION GRAPH</span>
          <button
            type="button"
            onClick={() => navigate(`/execution-monitor?graph=${action.execution_graph_id}`)}
            className="bg-transparent border border-green/30 text-green py-0.5 px-2.5 rounded text-[0.65rem] font-bold tracking-[0.08em] cursor-pointer"
          >
            VIEW GRAPH #{action.execution_graph_id} ↗
          </button>
        </div>
      )}

      {/* Agent info */}
      {action.agent_role && (
        <div className="flex items-center gap-2">
          <span className={sectionLabelClass}>AGENT</span>
          <span style={{ ...pillBase, color: '#8b5cf6', background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.2)' }}>
            {action.agent_role}
          </span>
          {action.agent_thread_id && (
            <code className="text-[#94a3b8] text-[0.7rem]">
              thread #{action.agent_thread_id}
            </code>
          )}
        </div>
      )}

      {/* Timestamps */}
      <div className={timestampRowClass}>
        <span>Created: {formatTimestamp(action.created_at)}</span>
        {action.started_at && <span>Started: {formatTimestamp(action.started_at)}</span>}
        {action.completed_at && <span>Completed: {formatTimestamp(action.completed_at)}</span>}
      </div>
    </div>
  );
}
