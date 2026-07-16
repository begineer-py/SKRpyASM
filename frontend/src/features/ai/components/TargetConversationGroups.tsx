import { useMemo, useState, type ReactNode } from 'react';
import { ChevronDown, ChevronRight, MessageSquarePlus, Search, X } from 'lucide-react';
import { GET_TARGETS_QUERY } from '../../target/services/targetApi';
import type { Target } from '../../target/types';
import { useHasuraQuery } from '../../../hooks/useHasuraQuery';
import type { ThreadSummary } from '../../../services/assistantApi';

interface TargetConversationGroupsProps {
  readonly threads: readonly ThreadSummary[];
  readonly selectedThreadId: string | null;
  readonly targetSearchId: string;
  readonly onSelectThread: (thread: ThreadSummary) => void;
  readonly onDeleteThread: (threadId: string) => void;
  readonly onCreateThread: (targetId?: number) => void;
  readonly onNavigate: (path: string) => void;
}

interface ConversationGroup {
  readonly key: string;
  readonly label: string;
  readonly targetId: number | null;
  readonly unavailable: boolean;
  readonly threads: readonly ThreadSummary[];
}

interface TargetQueryData {
  readonly core_target: readonly Target[];
}

const threadTimestamp = (thread: ThreadSummary): number => {
  const timestamp = Date.parse(thread.created_at ?? '');
  return Number.isNaN(timestamp) ? 0 : timestamp;
};

const sortThreads = (threads: readonly ThreadSummary[]): ThreadSummary[] =>
  [...threads].sort((left, right) =>
    threadTimestamp(right) - threadTimestamp(left)
    || String(right.id).localeCompare(String(left.id), undefined, { numeric: true }),
  );

const sortTargets = (targets: readonly Target[]): Target[] =>
  [...targets].sort((left, right) =>
    left.name.localeCompare(right.name, undefined, { sensitivity: 'base', numeric: true })
    || left.id - right.id,
  );

function ThreadItem({
  thread,
  selected,
  onSelect,
  onDelete,
}: {
  readonly thread: ThreadSummary;
  readonly selected: boolean;
  readonly onSelect: (thread: ThreadSummary) => void;
  readonly onDelete: (threadId: string) => void;
}): ReactNode {
  return (
    <div className={`ai-thread-item ${selected ? 'is-selected' : ''}`}>
      <button className="ai-thread-item__main" type="button" onClick={() => onSelect(thread)} aria-current={selected ? 'page' : undefined}>
        <span className="ai-thread-item__icon"><MessageSquarePlus size={15} /></span>
        <span className="ai-thread-item__copy">
          <strong>{thread.name || 'Untitled conversation'}</strong>
          <small>{thread.assistant_id || 'AI agent'}</small>
        </span>
        <ChevronRight className="ai-thread-item__chevron" size={15} />
      </button>
      {selected && (
        <button
          className="ai-thread-item__delete"
          type="button"
          onClick={() => onDelete(String(thread.id))}
          title="Delete conversation"
          aria-label={`Delete ${thread.name || 'conversation'}`}
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}

export function TargetConversationGroups({
  threads,
  selectedThreadId,
  targetSearchId,
  onSelectThread,
  onDeleteThread,
  onCreateThread,
  onNavigate,
}: TargetConversationGroupsProps): ReactNode {
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});
  const { data, loading: targetsLoading, error: targetsError, refetch } = useHasuraQuery<TargetQueryData>(GET_TARGETS_QUERY);
  const targets = useMemo(() => sortTargets(data?.core_target ?? []), [data]);

  const groups = useMemo((): readonly ConversationGroup[] => {
    const filterTargetId = targetSearchId ? Number(targetSearchId) : null;
    const hasTargetFilter = filterTargetId !== null && Number.isSafeInteger(filterTargetId);
    const targetThreads = new Map<number, ThreadSummary[]>();
    const unboundThreads: ThreadSummary[] = [];

    for (const thread of threads) {
      if (thread.bound_target_id == null) {
        unboundThreads.push(thread);
        continue;
      }

      const existing = targetThreads.get(thread.bound_target_id) ?? [];
      existing.push(thread);
      targetThreads.set(thread.bound_target_id, existing);
    }

    const visibleTargets = hasTargetFilter
      ? targets.filter((target) => target.id === filterTargetId)
      : targets;
    const knownTargetIds = new Set(visibleTargets.map((target) => target.id));
    const targetGroups = visibleTargets.map((target) => ({
      key: `target-${target.id}`,
      label: target.name || `Target #${target.id}`,
      targetId: target.id,
      unavailable: false,
      threads: sortThreads(targetThreads.get(target.id) ?? []),
    }));
    const unavailableGroups = [...targetThreads.entries()]
      .filter(([targetId]) => !knownTargetIds.has(targetId) && (!hasTargetFilter || targetId === filterTargetId))
      .sort(([left], [right]) => left - right)
      .map(([targetId, boundThreads]) => ({
        key: `unavailable-target-${targetId}`,
        label: `Unavailable target #${targetId}`,
        targetId,
        unavailable: true,
        threads: sortThreads(boundThreads),
      }));

    if (hasTargetFilter) return [...targetGroups, ...unavailableGroups];

    return [
      ...targetGroups,
      ...unavailableGroups,
      {
        key: 'unbound',
        label: 'Unbound conversations',
        targetId: null,
        unavailable: false,
        threads: sortThreads(unboundThreads),
      },
    ];
  }, [targetSearchId, targets, threads]);

  const toggleGroup = (groupKey: string): void => {
    setExpandedGroups((current) => ({ ...current, [groupKey]: !(current[groupKey] ?? true) }));
  };

  if (targetsLoading) {
    return <div className="ai-sidebar-state"><span className="ai-loader" /> Loading targets</div>;
  }

  return (
    <div className="ai-thread-list">
      {targetsError && (
        <div className="ai-sidebar-state ai-sidebar-state--error" role="status">
          <strong>Could not load targets</strong>
          <span>{targetsError.message}</span>
          <button className="ai-text-button" type="button" onClick={() => { void refetch(); }}>Retry</button>
        </div>
      )}
      {groups.length === 0 && (
        <div className="ai-sidebar-empty">
          <span className="ai-empty-icon"><Search size={18} /></span>
          <strong>No matching target</strong>
          <span>Clear the Target filter or choose another Target.</span>
        </div>
      )}
      {groups.map((group) => {
        const expanded = expandedGroups[group.key] ?? true;
        const contentId = `conversation-group-${group.key}`;
        return (
          <section key={group.key} className="rounded-xl border border-border-subtle bg-bg-card">
            <div className="flex items-center gap-1 p-2">
              <button
                className="flex min-w-0 flex-1 items-center gap-2 rounded-lg px-2 py-2 text-left text-sm font-semibold text-text-primary transition-colors hover:bg-bg-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan/60"
                type="button"
                onClick={() => toggleGroup(group.key)}
                aria-expanded={expanded}
                aria-controls={contentId}
              >
                <ChevronDown className={`shrink-0 transition-transform ${expanded ? '' : '-rotate-90'}`} size={15} aria-hidden="true" />
                <span className="truncate">{group.label}</span>
                <span className="ml-auto font-mono text-xs text-text-muted">{group.threads.length}</span>
              </button>
              {group.targetId !== null && !group.unavailable && (
                <>
                  <button className="ai-icon-button" type="button" onClick={() => onNavigate(`/target/${group.targetId}`)} aria-label={`Open ${group.label}`} title="Open target">
                    <ChevronRight size={15} />
                  </button>
                  <button className="ai-icon-button" type="button" onClick={() => onCreateThread(group.targetId ?? undefined)} aria-label={`Start a conversation for ${group.label}`} title="New chat for target">
                    <MessageSquarePlus size={15} />
                  </button>
                </>
              )}
            </div>
            {expanded && (
              <div id={contentId} className="flex flex-col gap-1 border-t border-border-subtle p-2">
                {group.threads.length === 0 ? (
                  <div className="px-2 py-3 text-sm text-text-secondary">
                    {group.targetId === null ? 'No unbound conversations.' : 'No conversations for this Target.'}
                  </div>
                ) : (
                  group.threads.map((thread) => (
                    <ThreadItem
                      key={thread.id}
                      thread={thread}
                      selected={selectedThreadId === String(thread.id)}
                      onSelect={onSelectThread}
                      onDelete={onDeleteThread}
                    />
                  ))
                )}
              </div>
            )}
          </section>
        );
      })}
    </div>
  );
}
