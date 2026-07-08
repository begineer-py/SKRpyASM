import { useEffect, useMemo, useState } from 'react';
import { AttackPlanService } from '../../../services/attackPlanService';
import type { AttackPlanOut } from '../../../types/attackPlan';
import JsonMonacoEditor from './JsonMonacoEditor';
import PlanRenderer from './PlanRenderer';

// ─── Props ──────────────────────────────────────────────────────────────────

interface PlanTabProps {
  /** Target ID — used to fetch associated attack plans from REST API. */
  targetId: number;
}

type ViewMode = 'visual' | 'json';

/**
 * PlanTab — consumes the new AttackPlan REST API.
 *
 * Loads plans from `GET /api/core/attack-plans?target_id=X`, shows the
 * ACTIVE plan (or most recent DRAFT), and provides a plan selector dropdown
 * when multiple plans exist.
 */
export default function PlanTab({ targetId }: PlanTabProps) {
  const [plans, setPlans] = useState<AttackPlanOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('visual');

  // ─── Fetch plans on mount / targetId change ────────────────────────────────

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setPlans([]);
    setSelectedPlanId(null);

    AttackPlanService.listPlans(targetId)
      .then((res) => {
        if (cancelled) return;
        const items = Array.isArray(res.items) ? res.items : [];
        setPlans(items);
        // Auto-select: ACTIVE first, else most recent DRAFT, else first
        const active = items.find((p) => p.status === 'ACTIVE');
        const draft = items.find((p) => p.status === 'DRAFT');
        setSelectedPlanId(active?.id ?? draft?.id ?? (items.length > 0 ? items[0].id : null));
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load attack plans');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [targetId]);

  // ─── Enrich selected plan with full detail (nested actions) ────────────────

  const [detailPlan, setDetailPlan] = useState<AttackPlanOut | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    if (!selectedPlanId) { setDetailPlan(null); return; }
    let cancelled = false;
    setDetailLoading(true);

    AttackPlanService.getPlan(selectedPlanId)
      .then((plan) => {
        if (!cancelled) setDetailPlan(plan);
      })
      .catch(() => {
        // Fallback to the list-view plan data
        if (!cancelled) {
          const fallback = plans.find((p) => p.id === selectedPlanId) ?? null;
          setDetailPlan(fallback);
        }
      })
      .finally(() => {
        if (!cancelled) setDetailLoading(false);
      });

    return () => { cancelled = true; };
  }, [selectedPlanId, plans]);

  const selectedPlan = detailPlan;

  // ─── JSON fallback value for Raw JSON mode ─────────────────────────────────

  const jsonStr = useMemo(
    () => (selectedPlan ? JSON.stringify(selectedPlan, null, 2) : ''),
    [selectedPlan],
  );

  // ─── Render: Loading ──────────────────────────────────────────────────────

  if (loading) {
    return (
      <div style={emptyStyle}>
        <span style={{ color: '#60a5fa' }}>Loading attack plans...</span>
      </div>
    );
  }

  // ─── Render: Error ────────────────────────────────────────────────────────

  if (error) {
    return (
      <div style={{ ...emptyStyle, color: '#ef4444' }}>
        <div style={{ marginBottom: 8 }}>Failed to load attack plans</div>
        <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{error}</div>
      </div>
    );
  }

  // ─── Render: Empty ────────────────────────────────────────────────────────

  if (plans.length === 0) {
    return (
      <div style={emptyStyle}>
        <div style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: 4 }}>No attack plans for this target.</div>
        <div style={{ fontSize: '0.72rem', color: '#475569' }}>
          Plans are created by the AI agent during reconnaissance and analysis.
        </div>
      </div>
    );
  }

  // ─── Toggle buttons ───────────────────────────────────────────────────────

  const renderToggle = (): React.ReactNode => (
    <div
      style={{
        display: 'flex',
        gap: 4,
        padding: 4,
        background: 'rgba(0,0,0,0.3)',
        borderRadius: 4,
        border: '1px solid rgba(255,255,255,0.05)',
      }}
    >
      <button
        type="button"
        onClick={() => setViewMode('visual')}
        style={toggleBtnStyle(viewMode === 'visual')}
      >
        VISUAL
      </button>
      <button
        type="button"
        onClick={() => setViewMode('json')}
        style={toggleBtnStyle(viewMode === 'json')}
      >
        JSON
      </button>
    </div>
  );

  // ─── Plan selector dropdown (if multiple plans) ───────────────────────────

  const renderPlanSelector = (): React.ReactNode => {
    if (plans.length <= 1) return null;
    return (
      <select
        value={selectedPlanId ?? ''}
        onChange={(e) => {
          const val = parseInt(e.target.value, 10);
          setSelectedPlanId(isNaN(val) ? null : val);
          setViewMode('visual');
        }}
        style={{
          background: 'rgba(0,0,0,0.3)',
          border: '1px solid rgba(255,255,255,0.1)',
          color: '#e2e8f0',
          padding: '4px 8px',
          borderRadius: 4,
          fontSize: '0.72rem',
          fontWeight: 600,
          cursor: 'pointer',
          outline: 'none',
        }}
      >
        {plans.map((p) => (
          <option key={p.id} value={p.id}>
            #{p.id} — {p.status} — {p.objective.slice(0, 60)}{p.objective.length > 60 ? '…' : ''}
          </option>
        ))}
      </select>
    );
  };

  // ─── Toolbar ──────────────────────────────────────────────────────────────

  const renderToolbar = (): React.ReactNode => (
    <div
      style={{
        display: 'flex',
        justifyContent: 'flex-end',
        alignItems: 'center',
        gap: 8,
        padding: '6px 12px',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
      }}
    >
      {renderPlanSelector()}
      {renderToggle()}
    </div>
  );

  // ─── Visual mode ──────────────────────────────────────────────────────────

  if (viewMode === 'visual') {
    return (
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        {renderToolbar()}
        <div style={{ flex: 1, overflow: 'hidden' }}>
          {detailLoading && !selectedPlan ? (
            <div style={emptyStyle}>
              <span style={{ color: '#60a5fa' }}>Loading plan details...</span>
            </div>
          ) : selectedPlan ? (
            <PlanRenderer plan={selectedPlan} />
          ) : (
            <div style={emptyStyle}>
              <span style={{ color: '#475569' }}>No plan selected.</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ─── JSON mode ────────────────────────────────────────────────────────────

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {renderToolbar()}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <JsonMonacoEditor
          value={jsonStr}
          onChange={() => { /* read-only — no-op */ }}
          placeholder='{ "objective": "..." }'
          readOnly
        />
      </div>
    </div>
  );
}

// ─── Styles ─────────────────────────────────────────────────────────────────

const emptyStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  minHeight: 180,
  color: '#64748b',
};

function toggleBtnStyle(active: boolean): React.CSSProperties {
  return {
    background: active ? 'rgba(0,255,0,0.1)' : 'transparent',
    border: 'none',
    color: active ? '#00ff00' : '#64748b',
    padding: '4px 10px',
    borderRadius: 3,
    fontSize: '0.65rem',
    fontWeight: 700,
    letterSpacing: '0.08em',
    cursor: 'pointer',
  };
}
