# CR-0006：狀態資訊僅透過顏色表達，缺乏文字/圖示輔助

- Status: **Partially Fixed**
- Severity: P2
- Domain: Frontend
- Confidence: High
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Fingerprint: frontend/color-only-status/global.css/status-indicators

## Summary

多處狀態指示器（連線狀態、執行狀態、嚴重程度等）僅使用顏色區分，缺乏文字標籤或圖示輔助，違反 CLAUDE.md 6.4 節「狀態資訊是否只透過顏色表達」規則，不符合無障礙設計原則（色盲用戶無法區分）。

## Evidence

- File: `frontend/src/global.css` (Lines 909-911), `frontend/src/components/SubAgentContainerBlock.tsx`, `frontend/src/components/ExecutionTimelineViewer.tsx`
- Symbol: status indicators

### Cycle 6 (2026-07-17) 重新審查結果：

1. **Agent Tree 連線狀態** (global.css Lines 909-911) - **仍有問題**：
```css
.tree-live-dot { display: inline-block; width: 7px; height: 7px; border-radius: 99px; }
.tree-live-dot.connected { background: #22c55e; box-shadow: 0 0 10px #22c55e; }
.tree-live-dot.disconnected { background: #f59e0b; }
```
❌ 僅用綠/黃色圓點，無文字說明「已連線/斷線」。無 `aria-label`。

2. **SubAgentContainerBlock 狀態標籤** (SubAgentContainerBlock.tsx Lines 88-93) - **已改善**：
```tsx
<span className={cn('text-[0.68rem] font-semibold px-2 py-0.5 rounded-full uppercase tracking-[0.04em]', STATUS_STYLES[statusKey])}>
  {graph.status}
</span>
```
✅ 同時顯示顏色標籤 + 狀態文字 (RUNNING/WAITING/COMPLETED/FAILED/CANCELLED)。

3. **ExecutionTimelineViewer 節點狀態** (ExecutionTimelineViewer.tsx Lines 52-61, 160-162) - **已改善**：
```tsx
const NODE_STATUSES = [
  { value: 'RUNNING', label: 'Running', icon: '▶' },
  { value: 'WAITING', label: 'Waiting', icon: '⏸' },
  { value: 'SUCCEEDED', label: 'Succeeded', icon: '✓' },
  // ...
];
```
✅ 篩選器中每個狀態皆有圖示 + 文字標籤。狀態圖示 (STATUS_PILL) 搭配文字顯示。

4. **Thread 項目選中狀態** (global.css) - **部分改善**：
選中狀態透過藍色邊框/陰影表示，但列表項目本身有文字內容（執行緒名稱），選中狀態為輔助視覺指示，主要資訊仍由文字傳達。

5. **狀態徽章** (`.ai-status-badge`) - **仍有問題**：
字體極小 (0.54rem = 8.6px)，且僅綠色系。雖有文字但可讀性差。

6. **嚴重程度徽章** (`.c2-badge--*`) - **仍有問題**：
純色區分嚴重程度（綠/青/紅/琥珀/紫/灰），無圖示或文字前綴。需在使用處添加文字說明。

### 改善摘要 (Cycle 6)：
- ✅ SubAgentContainerBlock：狀態標籤現在包含文字
- ✅ ExecutionTimelineViewer：節點狀態篩選器有圖示 + 文字，狀態顯示有顏色 + 文字
- ❌ Agent Tree 連線狀態 (`.tree-live-dot`)：仍僅用色點，無文字/aria-label
- ❌ 通用嚴重程度徽章 (`.c2-badge--*`)：仍純色區分，需使用處補充文字
- ❌ `.ai-status-badge`：字體過小，可讀性差

## Trigger

依據 CLAUDE.md 6.4 節檢查狀態資訊表達方式。

## Impact

1. **色盲用戶無法區分**：紅綠色盲無法分辨紅/綠/琥珀狀態；藍黃色盲難分青/綠
2. **高對比度模式失效**：系統高對比度模式下顏色可能被覆蓋，導致狀態資訊遺失
3. **螢幕閱讀器無法識別**：純視覺狀態無語義標記

## Why this matters

CLAUDE.md 6.4 明確要求：「狀態資訊是否只透過顏色表達」。安全作業平台的狀態資訊（掃描中/完成/失敗、連線/斷線、嚴重程度）至關重要，必須多重編碼。

## Recommended change

1. **所有狀態指示器添加文字/圖示**：
   - 連線狀態：綠點 +「已連線」文字 / 黃點 +「斷線」文字
   - 執行狀態：使用語義圖示（播放/暫停/錯誤/完成）+ 文字
   - 嚴重程度徽章：添加圖示（盾牌/警告/資訊）或文字前綴（P0/P1/P2/P3）

2. **CSS 實作模式**：
```css
.status-indicator::before { content: ''; /* 圖示 */ }
.status-indicator[data-status="connected"]::after { content: '已連線'; }
```

3. **確保 ARIA 語義**：`role="status"` + `aria-label` 完整描述狀態

## Verification

1. 在瀏覽器高對比度模式下測試所有狀態指示器可見度
2. 使用色盲模擬器（如 Chrome DevTools 渲染模擬）驗證可區分度
3. 使用螢幕閱讀器確認狀態資訊可被朗讀

**Cycle 6 驗證結果**:
- SubAgentContainerBlock 狀態標籤 - ✅ 有文字 + 顏色
- ExecutionTimelineViewer 節點狀態 - ✅ 有圖示 + 文字 + 顏色
- Agent Tree 連線狀態 - ❌ 僅色點，無文字/aria-label
- 通用徽章 - ❌ 仍需改善

## Resolution criteria

所有狀態資訊皆有至少兩種表達方式（顏色 + 文字/圖示），且通過無障礙檢查。

**Cycle 6 狀態**: Partially Fixed - 關鍵業務元件 (SubAgentContainerBlock, ExecutionTimelineViewer) 已改善，但通用樣式 (.tree-live-dot, .c2-badge--*, .ai-status-badge) 仍需修復。

## Notes

此為系統性無障礙問題，涉及全域樣式與多個元件（AgentPanel、Sidebar、ThreadItem、Badge 等）。修復需建立統一的狀態指示元件模式。