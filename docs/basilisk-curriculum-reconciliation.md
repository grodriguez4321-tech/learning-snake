# Curriculum Review Reconciliation — Basilisk Lessons 1–13

Agents: Architecture (1), Phase 1 curriculum (2), Intake curriculum (3), Beginner UX (4), Assessment (5). Integration (6) follows implementation of accepted items. Corrective pass (7) applied before merge of PR #14.

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

## Corrective pass (PR #14 pre-merge)

### C1 — Lesson 4 prerequisite violation (`camp_report`)

| Field | Detail |
|-------|--------|
| **Category** | Pedagogy / sequencing |
| **Current implementation** | `decisions_01_ex4` required `def camp_report(expedition, registered, bedrolls)` with returns — functions four lessons early |
| **Proposed correction** | Restore script-level Abandoned Camp: variables + if/else + `<` + f-string + `print()` |
| **Educational reasoning** | Never require a concept before it is taught; L4 teaches decisions, not functions |
| **Benefits** | Honest scaffolding; matches L1–3 script style |
| **Tradeoffs** | Loses multi-case function returns; one stdout path with fixed starter values |
| **Downstream effects** | SOLUTIONS + grading regressions updated |
| **Decision** | **Accepted** — script-level mini-project with `ops: ["Lt"]` so `!=` cannot fake fewer-than |
| **Tests added** | `test_abandoned_camp_is_script_level` |
| **Verification result** | Pending suite run |

### C2 — Lesson 12 contradictory hint

| Field | Detail |
|-------|--------|
| **Category** | Content accuracy |
| **Current implementation** | Hint 3 claimed 3 supplies / Denied; starter has 5 items, remove+append → 5 → Review |
| **Proposed correction** | Hint 3: 5 supplies / Review |
| **Educational reasoning** | Hints that contradict the graded path train the wrong model |
| **Benefits** | Hint ladder matches prompt and stdout |
| **Tradeoffs** | None material |
| **Downstream effects** | None |
| **Decision** | **Accepted** |
| **Tests added** | `test_quartermaster_hints_match_starter_and_expected` |
| **Verification result** | Pending suite run |

### C3 — Narrow construct checks (append / remove / pop / Boolean / len / range / scoped calls)

| Field | Detail |
|-------|--------|
| **Category** | Assessment fidelity |
| **Current implementation** | Broad `append_or_extend`; missing `and`/`or`/`not`/`len`; `range_call` any call; `calls_name` any site; `elif` AST-equivalent to `else: if` |
| **Proposed correction** | Add `append_call`, `remove_call`, `pop_call`, `len_call`, `boolean_and`, `boolean_or`, `unary_not`; `range_call` must be for-iter; `calls_name` + `inside: for_loop`; `elif_branch` requires real `elif` token + matching column offsets; optional `in_function` / `ops` |
| **Educational reasoning** | When the construct is the lesson objective, behavior-only grading lets bypass solutions pass |
| **Benefits** | Dummy constructs elsewhere fail; L6 teaches append specifically |
| **Tradeoffs** | Slightly less acceptance of equivalent idioms (`+=` on L6) |
| **Downstream effects** | Lessons 6, 8, 10–13 JSON; `course/lessons/README.md` |
| **Decision** | **Accepted** (stronger than original “keep append_or_extend” for append lessons) |
| **Tests added** | append bypasses, Boolean nested-if bypass, range dummy, inspect_clue outside loop, else:if rejection |
| **Verification result** | Pending suite run |

### C4 — List-method assessment (L12)

| Field | Detail |
|-------|--------|
| **Category** | Assessment / mutation |
| **Current implementation** | ex3 used `append_or_extend`; ex4 return-only; ex5 returned `[used, supplies]` + `return_shares_arg`; ex6 only append-or-extend |
| **Proposed correction** | ex3 `append_call`; ex4 `append_call`+`remove_call`+`arg_after`; ex5 return only removed item + `arg_after` + `pop_call`; ex6 `remove_call`+`append_call` |
| **Educational reasoning** | Teach mutation and the append→None trap without accepting replacement-list cheats |
| **Benefits** | Aligns with post-call mutation inspection |
| **Tradeoffs** | Learners who only rebuild lists must change approach |
| **Downstream effects** | SOLUTIONS for ex5 |
| **Decision** | **Accepted** |
| **Tests added** | `test_prepare_supplies_rejects_replacement_list`; updated `test_use_last_supply_rejects_list_copy` |
| **Verification result** | Pending suite run |

### C5 — Saved-progress migration

| Field | Detail |
|-------|--------|
| **Category** | Progress / compatibility |
| **Current implementation** | Defensive parse only; no curriculum version; old drafts attach to reused IDs |
| **Proposed correction** | `curriculum_version: 2`; on load of older files archive raw JSON, clear Phase 1 completions/drafts, keep mastery/mistakes, warn learner to retake L1–8 |
| **Educational reasoning** | Silent reuse of old code inside new exercises is worse than asking for a retake |
| **Benefits** | Predictable upgrade; archives recoverable |
| **Tradeoffs** | Phase 1 progress reset for pre-V2 learners |
| **Downstream effects** | `engine/progress.py` save payload; README Progress section |
| **Decision** | **Accepted — retake Phase 1**; do not preserve Phase 1 completions |
| **Tests added** | `test_pre_basilisk_progress_migration` + fixture |
| **Verification result** | Pending suite run |

### C6 — E2E must not delete production progress

| Field | Detail |
|-------|--------|
| **Category** | Developer safety |
| **Current implementation** | `e2e_learning_loop.py` deleted `data/progress.json`, prefs, and quarantines |
| **Proposed correction** | Temp `data_dir` via `build_controller(..., data_dir=)`; assert path ≠ production |
| **Educational reasoning** | N/A (engineering) |
| **Benefits** | Safe local E2E |
| **Tradeoffs** | None |
| **Downstream effects** | `main.build_controller` optional `data_dir` |
| **Decision** | **Accepted** |
| **Tests added** | `test_e2e_harness_refuses_production_data_dir` |
| **Verification result** | Pending suite run |

### C7 — README restoration

| Field | Detail |
|-------|--------|
| **Category** | Documentation |
| **Current implementation** | Progress / add-lesson / unlock / playground / roadmap sections shortened away |
| **Proposed correction** | Restore and update those sections for Basilisk + V2 migration |
| **Decision** | **Accepted** |

## Modified / partial

| ID | Decision | Reason |
|----|----------|--------|
| Ag2 F4 L7/L8 schema | Defer full desync | High content cost; A1 + C3 loop-scoped call already strengthen L8 |
| Ag2 F8 append→None debug | Covered by L12 ex3 | Corrective pass keeps L12 as the append→None teaching site |
| Ag3 P2 diversify 9.4 | Defer | Boundaries already solid |
| Ag3 P1 graded retrieval | Defer | Content openings retained |

## Rejected

| ID | Reason |
|----|--------|
| Revert lesson titles to curriculum wording | App titles clearer; harmless fidelity |
| Free-text architecture explain | Engine/UI scope |
| Keep treating `else: if` as equivalent to `elif` for grading | Corrective pass **supersedes**: tokenize + column offsets distinguish them when `elif` is the objective |

## Deferred (recorded for later batches)

- IndexError literacy lesson
- Mixed and/or parentheses exercise in L10
- Capstone light mutation step (after L12 checkpoint deepen)
- Worker stdout isolation when functions print during tests
- List-repr predict accepting double quotes
- Soften Hint 3 across curriculum (except C2 fix)
