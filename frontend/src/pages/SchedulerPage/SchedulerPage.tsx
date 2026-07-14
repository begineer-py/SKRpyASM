import { useState, useEffect, useCallback } from 'react';
import {
  SchedulerService,
  type PeriodicTask,
  type CreateTaskPayload,
  type UpdateTaskPayload,
  type RegisteredTask,
  type WatchdogStatus,
} from '../../services/api_scheduler';
import { TaskRow, DeleteConfirm } from './components/TaskRow';
import { TaskForm, type FormState, DEFAULT_FORM, taskToForm } from './components/TaskForm';
import WatchdogPanel from './components/WatchdogPanel';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

// ─── page ──────────────────────────────────────────────────────

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
  const [watchdogStatus, setWatchdogStatus] = useState<WatchdogStatus | null>(null);

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
      .catch(() => { /* non-critical */ });
    // 載入看門狗狀態
    SchedulerService.getWatchdogStatus()
      .then(setWatchdogStatus)
      .catch(() => { /* non-critical */ });
  }, [loadTasks]);

  const handleToggle = async (task: PeriodicTask) => {
    setTogglingId(task.id);
    try {
      const updated = await SchedulerService.updateTask(task.id, { enabled: !task.enabled });
      setTasks(prev => prev.map(t => t.id === task.id ? { ...t, enabled: updated.enabled } : t));
    } catch {
      // ignore
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

      {/* Watchdog Status Panel */}
      {watchdogStatus && (
        <WatchdogPanel
          status={watchdogStatus}
          onRefresh={() => {
            SchedulerService.getWatchdogStatus()
              .then(setWatchdogStatus)
              .catch(() => {});
          }}
        />
      )}

      {/* Create / Edit Form */}
      <Dialog open={formMode !== 'hidden'} onOpenChange={(open) => { if (!open) { setFormMode('hidden'); setEditingTask(null); setFormError(null); } }}>
        <DialogContent className="bg-bg-elevated border-border-subtle text-text-primary max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-text-primary font-body" style={{ color: 'var(--text-green)', fontFamily: 'var(--font-mono)' }}>
              {formMode === 'create' ? '+ New Task' : `Edit: ${editingTask?.name ?? ''}`}
            </DialogTitle>
          </DialogHeader>

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
          {formMode !== 'hidden' && (
            <TaskForm
              mode={formMode === 'create' ? 'create' : 'edit'}
              initial={formMode === 'edit' && editingTask ? taskToForm(editingTask) : DEFAULT_FORM}
              saving={saving}
              registeredTasks={registeredTasks}
              onSubmit={handleFormSubmit}
              onCancel={() => { setFormMode('hidden'); setEditingTask(null); setFormError(null); }}
            />
          )}
        </DialogContent>
      </Dialog>

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
