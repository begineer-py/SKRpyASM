import { useEffect, useState, useRef } from 'react';
import { createClient } from 'graphql-ws';
import { GLOBAL_CONFIG } from '../config';

const wsUrl = GLOBAL_CONFIG.HASURA_GRAPHQL_URL.replace('http', 'ws');

// 📍 P1 FIX: 改進 WebSocket 客戶端配置 - 添加自動重連和心跳
const wsClient = createClient({
  url: wsUrl,
  connectionParams: {
    headers: {
      'x-hasura-admin-secret': GLOBAL_CONFIG.HASURA_ADMIN_SECRET,
    }
  },
  keepAlive: 30_000, // 心跳間隔 30 秒
  retryAttempts: Infinity, // 無限重試
  shouldRetry: () => true, // 總是重試
});

export function useHasuraSubscription(query: string, variables?: Record<string, any>, enabled = true) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const retryCountRef = useRef(0);

  useEffect(() => {
    if (!enabled || !query.trim()) {
      setLoading(false);
      setIsConnected(false);
      return;
    }

    let unsubscribe: (() => void) | null = null;
    let reconnectTimeout: NodeJS.Timeout | null = null;

    const subscribe = () => {
      try {
        unsubscribe = wsClient.subscribe(
          { query, variables },
          {
            next: (res) => {
              setData(res.data);
              setLoading(false);
              setError(null);
              // 📍 P1 FIX: 成功收到數據時重置重試計數
              retryCountRef.current = 0;
              setIsConnected(true);
            },
            error: (err) => {
              console.error('GraphQL WS Error:', err);
              setError(new Error(JSON.stringify(err)));
              setIsConnected(false);
              
              // 📍 P1 FIX: 自動重連邏輯
              retryCountRef.current++;
              const backoffMs = Math.min(1000 * Math.pow(2, retryCountRef.current), 30_000);
              console.warn(`[WS] 連線失敗，${backoffMs}ms 後重連... (嘗試 #${retryCountRef.current})`);
              
              reconnectTimeout = setTimeout(() => {
                console.log(`[WS] 重新連線 (嘗試 #${retryCountRef.current})...`);
                subscribe();
              }, backoffMs);
            },
            complete: () => {
              // Subscription closed
              console.log('[WS] Subscription 已完成');
              setIsConnected(false);
            },
          }
        );
      } catch (err) {
        console.error('[WS] Subscribe failed:', err);
        setError(new Error(String(err)));
        setIsConnected(false);
      }
    };

    subscribe();

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (unsubscribe) unsubscribe();
    };
  }, [enabled, query, JSON.stringify(variables)]);

  return { data, loading, error, isConnected };
}
