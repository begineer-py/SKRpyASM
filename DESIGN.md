# SKRpyASM Design System

## 1. Atmosphere & Identity

SKRpyASM is a dark operations workspace: calm at rest, clear under pressure, and deliberately technical without becoming cramped. Its signature is restrained cyan telemetry over layered blue-black surfaces, where readable type and tonal depth carry hierarchy before borders do. Target is the primary workspace noun: target-owned work is organized from the target before users drill into an attack plan, action, or execution.

Every persistent element must provide data, an action, or essential context. Do not use the interface as a stage for decorative operational language, generic status claims, or repeated page names.

## 2. Color

### Palette

| Role | Token | Usage |
| --- | --- | --- |
| Base surface | `--bg-base` | Application canvas |
| Panel surface | `--bg-card` | Primary panels and cards |
| Control surface | `--bg-surface` | Inputs and selects |
| Elevated surface | `--bg-elevated` | Icons and selected utility areas |
| Primary text | `--text-primary` | Titles and primary content |
| Secondary text | `--text-secondary` | Supporting copy and metadata |
| Muted text | `--text-muted` | Placeholders and low-priority data |
| Subtle border | `--border-subtle` | Dividers and optional surface separation |
| Default border | `--border-normal` | Form controls and stronger separation |
| Interactive accent | `--cyan` | Focus, active controls, and telemetry |
| Success / warning / error | `--green`, `--purple`, `--red` | Execution status only |

Use existing CSS tokens rather than raw colors. Cyan is reserved for interaction, focus, and operational signals.

## 3. Typography

| Level | Tailwind scale | Weight | Usage |
| --- | --- | --- | --- |
| Page title | `text-2xl` / `text-3xl` | Bold | Only when the title adds necessary context |
| Section title | `text-xl` / `text-lg` | Semibold | Panel headings |
| Lead text | `text-base sm:text-lg` | Regular | Page description |
| Body / controls | `text-base` | Regular | Inputs, selects, and primary metadata |
| Supporting text | `text-sm` | Regular | Dense supporting data |
| Metadata | `text-xs font-mono` | Semibold | Status and machine identifiers |

Use `font-body` for readable content and `font-mono` for IDs, statuses, and operational metadata. Body content must not be smaller than `text-sm`.

- Do not keep a large hero area for a short title with no supporting, actionable information. Remove the heading entirely or use a compact section heading.
- Keep labels, their controls, and adjacent field groups visually separated: label-to-control spacing is at least 12px; primary-form field groups use at least 24px.
- Do not render every heading as large, bold, white text. Do not use all-caps labels as the dominant heading style, repeated gradient text, arbitrary offsets, or compressed line-height to manufacture hierarchy.
- Keep panel headings away from surface edges. A title, subtitle, metadata, and controls must not be stacked with only 4px separation.

## 4. Spacing & Layout

The base unit is 4px. Use Tailwind's 1, 2, 3, 4, 5, 6, 8, 10, and 12 spacing steps. Workspace padding is at least `p-6` (`md:p-8` where the viewport permits); panel interiors use `p-4` or `p-5`; control groups use `gap-3`; major regions use `gap-4` or `gap-6`.

- Do not stretch content to fill the viewport at the expense of page gutters. Preserve readable outer padding and breathing room around panels, especially on wide screens.
- A component may be dense when it presents data, but primary actions need deliberately generous space, not merely a full-width layout.
- Use `rounded-xl` for controls and compact cards, `rounded-2xl` for major panels and dialogs. Do not mix arbitrary corner radii or turn ordinary controls into pills; `rounded-full` is reserved for badges, avatars, and deliberate status markers.
- Do not use `p-2` or similarly compressed padding for normal panels, or stretch paragraphs across the entire viewport.

### Panel headers

Treat a panel header as a grouped region, not loose text at a surface edge. It contains one primary heading, optional supporting context, and optional actions aligned separately.

- Heading and supporting text use `gap-2`; the body starts at least `mt-4` later, preferably `mt-5` or after a `py-4` divider.
- Header actions must not force the heading into an uncomfortable width.
- Omit the header entirely when its text only repeats the route, the panel purpose, or data already obvious from the content.

## 5. Components

### Filters, search, and diagnostics
- **Default placement**: Filters, optional search, counts, and diagnostic detail are secondary controls. Put them behind a clearly labelled gear button that opens an existing Dialog or drawer, rather than permanently consuming workspace space.
- **Persistent exception**: Leave a control visible only when users must operate it continuously to complete the page's primary task. The exception must be intentional, not a convenience default.
- **Interaction**: Gear buttons use an `aria-label`, no warning dot or count badge unless the user explicitly requests an alert, and the Dialog must support keyboard close.
- **Control design**: Use `h-11` or larger controls, neutral subtle borders, cyan focus border/focus ring, and explicit accessible labels for non-text inputs.

### Primary actions and conditional regions
- **Primary action first**: The primary control on a Target card is the explicit “開啟目標” action. Secondary changes and destructive controls live in an accessible labelled more-actions menu.
- **Creation flow baseline**: Target creation is a secondary workflow in a right-side Drawer, not a permanent homepage panel. Use `text-base` labels, `text-lg` fields with at least `h-14`, `gap-6` field groups, inline field feedback, and an `h-14` primary action.
- **Target detail tabs**: Target detail uses URL-backed tabs in this order: Overview, Assets, Attack Plans, Findings, Executions, AI Activity, Settings. The tab list uses visible cyan focus, keyboard navigation, and a single active tab panel. Keep target context on target-owned overview and asset drill-down links with `returnTo` where the local route supports it.
- **Empty regions**: Do not reserve a panel, column, card, hero, or status block when it contains no useful content. Remove the region entirely. Keep an empty state only when it explains a required recovery action or missing data that the user must address.
- **Placeholder status**: Never show generic claims such as “all systems nominal”, “operational”, or live telemetry labels unless backed by actionable, current data.

### Drawer
- **Purpose**: Use the reusable Radix Dialog-based Drawer for focused secondary workflows, including Target creation. It enters from the right, uses `--bg-elevated` on desktop, and fills the viewport width on mobile.
- **Accessibility**: Every Drawer has a screen-reader title and description, Escape close, focus trapping and restoration through Radix Dialog, a visible close control, and labelled fields. Report validation and request failures beside the relevant field or action; never use browser alerts for form feedback.
- **Structure**: The Drawer is a `rounded-2xl` desktop panel with `p-6`, an optional structural divider, and a pinned action area only when it keeps a primary action available without obscuring fields.

### Operations panel
- **Structure**: Tonal card surface with optional divider between header and body.
- **Spacing**: `rounded-2xl`, `p-4` or `p-5`.
- **States**: Interactive child cards retain focus rings and status colors.

## 6. Motion & Interaction

Interactive controls use color transitions only; focus is always visible with the cyan ring. Loading uses the existing refresh icon rotation. Respect reduced-motion preferences supplied by the existing application styles.

## 7. Depth & Surface

Use a tonal-shift-first strategy: `--bg-base`, `--bg-card`, and `--bg-surface` establish layers. Apply `--shadow-soft` only to major panels. Use `--border-subtle` for structural dividers and `--border-normal` for editable controls; do not frame every nested surface.
