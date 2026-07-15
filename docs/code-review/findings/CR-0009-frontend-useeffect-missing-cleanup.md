# CR-0009：useEffect 缺乏清理函數可能導致記憶體洩漏

- Status: Open
- Severity: P2
- Domain: Frontend
- Confidence: High
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Fingerprint: frontend/useeffect-cleanup/AICenterPage/multiple-effects

## Summary

`AICenterPage.tsx` 中多個 `useEffect` 註冊訂閱、計時器、事件監聽器但缺乏完整清理邏輯，可能導致組件卸載後狀態更新、記憶體洩漏或競態條件。

## Evidence

- File: `frontend/src/features/ai/pages/AICenterPage.tsx`
- Lines: 135-145, 147-185, 187-223, 225-243, 245-254, 361-429
- Symbol: useEffect hooks

1. **Agent Tree 訂閱** (Lines 135-145)：
```tsx
useEffect(() => {
  if (!rootThreadId) { setAgentTree([]); return; }
  const nodes = buildTreeNodes(treeRawData, rootThreadId);
  setAgentTree(nodes);
}, [treeRawData, rootThreadId]);
```
- 依賴 `useHasuraSubscription` 回傳的 `treeRawData`，但未清理訂閱（由 hook 內部管理，需確認 hook 實作）

2. **Execution Graphs 載入** (Lines 147-185)：
```tsx
useEffect(() => {
  let cancelled = false;
  // ... async fetch
  return () => { cancelled = true; };
}, [activeNodeThreadId, graphPage, graphStatusFilter]);
```
- ✅ 有 `cancelled` 模式，但 `executionApi.listGraphs()` 返回的 Promise 無法取消，僅防止狀態更新

3. **Dispatch Tree 載入** (Lines 225-243)：
```tsx
useEffect(() => {
  let cancelled = false;
  void executionApi.getDispatchTree(rootThreadId).then(...)
  return () => { cancelled = true; };
}, [rootThreadId, dispatchedGraphs.length]);
```
- 依賴 `dispatchedGraphs.length` 會導致每次 dispatch 更新重新觸發，可能造成重複請求

4. **WebSocket 訊息串流 + 輪詢** (Lines 361-429) - **最關鍵**：
```tsx
useEffect(() => {
  if (!selectedThreadId) return;

  cleanupMessageEventsRef.current?.();
  if (pollTimerRef.current) { clearInterval(pollTimerRef.current); }

  let cancelled = false;
  const init = async () => {
    // ... setup SSE stream
    cleanupMessageEventsRef.current = assistantApi.streamMessageEvents(...);
    
    if (hasPending) {
      pollTimerRef.current = setInterval(async () => {
        // ... poll for completion
      }, 2000);
    }
  };
  init();

  return () => {
    cancelled = true;
    cleanupMessageEventsRef.current?.();
    if (pollTimerRef.current) { clearInterval(pollTimerRef.current); }
  };
}, [selectedThreadId]);
```
- ✅ 有清理 SSE 連線和計時器
- ⚠️ `loadMessagesForThread` 在清理後仍可能完成並觸發 `setMessages`，雖有 `cancelled` 檢查但非同步操作可能在清理後完成

5. **Thread 載入** (Lines 264-265)：
```tsx
// eslint-disable-next-line react-hooks/exhaustive-deps
useEffect(() => { loadThreads(); }, [targetSearchId, showInternal]);
```
- 註釋禁用 exhaustive-deps，`loadThreads` 內部呼叫 `setAllThreads`、`setSelectedThreadData` 等，依賴項不完整

6. **發送訊息** (Lines 491-554)：
```tsx
// eslint-disable-next-line react-hooks/exhaustive-deps
}, [inputVal, selectedThreadId, selectedThreadData, activeAssistantId, streamingText, clearDraft]);
```
- 依賴 `selectedThreadData` 物件參考，每次渲染可能新建導致重複發送
- `cleanupStreamRef.current` 清理但無 `cancelled` 保護非同步完成

## Trigger

審查 AICenterPage 核心邏輯的 useEffect 使用情況。

## Impact

1. **記憶體洩漏**：未清理的訂閱、計時器持續佔用資源
2. **競態條件**：組件卸載後非同步操作完成觸發 setState，React 警告 "Can't perform a React state update on an unmounted component"
3. **重複請求**：依賴項不精確導致重複 API 呼叫
4. **狀態不一致**：多個 effect 交互更新共享狀態可能造成不一致

## Why this matters

CLAUDE.md 6.6 節要求檢查：「非同步請求是否可能在 component unmount 後更新狀態」、「是否有未清理的 subscription、timer 或 event listener」。AICenterPage 是核心頁面，包含複雜的即時通訊邏輯，必須嚴格管理副作用生命週期。

## Recommended change

1. **統一使用 `cancelled` 模式保護所有非同步操作**：
```tsx
useEffect(() => {
  let cancelled = false;
  const fetch = async () => {
    const data = await api.call();
    if (!cancelled) setData(data);
  };
  fetch();
  return () => { cancelled = true; };
}, [deps]);
```

2. **修正 `loadThreads` effect 依賴項**：將 `loadThreads` 包裝在 `useCallback` 中，正確宣告依賴。

3. **`handleSend` effect 依賴項優化**：`selectedThreadData` 應改用 `selectedThreadId` + 從 state 取得，或使用 `useRef` 保存最新值。

4. **考慮使用 `useEffectEvent` (React 19)** 或 `useEvent` pattern 處理事件回調。

5. **SSE 連線管理提取到自定義 hook**：`useMessageStream(threadId)` 封裝連線、重連、清理邏輯。

## Verification

1. 開啟 React DevTools Profiler，檢查組件卸載後無狀態更新警告
2. 快速切換對話執行緒，觀察 Network 面板無重複/殘留請求
3. 長時間開啟頁面，檢查記憶體使用量無持續增長
4. 運行 `npm run test` 確認無測試回歸

## Resolution criteria

所有 useEffect 皆有完整清理邏輯，無 unmount 後 setState 警告，依賴項完整正確。

## Notes

此問題涉及核心頁面的即時通訊邏輯，修復需謹慎測試。建議優先處理 WebSocket/輪詢相關的 effect（Lines 361-429），風險最高。