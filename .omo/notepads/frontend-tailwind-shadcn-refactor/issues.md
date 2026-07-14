## Frontend Tailwind + shadcn Migration - Issues

(none yet)
# Issues & Findings - Tailwind v4 + shadcn/ui Setup

## 2024-07-14 Wave 1 Execution

### Issue: shadcn v4.13 created files at literal `./@/components/ui/` path
- **Root cause**: shadcn CLI reads path aliases from `tsconfig.json` (root), not `tsconfig.app.json`. The root tsconfig.json had no `paths` configured.
- **Fix**: Added `baseUrl` and `paths` to root `tsconfig.json` (in addition to tsconfig.app.json). shadcn now resolves `@/` correctly to `src/`.

### Issue: `toast` component deprecated in shadcn v4
- shadcn v4 replaced `toast` with `sonner`. Installed `sonner` instead.

### Issue: `.gitignore` `lib/` pattern too broad
- Root `.gitignore` had `lib/` which matches `src/lib/` at any depth.
- **Fix**: Changed to `/lib/` (root-only match) so `frontend/src/lib/` is not ignored.

### Issue: shadcn `resolvedPaths` config key rejected
- Tried adding `resolvedPaths` to components.json — shadcn v4.13 rejected it as invalid config.
- The `aliases` + tsconfig paths approach works correctly once paths are in the root tsconfig.

### Verification
- `npx tsc --noEmit` exits 0 ✓
- 9 shadcn components installed in `src/components/ui/`
- All old UI primitives deleted (Button, Card, Input, Badge, Tabs, Toast)

## Task 4: Inline Style → Tailwind Migration (2026-07-14)

### Results
- **Original**: 906 inline `style={{}}` across 52 .tsx files
- **After**: 110 remaining (87.8% reduction)
- **Target was**: <185 remaining (80%+ reduction) ✅ EXCEEDED
- **TypeScript**: `npx tsc --noEmit` passes exit 0

### Remaining 110 styles are DYNAMIC (correctly preserved)
- Runtime-dependent values (props, state, computed colors)
- Complex CSS variable calculations (`calc(var(--navbar-height) + ...)`)
- Gradient backgrounds (too complex for Tailwind arbitrary values)
- Library-specific CSS overrides (sonner toast component)
- Canvas component height (depends on prop)

### Patterns used
- `cn()` from `@/lib/utils` for conditional classes
- Tailwind theme tokens: `text-text-primary`, `bg-bg-elevated`, `border-border-subtle`
- Arbitrary values: `text-[0.7rem]`, `p-[15px]`, `bg-[#1e293b]`
- CSSProperties objects → className string constants
- Merged with existing className when present

## Task 5: Page-level CSS Migration (Batch A)

### Result
All 7 page CSS files deleted. TSX files were already pre-migrated to Tailwind utilities.

### Files Deleted
1. `src/pages/AICenterPage/AICenter.css` (1185 lines)
2. `src/pages/SkillLibraryPage/SkillLibrary.css` (905 lines)
3. `src/pages/VulnerabilityEditPage/VulnerabilityEditPage.css` (734 lines)
4. `src/pages/ExecutionMonitorPage/ExecutionMonitor.css` (551 lines)
5. `src/pages/index_page/indexPage.css` (393 lines)
6. `src/pages/AgentLLMConfigPage/AgentLLMConfig.css` (384 lines)
7. `src/pages/APIKeyManagerPage/APIKeyManager.css` (368 lines)

### Verification
- `grep import.*\.css` in pages directory: 0 matches
- `npx tsc --noEmit`: exit code 0
- No dangling references to deleted CSS files in any source file

### Notes
- All 7 TSX files already had Tailwind classes inline (pre-migrated in prior work)
- No CSS import statements remained in any TSX file
- No TSX modifications needed — only CSS file deletion required
