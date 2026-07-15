# CR-0003：前端響應式斷點未覆蓋所有要求的 viewport

- Status: Open
- Severity: P2
- Domain: Frontend
- Confidence: Medium
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Fingerprint: frontend/responsive-breakpoints/global.css/media-queries

## Summary

全域樣式檔 `frontend/src/global.css` 定義的媒體查詢斷點（1100px、900px、980px、720px、640px、1240px、560px）未完全覆蓋專案規範要求的所有 viewport。根據 CLAUDE.md 6.1 節，至少應考慮：360×800、390×844、768×1024、1366×768、1440×900、1920×1080、2560×1440、3840×2160。

## Evidence

- File: `frontend/src/global.css`
- Lines: 552, 557, 763, 771, 778, 796, 1198, 1212, 1256
- Symbol: @media queries

```css
@media (max-width: 1100px) { ... }
@media (max-width: 900px) { ... }
@media (max-width: 1240px) { ... }
@media (max-width: 980px) { ... }
@media (max-width: 720px) { ... }
@media (max-width: 640px) { ... }
@media (max-width: 560px) { ... }
```

對照要求的 viewport：
| 要求寬度 | 現有斷點 | 覆蓋狀態 |
|---------|---------|---------|
| 360px   | 640px, 560px | ⚠️ 無精確 360px 斷點 |
| 390px   | 640px, 560px | ⚠️ 無精確 390px 斷點 |
| 768px   | 720px, 900px | ⚠️ 無精確 768px 斷點 |
| 1366px  | 1240px, 1100px | ⚠️ 無精確 1366px 斷點 |
| 1440px  | 1240px | ⚠️ 無精確 1440px 斷點 |
| 1920px  | 無 | ❌ 無大螢幕斷點 |
| 2560px  | 無 | ❌ 無 4K 斷點 |
| 3840px  | 無 | ❌ 無 4K+ 斷點 |

## Trigger

依據持續代碼審查技能 6.1 節要求，檢查響應式設計斷點覆蓋情況。

## Impact

1. **小螢幕體驗**：360px、390px 手機 viewport 可能無最佳化佈局
2. **平板體驗**：768px iPad viewport 缺乏專用斷點
3. **大螢幕/4K**：1920px、2560px、3840px 缺乏 max-width 限制，內容可能過度延伸
4. **技術債務**：現有斷點似乎基於元件實際需求而非系統性規劃

## Why this matters

CLAUDE.md 明確要求至少考慮 8 種 viewport。缺乏大螢幕斷點違反 6.2 節「4K 與大型螢幕」規則：主要內容應使用 max-width、內容區域應適當置中、不應讓資訊貼近螢幕最左側與最右側。

## Recommended change

1. 補充缺失的關鍵斷點：
   - `@media (max-width: 390px)` - 小型手機
   - `@media (max-width: 768px)` - 平板直向
   - `@media (min-width: 1440px)` - 筆電/桌機基準
   - `@media (min-width: 1920px)` - 全高清螢幕
   - `@media (min-width: 2560px)` - 2K/4K 螢幕
   - `@media (min-width: 3840px)` - 4K+ 螢幕

2. 在大螢幕斷點中加入：
   - 內容容器 max-width 限制（建議 1400px-1600px）
   - 主要內容區置中
   - 避免元素過度分散

3. 考慮採用行動優先策略，使用 `min-width` 而非 `max-width` 為主

## Verification

1. 在瀏覽器開發工具中測試所有 8 種 viewport
2. 確認大螢幕下內容有 max-width 限制且置中
3. 確認小螢幕下無水平捲動、觸控目標足夠大

## Resolution criteria

所有 8 種要求的 viewport 皆有對應的樣式優化，且大螢幕下內容不會無限制延伸。

## Notes

現有斷點雖有實際作用，但非系統性規劃。建議重新梳理斷點策略，採用標準化的響應式設計斷點體系。