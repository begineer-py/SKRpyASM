import { useState, type ReactNode } from 'react';
import { Bot, ChevronRight, Filter, MessageSquarePlus, Search, Settings2, SlidersHorizontal, X } from 'lucide-react';
import type { OverviewData } from '../services/aiApi';
import type { ThreadSummary } from '../../../services/assistantApi';
import type { MessageFilterState } from '../../../components/MessageFilterBar';
import { FilterPopover, SettingsDrawer } from './WorkbenchControls';

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
  sidebarTab: 'threads' | 'overviews';
  onSidebarTabChange: (tab: 'threads' | 'overviews') => void;
  threads: ThreadSummary[];
  selectedThreadId: string | null;
  onSelectThread: (thread: ThreadSummary) => void;
  onDeleteThread: (id: string | null) => void;
  onCreateThread: () => void;
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
  sidebarTab,
  onSidebarTabChange,
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
  const [filterOpen, setFilterOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
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
          <div>
            <span className="ai-kicker">AI WORKBENCH</span>
            <h1>Conversations</h1>
          </div>
        </div>
        <button className="ai-icon-button ai-icon-button--sidebar" type="button" onClick={onClose} title="Collapse conversations" aria-label="Collapse conversations">
          <X size={17} />
        </button>
      </div>

      <div className="ai-sidebar__actions">
        <button className="ai-primary-button ai-primary-button--new-chat" type="button" onClick={onCreateThread} disabled={threadsLoading}>
          <MessageSquarePlus size={16} />
          <span>New Chat</span>
          <kbd>⌘ K</kbd>
        </button>
        <div className="ai-sidebar__utility-row">
          <div className="ai-popover-anchor">
            <button className={`ai-secondary-button ai-secondary-button--utility ${filterCount > 0 ? 'is-active' : ''}`} type="button" onClick={() => setFilterOpen((value) => !value)} aria-expanded={filterOpen}>
              <Filter size={15} />
              <span>Filter</span>
              {filterCount > 0 && <b>{filterCount}</b>}
            </button>
            <FilterPopover
              open={filterOpen}
              onClose={() => setFilterOpen(false)}
              targetSearchId={targetSearchId}
              onTargetSearchChange={onTargetSearchChange}
              msgFilter={msgFilter}
              onMessageFilterChange={onMessageFilterChange}
              onReset={onResetFilters}
              activeCount={filterCount}
            />
          </div>
          <button className="ai-secondary-button ai-secondary-button--utility" type="button" onClick={() => setSettingsOpen(true)} title="Workbench settings">
            <Settings2 size={15} />
            <span>Settings</span>
          </button>
        </div>
      </div>

      <div className="ai-sidebar__context">
        <div className="ai-sidebar__context-label"><span className="ai-status-dot" /> CONVERSATION INDEX</div>
        <div className="ai-sidebar__context-copy">{threads.length} visible thread{threads.length === 1 ? '' : 's'}</div>
      </div>

      <div className="ai-sidebar__tabs" role="tablist" aria-label="Conversation views">
        <button className={`ai-sidebar-tab ${sidebarTab === 'threads' ? 'is-active' : ''}`} type="button" role="tab" aria-selected={sidebarTab === 'threads'} onClick={() => onSidebarTabChange('threads')}>
          <MessageSquarePlus size={14} /> Threads <span>{threads.length}</span>
        </button>
        <button className={`ai-sidebar-tab ${sidebarTab === 'overviews' ? 'is-active' : ''}`} type="button" role="tab" aria-selected={sidebarTab === 'overviews'} onClick={() => onSidebarTabChange('overviews')}>
          <SlidersHorizontal size={14} /> Overviews <span>{overviews.length}</span>
        </button>
      </div>

      <div className="ai-sidebar__body">
        {threadsLoading && <div className="ai-sidebar-state"><span className="ai-loader" /> Loading conversations</div>}
        {threadsError && <div className="ai-sidebar-state ai-sidebar-state--error"><strong>Could not load conversations</strong><span>{threadsError}</span></div>}

        {sidebarTab === 'threads' && !threadsLoading && !threadsError && (
          <div className="ai-thread-list">
            {threads.length === 0 && (
              <div className="ai-sidebar-empty">
                <span className="ai-empty-icon"><Search size={18} /></span>
                <strong>No conversations found</strong>
                <span>Try clearing your filters or start a new chat.</span>
                {filterCount > 0 && <button className="ai-text-button" type="button" onClick={onResetFilters}>Clear filters</button>}
              </div>
            )}
            {threads.map((thread) => {
              const selected = selectedThreadId === String(thread.id);
              return (
                <div key={thread.id} className={`ai-thread-item ${selected ? 'is-selected' : ''}`}>
                  <button className="ai-thread-item__main" type="button" onClick={() => onSelectThread(thread)} aria-current={selected ? 'page' : undefined}>
                    <span className="ai-thread-item__icon"><MessageSquarePlus size={15} /></span>
                    <span className="ai-thread-item__copy">
                      <strong>{thread.name || 'Untitled conversation'}</strong>
                      <small>{thread.bound_target_id ? `Target #${thread.bound_target_id}` : 'No target bound'} · {thread.assistant_id || 'AI agent'}</small>
                    </span>
                    <ChevronRight className="ai-thread-item__chevron" size={15} />
                  </button>
                  {selected && (
                    <button className="ai-thread-item__delete" type="button" onClick={(event) => { event.stopPropagation(); onDeleteThread(String(thread.id)); }} title="Delete conversation" aria-label={`Delete ${thread.name || 'conversation'}`}>
                      <X size={14} />
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {sidebarTab === 'overviews' && (
          <div className="ai-overview-list">
            {overviewsLoading && <div className="ai-sidebar-state"><span className="ai-loader" /> Loading overviews</div>}
            {!boundTargetId && !overviewsLoading && <div className="ai-sidebar-empty"><span className="ai-empty-icon"><SlidersHorizontal size={18} /></span><strong>Bind a target first</strong><span>Select a target-bound conversation to inspect overviews.</span></div>}
            {!overviewsLoading && boundTargetId && overviews.length === 0 && <div className="ai-sidebar-empty"><span className="ai-empty-icon"><SlidersHorizontal size={18} /></span><strong>No overviews yet</strong><span>Generated target overviews will appear here.</span></div>}
            {overviews.map((overview) => (
              <div key={overview.id} className="ai-overview-card">
                <div className="ai-overview-card__topline"><span>OVERVIEW #{overview.id}</span><span className="ai-status-badge">{overview.status}</span></div>
                <div className="ai-overview-card__meta">Risk score <strong>{overview.risk_score}</strong></div>
                <div className="ai-overview-card__actions">
                  {overview.thread_id != null && <button className="ai-secondary-button ai-secondary-button--tiny" type="button" onClick={() => onSelectThread({ id: overview.thread_id as number, name: `Overview #${overview.id}`, assistant_id: 'automation_agent', is_hidden: true, bound_target_id: null })}>View thread</button>}
                  <button className="ai-secondary-button ai-secondary-button--tiny" type="button" onClick={() => onNavigate(`/overviews/${overview.id}`)}>Open detail</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {boundTargetId && (
        <div className="ai-sidebar__footer">
          <div className="ai-bound-target"><span><span className="ai-status-dot" /> Target #{boundTargetId}</span><button type="button" onClick={onUnbindTarget} aria-label="Unbind target"><X size={14} /></button></div>
        </div>
      )}
      <SettingsDrawer open={settingsOpen} onClose={() => setSettingsOpen(false)} showInternal={showInternal} onShowInternalChange={onShowInternalChange} onResetFilters={onResetFilters} />
    </aside>
  );
}
