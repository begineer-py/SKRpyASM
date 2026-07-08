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

const panelStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: 12,
  padding: 14,
  background: 'rgba(255,255,255,0.015)',
  border: '1px solid rgba(255,255,255,0.06)',
  borderRadius: 6,
  marginTop: 6,
};

const sectionLabelStyle: React.CSSProperties = {
  fontSize: '0.65rem',
  fontWeight: 700,
  letterSpacing: '0.1em',
  color: '#64748b',
  textTransform: 'uppercase',
  marginBottom: 4,
};

const preStyle: React.CSSProperties = {
  margin: 0,
  padding: '8px 12px',
  background: 'rgba(0,0,0,0.4)',
  color: '#e2e8f0',
  borderRadius: 4,
  fontSize: '0.72rem',
  fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
  overflow: 'auto',
  maxHeight: 200,
  whiteSpace: 'pre-wrap',
  wordBreak: 'break-word',
  lineHeight: 1.5,
};

const resultBoxStyle: React.CSSProperties = {
  padding: '8px 12px',
  background: 'rgba(15,23,42,0.6)',
  border: '1px solid rgba(148,163,184,0.12)',
  borderRadius: 4,
  color: '#cbd5e1',
  fontSize: '0.78rem',
  lineHeight: 1.5,
  whiteSpace: 'pre-wrap',
};

const timestampRowStyle: React.CSSProperties = {
  display: 'flex',
  gap: 16,
  fontSize: '0.7rem',
  color: '#475569',
  flexWrap: 'wrap',
};

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
    <div style={panelStyle}>
      {/* Purpose JSON */}
      {purposeStr && (
        <div>
          <div style={sectionLabelStyle}>PURPOSE</div>
          <pre style={preStyle}>{purposeStr}</pre>
        </div>
      )}

      {/* Result summary */}
      {action.result_summary && (
        <div>
          <div style={sectionLabelStyle}>RESULT</div>
          <div style={resultBoxStyle}>{action.result_summary}</div>
        </div>
      )}

      {/* Asset links */}
      {action.asset_links.length > 0 && (
        <div>
          <div style={sectionLabelStyle}>ASSET LINKS ({action.asset_links.length})</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {action.asset_links.map((link) => {
              const assetId = assetIdForLink(link);
              return (
                <div
                  key={link.id}
                  style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.75rem' }}
                >
                  <span style={{ ...pillBase, ...ASSET_LINK_STATUS_STYLE[link.status] }}>
                    {link.status}
                  </span>
                  <code style={{ color: '#a5f3fc', background: 'rgba(0,0,0,0.4)', padding: '1px 6px', borderRadius: 3, fontSize: '0.7rem' }}>
                    {link.asset_type}#{assetId ?? '?'}
                  </code>
                  {link.agent_role && (
                    <span style={{ ...pillBase, color: '#8b5cf6', background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.2)' }}>
                      {link.agent_role}
                    </span>
                  )}
                  {link.last_result && (
                    <span style={{ color: '#475569', fontSize: '0.7rem', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 200, whiteSpace: 'nowrap' }}>
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
          <div style={sectionLabelStyle}>ATTACK VECTORS ({action.attack_vectors.length})</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {action.attack_vectors.map((v) => (
              <AttackVectorDisplay key={v.id} vector={v} />
            ))}
          </div>
        </div>
      )}

      {/* Execution graph link */}
      {action.execution_graph_id && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={sectionLabelStyle}>EXECUTION GRAPH</span>
          <button
            type="button"
            onClick={() => navigate(`/execution-monitor?graph=${action.execution_graph_id}`)}
            style={{
              background: 'transparent',
              border: '1px solid rgba(0,255,0,0.3)',
              color: '#00ff00',
              padding: '2px 10px',
              borderRadius: 3,
              fontSize: '0.65rem',
              fontWeight: 700,
              letterSpacing: '0.08em',
              cursor: 'pointer',
            }}
          >
            VIEW GRAPH #{action.execution_graph_id} ↗
          </button>
        </div>
      )}

      {/* Agent info */}
      {action.agent_role && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={sectionLabelStyle}>AGENT</span>
          <span style={{ ...pillBase, color: '#8b5cf6', background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.2)' }}>
            {action.agent_role}
          </span>
          {action.agent_thread_id && (
            <code style={{ color: '#94a3b8', fontSize: '0.7rem' }}>
              thread #{action.agent_thread_id}
            </code>
          )}
        </div>
      )}

      {/* Timestamps */}
      <div style={timestampRowStyle}>
        <span>Created: {formatTimestamp(action.created_at)}</span>
        {action.started_at && <span>Started: {formatTimestamp(action.started_at)}</span>}
        {action.completed_at && <span>Completed: {formatTimestamp(action.completed_at)}</span>}
      </div>
    </div>
  );
}
