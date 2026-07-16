import type { ComponentType, ReactNode } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { AssetMapGraph } from '@/features/target/assetMap/types'
import { AssetTopologyMap } from './AssetTopologyMap'

type FlowNode = {
  readonly id: string
  readonly data: unknown
  readonly selected?: boolean
}

type FlowProps = {
  readonly children?: ReactNode
  readonly edges: readonly unknown[]
  readonly fitView?: boolean
  readonly maxZoom?: number
  readonly minZoom?: number
  readonly nodeTypes: { readonly asset: ComponentType<{ readonly data: unknown; readonly selected?: boolean }> }
  readonly nodes: readonly FlowNode[]
  readonly onNodeClick?: (event: MouseEvent, node: FlowNode) => void
  readonly panOnScroll?: boolean
  readonly zoomOnScroll?: boolean
}

vi.mock('@xyflow/react', () => ({
  Background: () => <output data-testid="background" />,
  BackgroundVariant: { Dots: 'dots' },
  Controls: ({ showInteractive }: { readonly showInteractive?: boolean }) => (
    <output data-testid="controls">{String(showInteractive)}</output>
  ),
  Handle: () => null,
  MarkerType: { ArrowClosed: 'arrowclosed' },
  MiniMap: () => <output data-testid="minimap" />,
  Position: { Bottom: 'bottom', Top: 'top' },
  ReactFlow: ({ children, edges, fitView, maxZoom, minZoom, nodeTypes, nodes, onNodeClick, panOnScroll, zoomOnScroll }: FlowProps) => {
    const AssetNode = nodeTypes.asset

    return (
      <section
        data-edge-count={edges.length}
        data-fit-view={String(fitView)}
        data-max-zoom={maxZoom}
        data-min-zoom={minZoom}
        data-pan-on-scroll={String(panOnScroll)}
        data-testid="react-flow"
        data-zoom-on-scroll={String(zoomOnScroll)}
      >
        {nodes.map((node) => (
          <button key={node.id} type="button" onClick={() => onNodeClick?.(new MouseEvent('click'), node)}>
            <AssetNode data={node.data} selected={node.selected} />
          </button>
        ))}
        {children}
      </section>
    )
  },
  ReactFlowProvider: ({ children }: { readonly children?: ReactNode }) => <>{children}</>,
  useEdgesState: (edges: readonly unknown[]) => [edges, () => undefined, () => undefined],
  useNodesState: (nodes: readonly FlowNode[]) => [nodes, () => undefined, () => undefined],
  useReactFlow: () => ({ fitView: () => undefined }),
}))

const inactiveMetadata = {
  actions: [],
  attributes: {},
  isActive: false,
  plans: [],
} as const

const activeMetadata = {
  actions: [],
  attributes: {},
  isActive: true,
  plans: [],
} as const

const graph = {
  targetId: 'asset:target:1',
  nodes: [
    { id: 'asset:target:1', kind: 'target', label: 'example.com', metadata: inactiveMetadata },
    { id: 'asset:port:443', kind: 'port', label: '443/tcp', metadata: activeMetadata },
  ],
  edges: [
    {
      id: 'edge:target_ip:asset:target:1:asset:port:443',
      kind: 'target_ip',
      label: 'HOSTS',
      source: 'asset:target:1',
      target: 'asset:port:443',
    },
    {
      id: 'edge:target_ip:asset:target:1:asset:port:443',
      kind: 'target_ip',
      label: 'HOSTS',
      source: 'asset:target:1',
      target: 'asset:port:443',
    },
  ],
  diagnostics: {
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
    truncatedByKind: { ip: 0, port: 0, seed: 0, subdomain: 0, target: 0, url: 0 },
  },
} as const satisfies AssetMapGraph

describe('AssetTopologyMap', () => {
  it('renders normalized graph counts, one display edge per ID, active state, and fixed flow controls', () => {
    // Given
    render(<AssetTopologyMap graph={graph} />)

    // When
    const flow = screen.getByTestId('react-flow')

    // Then
    expect(screen.getByText(/2 nodes · 1 edges/)).toBeInTheDocument()
    expect(flow).toHaveAttribute('data-edge-count', '1')
    expect(flow).toHaveAttribute('data-fit-view', 'true')
    expect(flow).toHaveAttribute('data-pan-on-scroll', 'true')
    expect(flow).toHaveAttribute('data-zoom-on-scroll', 'true')
    expect(screen.getByTestId('controls')).toHaveTextContent('false')
    expect(screen.getByTestId('minimap')).toBeInTheDocument()
    expect(screen.getByTitle('Active operation')).toBeInTheDocument()
  })

  it('returns the normalized selected node to its caller', async () => {
    // Given
    const user = userEvent.setup()
    const onSelectNode = vi.fn()
    render(<AssetTopologyMap graph={graph} onSelectNode={onSelectNode} />)

    // When
    await user.click(screen.getByRole('button', { name: /443\/tcp/i }))

    // Then
    expect(onSelectNode).toHaveBeenCalledWith(graph.nodes[1])
  })

  it('explains when a normalized graph has no nodes', () => {
    // Given
    const emptyGraph = { ...graph, nodes: [] } satisfies AssetMapGraph

    // When
    render(<AssetTopologyMap graph={emptyGraph} />)

    // Then
    expect(screen.getByText('No assets to display')).toBeInTheDocument()
  })
})
