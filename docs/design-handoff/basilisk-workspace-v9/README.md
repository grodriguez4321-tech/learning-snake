# Basilisk Learning Workspace — Design Handoff

This package contains the approved Superdesign prototype at version 9 and its final logo asset.

## Contents

- `basilisk-workspace-v9.html` — complete interactive HTML/CSS/JavaScript prototype
- `assets/basilisk-app-mark-v2.png` — final blue-and-basil-green Basilisk emblem
- `source.json` — source draft identifiers and review links

## Review the prototype

Open `basilisk-workspace-v9.html` in a browser. Internet access is required for the prototype's Tailwind, Iconify, and Google Fonts CDN dependencies. The Basilisk logo itself is local and portable.

The prototype demonstrates:

- Expanded and collapsed curriculum rail
- Responsive Prompt/Code tabs below 900 px
- Learn, Examples, and Practice modes
- Editable code surface with live requirement states
- Run, Check, Hint, and Reset flows
- Resizable prompt pane and output drawer
- Output and Feedback tabs
- Keyboard shortcut: Ctrl/Cmd + Enter to run

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

## Content note

Lesson names and exercise copy are representative placeholders. Replace them with the real curriculum data while preserving the layout, states, and interaction hierarchy.

## Source

- Draft: `16ac8e91-e59d-4a71-ad04-c3a2755fae79`
- Approved version: `9`
- Superdesign project: `93e2aad1-11c7-40db-a9dd-0ad043166987`
