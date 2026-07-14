import { GLOBAL_CONFIG } from '../config';

interface GraphQLDocument {
  loc?: { source?: { body?: string } };
}

interface GraphQLQueryError {
  message: string;
}

/**
 * Typed GraphQL executor for Hasura.
 *
 * Takes a typed DocumentNode from graphql-codegen and returns the typed result.
 * Bridges the gap between codegen's DocumentNode and the raw fetch-based gqlFetcher.
 */
export async function executeGraphQL<TResult, TVariables>(
  document: GraphQLDocument,
  variables?: TVariables,
  options?: { adminSecret?: string },
): Promise<TResult> {
  const query = document.loc?.source?.body ?? '';

  const res = await fetch(GLOBAL_CONFIG.HASURA_GRAPHQL_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-hasura-admin-secret': options?.adminSecret ?? GLOBAL_CONFIG.HASURA_ADMIN_SECRET,
    },
    body: JSON.stringify({
      query,
      variables: variables ?? {},
    }),
  });

  const json = await res.json();
  if (json.errors) {
    const msg = (json.errors as GraphQLQueryError[]).map((e) => e.message).join(', ');
    throw new Error(msg);
  }
  return json.data as TResult;
}
