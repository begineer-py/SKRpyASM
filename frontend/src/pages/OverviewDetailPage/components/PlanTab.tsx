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
      <div className="flex flex-col items-center justify-center min-h-[180px] text-[#64748b]">
        <span className="text-[#60a5fa]">Loading attack plans...</span>
      </div>
    );
  }

  // ─── Render: Error ────────────────────────────────────────────────────────

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[180px] text-[#ef4444]">
        <div className="mb-2">Failed to load attack plans</div>
        <div className="text-[0.75rem] text-[#94a3b8]">{error}</div>
      </div>
    );
  }

  // ─── Render: Empty ────────────────────────────────────────────────────────

  if (plans.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[180px] text-[#64748b]">
        <div className="text-[0.85rem] text-[#64748b] mb-1">No attack plans for this target.</div>
        <div className="text-[0.72rem] text-[#475569]">
          Plans are created by the AI agent during reconnaissance and analysis.
        </div>
      </div>
    );
  }

  // ─── Toggle buttons ───────────────────────────────────────────────────────

  const renderToggle = (): React.ReactNode => (
    <div className="flex gap-1 p-1 bg-[rgba(0,0,0,0.3)] rounded border border-[rgba(255,255,255,0.05)]">
      <button
        type="button"
        onClick={() => setViewMode('visual')}
        className="border-none px-2.5 py-1 rounded-[3px] text-[0.65rem] font-bold tracking-[0.08em] cursor-pointer"
        style={{
          background: viewMode === 'visual' ? 'rgba(0,255,0,0.1)' : 'transparent',
          color: viewMode === 'visual' ? '#00ff00' : '#64748b',
        }}
      >
        VISUAL
      </button>
      <button
        type="button"
        onClick={() => setViewMode('json')}
        className="border-none px-2.5 py-1 rounded-[3px] text-[0.65rem] font-bold tracking-[0.08em] cursor-pointer"
        style={{
          background: viewMode === 'json' ? 'rgba(0,255,0,0.1)' : 'transparent',
          color: viewMode === 'json' ? '#00ff00' : '#64748b',
        }}
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
        className="bg-[rgba(0,0,0,0.3)] border border-[rgba(255,255,255,0.1)] text-[#e2e8f0] px-2 py-1 rounded text-[0.72rem] font-semibold cursor-pointer outline-none"
      >
        {plans.map((p) => (
          <option key={p.id} value={p.id}>
            #{p.id} — {p.status} — {p.objective.slice(0, 60)}{p.objective.length > 60 ? '\u2026' : ''}
          </option>
        ))}
      </select>
    );
  };

  // ─── Toolbar ──────────────────────────────────────────────────────────────

  const renderToolbar = (): React.ReactNode => (
    <div className="flex justify-end items-center gap-2 px-3 py-1.5 border-b border-[rgba(255,255,255,0.05)]">
      {renderPlanSelector()}
      {renderToggle()}
    </div>
  );

  // ─── Visual mode ──────────────────────────────────────────────────────────

  if (viewMode === 'visual') {
    return (
      <div className="h-full flex flex-col">
        {renderToolbar()}
        <div className="flex-1 overflow-hidden">
          {detailLoading && !selectedPlan ? (
            <div className="flex flex-col items-center justify-center min-h-[180px] text-[#64748b]">
              <span className="text-[#60a5fa]">Loading plan details...</span>
            </div>
          ) : selectedPlan ? (
            <PlanRenderer plan={selectedPlan} />
          ) : (
            <div className="flex flex-col items-center justify-center min-h-[180px] text-[#64748b]">
              <span className="text-[#475569]">No plan selected.</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ─── JSON mode ────────────────────────────────────────────────────────────

  return (
    <div className="h-full flex flex-col">
      {renderToolbar()}
      <div className="flex-1 overflow-hidden">
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
