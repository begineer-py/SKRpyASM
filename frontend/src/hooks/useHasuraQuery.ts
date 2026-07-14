import { useState, useEffect, useCallback } from 'react';
import { GLOBAL_CONFIG } from '../config';

/**
 * One-shot Hasura HTTP GraphQL query hook.
 * Use this for reads that don't need realtime updates.
 * For realtime, keep using useHasuraSubscription (WebSocket).
 */
interface GraphQLQueryError {
  message: string;
}

export function useHasuraQuery<T = unknown>(
  query: string,
  variables?: Record<string, unknown>,
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const execute = useCallback(async (overrideVars?: Record<string, unknown>) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(GLOBAL_CONFIG.HASURA_GRAPHQL_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-hasura-admin-secret': GLOBAL_CONFIG.HASURA_ADMIN_SECRET,
        },
        body: JSON.stringify({
          query,
          variables: overrideVars ?? variables,
        }),
      });
      const json = await res.json();
      if (json.errors) {
        throw new Error((json.errors as GraphQLQueryError[]).map((e) => e.message).join(', '));
      }
      setData(json.data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, JSON.stringify(variables)]);

  useEffect(() => {
    execute();
  }, [execute]);

  return { data, loading, error, refetch: execute };
}
