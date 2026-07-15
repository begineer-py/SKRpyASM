# CR-0005：前端存在低於可讀性閾值的字體大小

- Status: Open
- Severity: P3
- Domain: Frontend
- Confidence: Medium
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Fingerprint: frontend/small-font-sizes/global.css/font-size-tokens

## Summary

全域樣式定義的字體大小 token 中，`--font-size-metadata: 0.75rem` (12px) 以及多處使用 `0.58rem`、`0.59rem`、`0.61rem`、`0.63rem`、`0.65rem`、`0.66rem`、`0.67rem`、`0.68rem` 等小於 11px 的字體，違反 CLAUDE.md 6.4 節「UI 是否存在大量難以辨認的 10px 或 11px 字體」規則。

## Evidence

- File: `frontend/src/global.css`
- Lines: 67-70, 250-251, 275-276, 315-316, 364-365, 389-390, 408-409, 458-463, 550, 613-614, 624-628, 638-639, 653-654, 675-676, 698-700, 727-728, 747-748, 765-766, 838-840
- Symbol: font-size tokens and usages

定義的 token：
```css
--font-size-body: 1rem;           /* 16px */
--font-size-control: 0.9375rem;   /* 15px */
--font-size-supporting: 0.875rem; /* 14px */
--font-size-metadata: 0.75rem;    /* 12px - 接近閾值 */
```

實際使用的小字體（按大小排序）：
- `0.55rem` (8.8px) - 未發現但有更小的
- `0.58rem` (9.3px) - `.ai-kicker`, `.c2-navbar__group-label`
- `0.59rem` (9.4px) - `.ai-filter-count`, `.ai-composer__hint`
- `0.61rem` (9.8px) - `.ai-overview-card__topline`, `.ai-status-badge`
- `0.63rem` (10.1px) - `.agent-panel-tab`
- `0.65rem` (10.4px) - `.c2-badge`, `.ai-setting-row__icon` 等多處
- `0.66rem` (10.6px) - `.c2-navbar__brand-copy small`, `.c2-navbar__status strong`
- `0.67rem` (10.7px) - `.ai-field-label`
- `0.68rem` (10.9px) - `.c2-btn--sm`

## Trigger

依據 CLAUDE.md 6.4 節檢查字體可讀性。

## Impact

1. **可讀性問題**：10px-11px 字體在高 DPI 螢幕（Retina、4K）上極難閱讀
2. **無障礙合規**：WCAG 建議最小 16px (1rem) 正文，輔助文字不低於 12px
3. **資訊層級混淆**：過度使用微小字體作為次要資訊，導致層級不清

## Why this matters

CLAUDE.md 6.4 明確指出：「UI 是否存在大量難以辨認的 10px 或 11px 字體」「不得只因為畫面能容納更多資訊，就持續縮小文字」。專案大量使用 9px-11px 字體作為標籤、狀態、輔助文字，這在 4K 螢幕上會極度模糊。

## Recommended change

1. 建立最小字體大小規範：輔助/標籤文字不小於 `0.75rem` (12px)，正文不小於 `1rem` (16px)
2. 重新設計 token 階梯：
   ```css
   --font-size-metadata: 0.75rem;    /* 12px - 最小允許 */
   --font-size-supporting: 0.875rem; /* 14px - 次要文字 */
   --font-size-body: 1rem;           /* 16px - 正文 */
   --font-size-control: 1rem;        /* 16px - 控制項 */
   --font-size-heading-sm: 1.125rem; /* 18px - 小標題 */
   ```
3. 逐步替換所有 `< 0.75rem` 的字體用法
4. 使用視覺層級（顏色深淡、字重、間距）而非字體大小區分資訊優先級

## Verification

1. 搜尋代碼庫中所有 `font-size` 小於 `0.75rem` 的用法
2. 在 4K 螢幕 (3840px) 下實測可讀性
3. 使用無障礙工具檢查對比度與字體大小

## Resolution criteria

所有 UI 文字字體大小 ≥ 12px (0.75rem)，正文 ≥ 16px (1rem)，且資訊層級透過非字體大小方式區分。

## Notes

此為系統性設計債務，涉及全域樣式與多個元件。修復需謹慎規劃，避免破壞現有緊湊佈局。建議先從最高頻元件（按鈕、標籤、表格標題）開始調整。