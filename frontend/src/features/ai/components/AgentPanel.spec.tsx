import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { AssetMapGraph, AssetMapNode } from '../../target/assetMap/types'
import type { TargetTopology } from '../services/aiApi'
import { AgentPanel } from './AgentPanel'

type NeutralRendererProps = {
  readonly graph: AssetMapGraph | null
  readonly onSelectNode?: (node: AssetMapNode) => void
  readonly selectedNodeId?: string | null
}

vi.mock('../../../components/AgentInteractionTimeline', () => ({
  default: () => null,
}))

vi.mock('../../../components/AssetDetailPanel', () => ({
  default: () => null,
}))

vi.mock('./TreePanel', () => ({
  TreeNodeItem: () => null,
}))

vi.mock('../../../components/AssetTopologyMap', () => ({
  default: ({ graph, onSelectNode, selectedNodeId }: NeutralRendererProps) => {
    const selectedNode = graph?.nodes.find((node) => node.id === selectedNodeId) ?? null

    return (
      <section data-node-count={graph?.nodes.length ?? 0} data-selected-node-id={selectedNodeId ?? ''} data-testid="neutral-topology-renderer">
        <button
          disabled={selectedNode === null}
          onClick={() => {
            if (selectedNode !== null) onSelectNode?.(selectedNode)
          }}
          type="button"
        >
          {selectedNode?.label ?? 'No selected node'}
        </button>
      </section>
    )
  },
}))

const legacyTopology = {
  active_attacks: [],
  edges: [
    { edge_type: 'HAS_SUBDOMAIN', id: 'target-subdomain', source: 'target-7', target: 'subdomain-9' },
  ],
  nodes: [
    { id: 'target-7', label: 'example.com', type: 'target' },
    { id: 'subdomain-9', label: 'api.example.com', type: 'subdomain' },
  ],
  target_id: 7,
  target_name: 'example.com',
} as const satisfies TargetTopology

const selectedLegacyNode = legacyTopology.nodes[1]

describe('AgentPanel legacy topology compatibility', () => {
  it('renders an optional-field-free REST topology through the neutral renderer and returns its original node on selection', async () => {
    // Given
    const user = userEvent.setup()
    const onSelectTopoNode = vi.fn()
    const triggerRef = { current: null }
    render(
      <AgentPanel
        activeNodeThreadId={null}
        agentPanelTab="topology"
        agentTree={[]}
        boundTargetId={7}
        dispatchTree={null}
        onClose={vi.fn()}
        onOpenGraph={vi.fn()}
        onSelectTopoNode={onSelectTopoNode}
        onSelectTreeNode={vi.fn()}
        onTabChange={vi.fn()}
        rootNode={null}
        selectedTopoNode={selectedLegacyNode}
        showTree={true}
        topology={legacyTopology}
        triggerRef={triggerRef}
      />,
    )

    // When
    await user.click(screen.getByRole('button', { name: 'api.example.com' }))

    // Then
    expect(screen.getByTestId('neutral-topology-renderer')).toHaveAttribute('data-node-count', '2')
    expect(screen.getByTestId('neutral-topology-renderer')).toHaveAttribute('data-selected-node-id', 'asset:subdomain:subdomain-9')
    expect(onSelectTopoNode).toHaveBeenCalledOnce()
    expect(onSelectTopoNode).toHaveBeenCalledWith(selectedLegacyNode)
  })
})
