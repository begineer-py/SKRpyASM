# CR-0004：AI Workbench 使用固定 grid-template-columns 缺乏流體響應

- Status: Open
- Severity: P2
- Domain: Frontend
- Confidence: High
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Fingerprint: frontend/fixed-grid/ai-workbench-shell/grid-template-columns

## Summary

`.ai-workbench-shell` 使用固定的 `grid-template-columns: minmax(260px, 296px) minmax(420px, 1fr) minmax(300px, 360px)`，雖使用 `minmax()` 但缺乏針對小螢幕的流體響應策略。在 720px 以下才強制單欄，中間尺寸（768px-1240px）僅透過媒體查詢調整最小寬度，未考慮內容優先級重排。

## Evidence

- File: `frontend/src/global.css`
- Lines: 584, 763-780
- Symbol: .ai-workbench-shell grid-template-columns

```css
.ai-workbench-shell { 
  grid-template-columns: minmax(260px, 296px) minmax(420px, 1fr) minmax(300px, 360px); 
  ...
}

@media (max-width: 1240px) {
  .ai-workbench-shell { grid-template-columns: minmax(250px, 280px) minmax(420px, 1fr) minmax(270px, 310px); }
}
@media (max-width: 980px) {
  .ai-workbench-shell { grid-template-columns: minmax(250px, 286px) minmax(0, 1fr); }
  .agent-tree-panel { position: absolute; ... }
}
@media (max-width: 720px) {
  .ai-workbench-shell { grid-template-columns: minmax(0, 1fr); }
}
```

問題：
1. 980px-1240px 區間：右側面板（agent-tree-panel）最小寬度 270px-310px，加上左側 250px-280px，中間內容區最小 420px，總計最小 940px-1010px，超過 980px 斷點 → 會造成水平溢出或擠壓
2. 720px-980px 區間：雖隱藏右側面板為 absolute，但左側 sidebar 仍佔 250px-286px，中間內容區在小筆電上可能過窄
3. 缺乏 768px（平板）專用斷點優化

## Trigger

審查 AI Center 頁面佈局代碼與全域樣式時發現。

## Impact

1. **中等螢幕擠壓**：980px-1240px 範圍內三欄總最小寬度超過視窗寬度
2. **平板體驗缺失**：768px-980px 無專用優化，左側對話列佔固定寬度導致聊天區過窄
3. **內容優先級不明確**：未根據螢幕大小自動調整哪個面板優先顯示

## Why this matters

CLAUDE.md 6.3 節要求小螢幕下「Sidebar 是否可以收合」、「是否把桌面版直接縮小，而沒有重新安排資訊優先級」。目前實作在 980px 以下將右側面板改為 absolute 定位（可收合），但左側對話列在 720px 以下才收合，中間區間缺乏優化。

## Recommended change

1. 重新設計斷點策略，採用內容優先級：
   - ≥1240px：三欄完整顯示
   - 980px-1240px：右側面板預設收合（抽屜模式），左側保持、中間彈性
   - 768px-980px：左側對話列可收合，預設顯示中內容+右側面板
   - <768px：單欄，所有側邊欄為抽屜

2. 使用 CSS Container Queries 或更細緻的媒體查詢

3. 確保每個斷點下主要內容區（聊天區）有合理的最小寬度（建議 ≥320px）

## Verification

1. 在 1240px、980px、768px、720px、640px、390px、360px 測試佈局
2. 確認無水平捲動
3. 確認聊天區在所有尺寸下可用寬度 ≥320px
4. 確認側邊欄收合/展開交互正常

## Resolution criteria

所有 viewport 下佈局無溢出、主要內容區寬度合理、側邊欄收合邏輯符合內容優先級。

## Notes

此問題屬於架構級響應式設計缺陷，修復涉及多個元件（Sidebar、AgentPanel、ChatPane）的協同調整，建議納入前端重構計畫。