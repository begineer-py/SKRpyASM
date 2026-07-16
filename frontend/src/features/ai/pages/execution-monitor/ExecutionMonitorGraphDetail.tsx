import { useMemo } from 'react'
import { Network } from 'lucide-react'

import { cn } from '@/lib/utils'

import type { ExecutionGraphDetail, ExecutionNode } from '../../services/aiApi'
import { formatDuration, formatTime, statusClass } from './executionMonitorPresentation'

const panelClass = 'rounded-2xl bg-bg-card shadow-soft backdrop-blur-sm'
const statusBadgeClass = 'inline-flex items-center rounded-md border border-current/25 bg-black/20 px-2 py-1 font-mono text-xs font-semibold tracking-wide'

type ExecutionMonitorGraphDetailProps = {
  readonly graph: ExecutionGraphDetail
  readonly selectedNodeId: number | null
  readonly onNodeSelect: (nodeId: number) => void
}

export function ExecutionMonitorGraphDetail({ graph, selectedNodeId, onNodeSelect }: ExecutionMonitorGraphDetailProps) {
  const selectedNode = useMemo(() => graph.nodes.find((node) => node.id === selectedNodeId) ?? null, [graph.nodes, selectedNodeId])

  return (
    <main className={cn(panelClass, 'min-h-[560px] overflow-hidden xl:min-h-[calc(100vh-292px)]')}>
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border-subtle p-6">
        <div>
          <div className="flex items-center gap-2 font-mono text-xs font-semibold uppercase tracking-[0.12em] text-text-secondary">
            <Network className="size-3.5 text-cyan" aria-hidden="true" /> 執行圖
          </div>
          <h2 className="mt-2 text-xl font-semibold text-text-primary">Graph #{graph.id}</h2>
          <p className="mt-2 text-sm text-text-secondary">{graph.assistant_id} · thread {graph.thread_id ?? '-'} · started {formatTime(graph.started_at)}</p>
        </div>
        <span className={cn(statusBadgeClass, statusClass(graph.status))}>{graph.status}</span>
      </div>
      <div className="space-y-4 p-6">
        <div className="grid gap-3 sm:grid-cols-3">
          <Summary label="Nodes" value={graph.nodes.length} />
          <Summary label="Events" value={graph.events.length} />
          <Summary label="Artifacts" value={graph.artifacts.length} />
        </div>
        <div className="grid gap-3">
          {graph.nodes.map((node) => (
            <NodeButton key={node.id} node={node} selected={selectedNodeId === node.id} onSelect={onNodeSelect} />
          ))}
          {graph.nodes.length === 0 && <div className="rounded-xl border border-dashed border-border-normal bg-bg-panel p-6 text-sm text-text-secondary">這次執行尚未記錄任何節點。</div>}
        </div>
        {selectedNode && <SelectedNodeDetail node={selectedNode} />}
      </div>
    </main>
  )
}

function NodeButton({ node, selected, onSelect }: { readonly node: ExecutionNode; readonly selected: boolean; readonly onSelect: (nodeId: number) => void }) {
  return (
    <button
      type="button"
      onClick={() => onSelect(node.id)}
      className={cn(
        'rounded-xl border p-4 text-left transition-colors focus:outline-none focus:ring-2 focus:ring-green/60',
        selected
          ? 'border-green bg-green-glow shadow-glow-green'
          : 'border-border-subtle bg-bg-panel hover:border-border-normal hover:bg-bg-card-hover',
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <strong className="text-sm text-text-primary">#{node.sequence} {node.name}</strong>
        <span className={cn(statusBadgeClass, statusClass(node.status))}>{node.status}</span>
      </div>
      <p className="mt-2 text-sm text-text-secondary">{node.kind} · id {node.id} · task {node.external_task_id || '-'} · {formatDuration(node.started_at, node.completed_at)}</p>
      {node.wait_reason && <p className="mt-2 text-sm text-purple">等待原因：{node.wait_reason}</p>}
    </button>
  )
}

function SelectedNodeDetail({ node }: { readonly node: ExecutionNode }) {
  return (
    <section className="rounded-xl border border-border-subtle bg-bg-panel p-4">
      <h3 className="text-base font-semibold text-text-primary">選取節點資料</h3>
      <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border border-border-subtle bg-bg-base p-4 font-mono text-sm leading-6 text-text-secondary">{JSON.stringify({ input: node.input, output: node.output, error: node.error }, null, 2)}</pre>
    </section>
  )
}

function Summary({ label, value }: { readonly label: string; readonly value: number }) {
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-panel p-4">
      <p className="font-mono text-xs uppercase tracking-[0.12em] text-text-muted">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-text-primary">{value}</p>
    </div>
  )
}
