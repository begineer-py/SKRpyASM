export type GraphQuery =
  | { readonly kind: 'missing' }
  | { readonly kind: 'valid'; readonly graphId: number }
  | { readonly kind: 'invalid'; readonly value: string }

export function parseGraphQuery(value: string | null): GraphQuery {
  if (value === null) {
    return { kind: 'missing' }
  }

  if (!/^[1-9]\d*$/.test(value)) {
    return { kind: 'invalid', value }
  }

  const graphId = Number(value)
  if (!Number.isSafeInteger(graphId)) {
    return { kind: 'invalid', value }
  }

  return { kind: 'valid', graphId }
}
