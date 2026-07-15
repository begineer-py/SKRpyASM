# CR-0007：輸入框使用 placeholder 當作 label

- Status: Open
- Severity: P3
- Domain: Frontend
- Confidence: High
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Fingerprint: frontend/placeholder-as-label/ai-composer-input/placeholder

## Summary

AI Workbench 聊天輸入框（`.ai-composer__input`）使用 `placeholder="Message the active agent…"` 作為唯一標籤，缺乏關聯的 `<label>` 元素，違反 CLAUDE.md 6.4 節「placeholder 是否被當成 label」規則。

## Evidence

- File: `frontend/src/features/ai/pages/AICenterPage.tsx`
- Lines: 731-738
- Symbol: ai-composer__input textarea

```tsx
<textarea
  className="ai-composer__input"
  placeholder="Message the active agent…"
  value={inputVal}
  onChange={e => setInputVal(e.target.value)}
  onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
  disabled={isSending}
  rows={3}
/>
```

CSS 中無隱藏 label 的處理，輸入框無 `aria-label` 或 `aria-labelledby`。

## Trigger

審查 AICenterPage 聊天輸入區元件代碼。

## Impact

1. **無障礙問題**：螢幕閱讀器無法正確識別輸入框用途
2. **使用者體驗**：輸入內容後 placeholder 消失，使用者失去提示
3. **表單語義缺失**：違反 HTML 表單最佳實踐

## Why this matters

CLAUDE.md 6.4 明確指出：「placeholder 是否被當成 label」。安全作業平台的核心互動介面（AI 聊天輸入）必須符合無障礙標準。

## Recommended change

1. 添加關聯的 `<label>` 元素（可視覺隱藏）：
```tsx
<label htmlFor="ai-composer-input" className="sr-only">
  Message the active agent
</label>
<textarea
  id="ai-composer-input"
  className="ai-composer__input"
  placeholder="Message the active agent…"
  ...
/>
```

2. 或使用 `aria-label`：
```tsx
<textarea
  aria-label="Message the active agent"
  placeholder="Message the active agent…"
  ...
/>
```

3. CSS 添加 `.sr-only` 工具類（若不存在）：
```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

## Verification

1. 使用螢幕閱讀器（NVDA/VoiceOver）測試輸入框語義
2. 檢查瀏覽器無障礙樹確認 label 關聯
3. 確認視覺上無多餘 label 顯示

## Resolution criteria

輸入框有正確的可存取名稱（accessible name），螢幕閱讀器可正確朗讀。

## Notes

此為單一元件修復，風險低。建議同步檢查專案中其他輸入框（搜尋框、設定表單等）是否有相同問題。