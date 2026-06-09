/**
 * useStepLogGql — Hasura GQL 版的工具調用日誌 hook
 *
 * 與 useStepLogStream (SSE) 介面相容，StepLogViewer 可直接替換。
 * 依賴 Hasura 已追蹤 core_steplog 表，並有 x-hasura-admin-secret 可存取。
 */

import { useMemo } from 'react';
import { useHasuraSubscription } from './useHasuraSubscription';
import { SUBSCRIBE_STEP_LOGS } from '../queries';
import type { StepLog } from './useStepLogStream';

const NOOP_SUB = `subscription { __typename }`;

export function useStepLogGql(stepId: number | null) {
  const vars = useMemo(
    () => (stepId && stepId > 0 ? { stepId } : undefined),
    [stepId]
  );

  const { data, isConnected, error } = useHasuraSubscription(
    stepId && stepId > 0 ? SUBSCRIBE_STEP_LOGS : NOOP_SUB,
    vars
  );

  const logs: StepLog[] = useMemo(
    () => (data?.core_steplog ?? []) as StepLog[],
    [data]
  );

  const lastSequence = logs.length > 0 ? logs[logs.length - 1].sequence : 0;

  return { logs, isConnected, error, lastSequence };
}
