import { Activity, LockKeyhole, X } from 'lucide-react'
import type { AssetActionStatus, AssetMapMetadataValue, AssetMapNode } from '../assetMap/types'

interface AssetMapInspectorProps {
  readonly node: AssetMapNode
  readonly onClose: () => void
}

const STATUS_BADGE_CLASS = {
  cancelled: 'c2-badge--muted',
  completed: 'c2-badge--green',
  failed: 'c2-badge--red',
  pending: 'c2-badge--amber',
  running: 'c2-badge--cyan',
  unknown: 'c2-badge--muted',
} as const satisfies Record<AssetActionStatus, string>

const LOCK_ATTRIBUTE_KEYS = new Set(['lockStatus', 'lockAgentRole', 'lockAcquiredAt'])

function statusBadgeClass(status: AssetActionStatus): string {
  return STATUS_BADGE_CLASS[status]
}

function displayValue(value: AssetMapMetadataValue): string {
  return value === null ? 'Not recorded' : String(value)
}

function displayAttributeName(attribute: string): string {
  return attribute.replace(/([A-Z])/g, ' $1').replace(/^./, (value) => value.toUpperCase())
}

export function AssetMapInspector({ node, onClose }: AssetMapInspectorProps) {
  if (node.kind === 'target' || node.kind === 'seed') return null

  const lockStatus = node.metadata.attributes.lockStatus
  const lockAgentRole = node.metadata.attributes.lockAgentRole
  const unlockedAttributes = Object.entries(node.metadata.attributes)
    .filter(([key]) => !LOCK_ATTRIBUTE_KEYS.has(key))

  return (
    <aside
      aria-labelledby={`asset-map-inspector-${node.id}`}
      className="rounded-2xl border border-border-subtle bg-bg-card p-5 shadow-soft"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-mono text-xs text-text-muted">Selected asset</p>
          <h2 id={`asset-map-inspector-${node.id}`} className="mt-2 break-all text-lg font-semibold text-text-primary">
            {node.label}
          </h2>
        </div>
        <div className="flex items-center gap-3">
          <span className="c2-badge c2-badge--cyan">{node.kind}</span>
          <button
            type="button"
            className="c2-btn c2-btn--ghost c2-btn--icon"
            aria-label="Close asset inspector"
            onClick={onClose}
          >
            <X aria-hidden="true" size={18} />
          </button>
        </div>
      </div>

      {node.metadata.isActive ? (
        <div className="mt-5 flex items-center gap-3 rounded-xl border border-border-cyan bg-bg-surface p-4 text-sm text-text-primary">
          <Activity aria-hidden="true" className="shrink-0 text-cyan" size={18} />
          <span>Active operation</span>
        </div>
      ) : null}

      {lockStatus === 'HELD' ? (
        <div className="mt-4 flex items-center gap-3 rounded-xl border border-border-subtle bg-bg-surface p-4 text-sm text-text-secondary">
          <LockKeyhole aria-hidden="true" className="shrink-0 text-cyan" size={18} />
          <span>HELD{typeof lockAgentRole === 'string' && lockAgentRole ? ` by ${lockAgentRole}` : ''}</span>
        </div>
      ) : null}

      {unlockedAttributes.length > 0 ? (
        <section className="mt-5 border-t border-border-subtle pt-5" aria-labelledby={`asset-map-attributes-${node.id}`}>
          <h3 id={`asset-map-attributes-${node.id}`} className="text-sm font-semibold text-text-primary">Metadata</h3>
          <dl className="mt-3 grid gap-3 sm:grid-cols-2">
            {unlockedAttributes.map(([key, value]) => (
              <div key={key} className="rounded-xl border border-border-subtle bg-bg-surface p-3">
                <dt className="font-mono text-xs text-text-muted">{displayAttributeName(key)}</dt>
                <dd className="mt-2 break-words text-sm text-text-primary">{displayValue(value)}</dd>
              </div>
            ))}
          </dl>
        </section>
      ) : null}

      {node.metadata.plans.length > 0 ? (
        <section className="mt-5 border-t border-border-subtle pt-5" aria-labelledby={`asset-map-plans-${node.id}`}>
          <h3 id={`asset-map-plans-${node.id}`} className="text-sm font-semibold text-text-primary">Plans</h3>
          <div className="mt-3 flex flex-col gap-3">
            {node.metadata.plans.map((plan) => (
              <div key={plan.id} className="rounded-xl border border-border-subtle bg-bg-surface p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-mono text-xs text-text-muted">{plan.id}</span>
                  <span className={`c2-badge ${statusBadgeClass(plan.status)}`}>{plan.status}</span>
                </div>
                <p className="mt-3 text-sm text-text-primary">{plan.objective}</p>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {node.metadata.actions.length > 0 ? (
        <section className="mt-5 border-t border-border-subtle pt-5" aria-labelledby={`asset-map-actions-${node.id}`}>
          <h3 id={`asset-map-actions-${node.id}`} className="text-sm font-semibold text-text-primary">Actions</h3>
          <div className="mt-3 flex flex-col gap-3">
            {node.metadata.actions.map((action) => (
              <div key={action.id} className="rounded-xl border border-border-subtle bg-bg-surface p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-mono text-xs text-text-muted">{action.id}</span>
                  <span className={`c2-badge ${statusBadgeClass(action.status)}`}>{action.status}</span>
                </div>
                {action.purpose ? <p className="mt-3 text-sm text-text-primary">{action.purpose}</p> : null}
                {action.resultSummary ? <p className="mt-3 text-sm text-text-secondary">{action.resultSummary}</p> : null}
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </aside>
  )
}
