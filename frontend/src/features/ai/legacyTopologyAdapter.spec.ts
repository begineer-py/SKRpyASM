import { describe, expect, it } from 'vitest'
import type { TargetTopology } from './services/aiApi'
import { adaptLegacyTopology } from './legacyTopologyAdapter'

const legacyTopology = {
  active_attacks: [{ node_id: 'port-443' }],
  edges: [
    { edge_type: 'HAS_PORT', id: 'target-port', source: 'target-7', target: 'port-443' },
  ],
  nodes: [
    { id: 'target-7', label: 'example.com', type: 'target' },
    { asset_id: 443, id: 'port-443', label: '443/tcp', type: 'port' },
    { id: 'finding-1', is_active_attack: true, label: 'CVE-2026-1', type: 'vulnerability' },
  ],
  target_id: 7,
  target_name: 'example.com',
} as const satisfies TargetTopology

describe('adaptLegacyTopology', () => {
  it('keeps legacy node identity and activity while producing the neutral graph shape', () => {
    // Given
    const topology = legacyTopology

    // When
    const adapted = adaptLegacyTopology(topology)
    const port = adapted.graph.nodes.find((node) => node.label === '443/tcp')
    const finding = adapted.graph.nodes.find((node) => node.label === 'CVE-2026-1')

    // Then
    expect(adapted.graph.targetId).toBe('asset:target:target-7')
    expect(adapted.graph.edges).toEqual([
      expect.objectContaining({
        id: 'edge:explicit:asset:target:target-7:asset:port:port-443',
        kind: 'explicit',
        label: 'HAS_PORT',
      }),
    ])
    expect(port?.metadata).toMatchObject({
      attributes: { assetId: 443, legacyType: 'port' },
      isActive: true,
    })
    expect(finding?.metadata).toMatchObject({
      attributes: { legacyType: 'vulnerability' },
      isActive: true,
    })
    expect(port === undefined ? undefined : adapted.legacyNodesByGraphId.get(port.id)).toBe(topology.nodes[1])
  })
})
