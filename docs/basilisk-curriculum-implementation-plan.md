# Basilisk Curriculum Implementation Plan

Status: working plan for Lessons 1–13 + branding. Not a product doc rewrite.

## Distinctions

| Workstream | Scope |
|------------|--------|
| Curriculum | Replace Phase 1 JSON (L1–8); add L9–13 JSON |
| Checkers | Narrow `source_uses` only if proven necessary (`elif_branch`, list mutation via return pairs) |
| Branding | Window title, sidebar masthead, README/AGENTS/docs user-facing names |
| Documentation | Phase 1 foundation (28 exercises), engagement doc Phase 1 no longer exception, Basilisk name |
| Tests | Catalog order/IDs, SOLUTIONS, exercise count 28 Phase 1, branding asserts, behavioral regressions |

## Architecture findings (Agent 1)

- No architecture rewrite needed. Catalog auto-loads JSON; unlock is linear.
- Exercise types already include predict/debug/architecture/mini_project.
- Function tests do not capture per-call stdout or post-mutation of args; for print_roster / use_last_supply use return-value designs when needed.
- Genuine blockers: pinned 8-ID catalog test; SOLUTIONS completeness; branding test asserts `"Python Course"`.

## Lesson ordering

| # | ID | File | section_order / order |
|---|-----|------|------------------------|
| 1–8 | existing Phase 1 IDs | rewrite in place | keep |
| 9 | `decisions_09_elif` | new | Making Decisions / 2 |
| 10 | `decisions_10_boolean_logic` | new | Making Decisions / 3 |
| 11 | `collections_11_len_range` | new | Collections / 4 |
| 12 | `collections_12_list_methods` | new | Collections / 5 |
| 13 | `collections_13_dictionaries` | new | Collections / 6 |

Phase 1 exercise total: **28**. Lessons 9–13 add ~29 more graded exercises (per curriculum).

## Implementation sequence

1. Branding constants + visible UI strings + README/AGENTS.
2. Rewrite Lessons 1–8 JSON to Phase 1 V2.
3. Add Lessons 9–13 JSON.
4. Update SOLUTIONS + catalog/order/count tests.
5. Add checker features only where curriculum cannot be assessed otherwise.
6. Update docs (phase2 foundation, engagement).
7. Collaborative agent reviews → reconciliation record → apply accepted changes.
8. Full suite, GUI smoke, manual learner path.

## Compatibility

- Preserve all Phase 1 lesson IDs.
- New exercise IDs may orphan old drafts in progress files (acceptable; progress keyed by exercise id).
- Do not rename IDs mid-flight.
