import { useState, useEffect, useCallback } from 'react';
import {
  SchedulerService,
  type PeriodicTask,
  type CreateTaskPayload,
  type UpdateTaskPayload,
  type RegisteredTask,
  type WatchdogStatus,
} from '../services/schedulerApi';
import { useApiQuery } from '../../../hooks/useApiQuery';
import { useMutation } from '../../../hooks/useMutation';
import { TaskRow, DeleteConfirm } from '../components/TaskRow';
import { TaskForm, type FormState, DEFAULT_FORM, taskToForm } from '../components/TaskForm';
import WatchdogPanel from '../components/WatchdogPanel';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

// ─── page ──────────────────────────────────────────────────────

export default function SchedulerPage() {
  const { data: tasksData, loading, error: queryError, refetch: refetchTasks } = useApiQuery<PeriodicTask[]>(
    () => SchedulerService.listTasks(),
    []
  );
  const tasks = tasksData ?? [];
  const pageError = queryError?.message ?? null;
  const [registeredTasks, setRegisteredTasks] = useState<RegisteredTask[]>([]);

  const [formMode, setFormMode] = useState<'hidden' | 'create' | 'edit'>('hidden');
  const [editingTask, setEditingTask] = useState<PeriodicTask | null>(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [togglingId, setTogglingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
  const [watchdogStatus, setWatchdogStatus] = useState<WatchdogStatus | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { mutate: deleteTask } = useMutation<void, number>(
    (taskId: number) => SchedulerService.deleteTask(taskId),
  );

  useEffect(() => {
    // 載入已登記的 Celery 任務（用於 task path datalist）
    SchedulerService.listRegisteredTasks()
      .then(data => setRegisteredTasks(data))
      .catch(() => { /* non-critical */ });
    // 載入看門狗狀態
    SchedulerService.getWatchdogStatus()
      .then(setWatchdogStatus)
      .catch(() => { /* non-critical */ });
  }, []);

  const handleToggle = async (task: PeriodicTask) => {
    setTogglingId(task.id);
    try {
      await SchedulerService.updateTask(task.id, { enabled: !task.enabled });
      refetchTasks();
    } catch {
      // ignore
    } finally {
      setTogglingId(null);
    }
  };

  const handleDeleteConfirm = async (taskId: number) => {
    setDeletingId(taskId);
    setDeleteError(null);
    try {
      await deleteTask(taskId);
      refetchTasks();
    } catch (e: unknown) {
      setDeleteError(e instanceof Error ? e.message : 'Delete failed');
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
        await SchedulerService.createTask(payload);
        refetchTasks();
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
        await SchedulerService.updateTask(editingTask.id, payload);
        refetchTasks();
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
    <div className="max-w-[960px] mx-auto px-5 pb-10 pt-[calc(var(--navbar-height)+24px)]">
      {/* Header */}
      <div className="flex justify-between items-start mb-5">
        <div>
          <h1 className="font-mono text-[1.1rem] text-green m-0 tracking-[0.06em]">
            CELERY SCHEDULER
          </h1>
          {!loading && (
            <p className="text-xs text-text-muted mt-1">
              {tasks.length} task{tasks.length !== 1 ? 's' : ''} · {enabledCount} enabled
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <button className="c2-btn c2-btn--sm" onClick={() => void refetchTasks()} disabled={loading}>
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
            <DialogTitle className="text-text-primary font-body text-green font-mono">
              {formMode === 'create' ? '+ New Task' : `Edit: ${editingTask?.name ?? ''}`}
            </DialogTitle>
          </DialogHeader>

          {formError && (
            <div className="text-red text-[0.82rem] mb-2 p-2 px-3 border border-red rounded">
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
      {(pageError || deleteError) && (
        <div className="text-red text-[0.85rem] mb-4 p-2.5 px-3.5 border border-red rounded">
          {pageError || deleteError}
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="text-center py-12 px-5 text-text-muted font-mono text-[0.8rem]">
          Loading tasks…
        </div>
      )}

      {/* Task list */}
      {!loading && tasks.length === 0 && !pageError && (
        <div className="text-center py-12 px-5 text-text-muted font-mono text-[0.8rem] border border-dashed border-border-normal rounded-md">
          No periodic tasks configured.
        </div>
      )}

      {!loading && tasks.length > 0 && (
        <div className="flex flex-col gap-2">
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
        <div className="mt-5 text-[0.68rem] text-text-muted font-mono flex gap-4">
          <span>● enabled</span>
          <span>○ disabled</span>
          <span className="ml-auto">
            {tasks.filter(t => !t.enabled).length > 0
              ? `${tasks.filter(t => !t.enabled).length} task${tasks.filter(t => !t.enabled).length !== 1 ? 's' : ''} disabled`
              : 'all tasks enabled'}
          </span>
        </div>
      )}
    </div>
  );
}
