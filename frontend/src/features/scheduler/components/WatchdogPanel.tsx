import type { WatchdogStatus } from '../services/schedulerApi';

// ─── IssueCounter ───────────────────────────────────────────────

function IssueCounter({ label, count, tone }: { label: string; count: number; tone: 'amber' | 'red' | 'purple' | 'green' }) {
  const colorVar = tone === 'amber' ? 'var(--amber)' : tone === 'red' ? 'var(--red)' : tone === 'purple' ? 'var(--purple)' : 'var(--green)';
  return (
    <div className="flex items-center gap-1.5 px-2.5 py-1 bg-[rgba(15,23,42,0.6)] rounded" style={{ border: `1px solid ${colorVar}` }}>
      <span className="font-bold text-[0.85rem]" style={{ color: colorVar }}>{count}</span>
      <span className="text-text-muted">{label}</span>
    </div>
  );
}

// ─── IssueList ──────────────────────────────────────────────────

function IssueList({ title, tone, items }: {
  title: string;
  tone: 'amber' | 'red' | 'purple';
  items: Array<{ id: number; primary: string; secondary: string; href?: string }>;
}) {
  const colorVar = tone === 'amber' ? 'var(--amber)' : tone === 'red' ? 'var(--red)' : 'var(--purple)';
  return (
    <div className="mt-2.5">
      <div className="text-[0.68rem] font-semibold tracking-[0.06em] mb-1.5" style={{ color: colorVar }}>
        {title}
      </div>
      <div className="flex flex-col gap-1">
        {items.map((item) => {
          const inner = (
            <>
              <span className="text-[0.75rem] text-text-primary">{item.primary}</span>
              <span className="text-[0.68rem] text-text-muted"> {item.secondary}</span>
            </>
          );
          return item.href ? (
            <a key={item.id} href={item.href} className="block px-2 py-1 bg-[rgba(15,23,42,0.5)] rounded no-underline">
              {inner}
            </a>
          ) : (
            <div key={item.id} className="px-2 py-1 bg-[rgba(15,23,42,0.5)] rounded">
              {inner}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── WatchdogPanel ──────────────────────────────────────────────

interface WatchdogPanelProps {
  status: WatchdogStatus;
  onRefresh: () => void;
}

export default function WatchdogPanel({ status, onRefresh }: WatchdogPanelProps) {
  const lastRun = status.watchdog_task_last_run_at
    ? new Date(status.watchdog_task_last_run_at).toLocaleString()
    : '(never)';

  const hasIssues =
    status.stalled_overviews.length > 0 ||
    status.zombie_graphs.length > 0 ||
    status.needs_guidance_overviews.length > 0;

  return (
    <div className="mb-5 p-3.5 bg-[rgba(15,23,42,0.5)] rounded-lg" style={{
      border: `1px solid ${hasIssues ? 'rgba(245,158,11,0.3)' : 'rgba(148,163,184,0.18)'}`,
    }}>
      <div className="flex justify-between items-center mb-2.5">
        <div className="flex items-center gap-2">
          <strong className="font-mono text-[0.82rem]">WATCHDOG STATUS</strong>
          <span className={`c2-badge ${status.watchdog_task_enabled ? 'c2-badge--green' : 'c2-badge--red'}`}>
            {status.watchdog_task_enabled ? 'ACTIVE' : 'DISABLED'}
          </span>
          {status.watchdog_task_interval && (
            <span className="text-[0.7rem] text-text-muted">{status.watchdog_task_interval}</span>
          )}
        </div>
        <button className="c2-btn c2-btn--sm c2-btn--ghost" onClick={onRefresh}>\u21BA</button>
      </div>

      <div className="grid grid-cols-[repeat(auto-fit,minmax(160px,1fr))] gap-2.5 text-[0.72rem] text-text-muted mb-3">
        <div><span className="text-text-secondary">LAST RUN:</span> <code>{lastRun}</code></div>
        <div><span className="text-text-secondary">TOTAL RUNS:</span> {status.watchdog_task_total_runs}</div>
      </div>

      <div className="flex gap-3 flex-wrap text-[0.75rem]">
        <IssueCounter label="Stalled" count={status.stalled_overviews.length} tone="amber" />
        <IssueCounter label="Needs Guidance" count={status.needs_guidance_overviews.length} tone="red" />
        <IssueCounter label="Zombie Graphs" count={status.zombie_graphs.length} tone="purple" />
      </div>

      {status.stalled_overviews.length > 0 && (
        <IssueList title="STALLED OVERVIEWS" tone="amber"
          items={status.stalled_overviews.map((o) => ({
            id: o.id,
            primary: `#${o.id}${o.target_name ? ` @${o.target_name}` : ''}`,
            secondary: `${o.status} \u00B7 rescue ${o.rescue_count}/${status.rescue_threshold_needs_guidance} \u00B7 ${new Date(o.updated_at).toLocaleString()}`,
            href: o.thread_id ? `/aicenter?thread=${o.thread_id}` : undefined,
          }))}
        />
      )}

      {status.needs_guidance_overviews.length > 0 && (
        <IssueList title="NEEDS GUIDANCE (escalated)" tone="red"
          items={status.needs_guidance_overviews.map((o) => ({
            id: o.id,
            primary: `#${o.id}${o.target_name ? ` @${o.target_name}` : ''}`,
            secondary: `${o.status} \u00B7 rescue ${o.rescue_count} \u00B7 ${new Date(o.updated_at).toLocaleString()}`,
            href: o.thread_id ? `/aicenter?thread=${o.thread_id}` : undefined,
          }))}
        />
      )}

      {status.zombie_graphs.length > 0 && (
        <IssueList title="ZOMBIE GRAPHS (auto-wake attempted)" tone="purple"
          items={status.zombie_graphs.map((g) => ({
            id: g.id,
            primary: `Graph #${g.id}`,
            secondary: `${g.assistant_id || '(no agent)'}${g.title ? ` \u00B7 ${g.title}` : ''} \u00B7 ${new Date(g.updated_at).toLocaleString()}`,
            href: `/execution-monitor?graph=${g.id}`,
          }))}
        />
      )}

      {!hasIssues && (
        <div className="text-[0.75rem] text-text-muted">
          \u2713 No stalled overviews or zombie graphs detected.
        </div>
      )}
    </div>
  );
}
