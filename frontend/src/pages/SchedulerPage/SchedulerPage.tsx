import { useState, useEffect, useCallback } from 'react';
import {
  SchedulerService,
  type PeriodicTask,
  type CreateTaskPayload,
  type UpdateTaskPayload,
  type RegisteredTask,
} from '../../services/api_scheduler';

// ─── helpers ──────────────────────────────────────────────────────────────────

function formatSchedule(task: PeriodicTask): string {
  if (task.interval) {
    const { every, period } = task.interval;
    return `every ${every} ${period}`;
  }
  if (task.crontab) {
    const { minute, hour, day_of_week, day_of_month, month_of_year } = task.crontab;
    return `${minute} ${hour} ${day_of_month} ${month_of_year} ${day_of_week}`;
  }
  return '—';
}

function formatTime(iso: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  const now = Date.now();
  const diffMs = now - d.getTime();
  const diffM = Math.floor(diffMs / 60000);
  if (diffM < 1) return 'just now';
  if (diffM < 60) return `${diffM}m ago`;
  const diffH = Math.floor(diffM / 60);
  if (diffH < 24) return `${diffH}h ago`;
  return d.toLocaleDateString();
}

const PERIOD_OPTIONS = ['seconds', 'minutes', 'hours', 'days'] as const;
type Period = typeof PERIOD_OPTIONS[number];

// ─── form state (used for both create and edit) ───────────────────────────────

interface FormState {
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

const DEFAULT_FORM: FormState = {
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

function taskToForm(t: PeriodicTask): FormState {
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

// ─── sub-components ───────────────────────────────────────────────────────────

interface TaskRowProps {
  task: PeriodicTask;
  toggling: boolean;
  deleting: boolean;
  onToggle: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

function TaskRow({ task, toggling, deleting, onToggle, onEdit, onDelete }: TaskRowProps) {
  const statusColor = task.enabled ? 'var(--text-green)' : 'var(--text-muted)';

  return (
    <div
      className="c2-card"
      style={{
        padding: '12px 16px',
        opacity: task.enabled ? 1 : 0.65,
        transition: 'opacity 0.2s',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        {/* Enabled toggle dot */}
        <button
          title={task.enabled ? 'Click to disable' : 'Click to enable'}
          onClick={onToggle}
          disabled={toggling}
          style={{
            background: 'none',
            border: 'none',
            cursor: toggling ? 'wait' : 'pointer',
            padding: '2px 0 0',
            flexShrink: 0,
          }}
        >
          <span style={{ fontSize: '0.9rem', color: statusColor }}>
            {toggling ? '…' : task.enabled ? '●' : '○'}
          </span>
        </button>

        {/* Main info */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.85rem',
              fontWeight: 700,
              color: 'var(--text-primary)',
            }}>
              {task.name}
            </span>
            {task.one_off && (
              <span className="c2-badge" style={{ fontSize: '0.65rem' }}>ONE-OFF</span>
            )}
          </div>

          <div style={{
            fontSize: '0.72rem',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
            marginTop: 2,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
            title={task.task}
          >
            {task.task}
          </div>

          {task.description && (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: 4 }}>
              {task.description}
            </div>
          )}

          {task.task_doc && !task.description && (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: 4 }}>
              {task.task_doc.split('\n')[0]}
            </div>
          )}
        </div>

        {/* Schedule + stats */}
        <div style={{
          display: 'flex',
          gap: 20,
          alignItems: 'center',
          flexShrink: 0,
          flexWrap: 'wrap',
          justifyContent: 'flex-end',
        }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              color: 'var(--text-cyan)',
            }}>
              {formatSchedule(task)}
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: 2 }}>
              Last: {formatTime(task.last_run_at)} · ×{task.total_run_count}
            </div>
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: 6 }}>
            <button
              className="c2-btn c2-btn--sm"
              onClick={onEdit}
              style={{ fontSize: '0.7rem' }}
            >
              Edit
            </button>
            <button
              className="c2-btn c2-btn--sm"
              onClick={onDelete}
              disabled={deleting}
              style={{
                fontSize: '0.7rem',
                color: 'var(--red)',
                borderColor: 'var(--red)',
              }}
            >
              {deleting ? '…' : 'Del'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── task form (create + edit) ─────────────────────────────────────────────────

interface TaskFormProps {
  mode: 'create' | 'edit';
  initial: FormState;
  saving: boolean;
  registeredTasks: RegisteredTask[];
  onSubmit: (f: FormState) => void;
  onCancel: () => void;
}

function TaskForm({ mode, initial, saving, registeredTasks, onSubmit, onCancel }: TaskFormProps) {
  const [f, setF] = useState<FormState>(initial);

  const set = <K extends keyof FormState>(key: K, val: FormState[K]) =>
    setF(prev => ({ ...prev, [key]: val }));

  return (
    <div className="c2-card" style={{ padding: '16px 18px', marginBottom: 16 }}>
      <div style={{
        fontFamily: 'var(--font-mono)',
        fontSize: '0.75rem',
        color: 'var(--text-green)',
        marginBottom: 14,
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
      }}>
        {mode === 'create' ? '+ New Task' : `Edit: ${initial.name}`}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
        <div>
          <label style={labelStyle}>Task Name *</label>
          <input
            className="c2-input"
            style={{ width: '100%' }}
            placeholder="my_task_name"
            value={f.name}
            onChange={e => set('name', e.target.value)}
          />
        </div>
        <div>
          <label style={labelStyle}>Task Path *</label>
          <input
            className="c2-input"
            list="registered-tasks-list"
            style={{ width: '100%', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}
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
        </div>
      </div>

      <div style={{ marginBottom: 10 }}>
        <label style={labelStyle}>Description</label>
        <input
          className="c2-input"
          style={{ width: '100%' }}
          placeholder="Optional description"
          value={f.description}
          onChange={e => set('description', e.target.value)}
        />
      </div>

      {/* Schedule type toggle */}
      <div style={{ marginBottom: 10 }}>
        <label style={labelStyle}>Schedule Type</label>
        <div style={{ display: 'flex', gap: 8 }}>
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
        <div style={{ display: 'flex', gap: 10, marginBottom: 10, alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <label style={labelStyle}>Every</label>
            <input
              className="c2-input"
              type="number"
              min={1}
              style={{ width: '100%' }}
              value={f.intervalEvery}
              onChange={e => set('intervalEvery', Math.max(1, parseInt(e.target.value) || 1))}
            />
          </div>
          <div style={{ flex: 1 }}>
            <label style={labelStyle}>Period</label>
            <select
              className="c2-input"
              style={{ width: '100%' }}
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
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8, marginBottom: 10 }}>
          {(
            [
              { key: 'crontabMinute' as const, label: 'Minute' },
              { key: 'crontabHour' as const, label: 'Hour' },
              { key: 'crontabDom' as const, label: 'Day/Month' },
              { key: 'crontabMoy' as const, label: 'Month' },
              { key: 'crontabDow' as const, label: 'Day/Week' },
            ] as const
          ).map(({ key, label }) => (
            <div key={key}>
              <label style={labelStyle}>{label}</label>
              <input
                className="c2-input"
                style={{ width: '100%', fontFamily: 'var(--font-mono)' }}
                value={f[key]}
                onChange={e => set(key, e.target.value)}
              />
            </div>
          ))}
        </div>
      )}

      {/* Args / Kwargs */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
        <div>
          <label style={labelStyle}>Args (JSON)</label>
          <input
            className="c2-input"
            style={{ width: '100%', fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}
            value={f.args}
            onChange={e => set('args', e.target.value)}
          />
        </div>
        <div>
          <label style={labelStyle}>Kwargs (JSON)</label>
          <input
            className="c2-input"
            style={{ width: '100%', fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}
            value={f.kwargs}
            onChange={e => set('kwargs', e.target.value)}
          />
        </div>
      </div>

      {/* Enabled + submit row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <label style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          fontSize: '0.8rem',
          color: 'var(--text-secondary)',
          cursor: 'pointer',
        }}>
          <input
            type="checkbox"
            checked={f.enabled}
            onChange={e => set('enabled', e.target.checked)}
          />
          Enabled
        </label>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <button className="c2-btn c2-btn--sm" onClick={onCancel} style={{ opacity: 0.6 }}>
            Cancel
          </button>
          <button
            className="c2-btn"
            onClick={() => onSubmit(f)}
            disabled={saving || !f.name.trim() || !f.task.trim()}
          >
            {saving ? 'SAVING…' : mode === 'create' ? 'CREATE' : 'SAVE'}
          </button>
        </div>
      </div>
    </div>
  );
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: '0.68rem',
  color: 'var(--text-muted)',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  marginBottom: 4,
};

// ─── delete confirmation inline ───────────────────────────────────────────────

interface DeleteConfirmProps {
  taskName: string;
  onConfirm: () => void;
  onCancel: () => void;
}

function DeleteConfirm({ taskName, onConfirm, onCancel }: DeleteConfirmProps) {
  return (
    <div style={{
      padding: '10px 14px',
      border: '1px solid var(--red)',
      borderRadius: 4,
      fontSize: '0.8rem',
      color: 'var(--text-secondary)',
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      marginBottom: 8,
    }}>
      <span>Delete <strong style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{taskName}</strong>?</span>
      <button className="c2-btn c2-btn--sm" onClick={onConfirm} style={{ color: 'var(--red)', borderColor: 'var(--red)', marginLeft: 'auto' }}>
        Confirm Delete
      </button>
      <button className="c2-btn c2-btn--sm" onClick={onCancel} style={{ opacity: 0.6 }}>
        Cancel
      </button>
    </div>
  );
}

// ─── page ──────────────────────────────────────────────────────────────────────

export default function SchedulerPage() {
  const [tasks, setTasks] = useState<PeriodicTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);
  const [registeredTasks, setRegisteredTasks] = useState<RegisteredTask[]>([]);

  const [formMode, setFormMode] = useState<'hidden' | 'create' | 'edit'>('hidden');
  const [editingTask, setEditingTask] = useState<PeriodicTask | null>(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [togglingId, setTogglingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  const loadTasks = useCallback(async () => {
    setLoading(true);
    setPageError(null);
    try {
      const data = await SchedulerService.listTasks();
      setTasks(data);
    } catch (e: unknown) {
      setPageError(e instanceof Error ? e.message : 'Failed to load tasks');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTasks();
    // 載入已登記的 Celery 任務（用於 task path datalist）
    SchedulerService.listRegisteredTasks()
      .then(data => setRegisteredTasks(data))
      .catch(() => { /* non-critical, datalist just won't show */ });
  }, [loadTasks]);

  const handleToggle = async (task: PeriodicTask) => {
    setTogglingId(task.id);
    try {
      const updated = await SchedulerService.updateTask(task.id, { enabled: !task.enabled });
      setTasks(prev => prev.map(t => t.id === task.id ? { ...t, enabled: updated.enabled } : t));
    } catch {
      // ignore — keep original state
    } finally {
      setTogglingId(null);
    }
  };

  const handleDeleteConfirm = async (taskId: number) => {
    setDeletingId(taskId);
    try {
      await SchedulerService.deleteTask(taskId);
      setTasks(prev => prev.filter(t => t.id !== taskId));
    } catch (e: unknown) {
      setPageError(e instanceof Error ? e.message : 'Delete failed');
    } finally {
      setDeletingId(null);
      setDeleteConfirmId(null);
    }
  };

  const openCreate = () => {
    setEditingTask(null);
    setFormError(null);
    setFormMode('create');
  };

  const openEdit = (task: PeriodicTask) => {
    setEditingTask(task);
    setFormError(null);
    setFormMode('edit');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleFormSubmit = async (f: FormState) => {
    setSaving(true);
    setFormError(null);
    try {
      if (formMode === 'create') {
        const payload: CreateTaskPayload = {
          name: f.name,
          task: f.task,
          description: f.description,
          enabled: f.enabled,
          interval: { every: f.intervalEvery, period: f.intervalPeriod },
          args: f.args,
          kwargs: f.kwargs,
        };
        const created = await SchedulerService.createTask(payload);
        setTasks(prev => [created, ...prev]);
        setFormMode('hidden');
      } else if (formMode === 'edit' && editingTask) {
        const payload: UpdateTaskPayload = {
          name: f.name,
          task: f.task,
          description: f.description,
          enabled: f.enabled,
          args: f.args,
          kwargs: f.kwargs,
        };
        if (f.scheduleType === 'interval') {
          payload.interval = { every: f.intervalEvery, period: f.intervalPeriod };
        } else {
          payload.crontab = {
            minute: f.crontabMinute,
            hour: f.crontabHour,
            day_of_week: f.crontabDow,
            day_of_month: f.crontabDom,
            month_of_year: f.crontabMoy,
          };
        }
        const updated = await SchedulerService.updateTask(editingTask.id, payload);
        setTasks(prev => prev.map(t => t.id === editingTask.id ? updated : t));
        setFormMode('hidden');
        setEditingTask(null);
      }
    } catch (e: unknown) {
      const axiosErr = e as { response?: { data?: { detail?: string } } };
      const msg = axiosErr.response?.data?.detail ?? (e instanceof Error ? e.message : 'Save failed');
      setFormError(msg);
    } finally {
      setSaving(false);
    }
  };

  const enabledCount = tasks.filter(t => t.enabled).length;

  return (
    <div style={{ maxWidth: 960, margin: '0 auto', padding: '0 20px 40px', paddingTop: 'calc(var(--navbar-height) + 24px)' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
        <div>
          <h1 style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '1.1rem',
            color: 'var(--text-green)',
            margin: 0,
            letterSpacing: '0.06em',
          }}>
            CELERY SCHEDULER
          </h1>
          {!loading && (
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '4px 0 0' }}>
              {tasks.length} task{tasks.length !== 1 ? 's' : ''} · {enabledCount} enabled
            </p>
          )}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="c2-btn c2-btn--sm" onClick={() => void loadTasks()} disabled={loading}>
            {loading ? 'Loading…' : '↺ Refresh'}
          </button>
          <button className="c2-btn" onClick={openCreate} disabled={formMode !== 'hidden'}>
            + New Task
          </button>
        </div>
      </div>

      {/* Create / Edit Form */}
      {formMode !== 'hidden' && (
        <>
          {formError && (
            <div style={{
              color: 'var(--red)',
              fontSize: '0.82rem',
              marginBottom: 8,
              padding: '8px 12px',
              border: '1px solid var(--red)',
              borderRadius: 4,
            }}>
              {formError}
            </div>
          )}
          <TaskForm
            mode={formMode === 'create' ? 'create' : 'edit'}
            initial={formMode === 'edit' && editingTask ? taskToForm(editingTask) : DEFAULT_FORM}
            saving={saving}
            registeredTasks={registeredTasks}
            onSubmit={handleFormSubmit}
            onCancel={() => { setFormMode('hidden'); setEditingTask(null); setFormError(null); }}
          />
        </>
      )}

      {/* Page-level error */}
      {pageError && (
        <div style={{
          color: 'var(--red)',
          fontSize: '0.85rem',
          marginBottom: 16,
          padding: '10px 14px',
          border: '1px solid var(--red)',
          borderRadius: 4,
        }}>
          {pageError}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div style={{
          textAlign: 'center',
          padding: '48px 20px',
          color: 'var(--text-muted)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.8rem',
        }}>
          Loading tasks…
        </div>
      )}

      {/* Task list */}
      {!loading && tasks.length === 0 && !pageError && (
        <div style={{
          textAlign: 'center',
          padding: '48px 20px',
          color: 'var(--text-muted)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.8rem',
          border: '1px dashed var(--border-color)',
          borderRadius: 6,
        }}>
          No periodic tasks configured.
        </div>
      )}

      {!loading && tasks.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {tasks.map(task => (
            <div key={task.id}>
              {deleteConfirmId === task.id && (
                <DeleteConfirm
                  taskName={task.name}
                  onConfirm={() => void handleDeleteConfirm(task.id)}
                  onCancel={() => setDeleteConfirmId(null)}
                />
              )}
              <TaskRow
                task={task}
                toggling={togglingId === task.id}
                deleting={deletingId === task.id}
                onToggle={() => void handleToggle(task)}
                onEdit={() => openEdit(task)}
                onDelete={() => {
                  setDeleteConfirmId(prev => prev === task.id ? null : task.id);
                }}
              />
            </div>
          ))}
        </div>
      )}

      {/* Footer legend */}
      {!loading && tasks.length > 0 && (
        <div style={{
          marginTop: 20,
          fontSize: '0.68rem',
          color: 'var(--text-muted)',
          fontFamily: 'var(--font-mono)',
          display: 'flex',
          gap: 16,
        }}>
          <span>● enabled</span>
          <span>○ disabled</span>
          <span style={{ marginLeft: 'auto' }}>
            {tasks.filter(t => !t.enabled).length > 0
              ? `${tasks.filter(t => !t.enabled).length} task${tasks.filter(t => !t.enabled).length !== 1 ? 's' : ''} disabled`
              : 'all tasks enabled'}
          </span>
        </div>
      )}
    </div>
  );
}

