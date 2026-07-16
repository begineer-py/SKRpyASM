import { GetTargetAssetMapDocument } from '@/gql/graphql'
import type { GetTargetAssetMapQuery, GetTargetAssetMapQueryVariables } from '@/gql/graphql'
import { executeGraphQL } from '@/services/gqlClient'
import { projectGraph } from '../assetMap/projectGraph'
import type { AssetMapGraph } from '../assetMap/types'

export const ASSET_MAP_LOAD_ERROR_KINDS = ['invalid_target', 'aborted', 'load_failed'] as const

export type AssetMapLoadErrorKind = (typeof ASSET_MAP_LOAD_ERROR_KINDS)[number]

export type TargetAssetMapLoadOptions = {
  readonly signal?: AbortSignal
}

const assetMapLoadErrorMessages = {
  invalid_target: 'Target ID must be a positive integer',
  aborted: 'Target asset map request was aborted',
  load_failed: 'Target asset map could not be loaded',
} as const satisfies Record<AssetMapLoadErrorKind, string>

export class AssetMapLoadError extends Error {
  readonly name = 'AssetMapLoadError'
  readonly kind: AssetMapLoadErrorKind

  constructor(
    kind: AssetMapLoadErrorKind,
    options?: ErrorOptions,
  ) {
    super(assetMapLoadErrorMessages[kind], options)
    this.kind = kind
  }
}

function awaitUntilAborted<T>(request: Promise<T>, signal: AbortSignal | undefined): Promise<T> {
  if (signal === undefined) return request
  if (signal.aborted) return Promise.reject(new AssetMapLoadError('aborted'))

  return new Promise<T>((resolve, reject) => {
    const rejectWhenAborted = () => {
      reject(new AssetMapLoadError('aborted'))
    }
    signal.addEventListener('abort', rejectWhenAborted, { once: true })
    request.then(
      (value) => {
        signal.removeEventListener('abort', rejectWhenAborted)
        resolve(value)
      },
      (error: unknown) => {
        signal.removeEventListener('abort', rejectWhenAborted)
        reject(error)
      },
    )
  })
}

export async function loadTargetAssetMap(
  targetId: number,
  options?: TargetAssetMapLoadOptions,
): Promise<AssetMapGraph | null> {
  if (!Number.isSafeInteger(targetId) || targetId <= 0) {
    throw new AssetMapLoadError('invalid_target')
  }
  if (options?.signal?.aborted) {
    throw new AssetMapLoadError('aborted')
  }

  try {
    const raw = await awaitUntilAborted(
      executeGraphQL<GetTargetAssetMapQuery, GetTargetAssetMapQueryVariables>(
        GetTargetAssetMapDocument,
        { targetId },
      ),
      options?.signal,
    )
    return projectGraph(raw)
  } catch (error) {
    if (error instanceof AssetMapLoadError) throw error
    if (options?.signal?.aborted || (error instanceof Error && error.name === 'AbortError')) {
      throw new AssetMapLoadError('aborted', { cause: error })
    }
    throw new AssetMapLoadError('load_failed', { cause: error })
  }
}
