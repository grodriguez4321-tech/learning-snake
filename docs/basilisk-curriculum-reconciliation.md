# Curriculum Review Reconciliation — Basilisk Lessons 1–13

Agents: Architecture (1), Phase 1 curriculum (2), Intake curriculum (3), Beginner UX (4), Assessment (5). Integration (6) follows implementation of accepted items.

## Accepted now (implemented in this pass)

| ID | Source | Decision | Change |
|----|--------|----------|--------|
| A1 | Ag2 F1 / Ag5 | Capstone must call `inspect_clue` | `source_uses: calls_name` on `functions_01_ex4` |
| A2 | Ag2 F2 / Ag5 | Conditionals must compare | `compares_names` on L4 exercises; multi-case where practical |
| A3 | Ag2 F3 / Ag5 | Print via variable names | `print_names` on `fundamentals_02_ex4` |
| A4 | Ag5 | `use_last_supply` identity | function `arg_after` mutation check |
| A5 | Ag5 | `can_depart` low supplies | add (True,0,False) and (True,8,False) |
| A6 | Ag5 | elif debug single-input | convert `decisions_09_ex2` to multi-case function repair |
| A7 | Ag4 | Sidebar ≠ unlock | rename L9–13 sections so UI matches unlock |
| A8 | Ag3 P5 / Ag4 | Status rule drift | L13 content contrasts Cleared≥5 vs L9 desk ≥10 |
| A9 | Ag5 | L1 dispatch structure | `print_min_calls` + multi-arg print check |
| A10 | Ag4 / Ag5 | `numbered_roster` requires range | `range_call` source_uses |
| A11 | Ag4 | `None` unexplained | replace fill blanks with `# TODO` placeholders |

## Modified / partial

| ID | Decision | Reason |
|----|----------|--------|
| Ag2 F4 L7/L8 schema | Defer full desync | High content cost; A1 already strengthens L8 mastery |
| Ag2 F8 append→None debug | Defer | L12 already teaches this; avoid Phase 1 exercise-count churn past 28 |
| Ag3 P2 diversify 9.4 | Defer | Boundaries already solid; transfer via domain rename accepted as intentional |
| Ag3 P1 graded retrieval | Defer | Content openings retained; interactive recall later |

## Rejected

| ID | Reason |
|----|--------|
| Revert lesson titles to curriculum wording | App titles clearer; harmless fidelity |
| Free-text architecture explain | Engine/UI scope |
| Treat `else: if` as failure | Same AST as elif; valid equivalent |

## Deferred (recorded for later batches)

- IndexError literacy lesson
- Mixed and/or parentheses exercise in L10
- Capstone light mutation step (after L12 checkpoint deepen)
- Worker stdout isolation when functions print during tests
- List-repr predict accepting double quotes
- Soften Hint 3 across curriculum
