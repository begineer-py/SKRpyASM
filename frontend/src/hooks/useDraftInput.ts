import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * localStorage 草稿 key 前綴，組合 threadId 後即為完整 key。
 * 匯出方便測試時驗證 key 命名規則。
 */
export const DRAFT_KEY_PREFIX = 'draft:thread:';

/** debounce 寫入 localStorage 的延遲毫秒數。 */
const PERSIST_DEBOUNCE_MS = 300;

/**
 * 以 thread 為單位的輸入草稿持久化 hook。
 *
 * 解決 AI 對話頁切換 navbar 分頁時，React Router unmount 整個頁面
 * 導致已打好但未送出的 prompt 遺失的問題。每個 thread 的草稿獨立儲存於
 * localStorage，並以 debounce 避免每次 keystroke 都寫入。
 *
 * 行為概要：
 * 1. `threadId` 變化（含初次 mount）時從 localStorage 還原草稿。
 * 2. `setValue` 立即更新 state，並 debounce 300ms 寫入 localStorage。
 * 3. `clearOnSend()` 移除 localStorage key 並清空 state。
 * 4. `threadId === null` 時退化為純記憶體 state，不讀寫 localStorage。
 *
 * @param threadId 當前對話 thread 的識別字；`null` 表示尚未選定 thread。
 * @returns `[value, setValue, clearOnSend]` 三元組。
 */
export function useDraftInput(
  threadId: string | null,
): [string, (v: string) => void, () => void] {
  const [value, setValue] = useState<string>('');

  // debounce timeout id，新寫入前必須清掉前一個。
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  /**
   * 還原草稿：threadId 變化時（含初次 mount）從 localStorage 讀取。
   * null threadId 跳過讀取，保留空字串。
   */
  useEffect(() => {
    setValue('');

    if (threadId === null) {
      return;
    }
    if (typeof window === 'undefined') {
      return;
    }

    const stored = window.localStorage.getItem(DRAFT_KEY_PREFIX + threadId);
    if (stored !== null) {
      setValue(stored);
    }
  }, [threadId]);

  /**
   * unmount 或 re-render 時清掉未觸發的 debounce timeout，
   * 避免元件已銷毀仍嘗試寫入 localStorage。
   */
  useEffect(() => {
    return () => {
      if (debounceRef.current !== null) {
        clearTimeout(debounceRef.current);
        debounceRef.current = null;
      }
    };
  }, []);

  /**
   * 更新草稿值：立即反映到 state，並 debounce 寫入 localStorage。
   * null threadId 時只更新 state，不觸碰 storage。
   */
  const setDraft = useCallback(
    (next: string) => {
      setValue(next);

      if (threadId === null) {
        return;
      }
      if (typeof window === 'undefined') {
        return;
      }

      if (debounceRef.current !== null) {
        clearTimeout(debounceRef.current);
      }

      debounceRef.current = setTimeout(() => {
        debounceRef.current = null;
        window.localStorage.setItem(DRAFT_KEY_PREFIX + threadId, next);
      }, PERSIST_DEBOUNCE_MS);
    },
    [threadId],
  );

  /**
   * 送出後清空草稿：移除 localStorage key 並重置 state。
   * 同時取消任何進行中的 debounce 寫入，避免覆寫回舊值。
   */
  const clearOnSend = useCallback(() => {
    if (debounceRef.current !== null) {
      clearTimeout(debounceRef.current);
      debounceRef.current = null;
    }

    setValue('');

    if (threadId === null) {
      return;
    }
    if (typeof window === 'undefined') {
      return;
    }

    window.localStorage.removeItem(DRAFT_KEY_PREFIX + threadId);
  }, [threadId]);

  return [value, setDraft, clearOnSend];
}
