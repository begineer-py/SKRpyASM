import { useState, useEffect, useCallback, useRef } from 'react';

interface UseApiQueryOptions {
  /** Auto-fetch on mount (default: true) */
  immediate?: boolean;
  /** Callback when fetch fails */
  onError?: (error: Error) => void;
}

interface UseApiQueryReturn<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<T | null>;
}

/**
 * Generic data-fetching hook for REST API calls.
 * Patterned after useHasuraQuery but with strict types and race-condition safety.
 *
 * @param fetcher - Async function that returns the data. Caller provides the
 *                  fetch logic (typically using an apiClient instance).
 * @param deps - Dependency array — changing any value triggers a re-fetch.
 * @param options - Controls initial fetch behavior and error handling.
 */
export function useApiQuery<T = unknown>(
  fetcher: () => Promise<T>,
  deps: readonly unknown[] = [],
  options?: UseApiQueryOptions,
): UseApiQueryReturn<T> {
  const immediate = options?.immediate !== false;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState<Error | null>(null);

  const mountedRef = useRef(true);
  const fetchVersionRef = useRef(0);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;
  const onErrorRef = useRef(options?.onError);
  onErrorRef.current = options?.onError;

  const execute = useCallback(async (): Promise<T | null> => {
    const version = ++fetchVersionRef.current;
    setLoading(true);
    setError(null);
    try {
      const result = await fetcherRef.current();
      if (!mountedRef.current || version !== fetchVersionRef.current) {
        return null;
      }
      setData(result);
      setLoading(false);
      return result;
    } catch (err: unknown) {
      if (!mountedRef.current || version !== fetchVersionRef.current) {
        return null;
      }
      const errorObj = err instanceof Error ? err : new Error(String(err));
      setError(errorObj);
      setLoading(false);
      onErrorRef.current?.(errorObj);
      return null;
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    if (immediate) {
      execute();
    }
    return () => {
      mountedRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [execute, immediate, ...deps]);

  return { data, loading, error, refetch: execute };
}
