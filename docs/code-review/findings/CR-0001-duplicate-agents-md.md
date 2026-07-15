# CR-0001：Agents.md 為 CLAUDE.md 的重複副本

- Status: Accepted risk
- Severity: P3
- Domain: Documentation
- Confidence: High
- First seen: 2026-07-15
- Last seen: 2026-07-15
- Fingerprint: documentation/duplicate-file/Agents.md/root

## Summary

專案根目錄下存在 `Agents.md` 檔案，其內容幾乎完全複製自 `CLAUDE.md`（僅缺少第 111-112 行的成本控制政策段落）。經確認，此為刻意設計：專案同時使用多種 AI 程式設計工具（Claude Code、其他 agents），`Agents.md` 為通用指引，`CLAUDE.md` 為 Claude Code 專用指引。兩份文件用途不同但內容高度重疊。

## Evidence

- File: `Agents.md`
- Lines: 1-240
- Symbol: entire file

```bash
# diff CLAUDE.md Agents.md
111,112d110
< **Cost policy**: Do not use Playwright or other browser automation for testing unless the user explicitly requests it. Prefer REST API checks with `curl`, existing non-browser tests through the Makefile workflow, and static checks such as `npx tsc --noEmit` and `npm run lint`.
<
```

## Trigger

發現專案根目錄下同時存在 CLAUDE.md 和 Agents.md，且內容高度相似。

## Impact

1. **維護負擔**：需同步更新兩份文件，增加人為錯誤風險
2. **內容不一致**：已發現 Agents.md 缺少「成本控制政策」段落
3. **混淆用途**：不清楚 Agents.md 的預期用途是否不同於 CLAUDE.md

## Why this matters

在 SKRpyASM 專案中，CLAUDE.md 是給 Claude Code 使用的主要指引文件。若 Agents.md 是為其他 AI agent 準備，應明確區分用途；若無特殊用途，應移除避免重複。

## Recommended change

選項 A：若 Agents.md 無特殊用途 → 刪除 `Agents.md`
選項 B：若 Agents.md 有特定用途 → 明確標註其用途與 CLAUDE.md 的差異，並建立同步機制

**決議採用選項 B**：已確認 Agents.md 為多工具共用指引。建議在 Agents.md 開頭添加說明其用途（通用 AI agent 指引），並在 CLAUDE.md 中註明兩者關係。建立同步機制（如共用模板或腳本）以避免內容漂移。

## Verification

1. 確認刪除 Agents.md 後，專案文件無遺漏
2. 確認 CLAUDE.md 仍包含所有必要指引

## Resolution criteria

Agents.md 已明確標註用途（通用 AI agent 指引），CLAUDE.md 註明兩者關係，且建立同步機制避免內容漂移。

## Notes

此問題屬於文件管理類，不影響執行時行為。經用戶確認，Agents.md 為多 AI 工具共用指引，屬預期設計。建議建立同步機制以降低維護成本。