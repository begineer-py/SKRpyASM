# CR-0002：前端頁面檔案僅存在備份版本

- Status: Open
- Severity: P2
- Domain: Frontend
- Confidence: High
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Fingerprint: frontend/missing-pages/src/pages/*/page-files

## Summary

`frontend/src/pages/` 目錄下的各頁面子目錄（AICenterPage、SkillLibraryPage、SkillEditPage、AgentLLMConfigPage、APIKeyManagerPage）僅包含 `.bak` 後綴的備份檔案，缺少實際的 `.tsx` 入口檔案。實際的頁面組件已移至 `frontend/src/features/*/pages/` 目錄。

## Evidence

- File: `frontend/src/pages/AICenterPage/`
- Lines: N/A (directory listing)
- Symbol: directory structure

```bash
# ls -la frontend/src/pages/AICenterPage/
AICenterPage.tsx.bak

# ls -la frontend/src/features/ai/pages/
AICenterPage.tsx
ExecutionMonitorPage.tsx
OverviewDetailPage.tsx
```

Router (`frontend/src/app/router.tsx`) 從 `../features/ai/pages/AICenterPage` 匯入，確認實際使用的是 features 目錄下的檔案。

## Trigger

檢查前端專案結構時發現 pages 目錄下只有備份檔案。

## Impact

1. **建構風險**：若建構工具掃描 `src/pages/` 可能會嘗試編譯 `.bak` 檔案導致錯誤
2. **開發困惑**：開發者可能誤以為 `src/pages/` 是主要頁面位置
3. **技術債務**：殘留的備份檔案佔用空間且無實際用途

## Why this matters

SKRpyASM 前端已遷移至 feature-based 架構（`src/features/*/pages/`），但舊的 `src/pages/` 目錄結構未清理。這違反「程式碼結構應反映實際架構」的原則。

## Recommended change

1. 刪除 `frontend/src/pages/` 目錄下所有 `.bak` 檔案
2. 若 `src/pages/` 目錄無其他用途，考慮整體移除該目錄
3. 更新相關文件或 IDE 設定，確認頁面組件位於 `features/*/pages/`

## Verification

1. 執行 `npm run build` 確認建構成功
2. 執行 `npm run lint` 確認無錯誤
3. 確認 `src/pages/` 目錄已清理或移除

## Resolution criteria

`frontend/src/pages/` 目錄不再包含 `.bak` 檔案，且建構/檢查正常通過。

## Notes

此為前端架構遷移後的殘留檔案清理問題。實際頁面組件已正確位於 `features/*/pages/` 並被 router 正確引用。