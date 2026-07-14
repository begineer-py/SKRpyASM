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
      presetConfig: {
        gqlTagName: 'gql',
      },
    },
  },
};

export default config;
