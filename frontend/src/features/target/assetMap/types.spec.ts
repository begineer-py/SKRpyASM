import { describe, expect, it } from 'vitest'
import {
  ASSET_KINDS,
  ASSET_MAP_QUERY_MAXIMUMS,
  MAX_GRAPH_EDGES,
  MAX_GRAPH_NODES,
  type AssetMapGraph,
  type AssetMapNode,
  type AssetMapNodeMetadata,
} from './types'

const inactiveMetadata = {
  attributes: {},
  plans: [],
  actions: [],
  isActive: false,
} as const satisfies AssetMapNodeMetadata

const activePortMetadata = {
  attributes: { portNumber: 443, protocol: 'tcp' },
  plans: [{ id: 'plan:7', objective: 'Verify HTTPS exposure', status: 'running' }],
  actions: [
    {
      id: 'action:12',
      planId: 'plan:7',
      purpose: 'Confirm TLS configuration',
      status: 'running',
      resultSummary: null,
      order: 1,
      isActive: true,
    },
  ],
  isActive: true,
} as const satisfies AssetMapNodeMetadata

const nodeFixtures = [
  { id: 'asset:target:1', kind: 'target', label: 'Example target', metadata: inactiveMetadata },
  { id: 'asset:seed:2', kind: 'seed', label: 'example.com', metadata: inactiveMetadata },
  { id: 'asset:subdomain:3', kind: 'subdomain', label: 'api.example.com', metadata: inactiveMetadata },
  { id: 'asset:ip:4', kind: 'ip', label: '192.0.2.10', metadata: inactiveMetadata },
  { id: 'asset:port:5', kind: 'port', label: '443/tcp', metadata: activePortMetadata },
  { id: 'asset:url:6', kind: 'url', label: 'https://api.example.com', metadata: inactiveMetadata },
] as const satisfies readonly AssetMapNode[]

const graphFixture = {
  targetId: 'asset:target:1',
  nodes: nodeFixtures,
  edges: [
    {
      id: 'edge:target_seed:asset:target:1:asset:seed:2',
      source: 'asset:target:1',
      target: 'asset:seed:2',
      kind: 'target_seed',
      label: 'seed',
    },
  ],
  diagnostics: {
    isTruncated: false,
    truncatedByKind: {
      target: 0,
      seed: 0,
      subdomain: 0,
      ip: 0,
      port: 0,
      url: 0,
    },
    skippedByReason: {
      cross_target: 0,
      malformed_relation: 0,
      missing_asset: 0,
      duplicate_edge: 0,
      url_without_related_subdomains: 0,
      url_with_too_many_related_subdomains: 0,
      graph_node_cap: 0,
      graph_edge_cap: 0,
    },
  },
} as const satisfies AssetMapGraph

describe('AssetMapGraph neutral contract', () => {
  it('accepts all six graphable asset kinds within the fixed graph bounds', () => {
    // Given
    const nodeKinds = graphFixture.nodes.map((node) => node.kind)

    // When / Then
    expect(nodeKinds).toEqual([...ASSET_KINDS])
    expect(MAX_GRAPH_NODES).toBe(400)
    expect(MAX_GRAPH_EDGES).toBe(800)
    expect(ASSET_MAP_QUERY_MAXIMUMS).toEqual({
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
    })
  })

  it('keeps plans and actions in asset metadata instead of graph nodes', () => {
    // Given
    const portNode = graphFixture.nodes[4]

    // When
    const action = portNode.metadata.actions[0]

    // Then
    expect(portNode.kind).toBe('port')
    expect(action).toMatchObject({ id: 'action:12', status: 'running', isActive: true })
    expect(graphFixture.nodes).toHaveLength(6)
  })
})
