import type { AssetKind, AssetMapDiagnostics, AssetMapEdge, AssetMapGraph, AssetMapNode, AssetMapNodeId, AssetMapNodeMetadata } from '../target/assetMap/types'
import type { TargetTopology, TopologyNode } from './services/aiApi'

export type LegacyTopologyAdapterResult = {
  readonly graph: AssetMapGraph
  readonly graphNodeIdsByLegacyId: ReadonlyMap<string, AssetMapNodeId>
  readonly legacyNodesByGraphId: ReadonlyMap<AssetMapNodeId, TopologyNode>
}

function normalizeKind(type: string): AssetKind {
  switch (type.toLowerCase()) {
    case 'target': return 'target'
    case 'seed': return 'seed'
    case 'subdomain': return 'subdomain'
    case 'ip': return 'ip'
    case 'port': return 'port'
    case 'url': return 'url'
    default: return 'url'
  }
}

type AdaptedNode = {
  readonly id: AssetMapNodeId
  readonly node: AssetMapNode
}

function nodeSuffix(node: TopologyNode, kind: AssetKind): string {
  return node.type.toLowerCase() === kind ? node.id : `${node.type}:${node.id}`
}

function targetGraphNodeId(node: TopologyNode): AssetMapNodeId<'target'> {
  return `asset:target:${nodeSuffix(node, 'target')}`
}

function fallbackTargetGraphNodeId(targetId: number): AssetMapNodeId<'target'> {
  return `asset:target:${targetId}`
}

function metadata(node: TopologyNode, activeLegacyNodeIds: ReadonlySet<string>): AssetMapNodeMetadata {
  return {
    actions: [],
    attributes: {
      assetId: node.asset_id ?? null,
      legacyType: node.type,
    },
    isActive: node.is_active_attack === true || activeLegacyNodeIds.has(node.id),
    plans: [],
  }
}

function normalizedNode(node: TopologyNode, kind: AssetKind, nodeMetadata: AssetMapNodeMetadata): AdaptedNode {
  switch (kind) {
    case 'target': {
      const id = targetGraphNodeId(node)
      return { id, node: { id, kind: 'target', label: node.label, metadata: nodeMetadata } }
    }
    case 'seed': {
      const id: AssetMapNodeId<'seed'> = `asset:seed:${nodeSuffix(node, kind)}`
      return { id, node: { id, kind: 'seed', label: node.label, metadata: nodeMetadata } }
    }
    case 'subdomain': {
      const id: AssetMapNodeId<'subdomain'> = `asset:subdomain:${nodeSuffix(node, kind)}`
      return { id, node: { id, kind: 'subdomain', label: node.label, metadata: nodeMetadata } }
    }
    case 'ip': {
      const id: AssetMapNodeId<'ip'> = `asset:ip:${nodeSuffix(node, kind)}`
      return { id, node: { id, kind: 'ip', label: node.label, metadata: nodeMetadata } }
    }
    case 'port': {
      const id: AssetMapNodeId<'port'> = `asset:port:${nodeSuffix(node, kind)}`
      return { id, node: { id, kind: 'port', label: node.label, metadata: nodeMetadata } }
    }
    case 'url': {
      const id: AssetMapNodeId<'url'> = `asset:url:${nodeSuffix(node, kind)}`
      return { id, node: { id, kind: 'url', label: node.label, metadata: nodeMetadata } }
    }
  }
}

function emptyDiagnostics(): AssetMapDiagnostics {
  return {
    isTruncated: false,
    skippedByReason: {
      cross_target: 0,
      duplicate_edge: 0,
      graph_edge_cap: 0,
      graph_node_cap: 0,
      malformed_relation: 0,
      missing_asset: 0,
      url_with_too_many_related_subdomains: 0,
      url_without_related_subdomains: 0,
    },
    truncatedByKind: {
      ip: 0,
      port: 0,
      seed: 0,
      subdomain: 0,
      target: 0,
      url: 0,
    },
  }
}

export function adaptLegacyTopology(topology: TargetTopology): LegacyTopologyAdapterResult {
  const activeLegacyNodeIds = new Set(
    topology.active_attacks.flatMap((attack) => attack.node_id === undefined || attack.node_id === null ? [] : [attack.node_id]),
  )
  const graphNodeIdsByLegacyId = new Map<string, AssetMapNodeId>()
  const legacyNodesByGraphId = new Map<AssetMapNodeId, TopologyNode>()
  const nodes: AssetMapNode[] = []

  for (const node of topology.nodes) {
    const kind = normalizeKind(node.type)
    const adaptedNode = normalizedNode(node, kind, metadata(node, activeLegacyNodeIds))
    const { id } = adaptedNode
    if (legacyNodesByGraphId.has(id)) continue
    graphNodeIdsByLegacyId.set(node.id, id)
    legacyNodesByGraphId.set(id, node)
    nodes.push(adaptedNode.node)
  }

  const targetNode = topology.nodes.find((node) => node.type.toLowerCase() === 'target')
  const targetId = targetNode === undefined
    ? fallbackTargetGraphNodeId(topology.target_id)
    : targetGraphNodeId(targetNode)

  if (targetId === undefined) {
    return {
      graph: {
        diagnostics: emptyDiagnostics(),
        edges: [],
        nodes: [],
        targetId: fallbackTargetGraphNodeId(topology.target_id),
      },
      graphNodeIdsByLegacyId,
      legacyNodesByGraphId,
    }
  }

  const edges: AssetMapEdge[] = []
  for (const edge of topology.edges) {
    const source = graphNodeIdsByLegacyId.get(edge.source)
    const target = graphNodeIdsByLegacyId.get(edge.target)
    if (source === undefined || target === undefined) continue
    edges.push({
      id: `edge:explicit:${source}:${target}`,
      kind: 'explicit',
      label: edge.edge_type || null,
      source,
      target,
    })
  }

  return {
    graph: {
      diagnostics: emptyDiagnostics(),
      edges,
      nodes,
      targetId,
    },
    graphNodeIdsByLegacyId,
    legacyNodesByGraphId,
  }
}
