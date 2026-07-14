import type { ReactNode } from 'react';
import type { OverviewData } from '../../../services/overviewService';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  targetSearchId: string;
  onTargetSearchChange: (value: string) => void;
  showInternal: boolean;
  onShowInternalChange: (value: boolean) => void;
  threadsLoading: boolean;
  threadsError: string | null;
  sidebarTab: 'threads' | 'overviews';
  onSidebarTabChange: (tab: 'threads' | 'overviews') => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  threads: any[];
  selectedThreadId: string | null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onSelectThread: (thread: any) => void;
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
  return (
    <aside className={`sidebar ${open ? 'open' : 'closed'}`}>
      <div className="sidebar-header">
        <h3>CONVERSATIONS</h3>
        <button className="sidebar-toggle" onClick={onClose} title="Collapse">✕</button>
      </div>

      <button className="new-chat-btn" onClick={onCreateThread} disabled={threadsLoading}>
        + New Chat
      </button>

      <div className="sidebar-filter">
        <input
          type="text"
          placeholder="Filter by Target ID..."
          value={targetSearchId}
          onChange={e => onTargetSearchChange(e.target.value)}
        />
        {targetSearchId && (
          <button className="clear-filter" onClick={() => onTargetSearchChange('')}>✕</button>
        )}
      </div>

      <div className="p-1 px-2 pb-2">
        <button
          className={`c2-btn c2-btn--sm w-full justify-center text-[0.7rem] ${showInternal ? 'c2-btn--primary' : 'c2-btn--ghost'}`}
          onClick={() => { const next = !showInternal; onShowInternalChange(next); }}
        >
          {showInternal ? 'Show system threads' : 'User conversations only'}
        </button>
      </div>

      {threadsLoading && <div className="sidebar-loading"><span className="pulse">●</span> Loading...</div>}
      {threadsError && <div className="sidebar-error">Error: {threadsError}</div>}

      <div className="sidebar-tabs flex gap-1 pt-1 px-2">
        <button
          className={`c2-btn c2-btn--sm flex-1 justify-center text-[0.7rem] ${sidebarTab === 'threads' ? 'c2-btn--primary' : 'c2-btn--ghost'}`}
          onClick={() => onSidebarTabChange('threads')}
        >
          THREADS
        </button>
        <button
          className={`c2-btn c2-btn--sm flex-1 justify-center text-[0.7rem] ${sidebarTab === 'overviews' ? 'c2-btn--primary' : 'c2-btn--ghost'}`}
          onClick={() => onSidebarTabChange('overviews')}
        >
          OVERVIEWS{overviews.length > 0 ? ' ✓' : ''}
        </button>
      </div>

      {sidebarTab === 'threads' && (
        <div className="threads-list">
          {threads.length === 0 && !threadsLoading && (
            <div className="empty-state">No conversations yet</div>
          )}
          {threads.map(thread => (
            <div
              key={thread.id}
              className={`thread-item ${selectedThreadId === String(thread.id) ? 'active' : ''}`}
              onClick={() => onSelectThread(thread)}
            >
              <div className="thread-name">{thread.name || 'Untitled'}</div>
              {selectedThreadId === String(thread.id) && (
                <button
                  className="delete-btn"
                  onClick={e => { e.stopPropagation(); onDeleteThread(String(thread.id)); }}
                  title="Delete conversation"
                >
                  Delete
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {sidebarTab === 'overviews' && (
        <div className="threads-list">
          {overviewsLoading && <div className="sidebar-loading"><span className="pulse">●</span> Loading...</div>}
          {!boundTargetId && !overviewsLoading && (
            <div className="empty-state">Select a thread bound to a target to see its overviews</div>
          )}
          {overviews.map(ov => (
            <div key={ov.id} className="thread-item flex flex-col items-stretch gap-1.5">
              <div className="flex justify-between items-center">
                <div>
                  <div className="thread-name">Overview #{ov.id}</div>
                  <div className="text-[11px] text-[#64748b] mt-0.5">{ov.status} · risk {ov.risk_score}</div>
                </div>
              </div>
              <div className="flex gap-1">
                {ov.thread_id && (
                  <button
                    className="c2-btn c2-btn--ghost c2-btn--sm flex-1 text-[0.65rem]"
                    onClick={() => onSelectThread({
                      id: ov.thread_id,
                      name: `Overview #${ov.id}`,
                      assistant_id: 'automation_agent',
                      is_hidden: true,
                      bound_target_id: null,
                    })}
                  >
                    VIEW THREAD
                  </button>
                )}
                <button
                  className="c2-btn c2-btn--ghost c2-btn--sm flex-1 text-[0.65rem]"
                  onClick={() => onNavigate(`/overviews/${ov.id}`)}
                >
                  EDIT DETAIL
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {boundTargetId && (
        <div className="sidebar-footer">
          <div className="target-badge">
            <span>Target: {boundTargetId}</span>
            <button onClick={onUnbindTarget} title="Release target">✕</button>
          </div>
        </div>
      )}
    </aside>
  );
}
