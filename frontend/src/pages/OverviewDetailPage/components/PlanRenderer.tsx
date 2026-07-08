import { useState } from 'react';
import type { AttackPlanOut, ActionOut, ActionStatus, PlanStatus } from '../../../types/attackPlan';
import ActionDetail from './ActionDetail';

// ─── Color Mappings ─────────────────────────────────────────────────────────

const PLAN_STATUS_STYLE: Record<PlanStatus, React.CSSProperties> = {
  DRAFT:     { color: '#94a3b8', background: 'rgba(148,163,184,0.1)', border: '1px solid rgba(148,163,184,0.25)' },
  ACTIVE:    { color: '#00ff00', background: 'rgba(0,255,0,0.08)', border: '1px solid rgba(0,255,0,0.25)' },
  COMPLETED: { color: '#60a5fa', background: 'rgba(96,165,250,0.12)', border: '1px solid rgba(96,165,250,0.3)' },
  ABANDONED: { color: '#475569', background: 'rgba(71,85,105,0.1)', border: '1px solid rgba(71,85,105,0.25)' },
};

const ACTION_DOT_COLOR: Record<ActionStatus, string> = {
  PENDING:     '#64748b',
  IN_PROGRESS: '#3b82f6',
  COMPLETED:   '#00ff00',
  FAILED:      '#ef4444',
  SKIPPED:     '#f59e0b',
};

const ACTION_STATUS_STYLE: Record<ActionStatus, React.CSSProperties> = {
  PENDING:     { color: '#94a3b8', background: 'rgba(148,163,184,0.1)', border: '1px solid rgba(148,163,184,0.25)' },
  IN_PROGRESS: { color: '#60a5fa', background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.3)' },
  COMPLETED:   { color: '#00ff00', background: 'rgba(0,255,0,0.08)', border: '1px solid rgba(0,255,0,0.25)' },
  FAILED:      { color: '#ef4444', background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.35)' },
  SKIPPED:     { color: '#f59e0b', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)' },
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

function formatTimestamp(ts: string | null): string {
  if (!ts) return '—';
  try {
    return new Date(ts).toLocaleTimeString();
  } catch {
    return ts;
  }
}

// ─── Styles ─────────────────────────────────────────────────────────────────

const headerStyle: React.CSSProperties = {
  marginBottom: 20,
};

const objectiveStyle: React.CSSProperties = {
  fontSize: '1.05rem',
  fontWeight: 700,
  color: '#e2e8f0',
  lineHeight: 1.4,
};

const metaRowStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 10,
  marginTop: 8,
  flexWrap: 'wrap',
};

const actionCardStyle: React.CSSProperties = {
  background: 'rgba(255,255,255,0.02)',
  border: '1px solid rgba(255,255,255,0.06)',
  borderRadius: 8,
  overflow: 'hidden',
};

const actionHeaderStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: 10,
  padding: '10px 14px',
  background: 'rgba(0,0,0,0.25)',
  borderBottom: '1px solid rgba(255,255,255,0.05)',
  flexWrap: 'wrap',
};

const dotPulseStyle = (color: string, pulsing: boolean): React.CSSProperties => ({
  width: 8,
  height: 8,
  borderRadius: '50%',
  background: color,
  marginTop: 6,
  flexShrink: 0,
  animation: pulsing ? 'planDotPulse 1.5s ease-in-out infinite' : undefined,
});

// ─── Sub-components ─────────────────────────────────────────────────────────

interface ActionCardProps {
  action: ActionOut;
  expanded: boolean;
  onToggle: () => void;
}

function ActionCard({ action, expanded, onToggle }: ActionCardProps) {
  const dotColor = ACTION_DOT_COLOR[action.status];
  const isPulsing = action.status === 'IN_PROGRESS';

  // Parse purpose for display text
  const purposeText = action.purpose_text
    || (Object.keys(action.purpose).length > 0
      ? (action.purpose as Record<string, unknown>).description as string
        || (action.purpose as Record<string, unknown>).tool as string
        || JSON.stringify(action.purpose)
      : '(no purpose)');

  return (
    <div style={actionCardStyle}>
      {/* Collapsed header — always visible */}
      <button
        type="button"
        onClick={onToggle}
        style={{
          ...actionHeaderStyle,
          cursor: 'pointer',
          width: '100%',
          textAlign: 'left',
          background: expanded ? 'rgba(0,0,0,0.35)' : 'rgba(0,0,0,0.25)',
          border: 'none',
          color: 'inherit',
        }}
      >
        {/* Status dot */}
        <div style={dotPulseStyle(dotColor, isPulsing)} title={action.status} />

        {/* Order + purpose */}
        <span style={{ color: '#475569', fontSize: '0.7rem', fontFamily: "'JetBrains Mono', monospace", fontWeight: 700 }}>
          #{action.order}
        </span>
        <span style={{ color: '#e2e8f0', fontSize: '0.85rem', fontWeight: 600, flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {purposeText}
        </span>

        {/* Status pill */}
        <span style={{ ...pillBase, ...ACTION_STATUS_STYLE[action.status] }}>
          {action.status}
        </span>

        {/* Agent role badge */}
        {action.agent_role && (
          <span style={{ ...pillBase, color: '#8b5cf6', background: 'rgba(139,92,246,0.08)', border: '1px solid rgba(139,92,246,0.2)' }}>
            {action.agent_role}
          </span>
        )}

        {/* Asset badges */}
        {action.asset_links.length > 0 && (
          <span style={{ ...pillBase, color: '#a5f3fc', background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(165,243,252,0.2)' }}>
            {action.asset_links.length} asset{action.asset_links.length !== 1 ? 's' : ''}
          </span>
        )}

        {/* Vector count */}
        {action.attack_vectors.length > 0 && (
          <span style={{ ...pillBase, color: '#f472b6', background: 'rgba(244,114,182,0.08)', border: '1px solid rgba(244,114,182,0.2)' }}>
            {action.attack_vectors.length} vector{action.attack_vectors.length !== 1 ? 's' : ''}
          </span>
        )}

        {/* Timestamps */}
        <span style={{ color: '#475569', fontSize: '0.65rem', marginLeft: 'auto' }}>
          {formatTimestamp(action.created_at)}
          {action.completed_at && ` → ${formatTimestamp(action.completed_at)}`}
        </span>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div style={{ padding: '4px 14px 12px' }}>
          <ActionDetail action={action} />
        </div>
      )}
    </div>
  );
}

// ─── Main Component ─────────────────────────────────────────────────────────

interface PlanRendererProps {
  plan: AttackPlanOut;
}

/**
 * Read-only structured renderer for an AttackPlanOut.
 * Shows: header with objective + status, then a list of ActionCards
 * sorted by order.
 */
export default function PlanRenderer({ plan }: PlanRendererProps) {
  const [expandedActionId, setExpandedActionId] = useState<number | null>(null);

  const sortedActions = [...plan.actions].sort((a, b) => a.order - b.order);

  return (
    <div style={{ padding: 20, height: '100%', overflowY: 'auto' }}>
      {/* Inject keyframes for dot pulse */}
      <style>{`
        @keyframes planDotPulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.3); }
        }
      `}</style>

      {/* Header */}
      <div style={headerStyle}>
        <div style={objectiveStyle}>{plan.objective}</div>
        <div style={metaRowStyle}>
          <span style={{ ...pillBase, ...PLAN_STATUS_STYLE[plan.status] }}>
            {plan.status}
          </span>
          <span style={{ color: '#475569', fontSize: '0.7rem', fontFamily: "'JetBrains Mono', monospace" }}>
            PLAN #{plan.id}
          </span>
          {plan.thread_id && (
            <span style={{ color: '#475569', fontSize: '0.7rem' }}>
              thread #{plan.thread_id}
            </span>
          )}
          {plan.parent_plan_id && (
            <span style={{ color: '#475569', fontSize: '0.7rem' }}>
              parent #{plan.parent_plan_id}
            </span>
          )}
        </div>
        {/* Scope preview (if any keys) */}
        {Object.keys(plan.scope).length > 0 && (
          <div style={{ marginTop: 8, color: '#475569', fontSize: '0.72rem' }}>
            Scope: {Object.entries(plan.scope).map(([k, v]) => `${k}=${typeof v === 'string' ? v : JSON.stringify(v)}`).join(', ')}
          </div>
        )}
      </div>

      {/* Actions */}
      {sortedActions.length === 0 ? (
        <div style={{ color: '#64748b', fontSize: '0.85rem', padding: '24px 0', textAlign: 'center' }}>
          No actions in this plan yet.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {sortedActions.map((action) => (
            <ActionCard
              key={action.id}
              action={action}
              expanded={expandedActionId === action.id}
              onToggle={() => setExpandedActionId((cur) => (cur === action.id ? null : action.id))}
            />
          ))}
        </div>
      )}
    </div>
  );
}
