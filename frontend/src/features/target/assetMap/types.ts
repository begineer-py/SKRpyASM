export const ASSET_KINDS = ['target', 'seed', 'subdomain', 'ip', 'port', 'url'] as const

export type AssetKind = (typeof ASSET_KINDS)[number]

export type AssetMapNodeId<K extends AssetKind = AssetKind> = `asset:${K}:${string}`

export const ASSET_MAP_EDGE_KINDS = [
  'target_seed',
  'target_subdomain',
  'target_ip',
  'subdomain_ip',
  'ip_port',
  'subdomain_url',
  'explicit',
] as const

export type AssetMapEdgeKind = (typeof ASSET_MAP_EDGE_KINDS)[number]

export type AssetMapEdgeId<K extends AssetMapEdgeKind = AssetMapEdgeKind> =
  `edge:${K}:${AssetMapNodeId}:${AssetMapNodeId}`

export const ASSET_ACTION_STATUSES = ['pending', 'running', 'completed', 'failed', 'cancelled', 'unknown'] as const

export type AssetActionStatus = (typeof ASSET_ACTION_STATUSES)[number]

export type AssetPlanSummary = {
  readonly id: `plan:${string}`
  readonly objective: string
  readonly status: AssetActionStatus
}

export type AssetActionSummary = {
  readonly id: `action:${string}`
  readonly planId: AssetPlanSummary['id'] | null
  readonly purpose: string | null
  readonly status: AssetActionStatus
  readonly resultSummary: string | null
  readonly order: number
  readonly isActive: boolean
}

export type AssetMapMetadataValue = string | number | boolean | null

export type AssetMapNodeMetadata = {
  readonly attributes: Readonly<Record<string, AssetMapMetadataValue>>
  readonly plans: readonly AssetPlanSummary[]
  readonly actions: readonly AssetActionSummary[]
  readonly isActive: boolean
}

export type AssetMapNode<K extends AssetKind = AssetKind> = K extends AssetKind
  ? {
      readonly id: AssetMapNodeId<K>
      readonly kind: K
      readonly label: string
      readonly metadata: AssetMapNodeMetadata
    }
  : never

export type AssetMapEdge<K extends AssetMapEdgeKind = AssetMapEdgeKind> = K extends AssetMapEdgeKind
  ? {
      readonly id: AssetMapEdgeId<K>
      readonly source: AssetMapNodeId
      readonly target: AssetMapNodeId
      readonly kind: K
      readonly label: string | null
    }
  : never

export const ASSET_MAP_QUERY_MAXIMUMS = {
  seeds: 30,
  subdomains: 80,
  subdomainIps: 5,
  ips: 80,
  ports: 80,
  urls: 60,
  urlRelatedSubdomains: 3,
  assetEdges: 200,
  actions: 100,
  actionAssetLinks: 200,
  assetLocks: 20,
} as const

export const MAX_GRAPH_NODES = 400
export const MAX_GRAPH_EDGES = 800

export const ASSET_MAP_DIAGNOSTIC_REASONS = [
  'cross_target',
  'malformed_relation',
  'missing_asset',
  'duplicate_edge',
  'url_without_related_subdomains',
  'url_with_too_many_related_subdomains',
  'graph_node_cap',
  'graph_edge_cap',
] as const

export type AssetMapDiagnosticReason = (typeof ASSET_MAP_DIAGNOSTIC_REASONS)[number]

export type AssetMapDiagnostics = {
  readonly isTruncated: boolean
  readonly truncatedByKind: Readonly<Record<AssetKind, number>>
  readonly skippedByReason: Readonly<Record<AssetMapDiagnosticReason, number>>
}

export type AssetMapGraph = {
  readonly targetId: AssetMapNodeId<'target'>
  readonly nodes: readonly AssetMapNode[]
  readonly edges: readonly AssetMapEdge[]
  readonly diagnostics: AssetMapDiagnostics
}
