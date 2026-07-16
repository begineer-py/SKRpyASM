import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { AssetMapGraph, AssetMapNode } from '../assetMap/types'
import { AssetMapLoadError, loadTargetAssetMap } from '../services/assetMapService'
import { AssetMapTabContent } from './AssetMapTabContent'

vi.mock('@/components/AssetTopologyMap', () => ({
  default: vi.fn(({ graph, onSelectNode }: {
    readonly graph: AssetMapGraph | null
    readonly onSelectNode?: (node: AssetMapNode) => void
  }) => (
    <div data-testid="topology-map">
      {graph?.nodes.map((node) => (
        <button key={node.id} type="button" onClick={() => onSelectNode?.(node)}>
          Select {node.label}
        </button>
      ))}
    </div>
  )),
}))

vi.mock('../services/assetMapService', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/assetMapService')>()
  return { ...actual, loadTargetAssetMap: vi.fn() }
})

const loadTargetAssetMapMock = vi.mocked(loadTargetAssetMap)

const graph = {
  targetId: 'asset:target:7',
  nodes: [
    {
      id: 'asset:target:7',
      kind: 'target',
      label: 'Example target',
      metadata: { attributes: {}, plans: [], actions: [], isActive: false },
    },
    {
      id: 'asset:seed:8',
      kind: 'seed',
      label: 'DOMAIN:example.test',
      metadata: { attributes: {}, plans: [], actions: [], isActive: false },
    },
    {
      id: 'asset:port:9',
      kind: 'port',
      label: '443/tcp',
      metadata: {
        attributes: { lockStatus: 'HELD', lockAgentRole: 'recon', protocol: 'tcp' },
        plans: [{ id: 'plan:10', objective: 'Verify HTTPS exposure', status: 'running' }],
        actions: [{
          id: 'action:11',
          planId: 'plan:10',
          purpose: 'Confirm TLS configuration',
          status: 'running',
          resultSummary: 'TLS is configured',
          order: 1,
          isActive: true,
        }],
        isActive: true,
      },
    },
  ],
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
} as const satisfies AssetMapGraph

function truncatedGraph(): AssetMapGraph {
  return {
    ...graph,
    diagnostics: {
      ...graph.diagnostics,
      isTruncated: true,
      truncatedByKind: { ...graph.diagnostics.truncatedByKind, subdomain: 12 },
      skippedByReason: { ...graph.diagnostics.skippedByReason, malformed_relation: 3 },
    },
  }
}

function emptyGraph(): AssetMapGraph {
  return {
    ...graph,
    nodes: graph.nodes.filter((node) => node.kind === 'target'),
  }
}

describe('AssetMapTabContent', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders an explicit loading state then inspects a selected normalized asset', async () => {
    // Given
    let resolveGraph: ((value: AssetMapGraph) => void) | undefined
    loadTargetAssetMapMock.mockReturnValueOnce(new Promise((resolve) => {
      resolveGraph = resolve
    }))
    const user = userEvent.setup()
    render(<AssetMapTabContent targetId={7} />)

    // When
    expect(screen.getByRole('status')).toHaveTextContent('Loading asset map')
    resolveGraph?.(graph)
    await user.click(await screen.findByRole('button', { name: 'Select 443/tcp' }))

    // Then
    expect(screen.getByRole('heading', { name: '443/tcp' })).toBeVisible()
    expect(screen.getByText('port')).toBeVisible()
    expect(screen.getByText('Active operation')).toBeVisible()
    expect(screen.getByText('HELD by recon')).toBeVisible()
    expect(screen.getByText('Verify HTTPS exposure')).toBeVisible()
    expect(screen.getByText('Confirm TLS configuration')).toBeVisible()
    expect(screen.getByText('TLS is configured')).toBeVisible()

    // When
    await user.click(screen.getByRole('button', { name: 'Close asset inspector' }))

    // Then
    expect(screen.queryByRole('complementary')).not.toBeInTheDocument()
  })

  it('does not reserve an action-detail inspector for Target or seed selections', async () => {
    // Given
    loadTargetAssetMapMock.mockResolvedValueOnce(graph)
    const user = userEvent.setup()
    render(<AssetMapTabContent targetId={7} />)

    // When
    await user.click(await screen.findByRole('button', { name: 'Select Example target' }))

    // Then
    expect(screen.queryByRole('complementary')).not.toBeInTheDocument()

    // When
    await user.click(screen.getByRole('button', { name: 'Select DOMAIN:example.test' }))

    // Then
    expect(screen.queryByRole('complementary')).not.toBeInTheDocument()
  })

  it('keeps a load failure recoverable with an accessible retry control', async () => {
    // Given
    loadTargetAssetMapMock
      .mockRejectedValueOnce(new AssetMapLoadError('load_failed'))
      .mockResolvedValueOnce(graph)
    const user = userEvent.setup()
    render(<AssetMapTabContent targetId={7} />)

    // When
    await user.click(await screen.findByRole('button', { name: 'Retry loading asset map' }))

    // Then
    expect(await screen.findByTestId('topology-map')).toBeVisible()
    expect(loadTargetAssetMapMock).toHaveBeenCalledTimes(2)
  })

  it('distinguishes a missing or empty target map and provides a next action', async () => {
    // Given
    loadTargetAssetMapMock.mockResolvedValueOnce(null)
    render(<AssetMapTabContent targetId={7} />)

    // When / Then
    expect(await screen.findByText('This target was not found or is no longer available.')).toBeVisible()
    expect(screen.getByText('Return to Targets to choose an available target.')).toBeVisible()
  })

  it('guides the user to populate an existing target with no discovered assets', async () => {
    // Given
    loadTargetAssetMapMock.mockResolvedValueOnce(emptyGraph())
    render(<AssetMapTabContent targetId={7} />)

    // When / Then
    expect(await screen.findByText('No discovered assets are available yet.')).toBeVisible()
    expect(screen.getByText('Add a seed or run reconnaissance to populate this map.')).toBeVisible()
  })

  it('shows truncation and safely exposes malformed diagnostics in a dismissible settings dialog', async () => {
    // Given
    loadTargetAssetMapMock.mockResolvedValueOnce(truncatedGraph())
    const user = userEvent.setup()
    render(<AssetMapTabContent targetId={7} />)

    // When
    await screen.findByTestId('topology-map')
    await user.click(screen.getByRole('button', { name: 'Asset map settings and diagnostics' }))

    // Then
    expect(screen.getByRole('dialog')).toBeVisible()
    expect(screen.getByText('Some asset-map results were truncated.')).toBeVisible()
    expect(screen.getByText('Malformed relations skipped')).toBeVisible()
    expect(screen.getByText('3')).toBeVisible()

    // When
    await user.keyboard('{Escape}')

    // Then
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('aborts stale requests when the target changes or the component unmounts', async () => {
    // Given
    let firstSignal: AbortSignal | undefined
    let secondSignal: AbortSignal | undefined
    loadTargetAssetMapMock
      .mockImplementationOnce((_targetId, options) => {
        firstSignal = options?.signal
        return new Promise(() => undefined)
      })
      .mockImplementationOnce((_targetId, options) => {
        secondSignal = options?.signal
        return new Promise(() => undefined)
      })
    const { rerender, unmount } = render(<AssetMapTabContent targetId={7} />)

    // When
    rerender(<AssetMapTabContent targetId={8} />)

    // Then
    await waitFor(() => expect(firstSignal?.aborted).toBe(true))

    // When
    unmount()

    // Then
    expect(secondSignal?.aborted).toBe(true)
  })
})
