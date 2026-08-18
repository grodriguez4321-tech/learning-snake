# Basilisk Learning Workspace — Design Handoff

This package contains the approved Superdesign prototype at version 9 and its final logo asset.

## Contents

- `basilisk-workspace-v9.html` — complete interactive HTML/CSS/JavaScript prototype
- `assets/basilisk-app-mark-v2.png` — final blue-and-basil-green Basilisk emblem
- `source.json` — source draft identifiers and review links
- `screenshots/` — durable desktop references (1440×900) for key states
- `references/` — local static Learn/Examples reference HTML used to render durable images

## Review the prototype

Open `basilisk-workspace-v9.html` in a browser. Internet access is required for the prototype's Tailwind, Iconify, and Google Fonts CDN dependencies. The Basilisk logo itself is local and portable.

The prototype demonstrates:

- Expanded and collapsed curriculum rail
- Responsive Prompt/Code tabs below 900 px
- Learn / Examples / Practice segmented tabs in the header (visual-only in this HTML)
- Editable code surface with live requirement states
- Run, Check, Hint, and Reset flows
- Resizable prompt pane and output drawer
- Output and Feedback tabs
- Keyboard shortcut: Ctrl/Cmd + Enter to run

### Authoritative mode states (Learn / Examples / Practice)

- The packaged HTML renders a single Practice-style prompt/editor state. The header tabs (`Learn`, `Examples`, `Practice`) are illustrative only and do not switch content in this prototype.
- The authoritative visual and content states for Learn and Examples live in the approved Superdesign file. See `source.json`:
  - `canvasUrl` — design canvas with approved Learn and Examples compositions
  - `previewUrl` — external preview of the approved draft
- Production must implement all three modes per the design sources above. This prototype demonstrates layout, interaction chrome, and Run/Check separation only.

## Production implementation guidance

Treat the HTML as the visual and interaction specification. Translate it into the project's existing framework and component architecture rather than embedding the prototype unchanged.

Preserve these design decisions:

- Inter for interface text and JetBrains Mono for code
- Dark surface hierarchy: `#080B10`, `#0D1219`, `#111823`, and `#172131`
- Primary blue `#3B82F6`, hover blue `#60A5FA`, and basil green `#54D6A1`
- Expanded curriculum rail: 232 px
- Collapsed curriculum rail: 64 px
- Logo: 56 px expanded and 52 px collapsed
- Minimum desktop editor width: 520 px
- Automatic rail collapse below 1180 px
- Prompt/Code mobile tabs below 900 px
- Output drawer: 40 px collapsed, approximately 140 px idle, and approximately 240 px active

### Native desktop menu (required in production)

- The desktop application must include a real Qt menu bar with `File`, `Edit`, `View`, and `Help` menus.
- Standard editing shortcuts (Undo, Redo, Cut, Copy, Paste, Select All) must be wired to shared actions and operate consistently across text inputs and the code editor.
- This browser prototype does not render the menu bar; do not treat its absence here as a scope cut.

### Visual-only prototype controls (not wired in this HTML)

The following controls are intentionally illustrative in the packaged prototype and have no behavior:

- Header: `Settings` (gear) and `Change layout` (grid) buttons
- Header: `Learn / Examples / Practice` segmented tabs (no content switching)
- Curriculum rail: individual lesson links (navigation is non-functional)
- Editor toolbar: `Copy code`, `Full screen`
- Output drawer: `Output / Feedback` tab contents are demo-only

Production must implement final behaviors per the Superdesign sources and product specs; do not infer behavior from these static controls.

## Content note

Lesson names and exercise copy are representative placeholders. Replace them with the real curriculum data while preserving the layout, states, and interaction hierarchy.

## Durable visual references (committed screenshots)

To make the approved appearance reviewable offline (without CDNs or external links), the following 1440×900 references are included under `screenshots/`:

- `practice-1440x900.png` — default desktop layout
- `practice-collapsed-rail-1440x900.png` — collapsed curriculum rail variant
- `learn-1440x900.png` — Learn mode reference captured from `references/learn-reference.html` (durable local approximation of the approved Learn composition; see `source.json` for the authoritative source)
- `examples-1440x900.png` — Examples mode reference captured from `references/examples-reference.html` (durable local approximation of the approved Examples composition; see `source.json` for the authoritative source)

## Source

- Draft: `16ac8e91-e59d-4a71-ad04-c3a2755fae79`
- Approved version: `9`
- Superdesign project: `93e2aad1-11c7-40db-a9dd-0ad043166987`
