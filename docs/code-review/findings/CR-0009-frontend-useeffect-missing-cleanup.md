# CR-0009：useEffect 缺乏清理函數可能導致記憶體洩漏

- Status: **Partially Fixed**
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
- Lines: 128-238, 247, 326-394, 457-520
- Symbol: useEffect hooks

### Cycle 6 (2026-07-17) 重新審查結果：

1. **Agent Tree 訂閱** (Lines 128-138)：
```tsx
useEffect(() => {
  if (!rootThreadId) { setAgentTree([]); return; }
  // ... buildTreeNodes
  setAgentTree(nodes);
}, [treeRawData, rootThreadId]);
```
- 依賴 `useHasuraSubscription` 回傳的 `treeRawData`，訂閱由 hook 內部管理 (GraphQL subscription 會隨變數變化自動重新訂閱/清理)

2. **Execution Graphs 載入** (Lines 140-169)：
```tsx
useEffect(() => {
  let cancelled = false;
  // ... async fetch
  if (cancelled) return;
  setActiveThreadGraphs(graphs);
  return () => { cancelled = true; };
}, [activeNodeThreadId]);
```
- ✅ 有 `cancelled` 模式，正確保護非同步完成後的 setState

3. **Dispatches 載入** (Lines 171-188)：
```tsx
useEffect(() => {
  let cancelled = false;
  void executionApi.listDispatches(...).then(...)
  return () => { cancelled = true; };
}, [selectedThreadId]);
```
- ✅ 有 `cancelled` 模式，依賴項精確 (`selectedThreadId`)

4. **Dispatch Tree 載入** (Lines 190-207)：
```tsx
useEffect(() => {
  let cancelled = false;
  void executionApi.getDispatchTree(rootThreadId).then(...)
  return () => { cancelled = true; };
}, [rootThreadId, dispatchedGraphs.length]);
```
- ⚠️ 依賴 `dispatchedGraphs.length` 會導致每次 dispatch 更新重新觸發，可能造成重複請求

5. **Target Topology 載入** (Lines 209-227) 和 **Overviews 載入** (Lines 229-238)：
- ✅ 都有 `cancelled` 模式

6. **WebSocket 訊息串流 + 輪詢** (Lines 326-394) - **最關鍵**：
```tsx
useEffect(() => {
  if (!selectedThreadId) return;
  cleanupMessageEventsRef.current?.();
  if (pollTimerRef.current) { clearInterval(pollTimerRef.current); }
  let cancelled = false;
  const init = async () => {
    const parsed = await loadMessagesForThread(selectedThreadId);
    if (cancelled) return;
    // ... setup SSE stream
    if (hasPending) {
      pollTimerRef.current = setInterval(async () => {
        if (cancelled || attempts >= maxAttempts) { ... }
        attempts++;
        const msgs = await loadMessagesForThread(selectedThreadId);
        // ...
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
- ✅ 輪詢中有 `cancelled` 檢查和 `maxAttempts` 限制
- ✅ `loadMessagesForThread` 呼叫前有 `if (cancelled) return` 保護

7. **Thread 載入** (Line 247)：
```tsx
// eslint-disable-next-line react-hooks/exhaustive-deps
useEffect(() => { loadThreads(); }, [showInternal]);
```
- ❌ 仍註釋禁用 exhaustive-deps，`loadThreads` 內部呼叫多個 setState，依賴項不完整 (缺少 `selectedThreadId` 等)
- ❌ `loadThreads` 無 `cancelled` 保護，組件卸載時可能觸發 setState

8. **發送訊息** (Lines 457-520)：
```tsx
// eslint-disable-next-line react-hooks/exhaustive-deps
}, [inputVal, selectedThreadId, selectedThreadData, activeAssistantId, streamingText, clearDraft]);
```
- ⚠️ 依賴 `selectedThreadData` 物件參考，每次渲染可能新建導致重複發送
- ✅ 有 `cleanupStreamRef.current` 清理 SSE 連線
- ❌ 回調中無 `cancelled` 保護非同步完成 (`loadMessagesForThread` 等)

### 改善摘要 (Cycle 6)：
- ✅ 5 個 useEffect 新增/保持 `cancelled` 模式 (Execution Graphs, Dispatches, Dispatch Tree, Topology, Overviews)
- ✅ SSE/輪詢 effect (Lines 326-394) 現在有完整清理：`cancelled` 旗標、SSE 清理、計時器清理、輪詢最大嘗試次數限制
- ⚠️ `loadThreads` effect 仍有 exhaustive-deps 禁用和缺乏 cancelled 保護
- ⚠️ `handleSend` callback 依賴項包含物件參考，且回調無 cancelled 保護
- ⚠️ Dispatch Tree effect 依賴 `dispatchedGraphs.length` 可能造成重複請求

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

**Cycle 6 驗證結果**:
- `npm run lint` - ✅ 通過
- `npx tsc --noEmit` - ✅ 通過

## Resolution criteria

所有 useEffect 皆有完整清理邏輯，無 unmount 後 setState 警告，依賴項完整正確。

**Cycle 6 狀態**: Partially Fixed - 關鍵 SSE/輪詢 effect 已修復，`loadThreads` 和 `handleSend` 仍需改善。

## Notes

此問題涉及核心頁面的即時通訊邏輯，修復需謹慎測試。建議優先處理 WebSocket/輪詢相關的 effect（Lines 361-429），風險最高。

**Cycle 6 進展**: 關鍵的 SSE/輪詢 effect (Lines 326-394) 已大幅改善，具備完整清理邏輯。剩餘問題集中在 `loadThreads` effect (exhaustive-deps 禁用、無 cancelled) 和 `handleSend` callback (依賴項物件參考、回調無 cancelled)。