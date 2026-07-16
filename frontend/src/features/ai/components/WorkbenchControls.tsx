import { useEffect, useRef, useState, type ReactNode } from 'react';
import { Check, Filter, RotateCcw, Search, Settings2, SlidersHorizontal, X } from 'lucide-react';
import { Popover as PopoverPrimitive } from 'radix-ui';
import MessageFilterBar, { DEFAULT_MSG_FILTER, type MessageFilterState } from '../../../components/MessageFilterBar';
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerDismiss,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from '../../../components/ui/drawer';
import type { ThreadSummary } from '../../../services/assistantApi';
import type { OverviewData } from '../services/aiApi';

const FILTER_POPOVER_ID = 'ai-conversation-filter-popover';
const SETTINGS_DRAWER_ID = 'ai-workbench-settings-drawer';
const OVERVIEWS_DRAWER_ID = 'ai-target-overviews-drawer';

interface FilterPopoverProps {
  readonly targetSearchId: string;
  readonly onTargetSearchChange: (value: string) => void;
  readonly msgFilter: MessageFilterState;
  readonly onMessageFilterChange: (next: MessageFilterState) => void;
  readonly onReset: () => void;
  readonly activeCount: number;
}

export function FilterPopover({
  targetSearchId,
  onTargetSearchChange,
  msgFilter,
  onMessageFilterChange,
  onReset,
  activeCount,
}: FilterPopoverProps): ReactNode {
  const [open, setOpen] = useState(false);
  const [targetDraft, setTargetDraft] = useState(targetSearchId);
  const triggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => setTargetDraft(targetSearchId), [targetSearchId]);

  const applyTarget = (): void => {
    onTargetSearchChange(targetDraft.trim());
    setOpen(false);
  };

  return (
    <PopoverPrimitive.Root open={open} onOpenChange={(nextOpen) => {
      setOpen(nextOpen);
      if (!nextOpen) window.requestAnimationFrame(() => triggerRef.current?.focus());
    }}>
      <PopoverPrimitive.Trigger asChild>
        <button
          ref={triggerRef}
          className={`ai-secondary-button ai-secondary-button--utility ${activeCount > 0 ? 'is-active' : ''}`}
          type="button"
          aria-expanded={open}
          aria-controls={FILTER_POPOVER_ID}
        >
          <Filter size={15} />
          <span>Filter</span>
          {activeCount > 0 && <b>{activeCount}</b>}
        </button>
      </PopoverPrimitive.Trigger>
      <PopoverPrimitive.Portal>
        <PopoverPrimitive.Content
          id={FILTER_POPOVER_ID}
          className="ai-filter-popover"
          side="bottom"
          align="start"
          aria-labelledby={`${FILTER_POPOVER_ID}-title`}
          onCloseAutoFocus={(event) => { event.preventDefault(); triggerRef.current?.focus(); }}
        >
          <div className="ai-popover__header">
            <div><h3 id={`${FILTER_POPOVER_ID}-title`}>Focus the workbench</h3></div>
            <PopoverPrimitive.Close asChild>
              <button className="ai-icon-button" type="button" aria-label="Close filters"><X size={16} /></button>
            </PopoverPrimitive.Close>
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
              {targetDraft && <button className="ai-input-clear" type="button" onClick={() => setTargetDraft('')} aria-label="Clear target filter"><X size={14} /></button>}
            </div>
            <p className="ai-field-help">Only conversations bound to this target will appear.</p>
          </div>
          <div className="ai-filter-section ai-filter-section--messages">
            <div className="ai-section-heading">
              <div><span className="ai-field-label">Message visibility</span><p className="ai-field-help">Choose which events remain in the chat stream.</p></div>
              <SlidersHorizontal size={15} aria-hidden="true" />
            </div>
            <MessageFilterBar filter={msgFilter} onChange={onMessageFilterChange} />
          </div>
          <div className="ai-popover__footer">
            <button className="ai-text-button" type="button" onClick={() => { onReset(); setTargetDraft(''); }}><RotateCcw size={14} /> Reset</button>
            <button className="ai-primary-button ai-primary-button--compact" type="button" onClick={applyTarget}><Check size={14} /> Apply filters</button>
          </div>
          <span className="ai-filter-count" aria-live="polite">{activeCount} active</span>
        </PopoverPrimitive.Content>
      </PopoverPrimitive.Portal>
    </PopoverPrimitive.Root>
  );
}

interface SettingsDrawerProps {
  readonly showInternal: boolean;
  readonly onShowInternalChange: (value: boolean) => void;
  readonly onResetFilters: () => void;
}

export function SettingsDrawer({ showInternal, onShowInternalChange, onResetFilters }: SettingsDrawerProps): ReactNode {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);

  return (
    <Drawer open={open} onOpenChange={(nextOpen) => {
      setOpen(nextOpen);
      if (!nextOpen) window.requestAnimationFrame(() => triggerRef.current?.focus());
    }}>
      <DrawerTrigger asChild>
        <button ref={triggerRef} className="ai-secondary-button ai-secondary-button--utility" type="button" title="Workbench settings" aria-expanded={open} aria-controls={SETTINGS_DRAWER_ID}><Settings2 size={15} /><span>Settings</span></button>
      </DrawerTrigger>
      <DrawerContent id={SETTINGS_DRAWER_ID} aria-describedby="ai-settings-description" onCloseAutoFocus={(event) => { event.preventDefault(); triggerRef.current?.focus(); }}>
        <DrawerHeader>
          <div>
            <DrawerTitle>Workspace controls</DrawerTitle>
            <DrawerDescription id="ai-settings-description">Choose which conversations and message details the workbench shows.</DrawerDescription>
          </div>
          <DrawerDismiss />
        </DrawerHeader>
        <div className="mt-6 space-y-6">
          <section className="ai-settings-section">
            <span className="ai-field-label">Conversation scope</span>
            <p className="ai-field-help">Control whether internal automation threads join the conversation index.</p>
            <button className={`ai-setting-row ${showInternal ? 'is-active' : ''}`} type="button" onClick={() => onShowInternalChange(!showInternal)} aria-pressed={showInternal}>
              <span className="ai-setting-row__icon"><Settings2 size={16} /></span>
              <span><strong>{showInternal ? 'Include system threads' : 'User conversations only'}</strong><small>{showInternal ? 'Automation and hidden agent threads are visible.' : 'Internal execution threads stay out of the list.'}</small></span>
              <span className="ai-switch" aria-hidden="true"><span /></span>
            </button>
          </section>
          <section className="ai-settings-section">
            <span className="ai-field-label">Message filters</span>
            <p className="ai-field-help">Saved locally for this browser and restored on your next visit.</p>
            <button className="ai-secondary-button" type="button" onClick={onResetFilters}><RotateCcw size={14} /> Restore default message filters</button>
          </section>
        </div>
      </DrawerContent>
    </Drawer>
  );
}

interface OverviewDrawerProps {
  readonly overviews: readonly OverviewData[];
  readonly overviewsLoading: boolean;
  readonly boundTargetId: number | null;
  readonly onSelectThread: (thread: ThreadSummary) => void;
  readonly onNavigate: (path: string) => void;
}

export function OverviewDrawer({ overviews, overviewsLoading, boundTargetId, onSelectThread, onNavigate }: OverviewDrawerProps): ReactNode {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);

  return (
    <Drawer open={open} onOpenChange={(nextOpen) => {
      setOpen(nextOpen);
      if (!nextOpen) window.requestAnimationFrame(() => triggerRef.current?.focus());
    }}>
      <DrawerTrigger asChild>
        <button ref={triggerRef} className="ai-secondary-button ai-secondary-button--utility" type="button" title="Target overviews" aria-expanded={open} aria-controls={OVERVIEWS_DRAWER_ID}><SlidersHorizontal size={15} /><span>Overviews</span></button>
      </DrawerTrigger>
      <DrawerContent id={OVERVIEWS_DRAWER_ID} aria-describedby="ai-overviews-description" onCloseAutoFocus={(event) => { event.preventDefault(); triggerRef.current?.focus(); }}>
        <DrawerHeader>
          <div>
            <DrawerTitle>Target overviews</DrawerTitle>
            <DrawerDescription id="ai-overviews-description">Review generated target summaries for the selected conversation.</DrawerDescription>
          </div>
          <DrawerDismiss />
        </DrawerHeader>
        <div className="ai-overview-list mt-6">
          {overviewsLoading && <div className="ai-sidebar-state"><span className="ai-loader" /> Loading overviews</div>}
          {!boundTargetId && !overviewsLoading && <div className="ai-sidebar-empty"><strong>Bind a target first</strong><span>Select a target-bound conversation to inspect overviews.</span></div>}
          {!overviewsLoading && boundTargetId && overviews.length === 0 && <div className="ai-sidebar-empty"><strong>No overviews yet</strong><span>Generated target overviews will appear here.</span></div>}
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
      </DrawerContent>
    </Drawer>
  );
}

export { DEFAULT_MSG_FILTER };
