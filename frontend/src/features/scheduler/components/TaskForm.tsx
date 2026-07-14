import { useState, useEffect } from 'react';
import { GLOBAL_CONFIG } from '../../../config';
import type { RegisteredTask } from '../services/schedulerApi';

export const PERIOD_OPTIONS = ['seconds', 'minutes', 'hours', 'days'] as const;
export type Period = typeof PERIOD_OPTIONS[number];

export interface TaskRequirements {
  task: string;
  requires_api: boolean;
  agent_id: string | null;
  provider: string | null;
  has_key: boolean;
  description: string | null;
  missing_key_hint: string | null;
}

// ─── form state (used for both create and edit) ───────────────

export interface FormState {
  name: string;
  task: string;
  description: string;
  enabled: boolean;
  scheduleType: 'interval' | 'crontab';
  intervalEvery: number;
  intervalPeriod: Period;
  crontabMinute: string;
  crontabHour: string;
  crontabDow: string;
  crontabDom: string;
  crontabMoy: string;
  args: string;
  kwargs: string;
}

export const DEFAULT_FORM: FormState = {
  name: '',
  task: '',
  description: '',
  enabled: true,
  scheduleType: 'interval',
  intervalEvery: 5,
  intervalPeriod: 'minutes',
  crontabMinute: '*',
  crontabHour: '*',
  crontabDow: '*',
  crontabDom: '*',
  crontabMoy: '*',
  args: '[]',
  kwargs: '{}',
};

export function taskToForm(t: { name: string; task: string; description: string; enabled: boolean; crontab?: { minute: string; hour: string; day_of_week: string; day_of_month: string; month_of_year: string } | null; interval?: { every: number; period: string } | null; args: string; kwargs: string }): FormState {
  return {
    name: t.name,
    task: t.task,
    description: t.description,
    enabled: t.enabled,
    scheduleType: t.crontab ? 'crontab' : 'interval',
    intervalEvery: t.interval?.every ?? 5,
    intervalPeriod: (t.interval?.period as Period) ?? 'minutes',
    crontabMinute: t.crontab?.minute ?? '*',
    crontabHour: t.crontab?.hour ?? '*',
    crontabDow: t.crontab?.day_of_week ?? '*',
    crontabDom: t.crontab?.day_of_month ?? '*',
    crontabMoy: t.crontab?.month_of_year ?? '*',
    args: t.args || '[]',
    kwargs: t.kwargs || '{}',
  };
}

const labelClass = 'block text-[0.68rem] text-text-muted uppercase tracking-[0.05em] mb-1';

// ─── TaskForm ──────────────────────────────────────────────────

interface TaskFormProps {
  mode: 'create' | 'edit';
  initial: FormState;
  saving: boolean;
  registeredTasks: RegisteredTask[];
  onSubmit: (f: FormState) => void;
  onCancel: () => void;
}

export function TaskForm({ mode, initial, saving, registeredTasks, onSubmit, onCancel }: TaskFormProps) {
  const [f, setF] = useState<FormState>(initial);
  const [taskReq, setTaskReq] = useState<TaskRequirements | null>(null);

  const set = <K extends keyof FormState>(key: K, val: FormState[K]) =>
    setF(prev => ({ ...prev, [key]: val }));

  // Debounced query for AI API key requirements
  useEffect(() => {
    if (!f.task) { setTaskReq(null); return; }
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(
          `${GLOBAL_CONFIG.DJANGO_API_BASE}/scheduler/task-requirements?task=${encodeURIComponent(f.task)}`
        );
        if (res.ok) setTaskReq(await res.json());
      } catch { setTaskReq(null); }
    }, 400);
    return () => clearTimeout(timer);
  }, [f.task]);

  const hasApiBlock = taskReq?.requires_api === true && taskReq?.has_key === false;

  return (
    <div className="c2-card p-[16px_18px] mb-4">
      <div className="font-mono text-[0.75rem] text-green mb-[14px] uppercase tracking-[0.06em]">
        {mode === 'create' ? '+ New Task' : `Edit: ${initial.name}`}
      </div>

      <div className="grid grid-cols-2 gap-2.5 mb-2.5">
        <div>
          <label className={labelClass}>Task Name *</label>
          <input
            className="c2-input w-full"
            placeholder="my_task_name"
            value={f.name}
            onChange={e => set('name', e.target.value)}
          />
        </div>
        <div>
          <label className={labelClass}>Task Path *</label>
          <input
            className="c2-input w-full font-mono text-[0.8rem]"
            list="registered-tasks-list"
            placeholder="apps.auto.tasks.my_task"
            value={f.task}
            onChange={e => set('task', e.target.value)}
          />
          {registeredTasks.length > 0 && (
            <datalist id="registered-tasks-list">
              {registeredTasks.map(t => (
                <option key={t.name} value={t.name} label={t.doc ?? undefined} />
              ))}
            </datalist>
          )}
          {taskReq?.requires_api && (
            <div
              className="mt-1.5 p-[6px_10px] rounded text-[0.72rem] font-mono leading-[1.5]"
              style={{
                background: taskReq.has_key ? 'rgba(20, 83, 45, 0.5)' : 'rgba(69, 10, 10, 0.5)',
                color: taskReq.has_key ? '#86efac' : '#fca5a5',
                border: `1px solid ${taskReq.has_key ? '#166534' : '#7f1d1d'}`,
              }}
            >
              {taskReq.has_key
                ? `✓ API 密鑰已配置（${taskReq.agent_id || taskReq.provider}）`
                : `⚠ ${taskReq.description} — 請至 /agent-config 或 /api-keys 配置後再創建`}
            </div>
          )}
        </div>
      </div>

      <div className="mb-2.5">
        <label className={labelClass}>Description</label>
        <input
          className="c2-input w-full"
          placeholder="Optional description"
          value={f.description}
          onChange={e => set('description', e.target.value)}
        />
      </div>

      {/* Schedule type toggle */}
      <div className="mb-2.5">
        <label className={labelClass}>Schedule Type</label>
        <div className="flex gap-2">
          <button
            type="button"
            className={`c2-btn c2-btn--sm${f.scheduleType === 'interval' ? ' c2-btn--active' : ''}`}
            style={{ opacity: f.scheduleType === 'interval' ? 1 : 0.5 }}
            onClick={() => set('scheduleType', 'interval')}
          >
            Interval
          </button>
          <button
            type="button"
            className={`c2-btn c2-btn--sm${f.scheduleType === 'crontab' ? ' c2-btn--active' : ''}`}
            style={{ opacity: f.scheduleType === 'crontab' ? 1 : 0.5, ...(mode === 'create' ? { cursor: 'not-allowed' } : {}) }}
            onClick={() => mode === 'edit' && set('scheduleType', 'crontab')}
            title={mode === 'create' ? 'Crontab only available when editing an existing task' : undefined}
          >
            Crontab{mode === 'create' ? ' (edit only)' : ''}
          </button>
        </div>
      </div>

      {/* Interval fields */}
      {f.scheduleType === 'interval' && (
        <div className="flex gap-2.5 mb-2.5 items-end">
          <div className="flex-1">
            <label className={labelClass}>Every</label>
            <input
              className="c2-input w-full"
              type="number"
              min={1}
              value={f.intervalEvery}
              onChange={e => set('intervalEvery', Math.max(1, parseInt(e.target.value) || 1))}
            />
          </div>
          <div className="flex-1">
            <label className={labelClass}>Period</label>
            <select
              className="c2-input w-full"
              value={f.intervalPeriod}
              onChange={e => set('intervalPeriod', e.target.value as Period)}
            >
              {PERIOD_OPTIONS.map(p => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Crontab fields */}
      {f.scheduleType === 'crontab' && (
        <div className="grid grid-cols-5 gap-2 mb-2.5">
          {([
            { key: 'crontabMinute' as const, label: 'Minute' },
            { key: 'crontabHour' as const, label: 'Hour' },
            { key: 'crontabDom' as const, label: 'Day/Month' },
            { key: 'crontabMoy' as const, label: 'Month' },
            { key: 'crontabDow' as const, label: 'Day/Week' },
          ]).map(({ key, label }) => (
            <div key={key}>
              <label className={labelClass}>{label}</label>
              <input
                className="c2-input w-full font-mono"
                value={f[key]}
                onChange={e => set(key, e.target.value)}
              />
            </div>
          ))}
        </div>
      )}

      {/* Args / Kwargs */}
      <div className="grid grid-cols-2 gap-2.5 mb-3">
        <div>
          <label className={labelClass}>Args (JSON)</label>
          <input
            className="c2-input w-full font-mono text-[0.78rem]"
            value={f.args}
            onChange={e => set('args', e.target.value)}
          />
        </div>
        <div>
          <label className={labelClass}>Kwargs (JSON)</label>
          <input
            className="c2-input w-full font-mono text-[0.78rem]"
            value={f.kwargs}
            onChange={e => set('kwargs', e.target.value)}
          />
        </div>
      </div>

      {/* Enabled + submit row */}
      <div className="flex items-center gap-3">
        <label className="flex items-center gap-1.5 text-[0.8rem] text-text-secondary cursor-pointer">
          <input
            type="checkbox"
            checked={f.enabled}
            onChange={e => set('enabled', e.target.checked)}
          />
          Enabled
        </label>
        <div className="ml-auto flex gap-2">
          <button className="c2-btn c2-btn--sm opacity-60" onClick={onCancel}>
            Cancel
          </button>
          <button
            className="c2-btn"
            onClick={() => onSubmit(f)}
            disabled={saving || !f.name.trim() || !f.task.trim() || hasApiBlock}
            title={hasApiBlock ? '請先配置所需的 AI API 密鑰' : undefined}
          >
            {saving ? 'SAVING…' : mode === 'create' ? 'CREATE' : 'SAVE'}
          </button>
        </div>
      </div>
    </div>
  );
}
