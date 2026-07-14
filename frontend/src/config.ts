
// Vite 只暴露 VITE_ 前綴的環境變數（舊的 REACT_APP_ 前綴會被忽略）
// fallback 值對齊 docker-compose.yml 的 HASURA_GRAPHQL_ADMIN_SECRET，方便本機快速啟動
const FALLBACK_SECRET = 'YourSuperStrongAdminSecretHere';

export const GLOBAL_CONFIG = {
    DJANGO_API_BASE: `${window.location.origin}/api`,
    HASURA_GRAPHQL_URL: `${window.location.origin}/graphql`,
    HASURA_ADMIN_SECRET: import.meta.env.VITE_HASURA_ADMIN_SECRET ?? FALLBACK_SECRET,
};