import { type ReactNode } from 'react';
import { Bot, MessageSquarePlus, X } from 'lucide-react';
import type { OverviewData } from '../services/aiApi';
import type { ThreadSummary } from '../../../services/assistantApi';
import type { MessageFilterState } from '../../../components/MessageFilterBar';
import { FilterPopover, OverviewDrawer, SettingsDrawer } from './WorkbenchControls';
import { TargetConversationGroups } from './TargetConversationGroups';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  targetSearchId: string;
  onTargetSearchChange: (value: string) => void;
  showInternal: boolean;
  onShowInternalChange: (value: boolean) => void;
  msgFilter: MessageFilterState;
  onMessageFilterChange: (next: MessageFilterState) => void;
  onResetFilters: () => void;
  threadsLoading: boolean;
  threadsError: string | null;
  threads: ThreadSummary[];
  selectedThreadId: string | null;
  onSelectThread: (thread: ThreadSummary) => void;
  onDeleteThread: (id: string | null) => void;
  onCreateThread: (targetId?: number) => void;
  overviews: OverviewData[];
  overviewsLoading: boolean;
  boundTargetId: number | null;
  onNavigate: (path: string) => void;
  onUnbindTarget: () => void;
}

export function Sidebar({
  open,
  onClose,
  targetSearchId,
  onTargetSearchChange,
  showInternal,
  onShowInternalChange,
  msgFilter,
  onMessageFilterChange,
  onResetFilters,
  threadsLoading,
  threadsError,
  threads,
  selectedThreadId,
  onSelectThread,
  onDeleteThread,
  onCreateThread,
  overviews,
  overviewsLoading,
  boundTargetId,
  onNavigate,
  onUnbindTarget,
}: SidebarProps): ReactNode {
  const filterCount = [
    Boolean(targetSearchId),
    !msgFilter.showUserConv,
    !msgFilter.showAiResponse,
    msgFilter.showToolCalls,
    !msgFilter.showSubagent,
    msgFilter.showSystem,
    msgFilter.agentFilter.length > 0,
  ].filter(Boolean).length;

  return (
    <aside className={`ai-conversation-sidebar ${open ? 'is-open' : 'is-closed'}`} aria-label="Conversation navigation">
      <div className="ai-sidebar__header">
        <div className="ai-sidebar__identity">
          <span className="ai-sidebar__mark"><Bot size={17} /></span>
          <h1>Conversations</h1>
        </div>
        <button className="ai-icon-button ai-icon-button--sidebar" type="button" onClick={onClose} title="Collapse conversations" aria-label="Collapse conversations">
          <X size={17} />
        </button>
      </div>

      <div className="ai-sidebar__actions">
        <button className="ai-primary-button ai-primary-button--new-chat" type="button" onClick={() => onCreateThread()} disabled={threadsLoading}>
          <MessageSquarePlus size={16} />
          <span>New Chat</span>
          <kbd>⌘ K</kbd>
        </button>
        <div className="ai-sidebar__utility-row">
          <div className="ai-popover-anchor"><FilterPopover targetSearchId={targetSearchId} onTargetSearchChange={onTargetSearchChange} msgFilter={msgFilter} onMessageFilterChange={onMessageFilterChange} onReset={onResetFilters} activeCount={filterCount} /></div>
          <SettingsDrawer showInternal={showInternal} onShowInternalChange={onShowInternalChange} onResetFilters={onResetFilters} />
          <OverviewDrawer overviews={overviews} overviewsLoading={overviewsLoading} boundTargetId={boundTargetId} onSelectThread={onSelectThread} onNavigate={onNavigate} />
        </div>
      </div>

      <div className="ai-sidebar__context">
        <div className="ai-sidebar__context-label"><span className="ai-status-dot" /> CONVERSATION INDEX</div>
        <div className="ai-sidebar__context-copy">{threads.length} visible thread{threads.length === 1 ? '' : 's'}</div>
      </div>

      <div className="ai-sidebar__body">
        {threadsLoading && <div className="ai-sidebar-state"><span className="ai-loader" /> Loading conversations</div>}
        {threadsError && <div className="ai-sidebar-state ai-sidebar-state--error"><strong>Could not load conversations</strong><span>{threadsError}</span></div>}
        {!threadsLoading && !threadsError && (
          <TargetConversationGroups
            threads={threads}
            selectedThreadId={selectedThreadId}
            targetSearchId={targetSearchId}
            onSelectThread={onSelectThread}
            onDeleteThread={onDeleteThread}
            onCreateThread={onCreateThread}
            onNavigate={onNavigate}
          />
        )}
      </div>

      {boundTargetId && (
        <div className="ai-sidebar__footer">
          <div className="ai-bound-target"><span><span className="ai-status-dot" /> Target #{boundTargetId}</span><button type="button" onClick={onUnbindTarget} aria-label="Unbind target"><X size={14} /></button></div>
        </div>
      )}
    </aside>
  );
}
