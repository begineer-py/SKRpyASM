# CR-0006：狀態資訊僅透過顏色表達，缺乏文字/圖示輔助

- Status: Open
- Severity: P2
- Domain: Frontend
- Confidence: High
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Fingerprint: frontend/color-only-status/global.css/status-indicators

## Summary

多處狀態指示器（連線狀態、執行狀態、嚴重程度等）僅使用顏色區分，缺乏文字標籤或圖示輔助，違反 CLAUDE.md 6.4 節「狀態資訊是否只透過顏色表達」規則，不符合無障礙設計原則（色盲用戶無法區分）。

## Evidence

- File: `frontend/src/global.css`
- Lines: 591-592, 711-713, 653-654, 398-402
- Symbol: status indicators

1. **Agent Tree 連線狀態** (Line 711-713)：
```css
.tree-live-dot { display: inline-block; width: 7px; height: 7px; border-radius: 99px; }
.tree-live-dot.connected { background: #22c55e; box-shadow: 0 0 10px #22c55e; }
.tree-live-dot.disconnected { background: #f59e0b; }
```
僅用綠/黃色圓點，無文字說明「已連線/斷線」。

2. **Thread 項目選中狀態** (Line 633-634)：
```css
.ai-thread-item.is-selected { background: linear-gradient(...); border-color: rgba(96, 165, 250, 0.35); box-shadow: inset 2px 0 0 #38bdf8; }
```
僅用藍色邊框/陰影表示選中，無輔助指示。

3. **狀態徽章** (Line 653-654)：
```css
.ai-status-badge { padding: 3px 6px; color: #a7f3d0; font: 700 0.54rem var(--font-mono); text-transform: uppercase; background: rgba(34, 197, 94, 0.11); border: 1px solid rgba(34, 197, 94, 0.22); border-radius: 99px; }
```
雖有文字但字體極小 (0.54rem = 8.6px)，且僅綠色系。

4. **嚴重程度徽章** (Line 398-402)：
```css
.c2-badge--green  { color: var(--green); background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.3); }
.c2-badge--cyan   { color: var(--cyan);  background: rgba(0,240,255,0.1); border: 1px solid rgba(0,240,255,0.3); }
.c2-badge--red    { color: var(--red);   background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); }
.c2-badge--amber  { color: var(--amber); background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.3); }
.c2-badge--purple { color: var(--purple); background: rgba(168,85,247,0.1); border: 1px solid rgba(168,85,247,0.3); }
.c2-badge--muted  { color: var(--text-secondary); background: rgba(71,85,105,0.2); border: 1px solid rgba(71,85,105,0.3); }
```
純色區分嚴重程度（綠/青/紅/琥珀/紫/灰），無圖示或文字前綴。

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

## Resolution criteria

所有狀態資訊皆有至少兩種表達方式（顏色 + 文字/圖示），且通過無障礙檢查。

## Notes

此為系統性無障礙問題，涉及全域樣式與多個元件（AgentPanel、Sidebar、ThreadItem、Badge 等）。修復需建立統一的狀態指示元件模式。