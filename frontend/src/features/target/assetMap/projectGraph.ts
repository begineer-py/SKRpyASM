import { ASSET_MAP_QUERY_MAXIMUMS, MAX_GRAPH_EDGES, MAX_GRAPH_NODES } from './types'
import type { AssetActionStatus, AssetActionSummary, AssetKind, AssetMapDiagnosticReason, AssetMapEdge, AssetMapEdgeKind, AssetMapGraph, AssetMapMetadataValue, AssetMapNode, AssetMapNodeId, AssetPlanSummary } from './types'

type Aggregate = { readonly aggregate: { readonly count: number } | null }
type TargetRow = { readonly id: number; readonly name: string; readonly description: string | null }
type SeedRow = { readonly id: number; readonly target_id: number; readonly value: string; readonly type: string; readonly is_active: boolean }
type SubdomainRow = { readonly id: number; readonly target_id: number | null; readonly name: string; readonly is_active: boolean; readonly is_resolvable: boolean; readonly core_subdomain_ips: readonly ({ readonly ip_id: number } | null)[] | null }
type IpRow = { readonly id: number; readonly target_id: number | null; readonly address: unknown; readonly version: unknown }
type PortRow = { readonly id: number; readonly ip_id: number; readonly port_number: number; readonly protocol: string; readonly state: string; readonly service_name: string | null; readonly service_version: string | null }
type UrlRow = { readonly id: number; readonly target_id: number | null; readonly url: string; readonly method: string; readonly status_code: number | null; readonly title: string | null; readonly content_fetch_status: string; readonly is_important: boolean; readonly core_urlresult_related_subdomains: readonly ({ readonly subdomain_id: number } | null)[] | null }
type AssetReference = { readonly asset_type: string; readonly ip_asset_id: number | null; readonly subdomain_asset_id: number | null; readonly url_asset_id: number | null; readonly port_asset_id: number | null }
type AssetEdgeRow = { readonly id: number; readonly target_id: number; readonly from_asset_type: string; readonly from_ip_id: number | null; readonly from_subdomain_id: number | null; readonly from_url_id: number | null; readonly from_port_id: number | null; readonly to_asset_type: string; readonly to_ip_id: number | null; readonly to_subdomain_id: number | null; readonly to_url_id: number | null; readonly to_port_id: number | null; readonly edge_type: string }
type PlanRow = { readonly id: number; readonly target_id: number; readonly objective: string; readonly status: string }
type ActionRow = { readonly id: number; readonly target_id: number; readonly plan_id: number | null; readonly purpose_text: string | null; readonly status: string; readonly result_summary: string | null; readonly order: number; readonly core_attackplan: PlanRow | null }
type ActionLinkRow = { readonly id: number; readonly action_id: number; readonly assetvectorlink_id: number; readonly core_assetvectorlink: ({ readonly id: number; readonly status: string } & AssetReference) | null }
type AssetLockRow = { readonly id: number; readonly target_id: number; readonly lock_status: string; readonly agent_role: string; readonly acquired_at: string } & AssetReference

export type AssetMapRawResult = {
  readonly target: TargetRow | null
  readonly seeds: readonly SeedRow[]; readonly seeds_aggregate: Aggregate
  readonly subdomains: readonly SubdomainRow[]; readonly subdomains_aggregate: Aggregate
  readonly ips: readonly IpRow[]; readonly ips_aggregate: Aggregate
  readonly ports: readonly PortRow[]; readonly ports_aggregate: Aggregate
  readonly urls: readonly UrlRow[]; readonly urls_aggregate: Aggregate
  readonly asset_edges: readonly AssetEdgeRow[]; readonly asset_edges_aggregate: Aggregate
  readonly actions: readonly ActionRow[]; readonly actions_aggregate: Aggregate
  readonly action_asset_links: readonly ActionLinkRow[]; readonly action_asset_links_aggregate: Aggregate
  readonly asset_locks: readonly AssetLockRow[]; readonly asset_locks_aggregate: Aggregate
}

type MutableMetadata = { attributes: Record<string, AssetMapMetadataValue>; plans: AssetPlanSummary[]; actions: AssetActionSummary[]; isActive: boolean }
type Diagnostics = ReturnType<typeof createDiagnostics>
type NodeState = { nodes: AssetMapNode[]; metadata: Map<AssetMapNodeId, MutableMetadata>; known: Set<AssetMapNodeId>; diagnostics: Diagnostics }
type EdgeCandidate = { readonly kind: AssetMapEdgeKind; readonly source: AssetMapNodeId; readonly target: AssetMapNodeId; readonly label: string | null }
type EdgeState = { edges: AssetMapEdge[]; keys: Set<string>; nodes: NodeState; diagnostics: Diagnostics }

const ROOT_COUNTS = [['seed', 'seeds', 'seeds_aggregate'], ['subdomain', 'subdomains', 'subdomains_aggregate'], ['ip', 'ips', 'ips_aggregate'], ['port', 'ports', 'ports_aggregate'], ['url', 'urls', 'urls_aggregate']] as const
const AUXILIARY_COUNTS = [['asset_edges', 'asset_edges_aggregate'], ['actions', 'actions_aggregate'], ['action_asset_links', 'action_asset_links_aggregate'], ['asset_locks', 'asset_locks_aggregate']] as const

function createDiagnostics() {
  return {
    isTruncated: false,
    truncatedByKind: { target: 0, seed: 0, subdomain: 0, ip: 0, port: 0, url: 0 },
    skippedByReason: { cross_target: 0, malformed_relation: 0, missing_asset: 0, duplicate_edge: 0, url_without_related_subdomains: 0, url_with_too_many_related_subdomains: 0, graph_node_cap: 0, graph_edge_cap: 0 },
  }
}

function validId(value: number): boolean { return Number.isSafeInteger(value) && value > 0 }
function byId<T extends { readonly id: number }>(left: T, right: T): number { return (validId(left.id) ? left.id : Number.MAX_SAFE_INTEGER) - (validId(right.id) ? right.id : Number.MAX_SAFE_INTEGER) }
function metadata(attributes: Record<string, AssetMapMetadataValue>): MutableMetadata { return { attributes, plans: [], actions: [], isActive: false } }
function valueOrNull(value: unknown): AssetMapMetadataValue { return typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean' ? value : null }
function skip(diagnostics: Diagnostics, reason: AssetMapDiagnosticReason): void { diagnostics.skippedByReason[reason] += 1 }
function malformedReference(diagnostics: Diagnostics): null { skip(diagnostics, 'malformed_relation'); return null }
function boundedRootRows<T extends { readonly id: number }>(rows: readonly T[], kind: AssetKind, diagnostics: Diagnostics): T[] {
  const omitted = Math.max(0, rows.length - MAX_GRAPH_NODES)
  diagnostics.skippedByReason.graph_node_cap += omitted; diagnostics.truncatedByKind[kind] += omitted
  return [...rows.slice(0, MAX_GRAPH_NODES)].sort(byId)
}

function addNode(state: NodeState, node: AssetMapNode, nodeMetadata: MutableMetadata): boolean {
  if (state.metadata.has(node.id)) { skip(state.diagnostics, 'malformed_relation'); return false }
  if (state.nodes.length >= MAX_GRAPH_NODES) {
    skip(state.diagnostics, 'graph_node_cap')
    state.diagnostics.truncatedByKind[node.kind] += 1
    return false
  }
  state.nodes.push(node)
  state.metadata.set(node.id, nodeMetadata)
  state.known.add(node.id)
  return true
}

function assertNever(value: never): never { throw new TypeError(`Unsupported edge kind: ${value}`) }

function appendEdge(state: EdgeState, candidate: EdgeCandidate): void {
  if (!state.nodes.metadata.has(candidate.source) || !state.nodes.metadata.has(candidate.target)) { skip(state.diagnostics, 'missing_asset'); return }
  const key = `${candidate.kind}:${candidate.source}:${candidate.target}`
  if (state.keys.has(key)) { skip(state.diagnostics, 'duplicate_edge'); return }
  if (state.edges.length >= MAX_GRAPH_EDGES) { skip(state.diagnostics, 'graph_edge_cap'); return }
  state.keys.add(key)
  const shared = { source: candidate.source, target: candidate.target, label: candidate.label }
  switch (candidate.kind) {
    case 'target_seed': state.edges.push({ ...shared, id: `edge:target_seed:${candidate.source}:${candidate.target}`, kind: 'target_seed' }); return
    case 'target_subdomain': state.edges.push({ ...shared, id: `edge:target_subdomain:${candidate.source}:${candidate.target}`, kind: 'target_subdomain' }); return
    case 'target_ip': state.edges.push({ ...shared, id: `edge:target_ip:${candidate.source}:${candidate.target}`, kind: 'target_ip' }); return
    case 'subdomain_ip': state.edges.push({ ...shared, id: `edge:subdomain_ip:${candidate.source}:${candidate.target}`, kind: 'subdomain_ip' }); return
    case 'ip_port': state.edges.push({ ...shared, id: `edge:ip_port:${candidate.source}:${candidate.target}`, kind: 'ip_port' }); return
    case 'subdomain_url': state.edges.push({ ...shared, id: `edge:subdomain_url:${candidate.source}:${candidate.target}`, kind: 'subdomain_url' }); return
    case 'explicit': state.edges.push({ ...shared, id: `edge:explicit:${candidate.source}:${candidate.target}`, kind: 'explicit' }); return
    default: assertNever(candidate.kind)
  }
}

function normalizeStatus(status: string): AssetActionStatus {
  switch (status.toUpperCase()) {
    case 'PENDING': case 'DRAFT': case 'TARGETED': return 'pending'
    case 'IN_PROGRESS': case 'ACTIVE': return 'running'
    case 'COMPLETED': return 'completed'
    case 'FAILED': return 'failed'
    case 'CANCELLED': case 'ABANDONED': case 'SKIPPED': return 'cancelled'
    default: return 'unknown'
  }
}

function assetReference(reference: AssetReference, diagnostics: Diagnostics): AssetMapNodeId | null {
  const ids = [reference.ip_asset_id, reference.subdomain_asset_id, reference.url_asset_id, reference.port_asset_id]
  if (ids.filter((id) => id !== null).length !== 1 || ids.some((id) => id !== null && !validId(id))) { skip(diagnostics, 'malformed_relation'); return null }
  switch (reference.asset_type.toUpperCase()) {
    case 'IP': return reference.ip_asset_id === null ? malformedReference(diagnostics) : `asset:ip:${reference.ip_asset_id}`
    case 'SUBDOMAIN': return reference.subdomain_asset_id === null ? malformedReference(diagnostics) : `asset:subdomain:${reference.subdomain_asset_id}`
    case 'URL': return reference.url_asset_id === null ? malformedReference(diagnostics) : `asset:url:${reference.url_asset_id}`
    case 'PORT': return reference.port_asset_id === null ? malformedReference(diagnostics) : `asset:port:${reference.port_asset_id}`
    default: skip(diagnostics, 'malformed_relation'); return null
  }
}

function applyTruncation(raw: AssetMapRawResult, diagnostics: Diagnostics): void {
  for (const [kind, rowsKey, aggregateKey] of ROOT_COUNTS) {
    const omitted = Math.max(0, (raw[aggregateKey].aggregate?.count ?? raw[rowsKey].length) - raw[rowsKey].length)
    diagnostics.truncatedByKind[kind] += omitted
  }
  const auxiliaryTruncated = AUXILIARY_COUNTS.some(([rowsKey, aggregateKey]) => (raw[aggregateKey].aggregate?.count ?? raw[rowsKey].length) > raw[rowsKey].length) || raw.actions.length > ASSET_MAP_QUERY_MAXIMUMS.actions || raw.action_asset_links.length > ASSET_MAP_QUERY_MAXIMUMS.actionAssetLinks || raw.asset_locks.length > ASSET_MAP_QUERY_MAXIMUMS.assetLocks
  diagnostics.isTruncated ||= auxiliaryTruncated || Object.values(diagnostics.truncatedByKind).some((count) => count > 0) || diagnostics.skippedByReason.graph_edge_cap > 0
}

export function projectGraph(raw: AssetMapRawResult): AssetMapGraph | null {
  if (raw.target === null || !validId(raw.target.id)) return null
  const diagnostics = createDiagnostics()
  const nodeState: NodeState = { nodes: [], metadata: new Map(), known: new Set(), diagnostics }
  const targetId: AssetMapNodeId<'target'> = `asset:target:${raw.target.id}`
  const targetMetadata = metadata({ description: raw.target.description })
  addNode(nodeState, { id: targetId, kind: 'target', label: raw.target.name.slice(0, 120), metadata: targetMetadata }, targetMetadata)
  const inferred: EdgeCandidate[] = []

  for (const row of boundedRootRows(raw.seeds, 'seed', diagnostics)) {
    if (!validId(row.id)) { skip(diagnostics, 'malformed_relation'); continue }
    if (row.target_id !== raw.target.id) { skip(diagnostics, 'cross_target'); continue }
    const id: AssetMapNodeId<'seed'> = `asset:seed:${row.id}`
    const meta = metadata({ type: row.type, isActive: row.is_active })
    if (addNode(nodeState, { id, kind: 'seed', label: `${row.type}:${row.value}`.slice(0, 120), metadata: meta }, meta)) inferred.push({ kind: 'target_seed', source: targetId, target: id, label: 'HOSTS' })
  }

  const retainedSubdomains: SubdomainRow[] = []
  for (const row of boundedRootRows(raw.subdomains, 'subdomain', diagnostics)) {
    if (!validId(row.id)) { skip(diagnostics, 'malformed_relation'); continue }
    if (row.target_id !== raw.target.id) { skip(diagnostics, 'cross_target'); continue }
    const id: AssetMapNodeId<'subdomain'> = `asset:subdomain:${row.id}`
    const meta = metadata({ isActive: row.is_active, isResolvable: row.is_resolvable })
    retainedSubdomains.push(row)
    if (addNode(nodeState, { id, kind: 'subdomain', label: row.name.slice(0, 120), metadata: meta }, meta)) inferred.push({ kind: 'target_subdomain', source: targetId, target: id, label: 'HOSTS' })
  }

  for (const row of boundedRootRows(raw.ips, 'ip', diagnostics)) {
    if (!validId(row.id)) { skip(diagnostics, 'malformed_relation'); continue }
    if (row.target_id !== raw.target.id) { skip(diagnostics, 'cross_target'); continue }
    const id: AssetMapNodeId<'ip'> = `asset:ip:${row.id}`
    const meta = metadata({ version: valueOrNull(row.version) })
    const label = typeof row.address === 'string' ? row.address : String(row.id)
    if (addNode(nodeState, { id, kind: 'ip', label: label.slice(0, 120), metadata: meta }, meta)) inferred.push({ kind: 'target_ip', source: targetId, target: id, label: 'HOSTS' })
  }

  for (const row of boundedRootRows(raw.ports, 'port', diagnostics)) {
    if (!validId(row.id) || !validId(row.ip_id)) { skip(diagnostics, 'malformed_relation'); continue }
    const parent: AssetMapNodeId<'ip'> = `asset:ip:${row.ip_id}`
    if (!nodeState.known.has(parent)) { skip(diagnostics, 'missing_asset'); continue }
    const id: AssetMapNodeId<'port'> = `asset:port:${row.id}`
    const meta = metadata({ portNumber: row.port_number, protocol: row.protocol, state: row.state, serviceName: row.service_name, serviceVersion: row.service_version })
    if (addNode(nodeState, { id, kind: 'port', label: `${row.port_number}/${row.protocol}`.slice(0, 120), metadata: meta }, meta)) inferred.push({ kind: 'ip_port', source: parent, target: id, label: 'HOSTS' })
  }

  for (const row of retainedSubdomains) {
    if (row.core_subdomain_ips === null) { skip(diagnostics, 'malformed_relation'); continue }
    const relations = row.core_subdomain_ips.slice(0, ASSET_MAP_QUERY_MAXIMUMS.subdomainIps)
    if (relations.length < row.core_subdomain_ips.length) diagnostics.isTruncated = true
    for (const relation of relations) {
      if (relation === null || !validId(relation.ip_id)) { skip(diagnostics, 'malformed_relation'); continue }
      const source: AssetMapNodeId<'subdomain'> = `asset:subdomain:${row.id}`
      const target: AssetMapNodeId<'ip'> = `asset:ip:${relation.ip_id}`
      if (!nodeState.known.has(target)) { skip(diagnostics, 'missing_asset'); continue }
      inferred.push({ kind: 'subdomain_ip', source, target, label: 'RESOLVES_TO' })
    }
  }

  for (const row of boundedRootRows(raw.urls, 'url', diagnostics)) {
    if (!validId(row.id)) { skip(diagnostics, 'malformed_relation'); continue }
    if (row.target_id !== raw.target.id) { skip(diagnostics, 'cross_target'); continue }
    const relations = row.core_urlresult_related_subdomains
    if (relations === null) { skip(diagnostics, 'malformed_relation'); skip(diagnostics, 'url_without_related_subdomains'); continue }
    if (relations.length === 0) { skip(diagnostics, 'url_without_related_subdomains'); continue }
    if (relations.length >= 3) { skip(diagnostics, 'url_with_too_many_related_subdomains'); continue }
    const related: AssetMapNodeId<'subdomain'>[] = []
    for (const relation of [...relations].sort((left, right) => (left?.subdomain_id ?? Number.MAX_SAFE_INTEGER) - (right?.subdomain_id ?? Number.MAX_SAFE_INTEGER))) {
      if (relation === null || !validId(relation.subdomain_id)) { skip(diagnostics, 'malformed_relation'); continue }
      const id: AssetMapNodeId<'subdomain'> = `asset:subdomain:${relation.subdomain_id}`
      if (!nodeState.known.has(id)) { skip(diagnostics, 'missing_asset'); continue }
      related.push(id)
    }
    if (related.length === 0) { skip(diagnostics, 'url_without_related_subdomains'); continue }
    const id: AssetMapNodeId<'url'> = `asset:url:${row.id}`
    const meta = metadata({ method: row.method, statusCode: row.status_code, title: row.title, contentFetchStatus: row.content_fetch_status, isImportant: row.is_important })
    if (addNode(nodeState, { id, kind: 'url', label: row.url.slice(0, 120), metadata: meta }, meta)) {
      for (const source of related) inferred.push({ kind: 'subdomain_url', source, target: id, label: 'LINKS_TO' })
    }
  }

  const edgeState: EdgeState = { edges: [], keys: new Set(), nodes: nodeState, diagnostics }
  for (const edge of inferred) appendEdge(edgeState, edge)
  const explicitRows = raw.asset_edges.slice(0, MAX_GRAPH_EDGES)
  diagnostics.skippedByReason.graph_edge_cap += raw.asset_edges.length - explicitRows.length
  for (const row of [...explicitRows].sort(byId)) {
    if (!validId(row.id)) { skip(diagnostics, 'malformed_relation'); continue }
    if (row.target_id !== raw.target.id) { skip(diagnostics, 'cross_target'); continue }
    const source = assetReference({ asset_type: row.from_asset_type, ip_asset_id: row.from_ip_id, subdomain_asset_id: row.from_subdomain_id, url_asset_id: row.from_url_id, port_asset_id: row.from_port_id }, diagnostics)
    const target = assetReference({ asset_type: row.to_asset_type, ip_asset_id: row.to_ip_id, subdomain_asset_id: row.to_subdomain_id, url_asset_id: row.to_url_id, port_asset_id: row.to_port_id }, diagnostics)
    if (source === null || target === null) continue
    if (!nodeState.known.has(source) || !nodeState.known.has(target)) { skip(diagnostics, 'missing_asset'); continue }
    appendEdge(edgeState, { kind: 'explicit', source, target, label: row.edge_type || null })
  }

  const actions = new Map<number, { readonly summary: AssetActionSummary; readonly plan: AssetPlanSummary | null }>()
  for (const row of [...raw.actions.slice(0, ASSET_MAP_QUERY_MAXIMUMS.actions)].sort(byId)) {
    if (!validId(row.id)) { skip(diagnostics, 'malformed_relation'); continue }
    if (row.target_id !== raw.target.id) { skip(diagnostics, 'cross_target'); continue }
    let plan: AssetPlanSummary | null = null
    if (row.plan_id === null) {
      if (row.core_attackplan !== null) skip(diagnostics, 'malformed_relation')
    } else if (row.core_attackplan === null || row.core_attackplan.id !== row.plan_id) {
      skip(diagnostics, 'malformed_relation')
    } else if (row.core_attackplan.target_id !== raw.target.id) {
      skip(diagnostics, 'cross_target')
    } else {
      plan = { id: `plan:${row.core_attackplan.id}`, objective: row.core_attackplan.objective, status: normalizeStatus(row.core_attackplan.status) }
    }
    if (actions.has(row.id)) { skip(diagnostics, 'malformed_relation'); continue }
    const status = normalizeStatus(row.status)
    actions.set(row.id, { summary: { id: `action:${row.id}`, planId: plan?.id ?? null, purpose: row.purpose_text, status, resultSummary: row.result_summary, order: row.order, isActive: status === 'running' }, plan })
  }

  for (const row of [...raw.action_asset_links.slice(0, ASSET_MAP_QUERY_MAXIMUMS.actionAssetLinks)].sort(byId)) {
    const link = row.core_assetvectorlink
    if (!validId(row.id) || !validId(row.action_id) || !validId(row.assetvectorlink_id) || link === null || link.id !== row.assetvectorlink_id) { skip(diagnostics, 'malformed_relation'); continue }
    const target = assetReference(link, diagnostics)
    if (target === null) continue
    const action = actions.get(row.action_id)
    const targetMetadata = nodeState.metadata.get(target)
    if (action === undefined || targetMetadata === undefined) { skip(diagnostics, 'missing_asset'); continue }
    if (!targetMetadata.actions.some((item) => item.id === action.summary.id)) targetMetadata.actions.push(action.summary)
    if (action.plan !== null && !targetMetadata.plans.some((item) => item.id === action.plan?.id)) targetMetadata.plans.push(action.plan)
    targetMetadata.isActive ||= action.summary.isActive
  }

  for (const row of [...raw.asset_locks.slice(0, ASSET_MAP_QUERY_MAXIMUMS.assetLocks)].sort(byId)) {
    if (!validId(row.id)) { skip(diagnostics, 'malformed_relation'); continue }
    if (row.target_id !== raw.target.id) { skip(diagnostics, 'cross_target'); continue }
    if (row.lock_status !== 'HELD') { skip(diagnostics, 'malformed_relation'); continue }
    const target = assetReference(row, diagnostics)
    if (target === null) continue
    const targetMetadata = nodeState.metadata.get(target)
    if (targetMetadata === undefined) { skip(diagnostics, 'missing_asset'); continue }
    if (targetMetadata.attributes.lockStatus === undefined) {
      targetMetadata.attributes.lockStatus = row.lock_status
      targetMetadata.attributes.lockAgentRole = row.agent_role
      targetMetadata.attributes.lockAcquiredAt = row.acquired_at
    }
    targetMetadata.isActive = true
  }

  for (const item of nodeState.metadata.values()) {
    item.actions.sort((left, right) => left.order - right.order || left.id.localeCompare(right.id))
    item.plans.sort((left, right) => left.id.localeCompare(right.id))
  }
  applyTruncation(raw, diagnostics)
  return { targetId, nodes: nodeState.nodes, edges: edgeState.edges, diagnostics }
}
