import { useEffect, useState } from 'react';
import { createClient } from 'graphql-ws';
import { GLOBAL_CONFIG } from '../config';

const wsUrl = GLOBAL_CONFIG.HASURA_GRAPHQL_URL.replace('http', 'ws');

const wsClient = createClient({
  url: wsUrl,
  connectionParams: {
    headers: {
      'x-hasura-admin-secret': GLOBAL_CONFIG.HASURA_ADMIN_SECRET,
    }
  }
});

export function useHasuraSubscription(query: string) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const unsubscribe = wsClient.subscribe(
      { query },
      {
        next: (res) => {
          setData(res.data);
          setLoading(false);
        },
        error: (err) => {
          console.error('GraphQL WS Error:', err);
          setError(new Error(JSON.stringify(err)));
          setLoading(false);
        },
        complete: () => {
          // Subscription closed
        },
      }
    );

    return () => {
      unsubscribe();
    };
  }, [query]);

  return { data, loading, error };
}
