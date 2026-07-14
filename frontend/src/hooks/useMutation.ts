import { useState, useCallback, useRef, useEffect } from 'react';

interface UseMutationReturn<TData, TVariables> {
  mutate: (variables: TVariables) => Promise<TData | null>;
  data: TData | null;
  loading: boolean;
  error: Error | null;
  reset: () => void;
}

/**
 * Mutation hook for POST/PUT/PATCH/DELETE operations.
 * Does NOT auto-execute — call mutate() explicitly.
 *
 * When TVariables is void (default), call mutate() with no arguments.
 * When TVariables is a concrete type, pass the required variables.
 *
 * @param mutationFn - Async function that performs the mutation.
 */
export function useMutation<TData = unknown, TVariables = void>(
  mutationFn: (variables: TVariables) => Promise<TData>,
): UseMutationReturn<TData, TVariables> {
  const [data, setData] = useState<TData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const mountedRef = useRef(true);
  const mutationVersionRef = useRef(0);
  const mutationFnRef = useRef(mutationFn);
  mutationFnRef.current = mutationFn;

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const mutate = useCallback(
    async (variables: TVariables): Promise<TData | null> => {
      const version = ++mutationVersionRef.current;
      setLoading(true);
      setError(null);
      try {
        const result = await mutationFnRef.current(variables);
        if (!mountedRef.current || version !== mutationVersionRef.current) {
          return null;
        }
        setData(result);
        setLoading(false);
        return result;
      } catch (err: unknown) {
        if (!mountedRef.current || version !== mutationVersionRef.current) {
          return null;
        }
        const errorObj = err instanceof Error ? err : new Error(String(err));
        setError(errorObj);
        setLoading(false);
        return null;
      }
    },
    [],
  );

  const reset = useCallback(() => {
    setData(null);
    setLoading(false);
    setError(null);
  }, []);

  return { mutate, data, loading, error, reset };
}
