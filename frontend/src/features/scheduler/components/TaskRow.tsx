import type { PeriodicTask } from '../services/schedulerApi';
import { cn } from '@/lib/utils';

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

// ─── DeleteConfirm ───────────────────────────────────────────────

interface DeleteConfirmProps {
  taskName: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function DeleteConfirm({ taskName, onConfirm, onCancel }: DeleteConfirmProps) {
  return (
    <div className="p-2.5 px-3.5 border border-red rounded text-[0.8rem] text-text-secondary flex items-center gap-3 mb-2">
      <span>Delete <strong className="text-text-primary font-mono">{taskName}</strong>?</span>
      <button className="c2-btn c2-btn--sm text-red border-red ml-auto" onClick={onConfirm}>
        Confirm Delete
      </button>
      <button className="c2-btn c2-btn--sm opacity-60" onClick={onCancel}>
        Cancel
      </button>
    </div>
  );
}

// ─── TaskRow ────────────────────────────────────────────────────

interface TaskRowProps {
  task: PeriodicTask;
  toggling: boolean;
  deleting: boolean;
  onToggle: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

export function TaskRow({ task, toggling, deleting, onToggle, onEdit, onDelete }: TaskRowProps) {
  const statusColor = task.enabled ? 'var(--text-green)' : 'var(--text-muted)';

  return (
    <div
      className="c2-card p-3 px-4 transition-opacity duration-200"
      style={{ opacity: task.enabled ? 1 : 0.65 }}
    >
      <div className="flex items-start gap-3">
        {/* Enabled toggle dot */}
        <button
          title={task.enabled ? 'Click to disable' : 'Click to enable'}
          onClick={onToggle}
          disabled={toggling}
          className={cn("bg-transparent border-none pt-0.5 shrink-0", toggling ? "cursor-wait" : "cursor-pointer")}
        >
          <span className="text-[0.9rem]" style={{ color: statusColor }}>
            {toggling ? '…' : task.enabled ? '●' : '○'}
          </span>
        </button>

        {/* Main info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2.5 flex-wrap">
            <span className="font-mono text-[0.85rem] font-bold text-text-primary">
              {task.name}
            </span>
            {task.one_off && (
              <span className="c2-badge text-[0.65rem]">ONE-OFF</span>
            )}
          </div>

          <div className="text-[0.72rem] text-text-muted font-mono mt-0.5 overflow-hidden text-ellipsis whitespace-nowrap" title={task.task}>
            {task.task}
          </div>

          {task.description && (
            <div className="text-xs text-text-secondary mt-1">
              {task.description}
            </div>
          )}

          {task.task_doc && !task.description && (
            <div className="text-xs text-text-secondary mt-1">
              {task.task_doc.split('\n')[0]}
            </div>
          )}
        </div>

        {/* Schedule + stats */}
        <div className="flex gap-5 items-center shrink-0 flex-wrap justify-end">
          <div className="text-right">
            <div className="font-mono text-xs text-text-cyan">
              {formatSchedule(task)}
            </div>
            <div className="text-[0.68rem] text-text-muted mt-0.5">
              Last: {formatTime(task.last_run_at)} · ×{task.total_run_count}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-1.5">
            <button className="c2-btn c2-btn--sm text-[0.7rem]" onClick={onEdit}>
              Edit
            </button>
            <button
              className="c2-btn c2-btn--sm text-[0.7rem] text-red border-red"
              onClick={onDelete}
              disabled={deleting}
            >
              {deleting ? '…' : 'Del'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
