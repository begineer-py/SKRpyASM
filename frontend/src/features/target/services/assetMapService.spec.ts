import { beforeEach, describe, expect, it, vi } from 'vitest'
import { GetTargetAssetMapDocument } from '@/gql/graphql'
import { executeGraphQL } from '@/services/gqlClient'
import { projectGraph, type AssetMapRawResult } from '../assetMap/projectGraph'
import type { AssetMapGraph } from '../assetMap/types'
import { AssetMapLoadError, loadTargetAssetMap } from './assetMapService'

vi.mock('@/services/gqlClient', () => ({
  executeGraphQL: vi.fn(),
}))

vi.mock('../assetMap/projectGraph', () => ({
  projectGraph: vi.fn(),
}))

const executeGraphQLMock = vi.mocked(executeGraphQL)
const projectGraphMock = vi.mocked(projectGraph)

function rawResult(): AssetMapRawResult {
  return {
    target: { id: 7, name: 'example.com', description: 'Scoped target' },
    seeds: [],
    seeds_aggregate: { aggregate: { count: 0 } },
    subdomains: [],
    subdomains_aggregate: { aggregate: { count: 0 } },
    ips: [],
    ips_aggregate: { aggregate: { count: 0 } },
    ports: [],
    ports_aggregate: { aggregate: { count: 0 } },
    urls: [],
    urls_aggregate: { aggregate: { count: 0 } },
    asset_edges: [],
    asset_edges_aggregate: { aggregate: { count: 0 } },
    actions: [],
    actions_aggregate: { aggregate: { count: 0 } },
    action_asset_links: [],
    action_asset_links_aggregate: { aggregate: { count: 0 } },
    asset_locks: [],
    asset_locks_aggregate: { aggregate: { count: 0 } },
  }
}

function projectedGraph(): AssetMapGraph {
  return {
    targetId: 'asset:target:7',
    nodes: [],
    edges: [],
    diagnostics: {
      isTruncated: false,
      truncatedByKind: { target: 0, seed: 0, subdomain: 0, ip: 0, port: 0, url: 0 },
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
  }
}

describe('loadTargetAssetMap', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('dispatches the fixed target query and returns the projector result', async () => {
    // Given
    const raw = rawResult()
    const graph = projectedGraph()
    executeGraphQLMock.mockResolvedValueOnce(raw)
    projectGraphMock.mockReturnValueOnce(graph)

    // When
    const result = await loadTargetAssetMap(7)

    // Then
    expect(executeGraphQLMock).toHaveBeenCalledOnce()
    expect(executeGraphQLMock).toHaveBeenCalledWith(GetTargetAssetMapDocument, { targetId: 7 })
    expect(projectGraphMock).toHaveBeenCalledWith(raw)
    expect(result).toBe(graph)
  })

  it.each([0, -1, 1.5])('rejects target ID %d before dispatch', async (targetId) => {
    // Given
    const request = loadTargetAssetMap(targetId)

    // When / Then
    await expect(request).rejects.toMatchObject({
      name: 'AssetMapLoadError',
      kind: 'invalid_target',
    } satisfies Partial<AssetMapLoadError>)
    expect(executeGraphQLMock).not.toHaveBeenCalled()
  })

  it('maps a GraphQL rejection to a typed load error instead of a graph', async () => {
    // Given
    const failure = new Error('Hasura unavailable')
    executeGraphQLMock.mockRejectedValueOnce(failure)

    // When / Then
    await expect(loadTargetAssetMap(7)).rejects.toMatchObject({
      name: 'AssetMapLoadError',
      kind: 'load_failed',
      cause: failure,
    } satisfies Partial<AssetMapLoadError>)
    expect(projectGraphMock).not.toHaveBeenCalled()
  })

  it('rejects an already-aborted request before GraphQL dispatch', async () => {
    // Given
    const controller = new AbortController()
    controller.abort()

    // When / Then
    await expect(loadTargetAssetMap(7, { signal: controller.signal })).rejects.toMatchObject({
      name: 'AssetMapLoadError',
      kind: 'aborted',
    } satisfies Partial<AssetMapLoadError>)
    expect(executeGraphQLMock).not.toHaveBeenCalled()
  })

  it('rejects an in-flight request when its signal aborts', async () => {
    // Given
    const controller = new AbortController()
    executeGraphQLMock.mockReturnValueOnce(new Promise<AssetMapRawResult>(() => undefined))
    const request = loadTargetAssetMap(7, { signal: controller.signal })

    // When
    controller.abort()

    // Then
    await expect(request).rejects.toMatchObject({
      name: 'AssetMapLoadError',
      kind: 'aborted',
    } satisfies Partial<AssetMapLoadError>)
    expect(executeGraphQLMock).toHaveBeenCalledWith(GetTargetAssetMapDocument, { targetId: 7 })
    expect(projectGraphMock).not.toHaveBeenCalled()
  })
})
