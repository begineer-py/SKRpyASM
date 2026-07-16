import { useRef } from 'react'
import { RefreshCw, Search, Settings } from 'lucide-react'

import { cn } from '@/lib/utils'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

import type { ExecutionGraph } from '../../services/aiApi'
import { formatDuration, statusClass } from './executionMonitorPresentation'

const STATUS_OPTIONS = ['RUNNING', 'WAITING', 'SUCCEEDED', 'FAILED', 'CANCELLED', 'BLOCKED'] as const
const ASSISTANT_OPTIONS = ['automation_agent', 'recon_agent', 'post_exploit_agent', 'reporting_agent', 'hacker_assistant_agent'] as const
const searchInputClass = 'h-11 w-full rounded-xl border border-border-subtle bg-bg-surface px-3.5 text-base text-text-primary outline-none transition-colors placeholder:text-text-muted focus:border-cyan focus:shadow-[0_0_0_3px_rgba(6,182,212,0.12)]'
const filterSelectClass = 'h-11 w-full cursor-pointer rounded-xl border border-border-subtle bg-bg-surface px-3.5 text-base text-text-primary outline-none transition-colors focus:border-cyan focus:shadow-[0_0_0_3px_rgba(6,182,212,0.12)]'
const statusBadgeClass = 'inline-flex items-center rounded-md border border-current/25 bg-black/20 px-2 py-1 font-mono text-xs font-semibold tracking-wide'

export type MonitorFilters = {
  readonly status: string
  readonly assistant: string
  readonly thread: string
  readonly target: string
  readonly search: string
}

type ExecutionMonitorControlsDialogProps = {
  readonly open: boolean
  readonly graphs: readonly ExecutionGraph[]
  readonly selectedGraphId: number | null
  readonly filters: MonitorFilters
  readonly loading: boolean
  readonly error: string | null
  readonly onOpenChange: (open: boolean) => void
  readonly onFiltersChange: (filters: MonitorFilters) => void
  readonly onRefresh: () => void
  readonly onSelectGraph: (graphId: number) => void
}

export function ExecutionMonitorControlsDialog({
  open,
  graphs,
  selectedGraphId,
  filters,
  loading,
  error,
  onOpenChange,
  onFiltersChange,
  onRefresh,
  onSelectGraph,
}: ExecutionMonitorControlsDialogProps) {
  const triggerRef = useRef<HTMLButtonElement>(null)
  const filteredGraphs = graphs.filter((graph) => {
    if (filters.assistant && graph.assistant_id !== filters.assistant) return false
    const query = filters.search.trim().toLowerCase()
    return !query || [graph.title, graph.assistant_id, graph.status, String(graph.id), String(graph.thread_id ?? '')]
      .some((value) => value.toLowerCase().includes(query))
  })
  const stats = graphs.reduce((counts, graph) => ({
    ...counts,
    [statusClass(graph.status)]: (counts[statusClass(graph.status)] ?? 0) + 1,
  }), { running: 0, waiting: 0, completed: 0, failed: 0 } as Record<string, number>)

  return (
    <>
      <button
        ref={triggerRef}
        className="inline-flex size-11 shrink-0 items-center justify-center rounded-xl border border-border-subtle bg-bg-surface text-text-secondary transition-colors hover:border-cyan hover:text-cyan focus:outline-none focus:ring-2 focus:ring-cyan/60"
        type="button"
        aria-label="開啟執行控制"
        title="執行控制"
        onClick={() => onOpenChange(true)}
      >
        <Settings className="size-5" aria-hidden="true" />
      </button>

      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent
          className="max-h-[85vh] max-w-2xl overflow-y-auto border-border-subtle bg-bg-elevated text-text-primary"
          onCloseAutoFocus={(event) => {
            event.preventDefault()
            triggerRef.current?.focus()
          }}
        >
          <DialogHeader>
            <DialogTitle>執行控制</DialogTitle>
          </DialogHeader>
          {error && <div role="alert" className="rounded-xl border border-red/30 bg-red/10 p-3 text-sm text-red">{error}</div>}
          <section aria-labelledby="execution-status-heading">
            <h2 id="execution-status-heading" className="mb-3 text-base font-semibold text-text-primary">執行狀態</h2>
            <dl className="grid grid-cols-2 gap-3">
              <StatusCount label="執行中" value={stats.running ?? 0} />
              <StatusCount label="等待中" value={stats.waiting ?? 0} />
              <StatusCount label="已完成" value={stats.completed ?? 0} />
              <StatusCount label="失敗" value={stats.failed ?? 0} />
            </dl>
          </section>

          <section className="mt-6 border-t border-border-subtle pt-5" aria-labelledby="execution-filter-heading">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h2 id="execution-filter-heading" className="text-base font-semibold text-text-primary">篩選與搜尋</h2>
                <p className="mt-1 text-sm text-text-secondary">{filteredGraphs.length} 筆結果</p>
              </div>
              <button
                className="inline-flex h-11 shrink-0 items-center justify-center gap-2 rounded-xl border border-border-cyan bg-cyan-glow px-4 text-sm font-semibold text-text-cyan transition-colors hover:border-cyan hover:bg-cyan/20 focus:outline-none focus:ring-2 focus:ring-cyan/60 disabled:cursor-not-allowed disabled:opacity-50"
                type="button"
                onClick={onRefresh}
                disabled={loading}
              >
                <RefreshCw className={cn('size-4', loading && 'animate-spin')} aria-hidden="true" />
                {loading ? '重新整理中' : '重新整理'}
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="relative col-span-2">
                <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-cyan" aria-hidden="true" />
                <input id="graph-search" className={cn(searchInputClass, 'pl-10')} value={filters.search} onChange={(event) => onFiltersChange({ ...filters, search: event.target.value })} placeholder="搜尋圖形、代理或對話串" />
              </div>
              <input aria-label="依 Thread ID 篩選" className={searchInputClass} value={filters.thread} onChange={(event) => onFiltersChange({ ...filters, thread: event.target.value })} placeholder="Thread ID" />
              <input aria-label="依 Target ID 篩選" className={searchInputClass} value={filters.target} onChange={(event) => onFiltersChange({ ...filters, target: event.target.value })} placeholder="Target ID" />
              <select aria-label="依代理篩選" className={filterSelectClass} value={filters.assistant} onChange={(event) => onFiltersChange({ ...filters, assistant: event.target.value })}>
                <option value="">所有代理</option>
                {ASSISTANT_OPTIONS.map((assistant) => <option key={assistant} value={assistant}>{assistant}</option>)}
              </select>
              <select aria-label="依狀態篩選" className={filterSelectClass} value={filters.status} onChange={(event) => onFiltersChange({ ...filters, status: event.target.value })}>
                <option value="">所有狀態</option>
                {STATUS_OPTIONS.map((status) => <option key={status} value={status}>{status}</option>)}
              </select>
            </div>
          </section>

          <section className="mt-6 border-t border-border-subtle pt-5" aria-labelledby="execution-list-heading">
            <h2 id="execution-list-heading" className="mb-3 text-base font-semibold text-text-primary">執行清單</h2>
            {filteredGraphs.length === 0 ? (
              <p className="text-sm text-text-secondary">沒有符合目前搜尋與篩選條件的執行圖。</p>
            ) : (
              <div className="max-h-72 space-y-3 overflow-y-auto pr-1">
                {filteredGraphs.map((graph) => (
                  <button
                    key={graph.id}
                    type="button"
                    onClick={() => onSelectGraph(graph.id)}
                    className={cn(
                      'w-full rounded-xl border p-4 text-left text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-cyan/60',
                      selectedGraphId === graph.id
                        ? 'border-cyan bg-cyan-glow shadow-glow-cyan'
                        : 'border-border-subtle bg-bg-panel hover:border-border-normal hover:bg-bg-card-hover',
                    )}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <strong className="font-mono text-sm text-text-primary">Graph #{graph.id}</strong>
                      <span className={cn(statusBadgeClass, statusClass(graph.status))}>{graph.status}</span>
                    </div>
                    <p className="mt-3 line-clamp-2 text-sm leading-5 text-text-primary">{graph.title || graph.assistant_id}</p>
                    <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1 font-mono text-xs text-text-muted">
                      <span>thread {graph.thread_id ?? '-'}</span>
                      <span>{formatDuration(graph.started_at, graph.completed_at)}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </section>
        </DialogContent>
      </Dialog>
    </>
  )
}

function StatusCount({ label, value }: { readonly label: string; readonly value: number }) {
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-panel p-4">
      <dt className="text-sm text-text-secondary">{label}</dt>
      <dd className="mt-2 text-2xl font-semibold text-text-primary">{value}</dd>
    </div>
  )
}
