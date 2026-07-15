import type { CodegenConfig } from '@graphql-codegen/cli';

const config: CodegenConfig = {
  schema: [
    {
      'http://localhost:8085/v1/graphql': {
        headers: {
          'x-hasura-admin-secret': 'YourSuperStrongAdminSecretHere',
        },
      },
    },
  ],
  documents: ['src/**/*.{ts,tsx}', 'src/**/*.graphql'],
  ignoreNoDocuments: true,
  generates: {
    './src/gql/': {
      preset: 'client',
      config: {
        useTypeImports: true,
        // Hasura exposes PostgreSQL scalars as custom GraphQL scalars.  Without
        // explicit mappings codegen falls back to `unknown`, which makes every
        // generated operation incompatible with the application domain types.
        scalars: {
          bigint: { input: 'number', output: 'number' },
          numeric: { input: 'number', output: 'number' },
          timestamptz: { input: 'string', output: 'string' },
          timestamp: { input: 'string', output: 'string' },
          date: { input: 'string', output: 'string' },
          jsonb: { input: 'unknown', output: 'unknown' },
          uuid: { input: 'string', output: 'string' },
        },
      },
      presetConfig: {
        gqlTagName: 'gql',
      },
    },
  },
};

export default config;
