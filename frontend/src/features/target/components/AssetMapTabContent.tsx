import { useCallback, useEffect, useState } from 'react'
import { RefreshCw, Settings2 } from 'lucide-react'
import AssetTopologyMap from '@/components/AssetTopologyMap'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  ASSET_KINDS,
  ASSET_MAP_DIAGNOSTIC_REASONS,
  type AssetKind,
  type AssetMapDiagnosticReason,
  type AssetMapGraph,
  type AssetMapNode,
} from '../assetMap/types'
import { AssetMapLoadError, loadTargetAssetMap } from '../services/assetMapService'
import { AssetMapInspector } from './AssetMapInspector'

interface AssetMapTabContentProps {
  readonly targetId: number
}

type AssetMapViewState =
  | { readonly kind: 'loading' }
  | { readonly kind: 'error'; readonly error: AssetMapLoadError }
  | { readonly kind: 'not_found' }
  | { readonly kind: 'empty' }
  | { readonly kind: 'ready'; readonly graph: AssetMapGraph }

const ASSET_KIND_LABELS = {
  ip: 'IP assets',
  port: 'Ports',
  seed: 'Seeds',
  subdomain: 'Subdomains',
  target: 'Target',
  url: 'URLs',
} as const satisfies Record<AssetKind, string>

const DIAGNOSTIC_REASON_LABELS = {
  cross_target: 'Cross-target relations skipped',
  duplicate_edge: 'Duplicate edges skipped',
  graph_edge_cap: 'Graph edge cap reached',
  graph_node_cap: 'Graph node cap reached',
  malformed_relation: 'Malformed relations skipped',
  missing_asset: 'Missing assets skipped',
  url_with_too_many_related_subdomains: 'URLs with too many related subdomains skipped',
  url_without_related_subdomains: 'URLs without related subdomains skipped',
} as const satisfies Record<AssetMapDiagnosticReason, string>

function hasDiscoveredAssets(graph: AssetMapGraph): boolean {
  return graph.nodes.some((node) => node.kind !== 'target')
}

function nonZeroDiagnosticEntries<T extends string>(
  keys: readonly T[],
  values: Readonly<Record<T, number>>,
): readonly [T, number][] {
  return keys.flatMap((key) => values[key] > 0 ? [[key, values[key]] as const] : [])
}

function displayLoadError(error: AssetMapLoadError): string {
  switch (error.kind) {
    case 'invalid_target':
      return 'This target identifier is invalid. Return to Targets and choose a valid target.'
    case 'load_failed':
      return 'The asset map could not be loaded. Check the connection and try again.'
    case 'aborted':
      return 'The asset map request was interrupted. Try loading the map again.'
  }
}

function AssetMapDiagnostics({ graph }: { readonly graph: AssetMapGraph }) {
  const truncatedEntries = nonZeroDiagnosticEntries(ASSET_KINDS, graph.diagnostics.truncatedByKind)
  const skippedEntries = nonZeroDiagnosticEntries(ASSET_MAP_DIAGNOSTIC_REASONS, graph.diagnostics.skippedByReason)

  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          type="button"
          className="c2-btn c2-btn--ghost c2-btn--icon"
          aria-label="Asset map settings and diagnostics"
          title="Asset map settings and diagnostics"
        >
          <Settings2 aria-hidden="true" size={18} />
        </button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Asset map diagnostics</DialogTitle>
          <DialogDescription>
            Fixed data bounds keep this map readable. Diagnostics explain any omitted or malformed relations.
          </DialogDescription>
        </DialogHeader>
        {graph.diagnostics.isTruncated ? (
          <p className="rounded-xl border border-border-normal bg-bg-surface p-4 text-sm text-text-secondary">
            Some asset-map results were truncated.
          </p>
        ) : (
          <p className="rounded-xl border border-border-subtle bg-bg-surface p-4 text-sm text-text-secondary">
            The current map is within its fixed data bounds.
          </p>
        )}
        <section className="dialog-section" aria-labelledby="asset-map-truncation-heading">
          <div className="dialog-section__header">
            <h2 id="asset-map-truncation-heading">Truncated asset types</h2>
          </div>
          {truncatedEntries.length > 0 ? (
            <dl className="dialog-stat-grid">
              {truncatedEntries.map(([kind, count]) => (
                <div key={kind} className="dialog-stat">
                  <dt>{ASSET_KIND_LABELS[kind]}</dt>
                  <dd><strong>{count}</strong></dd>
                </div>
              ))}
            </dl>
          ) : <p className="text-sm text-text-secondary">No asset types were truncated.</p>}
        </section>
        <section className="dialog-section border-b-0 pb-0" aria-labelledby="asset-map-skipped-heading">
          <div className="dialog-section__header">
            <h2 id="asset-map-skipped-heading">Skipped relations</h2>
          </div>
          {skippedEntries.length > 0 ? (
            <dl className="dialog-stat-grid">
              {skippedEntries.map(([reason, count]) => (
                <div key={reason} className="dialog-stat">
                  <dt>{DIAGNOSTIC_REASON_LABELS[reason]}</dt>
                  <dd><strong>{count}</strong></dd>
                </div>
              ))}
            </dl>
          ) : <p className="text-sm text-text-secondary">No relations were skipped.</p>}
        </section>
      </DialogContent>
    </Dialog>
  )
}

export function AssetMapTabContent({ targetId }: AssetMapTabContentProps) {
  const [loadAttempt, setLoadAttempt] = useState(0)
  const [viewState, setViewState] = useState<AssetMapViewState>({ kind: 'loading' })
  const [selectedNode, setSelectedNode] = useState<AssetMapNode | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setViewState({ kind: 'loading' })
    setSelectedNode(null)

    void loadTargetAssetMap(targetId, { signal: controller.signal })
      .then((graph) => {
        if (graph === null) {
          setViewState({ kind: 'not_found' })
          return
        }
        setViewState(hasDiscoveredAssets(graph) ? { kind: 'ready', graph } : { kind: 'empty' })
      })
      .catch((error: unknown) => {
        if (error instanceof AssetMapLoadError && error.kind === 'aborted') return
        setViewState({
          kind: 'error',
          error: error instanceof AssetMapLoadError ? error : new AssetMapLoadError('load_failed', { cause: error }),
        })
      })

    return () => controller.abort()
  }, [loadAttempt, targetId])

  const retry = useCallback(() => {
    setLoadAttempt((attempt) => attempt + 1)
  }, [])

  switch (viewState.kind) {
    case 'loading':
      return <div className="c2-loading" role="status">Loading asset map…</div>
    case 'error':
      return (
        <div className="c2-empty" role="alert">
          <p>{displayLoadError(viewState.error)}</p>
          <button type="button" className="c2-btn c2-btn--primary mt-5" onClick={retry}>
            <RefreshCw aria-hidden="true" size={16} />Retry loading asset map
          </button>
        </div>
      )
    case 'not_found':
      return (
        <div className="c2-empty">
          <p>This target was not found or is no longer available.</p>
          <p className="mt-3">Return to Targets to choose an available target.</p>
        </div>
      )
    case 'empty':
      return (
        <div className="c2-empty">
          <p>No discovered assets are available yet.</p>
          <p className="mt-3">Add a seed or run reconnaissance to populate this map.</p>
        </div>
      )
    case 'ready':
      return (
        <section aria-label="Target asset map" className="flex flex-col gap-5">
          <div className="flex justify-end">
            <AssetMapDiagnostics graph={viewState.graph} />
          </div>
          {viewState.graph.diagnostics.isTruncated ? (
            <p className="rounded-xl border border-border-normal bg-bg-surface p-4 text-sm text-text-secondary">
              Some asset-map results were truncated. Open diagnostics for details.
            </p>
          ) : null}
          <AssetTopologyMap
            graph={viewState.graph}
            selectedNodeId={selectedNode?.id ?? null}
            onSelectNode={setSelectedNode}
          />
          {selectedNode ? <AssetMapInspector node={selectedNode} onClose={() => setSelectedNode(null)} /> : null}
        </section>
      )
  }
}
