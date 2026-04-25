// frontend/src/apolloClient.ts
import { ApolloClient, InMemoryCache, HttpLink, split } from '@apollo/client';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { createClient } from 'graphql-ws';
import { getMainDefinition } from '@apollo/client/utilities';
import { GLOBAL_CONFIG } from './config';

// 1. HTTP 連結 (用於 Query / Mutation)
const httpLink = new HttpLink({
  uri: GLOBAL_CONFIG.HASURA_GRAPHQL_URL,
  headers: {
    'x-hasura-admin-secret': GLOBAL_CONFIG.HASURA_ADMIN_SECRET,
  },
});

// 2. WebSocket 連結 (用於 Subscription)
// 將 http:// 替換為 ws://
const wsUrl = GLOBAL_CONFIG.HASURA_GRAPHQL_URL.replace('http', 'ws');
const wsLink = new GraphQLWsLink(createClient({
  url: wsUrl,
  connectionParams: {
    headers: {
      'x-hasura-admin-secret': GLOBAL_CONFIG.HASURA_ADMIN_SECRET,
    }
  }
}));

// 3. 使用 split 路由請求: 如果是 subscription 走 wsLink，否則走 httpLink
const splitLink = split(
  ({ query }) => {
    const definition = getMainDefinition(query);
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    );
  },
  wsLink,
  httpLink,
);

export const apolloClient = new ApolloClient({
  link: splitLink,
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
    },
  },
});

