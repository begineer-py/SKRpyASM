import { useEffect, useRef, useState, type ReactNode } from 'react';
import { Check, RotateCcw, Search, Settings2, SlidersHorizontal, X } from 'lucide-react';
import MessageFilterBar, { DEFAULT_MSG_FILTER, type MessageFilterState } from '../../../components/MessageFilterBar';

interface FilterPopoverProps {
  open: boolean;
  onClose: () => void;
  targetSearchId: string;
  onTargetSearchChange: (value: string) => void;
  msgFilter: MessageFilterState;
  onMessageFilterChange: (next: MessageFilterState) => void;
  onReset: () => void;
  activeCount: number;
}

export function FilterPopover({
  open,
  onClose,
  targetSearchId,
  onTargetSearchChange,
  msgFilter,
  onMessageFilterChange,
  onReset,
  activeCount,
}: FilterPopoverProps): ReactNode {
  const [targetDraft, setTargetDraft] = useState(targetSearchId);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => setTargetDraft(targetSearchId), [targetSearchId]);

  useEffect(() => {
    if (!open) return;
    const handlePointerDown = (event: PointerEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) onClose();
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('pointerdown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open, onClose]);

  if (!open) return null;

  const applyTarget = () => {
    onTargetSearchChange(targetDraft.trim());
    onClose();
  };

  return (
    <div ref={rootRef} className="ai-filter-popover" role="dialog" aria-label="Conversation filters">
      <div className="ai-popover__header">
        <div>
          <span className="ai-kicker">WORKSPACE FILTERS</span>
          <h3>Focus the workbench</h3>
        </div>
        <button className="ai-icon-button" type="button" onClick={onClose} aria-label="Close filters">
          <X size={16} />
        </button>
      </div>

      <div className="ai-filter-section">
        <label className="ai-field-label" htmlFor="workbench-target-filter">Target ID</label>
        <div className="ai-input-with-icon">
          <Search size={15} aria-hidden="true" />
          <input
            id="workbench-target-filter"
            className="ai-control-input"
            value={targetDraft}
            onChange={(event) => setTargetDraft(event.target.value.replace(/[^0-9]/g, ''))}
            onKeyDown={(event) => { if (event.key === 'Enter') applyTarget(); }}
            placeholder="All targets"
            inputMode="numeric"
          />
          {targetDraft && (
            <button className="ai-input-clear" type="button" onClick={() => setTargetDraft('')} aria-label="Clear target filter">
              <X size={14} />
            </button>
          )}
        </div>
        <p className="ai-field-help">Only conversations bound to this target will appear.</p>
      </div>

      <div className="ai-filter-section ai-filter-section--messages">
        <div className="ai-section-heading">
          <div>
            <span className="ai-field-label">Message visibility</span>
            <p className="ai-field-help">Choose which events remain in the chat stream.</p>
          </div>
          <SlidersHorizontal size={15} aria-hidden="true" />
        </div>
        <MessageFilterBar filter={msgFilter} onChange={onMessageFilterChange} />
      </div>

      <div className="ai-popover__footer">
        <button className="ai-text-button" type="button" onClick={() => { onReset(); setTargetDraft(''); }}>
          <RotateCcw size={14} /> Reset
        </button>
        <button className="ai-primary-button ai-primary-button--compact" type="button" onClick={applyTarget}>
          <Check size={14} /> Apply filters
        </button>
      </div>
      <span className="ai-filter-count" aria-live="polite">{activeCount} active</span>
    </div>
  );
}

interface SettingsDrawerProps {
  open: boolean;
  onClose: () => void;
  showInternal: boolean;
  onShowInternalChange: (value: boolean) => void;
  onResetFilters: () => void;
}

export function SettingsDrawer({
  open,
  onClose,
  showInternal,
  onShowInternalChange,
  onResetFilters,
}: SettingsDrawerProps): ReactNode {
  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      <button className="ai-drawer-scrim" type="button" aria-label="Close settings" onClick={onClose} />
      <aside className="ai-settings-drawer" aria-label="Workbench settings">
        <div className="ai-drawer__header">
          <div>
            <span className="ai-kicker">WORKBENCH SETTINGS</span>
            <h2>Workspace controls</h2>
          </div>
          <button className="ai-icon-button" type="button" onClick={onClose} aria-label="Close settings">
            <X size={17} />
          </button>
        </div>

        <section className="ai-settings-section">
          <span className="ai-field-label">Conversation scope</span>
          <p className="ai-field-help">Control whether internal automation threads join the conversation index.</p>
          <button
            className={`ai-setting-row ${showInternal ? 'is-active' : ''}`}
            type="button"
            onClick={() => onShowInternalChange(!showInternal)}
            aria-pressed={showInternal}
          >
            <span className="ai-setting-row__icon"><Settings2 size={16} /></span>
            <span>
              <strong>{showInternal ? 'Include system threads' : 'User conversations only'}</strong>
              <small>{showInternal ? 'Automation and hidden agent threads are visible.' : 'Internal execution threads stay out of the list.'}</small>
            </span>
            <span className="ai-switch" aria-hidden="true"><span /></span>
          </button>
        </section>

        <section className="ai-settings-section">
          <span className="ai-field-label">Message filters</span>
          <p className="ai-field-help">Saved locally for this browser and restored on your next visit.</p>
          <button className="ai-secondary-button" type="button" onClick={onResetFilters}>
            <RotateCcw size={14} /> Restore default message filters
          </button>
        </section>

        <div className="ai-drawer__footer">
          <span><span className="ai-status-dot" /> Preferences saved locally</span>
        </div>
      </aside>
    </>
  );
}

export { DEFAULT_MSG_FILTER };
