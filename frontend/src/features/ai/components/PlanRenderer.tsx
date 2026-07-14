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
  if (!ts) return '\u2014';
  try {
    return new Date(ts).toLocaleTimeString();
  } catch {
    return ts;
  }
}

// ─── Dynamic style helpers ─────────────────────────────────────────────────

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
    <div className="bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)] rounded-lg overflow-hidden">
      {/* Collapsed header \u2014 always visible */}
      <button
        type="button"
        onClick={onToggle}
        className="flex items-center gap-2.5 px-3.5 py-2.5 flex-wrap cursor-pointer w-full text-left border-none text-inherit"
        style={{
          background: expanded ? 'rgba(0,0,0,0.35)' : 'rgba(0,0,0,0.25)',
        }}
      >
        {/* Status dot */}
        <div style={dotPulseStyle(dotColor, isPulsing)} title={action.status} />

        {/* Order + purpose */}
        <span className="text-[#475569] text-[0.7rem] font-mono font-bold">
          #{action.order}
        </span>
        <span className="flex-1 min-w-0 truncate text-[#e2e8f0] text-[0.85rem] font-semibold">
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
        <span className="text-[#475569] text-[0.65rem] ml-auto">
          {formatTimestamp(action.created_at)}
          {action.completed_at && ` \u2192 ${formatTimestamp(action.completed_at)}`}
        </span>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-3.5 pb-3 pt-1">
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
    <div className="p-5 h-full overflow-y-auto">
      {/* Inject keyframes for dot pulse */}
      <style>{`
        @keyframes planDotPulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.3); }
        }
      `}</style>

      {/* Header */}
      <div className="mb-5">
        <div className="text-[1.05rem] font-bold text-[#e2e8f0] leading-[1.4]">{plan.objective}</div>
        <div className="flex items-center gap-2.5 mt-2 flex-wrap">
          <span style={{ ...pillBase, ...PLAN_STATUS_STYLE[plan.status] }}>
            {plan.status}
          </span>
          <span className="text-[#475569] text-[0.7rem] font-mono">
            PLAN #{plan.id}
          </span>
          {plan.thread_id && (
            <span className="text-[#475569] text-[0.7rem]">
              thread #{plan.thread_id}
            </span>
          )}
          {plan.parent_plan_id && (
            <span className="text-[#475569] text-[0.7rem]">
              parent #{plan.parent_plan_id}
            </span>
          )}
        </div>
        {/* Scope preview (if any keys) */}
        {Object.keys(plan.scope).length > 0 && (
          <div className="mt-2 text-[#475569] text-[0.72rem]">
            Scope: {Object.entries(plan.scope).map(([k, v]) => `${k}=${typeof v === 'string' ? v : JSON.stringify(v)}`).join(', ')}
          </div>
        )}
      </div>

      {/* Actions */}
      {sortedActions.length === 0 ? (
        <div className="text-[#64748b] text-[0.85rem] py-6 text-center">
          No actions in this plan yet.
        </div>
      ) : (
        <div className="flex flex-col gap-2.5">
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
