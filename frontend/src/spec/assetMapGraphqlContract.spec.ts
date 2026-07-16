import {
  Kind,
  parse,
  type DocumentNode,
  type FieldNode,
  type OperationDefinitionNode,
  type SelectionNode,
} from 'graphql'
import { describe, expect, it } from 'vitest'
import assetMapQuery from '../graphql/asset-map.graphql?raw'

const twoHopRelationQuery = `
  query GetTargetAssetMap($targetId: bigint!) {
    subdomains: core_subdomain(where: { target_id: { _eq: $targetId } }) {
      core_subdomain_ips {
        core_ip {
          id
        }
      }
    }
  }
`

const aliasBypassRootQuery = `
  query GetTargetAssetMap($targetId: bigint!) {
    seeds: core_vulnerability(where: { target_id: { _eq: $targetId } }) {
      id
    }
  }
`

type RootContract = {
  readonly fieldName: string
  readonly directRelations: readonly string[]
}

const rootContracts = new Map<string, RootContract>([
  ['target', { fieldName: 'core_target_by_pk', directRelations: [] }],
  ['seeds', { fieldName: 'core_seed', directRelations: [] }],
  ['subdomains', { fieldName: 'core_subdomain', directRelations: ['core_subdomain_ips'] }],
  ['ips', { fieldName: 'core_ip', directRelations: [] }],
  ['ports', { fieldName: 'core_port', directRelations: [] }],
  ['urls', { fieldName: 'core_urlresult', directRelations: ['core_urlresult_related_subdomains'] }],
  ['asset_edges', { fieldName: 'core_assetedge', directRelations: [] }],
  ['actions', { fieldName: 'core_action', directRelations: ['core_attackplan'] }],
  ['action_asset_links', { fieldName: 'core_action_asset_links', directRelations: ['core_assetvectorlink'] }],
  ['asset_locks', { fieldName: 'core_assetlock', directRelations: [] }],
])

const aggregateRootFields = new Map<string, string>([
  ['seeds_aggregate', 'core_seed_aggregate'],
  ['subdomains_aggregate', 'core_subdomain_aggregate'],
  ['ips_aggregate', 'core_ip_aggregate'],
  ['ports_aggregate', 'core_port_aggregate'],
  ['urls_aggregate', 'core_urlresult_aggregate'],
  ['asset_edges_aggregate', 'core_assetedge_aggregate'],
  ['actions_aggregate', 'core_action_aggregate'],
  ['action_asset_links_aggregate', 'core_action_asset_links_aggregate'],
  ['asset_locks_aggregate', 'core_assetlock_aggregate'],
])

function getGetTargetAssetMapOperation(document: DocumentNode): OperationDefinitionNode {
  const operation = document.definitions.find(
    (definition): definition is OperationDefinitionNode =>
      definition.kind === Kind.OPERATION_DEFINITION && definition.name?.value === 'GetTargetAssetMap',
  )

  if (operation === undefined) {
    throw new Error('GetTargetAssetMap operation is missing')
  }

  return operation
}

function getFieldSelections(selections: readonly SelectionNode[], path: string): readonly FieldNode[] {
  return selections.map((selection) => {
    if (selection.kind !== Kind.FIELD) {
      throw new Error(`${path} must not use fragments`)
    }

    return selection
  })
}

function getChildFields(field: FieldNode, path: string): readonly FieldNode[] {
  if (field.selectionSet === undefined) {
    throw new Error(`${path} must have a selection set`)
  }

  return getFieldSelections(field.selectionSet.selections, path)
}

function assertScalarChildren(field: FieldNode, path: string): void {
  for (const child of getChildFields(field, path)) {
    if (child.selectionSet !== undefined) {
      throw new Error(`Relation path ${path} exceeds one direct relation at ${child.name.value}`)
    }
  }
}

function assertAggregateSelection(root: FieldNode, rootName: string): void {
  const aggregateFields = getChildFields(root, rootName)
  const aggregate = aggregateFields[0]

  if (aggregate === undefined || aggregateFields.length !== 1 || aggregate.name.value !== 'aggregate') {
    throw new Error(`${rootName} must select only aggregate`)
  }

  assertScalarChildren(aggregate, `${rootName}.aggregate`)
}

function assertOneHopRelationDepth(document: DocumentNode): readonly string[] {
  const relationPaths: string[] = []
  const operation = getGetTargetAssetMapOperation(document)
  const seenRootAliases = new Set<string>()
  const expectedRootAliases = new Set([...rootContracts.keys(), ...aggregateRootFields.keys()])

  for (const root of getFieldSelections(operation.selectionSet.selections, 'GetTargetAssetMap')) {
    const rootAlias = root.alias?.value ?? root.name.value
    const rootFieldName = root.name.value

    if (seenRootAliases.has(rootAlias)) {
      throw new Error(`Duplicate root response alias ${rootAlias}`)
    }

    seenRootAliases.add(rootAlias)
    const rootContract = rootContracts.get(rootAlias)

    if (rootContract !== undefined) {
      if (rootFieldName !== rootContract.fieldName) {
        throw new Error(`Root alias ${rootAlias} must select ${rootContract.fieldName}, received ${rootFieldName}`)
      }

      for (const child of getChildFields(root, rootAlias)) {
        if (child.selectionSet === undefined) {
          continue
        }

        if (!rootContract.directRelations.includes(child.name.value)) {
          throw new Error(`Unexpected relation ${rootAlias}.${child.name.value}`)
        }

        const relationPath = `${rootAlias}.${child.name.value}`
        assertScalarChildren(child, relationPath)
        relationPaths.push(relationPath)
      }
      continue
    }

    const aggregateFieldName = aggregateRootFields.get(rootAlias)
    if (aggregateFieldName !== undefined) {
      if (rootFieldName !== aggregateFieldName) {
        throw new Error(`Root alias ${rootAlias} must select ${aggregateFieldName}, received ${rootFieldName}`)
      }

      assertAggregateSelection(root, rootAlias)
      continue
    }

    throw new Error(`Unexpected root selection ${rootAlias}`)
  }

  if (seenRootAliases.size !== expectedRootAliases.size) {
    throw new Error('GetTargetAssetMap must select every expected root alias exactly once')
  }

  for (const rootAlias of expectedRootAliases) {
    if (!seenRootAliases.has(rootAlias)) {
      throw new Error(`GetTargetAssetMap is missing root alias ${rootAlias}`)
    }
  }

  return relationPaths
}

describe('GetTargetAssetMap GraphQL contract', () => {
  it('rejects a synthetic two-hop relation fixture', () => {
    // Given
    const document = parse(twoHopRelationQuery)

    // When / Then
    expect(() => assertOneHopRelationDepth(document)).toThrow('exceeds one direct relation')
  })

  it('rejects a response alias that disguises a forbidden root', () => {
    // Given
    const document = parse(aliasBypassRootQuery)

    // When / Then
    expect(() => assertOneHopRelationDepth(document)).toThrow('must select core_seed')
  })

  it('accepts the retained query with only the four allowed direct relations', () => {
    // Given
    const document = parse(assetMapQuery)

    // When
    const relationPaths = assertOneHopRelationDepth(document)

    // Then
    expect(relationPaths).toEqual([
      'subdomains.core_subdomain_ips',
      'urls.core_urlresult_related_subdomains',
      'actions.core_attackplan',
      'action_asset_links.core_assetvectorlink',
    ])
  })
})
