# CR-0008：全域樣式檔過大且職責不清

- Status: Open
- Severity: P2
- Domain: Frontend
- Confidence: High
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Fingerprint: frontend/large-css-file/global.css/size

## Summary

`frontend/src/global.css` 檔案達 65,633 字元（約 1250+ 行），包含設計系統 token、重置樣式、導覽列、卡片、按鈕、表格、輸入框、AI Workbench 完整佈局、響應式斷點、對話框、工具提示等所有樣式，違反單一職責原則，維護困難。

## Evidence

- File: `frontend/src/global.css`
- Lines: 1-1260+
- Size: 65,633 bytes

檔案包含的領域：
1. CSS Custom Properties / @theme tokens (Lines 10-132)
2. Reset & Base (Lines 134-177)
3. Scrollbar (Lines 178-183)
4. Application shell & Navbar (Lines 184-321)
5. Page Layout (Lines 322-327)
6. Cards (Lines 329-354)
7. Stat Badges (Lines 356-385)
8. Badges/Tags (Lines 386-403)
9. Buttons (Lines 405-473)
10. Targets overview (Lines 475-550)
11. Workspace layouts (Lines 551-561)
12. AI Workbench 完整佈局 (Lines 563-801) - 約 240 行
13. Inputs (Lines 802-828)
14. Tables (Lines 830-900+)
15. Dialogs/Modals (Lines 900-1200+)
16. Tooltips/Popovers (Lines 1200-1260+)
17. 響應式媒體查詢分散在各區塊中

## Trigger

檢查前端樣式架構時發現單一檔案過大。

## Impact

1. **維護困難**：修改樣式需在 1250+ 行中尋找，易造成衝突
2. **建構效能**：單一大檔案增加 CSS 解析時間
3. **團隊協作**：多人同時修改易產生合併衝突
4. **除錯困難**：開發工具中樣式來源難以追蹤
5. **樹搖失效**：無法按需載入，所有頁面載入所有樣式

## Why this matters

現代前端架構推薦模組化 CSS（CSS Modules、Scoped CSS、或按功能拆分檔案）。Vite 支援 CSS code splitting，但單一巨大檔案無法利用此優勢。

## Recommended change

1. **按功能拆分為多個 CSS 檔案**：
   ```
   src/styles/
   ├── tokens.css          # 設計系統 token
   ├── reset.css           # 重置與基礎
   ├── layout.css          # 應用殼層、導覽、頁面佈局
   ├── components/
   │   ├── buttons.css
   │   ├── cards.css
   │   ├── badges.css
   │   ├── inputs.css
   │   ├── tables.css
   │   └── ...
   ├── features/
   │   ├── ai-workbench.css
   │   ├── scheduler.css
   │   └── ...
   ├── utilities/
   │   ├── scrollbar.css
   │   ├── visually-hidden.css
   │   └── ...
   └── responsive.css      # 統一響應式斷點
   ```

2. **在 `main.tsx` 或 `App.tsx` 中按需匯入**：
   ```ts
   import './styles/reset.css'
   import './styles/tokens.css'
   import './styles/layout.css'
   // 按頁面/功能動態匯入或由路由決定
   ```

3. **考慮採用 CSS Modules 或 Tailwind CSS 組件類** 替代部分手寫 CSS

4. **建立樣式指引文件**，規範命名慣例、Token 使用、響應式策略

## Verification

1. 拆分後執行 `npm run build` 確認建構成功
2. 執行 `npm run lint` 確認無樣式錯誤
3. 視覺回歸測試確認所有頁面樣式正確
4. 檢查建構產物 CSS 大小是否優化

## Resolution criteria

global.css 拆分為多個職責單一的檔案，建構正常，視覺無回歸。

## Notes

此為架構級重構，工作量大。建議分階段進行：
- Phase 1: 提取 tokens.css、reset.css、utilities
- Phase 2: 提取通用元件樣式
- Phase 3: 提取功能區域樣式
- Phase 4: 統一響應式策略

可參考 Vite 的 CSS code splitting 最佳實踐。