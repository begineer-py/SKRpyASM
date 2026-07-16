import { describe, expect, it } from 'vitest'
import { projectGraph, type AssetMapRawResult } from './projectGraph'

function aggregate(count = 0) {
  return { aggregate: { count } }
}

function baseFixture(): AssetMapRawResult {
  return {
    target: { id: 1, name: 'example.com', description: 'Scoped target' },
    seeds: [],
    seeds_aggregate: aggregate(),
    subdomains: [],
    subdomains_aggregate: aggregate(),
    ips: [],
    ips_aggregate: aggregate(),
    ports: [],
    ports_aggregate: aggregate(),
    urls: [],
    urls_aggregate: aggregate(),
    asset_edges: [],
    asset_edges_aggregate: aggregate(),
    actions: [],
    actions_aggregate: aggregate(),
    action_asset_links: [],
    action_asset_links_aggregate: aggregate(),
    asset_locks: [],
    asset_locks_aggregate: aggregate(),
  }
}

type Fixture = ReturnType<typeof baseFixture>

function fixture(overrides: Partial<Fixture> = {}): Fixture {
  return { ...baseFixture(), ...overrides }
}

function subdomain(id: number, ipIds: readonly number[] = []) {
  return {
    id,
    target_id: 1,
    name: `s${id}.example.com`,
    is_active: true,
    is_resolvable: true,
    core_subdomain_ips: ipIds.map((ip_id) => ({ ip_id })),
  }
}

function ip(id: number, targetId = 1) {
  return { id, target_id: targetId, address: `192.0.2.${id}`, version: 4 }
}

function url(id: number, subdomainIds: readonly number[]) {
  return {
    id,
    target_id: 1,
    url: `https://s${id}.example.com`,
    method: 'GET',
    status_code: 200,
    title: null,
    content_fetch_status: 'SUCCESS_FETCHED',
    is_important: false,
    core_urlresult_related_subdomains: subdomainIds.map((subdomain_id) => ({ subdomain_id })),
  }
}

function explicitEdge(id: number, source: number, target: number) {
  return {
    id,
    target_id: 1,
    from_asset_type: 'IP',
    from_ip_id: source,
    from_subdomain_id: null,
    from_url_id: null,
    from_port_id: null,
    to_asset_type: 'IP',
    to_ip_id: target,
    to_subdomain_id: null,
    to_url_id: null,
    to_port_id: null,
    edge_type: id % 2 === 0 ? 'LINKS_TO' : 'RESOLVES_TO',
  }
}

describe('projectGraph', () => {
  it.each([
    { relationIds: [], visible: false, edgeCount: 0, reason: 'url_without_related_subdomains' },
    { relationIds: [1], visible: true, edgeCount: 1, reason: null },
    { relationIds: [10, 2], visible: true, edgeCount: 2, reason: null },
    { relationIds: [1, 2, 3], visible: false, edgeCount: 0, reason: 'url_with_too_many_related_subdomains' },
  ] as const)('applies the URL relation rule to $relationIds.length relations', ({ relationIds, visible, edgeCount, reason }) => {
    // Given
    const raw = fixture({ subdomains: [subdomain(1), subdomain(2), subdomain(3), subdomain(10)], urls: [url(9, relationIds)] })

    // When
    const graph = projectGraph(raw)
    const urlNode = graph?.nodes.find((node) => node.id === 'asset:url:9')
    const urlEdges = graph?.edges.filter((edge) => edge.kind === 'subdomain_url') ?? []
    const expectedSources = visible
      ? relationIds.slice().sort((a, b) => a - b).map((id) => `asset:subdomain:${id}`)
      : []

    // Then
    expect(Boolean(urlNode)).toBe(visible)
    expect(urlEdges).toHaveLength(edgeCount)
    expect(urlEdges.map((edge) => edge.source)).toEqual(expectedSources)
    if (reason !== null) expect(graph?.diagnostics.skippedByReason[reason]).toBe(1)
  })

  it('isolates cross-target roots and never creates nodes through relations', () => {
    // Given
    const crossTargetEdge = { ...explicitEdge(1, 20, 21), target_id: 2 }
    const raw = fixture({
      seeds: [{ id: 2, target_id: 2, value: 'foreign.example', type: 'DOMAIN', is_active: true }],
      subdomains: [subdomain(10, [20])],
      ips: [ip(20, 2)],
      ports: [{ id: 30, ip_id: 20, port_number: 443, protocol: 'tcp', state: 'open', service_name: null, service_version: null }],
      urls: [{ ...url(40, [10]), target_id: 2 }],
      asset_edges: [crossTargetEdge],
      actions: [{ id: 50, target_id: 2, plan_id: null, purpose_text: null, status: 'PENDING', result_summary: null, order: 0, core_attackplan: null }],
      asset_locks: [{ id: 60, target_id: 2, asset_type: 'PORT', ip_asset_id: null, subdomain_asset_id: null, url_asset_id: null, port_asset_id: 30, lock_status: 'HELD', agent_role: 'RECON', acquired_at: '2026-07-15T00:00:00Z' }],
    })

    // When
    const graph = projectGraph(raw)

    // Then
    expect(graph?.nodes.map((node) => node.id)).toEqual(['asset:target:1', 'asset:subdomain:10'])
    expect(graph?.diagnostics.skippedByReason.cross_target).toBe(6)
    expect(graph?.diagnostics.skippedByReason.missing_asset).toBe(2)
  })

  it('reports malformed nullable edge and link branches without attaching them', () => {
    // Given
    const malformedEdge = { ...explicitEdge(1, 1, 2), to_ip_id: null }
    const raw = fixture({
      subdomains: [{ ...subdomain(10), core_subdomain_ips: null }],
      ips: [ip(1), ip(2)],
      asset_edges: [malformedEdge],
      actions: [{ id: 20, target_id: 1, plan_id: null, purpose_text: null, status: 'PENDING', result_summary: null, order: 0, core_attackplan: null }],
      action_asset_links: [{ id: 30, action_id: 20, assetvectorlink_id: 40, core_assetvectorlink: null }],
      asset_locks: [{ id: 50, target_id: 1, asset_type: 'PORT', ip_asset_id: null, subdomain_asset_id: null, url_asset_id: null, port_asset_id: null, lock_status: 'HELD', agent_role: 'RECON', acquired_at: '2026-07-15T00:00:00Z' }],
    })

    // When
    const graph = projectGraph(raw)

    // Then
    expect(graph?.edges.some((edge) => edge.kind === 'explicit')).toBe(false)
    expect(graph?.nodes.every((node) => node.metadata.actions.length === 0)).toBe(true)
    expect(graph?.diagnostics.skippedByReason.malformed_relation).toBe(4)
  })

  it('orders valid roots deterministically when malformed IDs are interleaved', () => {
    // Given
    const raw = fixture({ ips: [ip(2), ip(Number.NaN), ip(1)] })

    // When
    const graph = projectGraph(raw)

    // Then
    expect(graph?.nodes.map((node) => node.id)).toEqual(['asset:target:1', 'asset:ip:1', 'asset:ip:2'])
    expect(graph?.diagnostics.skippedByReason.malformed_relation).toBe(1)
  })

  it('retains cyclic explicit edges once without recursive expansion', () => {
    // Given
    const raw = fixture({ ips: [ip(1), ip(2)], asset_edges: [explicitEdge(1, 1, 2), explicitEdge(2, 2, 1), explicitEdge(3, 1, 2)] })

    // When
    const graph = projectGraph(raw)
    const explicit = graph?.edges.filter((edge) => edge.kind === 'explicit') ?? []

    // Then
    expect(explicit.map((edge) => [edge.source, edge.target])).toEqual([
      ['asset:ip:1', 'asset:ip:2'],
      ['asset:ip:2', 'asset:ip:1'],
    ])
    expect(graph?.diagnostics.skippedByReason.duplicate_edge).toBe(1)
  })

  it('applies node and edge caps after retaining inferred structure before explicit edges', () => {
    // Given
    const ips = Array.from({ length: 405 }, (_, index) => ip(index + 1))
    const edges = Array.from({ length: 500 }, (_, index) => {
      const source = (index % 399) + 1
      const shift = Math.floor(index / 399) + 1
      return explicitEdge(index + 1, source, ((source + shift - 1) % 399) + 1)
    })
    const raw = fixture({ ips, ips_aggregate: aggregate(407), asset_edges: edges })

    // When
    const graph = projectGraph(raw)

    // Then
    expect(graph?.nodes).toHaveLength(400)
    expect(graph?.edges).toHaveLength(800)
    expect(graph?.edges.filter((edge) => edge.kind === 'target_ip')).toHaveLength(399)
    expect(graph?.edges.filter((edge) => edge.kind === 'explicit')).toHaveLength(401)
    expect(graph?.diagnostics).toMatchObject({
      isTruncated: true,
      truncatedByKind: { ip: 8 },
      skippedByReason: { graph_node_cap: 6, graph_edge_cap: 99 },
    })
  })

  it('diagnoses an edge to a node rejected by the node cap', () => {
    // Given
    const raw = fixture({
      ips: Array.from({ length: 400 }, (_, index) => ip(index + 1)),
      asset_edges: [explicitEdge(1, 400, 1)],
    })

    // When
    const graph = projectGraph(raw)

    // Then
    expect(graph?.nodes).toHaveLength(400)
    expect(graph?.nodes.some((node) => node.id === 'asset:ip:400')).toBe(false)
    expect(graph?.edges.some((edge) => edge.kind === 'explicit')).toBe(false)
    expect(graph?.diagnostics.skippedByReason).toEqual({
      cross_target: 0,
      malformed_relation: 0,
      missing_asset: 1,
      duplicate_edge: 0,
      url_without_related_subdomains: 0,
      url_with_too_many_related_subdomains: 0,
      graph_node_cap: 1,
      graph_edge_cap: 0,
    })
  })

  it('attaches only exact in-target plans, actions, and held locks to their asset', () => {
    // Given
    const ports = [100, 101].map((id) => ({ id, ip_id: 1, port_number: id, protocol: 'tcp', state: 'open', service_name: 'https', service_version: null }))
    const actions = [
      { id: 10, target_id: 1, plan_id: 50, purpose_text: 'Verify TLS', status: 'IN_PROGRESS', result_summary: null, order: 1, core_attackplan: { id: 50, target_id: 1, objective: 'Assess HTTPS', status: 'ACTIVE' } },
      { id: 11, target_id: 1, plan_id: 51, purpose_text: 'Finished check', status: 'COMPLETED', result_summary: 'done', order: 2, core_attackplan: { id: 51, target_id: 2, objective: 'Foreign plan', status: 'ACTIVE' } },
    ]
    const link = (id: number, actionId: number, portId: number) => ({ id, action_id: actionId, assetvectorlink_id: id + 100, core_assetvectorlink: { id: id + 100, asset_type: 'PORT', status: 'IN_PROGRESS', ip_asset_id: null, subdomain_asset_id: null, url_asset_id: null, port_asset_id: portId } })
    const raw = fixture({
      ips: [ip(1)],
      ports,
      actions,
      action_asset_links: [link(20, 10, 100), link(21, 11, 101)],
      asset_locks: [{ id: 30, target_id: 1, asset_type: 'PORT', ip_asset_id: null, subdomain_asset_id: null, url_asset_id: null, port_asset_id: 100, lock_status: 'HELD', agent_role: 'RECON', acquired_at: '2026-07-15T00:00:00Z' }],
    })

    // When
    const graph = projectGraph(raw)
    const first = graph?.nodes.find((node) => node.id === 'asset:port:100')
    const second = graph?.nodes.find((node) => node.id === 'asset:port:101')

    // Then
    expect(first?.metadata).toMatchObject({
      isActive: true,
      attributes: { lockStatus: 'HELD', lockAgentRole: 'RECON', lockAcquiredAt: '2026-07-15T00:00:00Z' },
      plans: [{ id: 'plan:50', objective: 'Assess HTTPS', status: 'running' }],
      actions: [{ id: 'action:10', planId: 'plan:50', purpose: 'Verify TLS', status: 'running', isActive: true }],
    })
    expect(second?.metadata).toMatchObject({ plans: [], actions: [{ id: 'action:11', planId: null, status: 'completed' }], isActive: false })
    expect(graph?.diagnostics.skippedByReason.cross_target).toBe(1)
  })

  it('bounds forged action and link collections before growing node metadata', () => {
    // Given
    const actions = Array.from({ length: 150 }, (_, index) => ({ id: index + 1, target_id: 1, plan_id: null, purpose_text: `Action ${index + 1}`, status: 'PENDING', result_summary: null, order: index, core_attackplan: null }))
    const links = actions.map((action, index) => ({ id: index + 1, action_id: action.id, assetvectorlink_id: index + 201, core_assetvectorlink: { id: index + 201, asset_type: 'PORT', status: 'TARGETED', ip_asset_id: null, subdomain_asset_id: null, url_asset_id: null, port_asset_id: 100 } }))
    const raw = fixture({
      ips: [ip(1)],
      ports: [{ id: 100, ip_id: 1, port_number: 443, protocol: 'tcp', state: 'open', service_name: 'https', service_version: null }],
      actions,
      actions_aggregate: aggregate(actions.length),
      action_asset_links: links,
      action_asset_links_aggregate: aggregate(links.length),
    })

    // When
    const graph = projectGraph(raw)
    const port = graph?.nodes.find((node) => node.id === 'asset:port:100')

    // Then
    expect(port?.metadata.actions).toHaveLength(100)
    expect(graph?.diagnostics.isTruncated).toBe(true)
  })
})
