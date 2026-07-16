# asset-map-fullscreen - Work Plan

## TL;DR (For humans)
<!-- Fill this LAST, after the detailed plan below is written, so it summarizes the REAL plan. -->
<!-- Plain English for a non-engineer: NO file paths, NO todo numbers, NO wave/agent/tool names. -->

**What you'll get:** A fullscreen button on the Asset Map that opens a modal dialog showing the topology graph at full viewport size, allowing users to explore large asset maps without the current 360px height constraint.

**Why this approach:** Uses existing Radix UI Dialog primitives (already in codebase for AssetMapDiagnostics), adds minimal UI (one Maximize2 button in header), and renders a separate ReactFlow instance in the modal to avoid state synchronization complexity. Follows the ExecutionTimelineViewer full-height workspace pattern.

**What it will NOT do:** Create a separate fullscreen page/route, persist fullscreen preference, modify parent layout (AssetMapTabContent.tsx), or change ReactFlow rendering logic.

**Effort:** Short
**Risk:** Low - self-contained component change using established patterns
**Decisions to sanity-check:** Fullscreen modal vs. drawer vs. separate page; auto-fit behavior on open; selection sync strategy

Your next move: approve to proceed with implementation. Full execution detail follows below.

---

> TL;DR (machine): Short effort, Low risk - Add fullscreen modal to AssetTopologyMap with Maximize2 button, Dialog with viewport-height ReactFlow, auto-fit on open, selection sync

## Scope
### Must have
- Fullscreen toggle button (Maximize2 icon) in AssetTopologyMap header
- Fullscreen Dialog modal with full-viewport ReactFlow canvas (calc(100vh - header))
- Auto-fit view (padding: 0.15, duration: 300) when fullscreen opens
- Close button (X icon) in fullscreen Dialog header + ESC key support
- Node selection synchronization between inline and fullscreen views
- Responsive: works on desktop and tablet viewports

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Separate fullscreen page/route (keep modal pattern)
- Persist fullscreen preference to localStorage
- Multi-tab fullscreen support
- Changes to AssetMapTabContent.tsx or parent layout
- Modifications to ReactFlow node/edge rendering logic
- New dependencies beyond existing lucide-react icons

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after + Vitest + React Testing Library (existing test setup)
- Evidence: .omo/evidence/task-<N>-asset-map-fullscreen.<ext>
- Existing test: frontend/src/components/AssetTopologyMap.spec.tsx (extend for fullscreen)

## Execution strategy
### Parallel execution waves
> Target 5-8 todos per wave. Fewer than 3 (except the final) means you under-split.

Wave 1: Core implementation (3 todos - sequential due to shared file)
Wave 2: Styles + tests (2 todos - parallel)

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1. Add fullscreen state + button to AssetTopologyMap header | - | 2, 3 | - |
| 2. Implement fullscreen Dialog with ReactFlow | 1 | 4 | 3 |
| 3. Add fullscreen modal styles to global.css | 1 | 4 | 2 |
| 4. Extend AssetTopologyMap.spec.tsx for fullscreen | 2, 3 | - | - |
| 5. Verify integration in TargetDashboard (manual QA) | 4 | - | - |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [x] 1. Add fullscreen state + maximize button to AssetTopologyMap header
  What to do / Must NOT do: Add `isFullscreen` state, `onFullscreenToggle` handler, and Maximize2/Minimize2 button in header (next to legend/settings). Do NOT modify AssetMapTabContent.tsx.
  Parallelization: Wave 1 | Blocked by: - | Blocks: 2, 3
  References: frontend/src/components/AssetTopologyMap.tsx:292-339 (AssetTopologyMap component), :306-318 (header section), frontend/src/features/target/components/AssetMapTabContent.tsx:89 (Settings2 button pattern)
  Acceptance criteria: Button renders in header, toggles isFullscreen state, shows Maximize2 when closed, Minimize2 when open
  QA scenarios: Click button toggles state; keyboard accessible; correct aria-label; Evidence .omo/evidence/task-1-asset-map-fullscreen.json
  Commit: Y | feat(asset-map): add fullscreen toggle button to topology map header

- [x] 2. Implement fullscreen Dialog with separate ReactFlow instance
  What to do / Must NOT do: Add Dialog modal that opens when isFullscreen=true. Render full ReactFlowProvider + TopologyFlowInside with height `calc(100vh - 120px)`. Call fitView on open. Sync selectedNodeId between inline and fullscreen. Do NOT share ReactFlow instance.
  Parallelization: Wave 1 | Blocked by: 1 | Blocks: 4
  References: frontend/src/components/AssetTopologyMap.tsx:211-290 (TopologyFlowInner), :319 (fixed height container), components/ui/dialog.tsx:50-82 (DialogContent), ExecutionTimelineViewer.tsx:273 (calc(100vh-...) pattern)
  Acceptance criteria: Dialog opens on fullscreen, ReactFlow fills viewport, fitView runs on open, node click selects in both views, ESC closes, close button works
  QA scenarios: Open fullscreen -> graph fits; click node -> selects in both; close -> returns to inline; Evidence .omo/evidence/task-2-asset-map-fullscreen.json
  Commit: Y | feat(asset-map): implement fullscreen modal with ReactFlow canvas

- [x] 3. Add fullscreen modal styles to global.css
  What to do / Must NOT do: Add `.asset-topology-map__fullscreen` styles for DialogContent override (max-w-none, full viewport), ensure ReactFlow canvas fills dialog. Do NOT modify existing .asset-topology-map styles.
  Parallelization: Wave 1 | Blocked by: 1 | Blocks: 4
  References: frontend/src/global.css:76-90 (.asset-topology-map), :63-65 (DialogContent max-w-lg default), components/ui/dialog.tsx:64 (max-w-[calc(100%-2rem)])
  Acceptance criteria: Fullscreen dialog uses full viewport width/height, ReactFlow canvas fills available space, no horizontal scroll
  QA scenarios: Fullscreen on 1920x1080 and 1366x768; Evidence .omo/evidence/task-3-asset-map-fullscreen.json
  Commit: Y | style(asset-map): add fullscreen modal viewport styles

- [ ] 4. Extend AssetTopologyMap.spec.tsx for fullscreen functionality
  What to do / Must NOT do: Add tests for fullscreen toggle, dialog render, fitView call, selection sync. Use existing test patterns.
  Parallelization: Wave 2 | Blocked by: 2, 3 | Blocks: 5
  References: frontend/src/components/AssetTopologyMap.spec.tsx (existing tests), frontend/src/features/target/components/AssetMapTabContent.spec.tsx:82 (truncatedGraph fixture)
  Acceptance criteria: Tests pass: render fullscreen button, click opens dialog, fitView called, selection syncs
  QA scenarios: npm run test AssetTopologyMap.spec.tsx; Evidence .omo/evidence/task-4-asset-map-fullscreen.json
  Commit: Y | test(asset-map): add fullscreen modal tests

- [ ] 5. Manual integration verification in TargetDashboard
  What to do / Must NOT do: Verify AssetMapTabContent renders fullscreen button, fullscreen works in tabs context, no layout regression. No code changes.
  Parallelization: Wave 2 | Blocked by: 4 | Blocks: -
  References: frontend/src/features/target/pages/TargetDashboard.tsx:495 (AssetMapTabContent in assets tab), :480 (TabsContent wrapper)
  Acceptance criteria: Navigate to /target/1?tab=assets -> Asset Map tab -> fullscreen button visible -> opens modal -> graph fits -> close works
  QA scenarios: Browser manual test; Evidence .omo/evidence/task-5-asset-map-fullscreen.json
  Commit: N | (verification only)

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [ ] F1. Plan compliance audit - verify all 5 todos completed per acceptance criteria
- [ ] F2. Code quality review - run `make check` (ruff, mypy, eslint), `npx tsc --noEmit`
- [ ] F3. Real manual QA - browser test at http://localhost:5173/target/1?tab=assets
- [ ] F4. Scope fidelity - confirm no changes to AssetMapTabContent.tsx, TargetDashboard.tsx, or ReactFlow rendering logic

## Commit strategy
Atomic commits per todo (4 commits):
1. `feat(asset-map): add fullscreen toggle button to topology map header`
2. `feat(asset-map): implement fullscreen modal with ReactFlow canvas`
3. `style(asset-map): add fullscreen modal viewport styles`
4. `test(asset-map): add fullscreen modal tests`

No push unless explicitly requested.

## Success criteria
- [ ] Fullscreen button visible in Asset Map header (Maximize2 icon)
- [ ] Clicking button opens fullscreen modal with ReactFlow canvas at viewport size
- [ ] Graph auto-fits on modal open (padding: 0.15, duration: 300)
- [ ] Node selection syncs between inline and fullscreen views
- [ ] ESC key and close button (X icon) close fullscreen modal
- [ ] No layout regression in TargetDashboard assets tab
- [ ] All existing tests pass + new fullscreen tests pass
- [ ] `make check` and `npx tsc --noEmit` pass
