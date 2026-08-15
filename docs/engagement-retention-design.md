# Engagement, Attention, and Retention Design

**Status:** Design document — principles for future curriculum and application development.  
**Scope:** No implementation in this document. No new lesson JSON. No UI redesign.  
**Audience:** Curriculum authors, assessment designers, engine developers, and UI developers.

---

## 1. Design philosophy

Basilisk exists to help learners **actually learn programming** — not to maximize completion rates, session counts, or superficial engagement metrics.

### Primary reward

The primary reward is competence:

> **"I can build something now that I couldn't build before."**

Every design decision should reinforce that feeling. Progress is measured by what the learner can **do**, not by points collected.

### What we optimize for

| Priority | Goal |
|----------|------|
| 1 | **Learning** — correct mental models, not syntax memorization |
| 2 | **Retention** — concepts remain usable weeks later |
| 3 | **Attention** — sustained focus through interaction, not spectacle |
| 4 | **Independence** — the learner needs less scaffolding over time |
| 5 | **Intrinsic motivation** — competence and visible capability growth |

### What we reject

The course must **not** become a shallow gamified app built around XP, streaks, coins, badges, loot boxes, or leaderboard pressure. Game-like presentation (RPG theme, narrative framing) is acceptable when it **supports learning**; extrinsic reward systems are not.

### Architectural alignment

| Layer | Owns |
|-------|------|
| `course/` | Curriculum content, exercise definitions, concept metadata |
| `engine/` | Grading, mastery signals, progress, retrieval scheduling |
| `app/` | Presentation, interaction, feedback display |

Engagement principles must not push grading rules into GUI widgets or curriculum policy into the engine without clear ownership.

---

## 2. Evidence-informed learning principles

These principles ground the design. They are not buzzwords — each maps to concrete exercise and product choices.

### Active learning over passive reading

Learners retain more when they **predict, attempt, debug, and explain** than when they read and copy. Instruction exists to prepare attempts, not replace them.

### Retrieval practice

Recalling prior knowledge while solving new problems strengthens memory more than re-reading old lessons. Review should be **embedded in forward progress**, not labeled as remedial homework.

### Spaced practice

Concepts need re-exposure at increasing intervals. A lightweight mastery model should eventually schedule short review challenges before forgetting becomes likely.

### Desirable difficulty

Tasks should be hard enough to require thought but not so hard that random trial-and-error succeeds. Scaffolding decreases as competence grows.

### Feedback as information, not judgment

Failure reveals **what to fix or what to revisit** — not that the learner is bad at programming. Distinguish conceptual gaps from normal implementation mistakes.

### Transfer over isolation

Exercises should require combining concepts (conditionals + loops + dicts) because real programming is integrative, not single-construct drills.

### Cognitive load management

One major new idea per lesson when practical. Short explanations alternated with interaction. Examples small enough to trace line-by-line.

### Worked-example → completion → generation effect

Early: study examples closely resembling the task. Middle: examples teach components, not the full solution. Late: requirements describe behavior; the learner designs the implementation.

---

## 3. Core engagement loops

Four nested loops reinforce one another. Curriculum and product features should explicitly serve each level.

### Micro loop (within one exercise)

The micro loop differs by exercise type:

**`predict_output` / `architecture` (non-code):**

```
Read → Commit answer → Check → (optional) self-verify by copying snippet to editor and Run
```

**`write_code` / `debug` / `fill_blank` / `mini_project`:**

```
Learn → Attempt → Run → Observe → Debug → Check → Reflect
```

| Stage | Purpose |
|-------|---------|
| **Learn** | Minimal explanation + example prepares the attempt |
| **Predict** | Mental model before execution; discourages blind trial-and-error |
| **Attempt** | Learner writes, fixes, or chooses |
| **Run** | Observe real behavior (code exercises; optional self-verify for predict) |
| **Observe** | Compare actual output/errors to expectation |
| **Debug** | Hypothesis → change → re-run (not random editing) |
| **Succeed** | Behavioral tests pass (Check) |
| **Reflect** | Completion feedback names capabilities demonstrated |

**Anti-pattern to avoid:** Read paragraph → copy syntax → submit → next lesson.

Every lesson from Phase 1 onward should contain at least one exercise that forces **prediction, debugging, or design reasoning** — not only `write_code`. Phase 1 V2 already opens with prediction and debugging in Lesson 1 and is not exempt from the richer teaching model.

### Lesson loop (within one lesson)

```
Learn new concept → Practice → Retrieve older concept → Combine
```

Example: a dictionary lesson introduces `{key: value}` but an exercise still requires a `for` loop and an `if` to filter entries. The loop is **retrieved**, not re-taught.

### Section loop (across several lessons)

```
Acquire abilities → Boss challenge → Build something → Advance
```

Every 4–6 lessons, a **boss challenge** combines prior concepts with minimal scaffolding. The persistent RPG project also advances at section boundaries.

### Course loop (entire curriculum arc)

```
Tiny scripts → structured programs → functions → objects → composed software
```

The persistent project evolves from a single variable through nested data, functions, classes, and composition — mirroring the course arc.

---

## 4. Persistent-project design

### Concept

A single **RPG/adventure program** grows throughout the course. Characters (Aria, Rook, Mira, Selene), health, gold, inventory, party, and quests provide continuity without forcing every concept into the theme.

**Phase 1 (Lessons 1–8):** Expedition 17 continuity through data and examples, ending in the Expedition 17 Report mini-project — **not** a pedagogical exception. Debugging begins in Lesson 1; retrieval in Lesson 2; integration by Lesson 3; a mini-project in Lesson 4; a cumulative program in Lesson 8.

**Lessons 9–13:** The persistent **Expedition Intake System** begins here with named capabilities (`readiness_status`, `can_depart`, roster helpers, supply mutation, dictionary records). Callback references to prior work continue in Lesson 14+.

Use simpler non-RPG examples when they teach more clearly (e.g., a shop checkout for pure arithmetic, a score analyzer for list processing).

### Evolution map

| Course stage | Project growth | Python concepts |
|--------------|----------------|-----------------|
| Variables | Simple character info (name, health, gold) | assignment, types, f-strings |
| Conditionals | Decisions (can buy? flee? tier label?) | if/elif/else, boolean logic |
| Lists | Inventory, party roster | indexing, append, iteration |
| Dictionaries | Structured stats | labeled data, key access |
| Nested collections | Party of dicts, equipment lists | nested indexing, loops |
| Loops | Process collections | for, while, range, len |
| Functions | Reusable actions | parameters, return, scope |
| Debugging | Fix the growing program | tracebacks, logic bugs |
| Classes | Character, Item objects | class, `__init__`, methods |
| Composition | Character has stats, inventory, equipment | has-a, multiple objects |

Future phases may add save/load, larger architecture, and additional systems.

### Design rules

1. **Learner modifies and rebuilds** — do not hand over an increasingly large completed program.
2. **Incremental steps** — each project touch adds one concern (max ~12–15 lines of new code per step in capstone-style work).
3. **Runnable at every stage** — the project should always be a small working script, not a pile of disconnected fragments.
4. **Theme serves pedagogy** — switch context when the RPG framing obscures the concept.
5. **Callback references** — later lessons refer to structures built in earlier lessons ("the party list you built in Lesson 18").
6. **Shared vocabulary, not a single codebase (Lessons 9–18)** — reuse names (Mira, gold, party) and canonical specs (`make_stats`), but do not require carrying forward buggy learner code until nested data and capstone work (Lessons 19–28). Early mistakes in a monolithic project obscure concept debugging.

### Project artifacts (future metadata)

Lessons may optionally declare:

```yaml
project:
  artifact_id: hero_stats        # stable name across lessons
  action: extend                 # create | extend | refactor | debug
  file_role: module_fragment     # not a full app until late course
```

---

## 5. Exercise taxonomy

Future lessons should **deliberately vary cognitive activity**. Avoid using `write_code` for everything.

| Type | What it assesses | Best used for | Status |
|------|------------------|---------------|--------|
| **predict_output** | Mental execution, branch/loop tracing | Before new syntax; after mutations | ✅ Supported |
| **fill_blank** | Syntax placement, keyword recall | First contact with a construct | ✅ Supported |
| **write_code** | Independent implementation | Application after scaffolding | ✅ Supported |
| **debug** | Error reading, hypothesis testing | Throughout course, not one chapter | ✅ Supported *(grades same as write_code)* |
| **architecture** | Design reasoning, trade-offs | print vs return, mutate vs copy, data model choice | ✅ Supported |
| **mini_project** | Multi-step cumulative build | Section/course milestones | ✅ Supported *(grades as write_code; no milestone UI yet)* |
| **modify_existing** | Reading + targeted change | Refactoring, extending behavior | *(future; use `fill_blank` or `debug`)* |
| **complete_partial** | Assembly from given pieces | Bridge between fill-in and write | *(future; use `fill_blank`)* |
| **parsons** | Program structure, ordering | Before full independent writing | *(future)* |
| **retrieval_challenge** | Recall without re-reading lesson | Spaced review | *(future; use tagged `write_code`)* |
| **boss_challenge** | Integration under low scaffolding | Section checkpoints | *(future type; use multi-test `write_code` until then)* |

### Recommended lesson mix (guideline)

| Phase | Typical mix per lesson |
|-------|------------------------|
| Early (Lessons 1–8) | 1 predict → 1 guided (fill/debug) → 1–2 write |
| Middle (Lessons 9–20) | 1 predict or debug → 1 apply → 1 combine/retrieve |
| Late (Lessons 21–28) | 1 debug or predict → 1–2 independent write → optional architecture |

At least **one non-write exercise** per lesson is a Phase 2 minimum (see §20).

---

## 6. Retrieval and spacing model

### Embedded retrieval

Previously learned concepts reappear in later exercises **without** announcing "This is review." The learner retrieves knowledge while solving a forward-moving problem.

Examples:

- Dictionary lesson: exercise requires a loop over `.items()`
- Function lesson: exercise requires conditionals inside the function body
- Class lesson: exercise requires lists and dicts as attributes

### Concept roles (metadata)

Each exercise should tag concepts with a **role**:

| Role | Meaning | Example in a dict lesson |
|------|---------|--------------------------|
| `introduced` | New in this exercise/lesson | `dictionaries` |
| `practiced` | Main focus, already taught | `f-strings`, `comparisons` |
| `retrieved` | Required recall, not the lesson focus | `for_loops`, `conditionals` |

### Proposed exercise metadata

```json
{
  "concepts": {
    "introduced": ["elif"],
    "practiced": ["conditionals", "comparisons"],
    "retrieved": ["f-strings", "variables"]
  },
  "retrieval_intent": "Apply branch chains to health-tier labeling",
  "spacing_group": "decisions"
}
```

Lesson-level metadata mirrors this:

```json
{
  "concepts_introduced": ["elif"],
  "concepts_practiced": ["conditionals"],
  "concepts_retrieved": ["f-strings", "variables", "comparisons"]
}
```

### Spacing schedule (future engine behavior)

When mastery data exists, the engine may:

1. Detect a `retrieved` concept with `potentially_forgotten` status
2. Insert or surface a **Quick Challenge** before the next lesson that depends heavily on it
3. Never block forward progress — review is offered, not mandatory gatekeeping

### Concept exposure budget (authoring rule)

Avoid stacking retrieval mechanisms in one lesson. Per lesson:

| Budget | Limit |
|--------|-------|
| **Introduced** (major new concept) | 1 |
| **Retrieved** (prior concepts) | 0–2 |
| **Debug/predict touch** | ≥1 on introduced or retrieved concept |

Boss challenges, Quick Challenges, and Bug Hunt exercises draw from the retrieval budget — they do not add extra concept load on top of a full lesson.

### Spacing and interference

- **Minimum spacing:** Re-test a concept as `practiced` no sooner than 2 lessons after introduction unless it appears as lightweight `retrieved`.
- **Interference pairs:** Avoid introducing multiple high-load constructs in one lesson (e.g., do not combine new `elif`, new boolean ops, and new dicts). Lesson 13 follows boolean logic — do not also boss-test Lessons 9–11 there.
- **Fixed path (Phase 2–3):** Adaptation may insert optional retrieval exercises only; never skip core lessons.

---

## 7. Future mastery model

**Not implemented yet.** This section defines a conceptual model for later engine work.

### Current engine behavior (do not ignore)

Today (`engine/progress.py`):

- `ProgressStore.mastery` stores coarse topic **floats** 0.0–1.0 (~11 topics)
- Pass: +0.15 per topic; fail: −0.05; hints do not reduce pass bump
- UI may show completion percent via `overall_percent()`

The future band model **replaces display and scheduling**, not lesson unlock. Do not author content that depends on per-concept bands until migration lands. Avoid surfacing fake-precision percentages to learners.

### Mastery bands (not percentages)

| Band | Meaning | Typical signals |
|------|---------|-----------------|
| **new** | Not yet attempted or just introduced | First exposure |
| **developing** | Some success with scaffolding | Passes with hints; fails combined tasks |
| **competent** | Reliable independent success | Passes without hints; combines with 1–2 other concepts |
| **strong** | Fast, independent, combines well | Boss success; debug without hint; retrieval success |
| **potentially_forgotten** | Was competent+; no recent retrieval | Time since last success exceeds threshold; retrieval failure |

Avoid displaying "73% mastery." Prefer qualitative bands and **capability statements** ("Can write functions that return dicts").

### Signal inputs

| Signal | Weight | Notes |
|--------|--------|-------|
| Successful attempts | + | Independent success weighs more than hinted success |
| Failed attempts | − (soft) | Repeated failure → more scaffolding, not punishment |
| Hints requested | neutral/informative | Never penalize; informs band ceiling |
| Hint level reached | − (soft) | Hint 4 used → unlikely `strong` until retrieval success |
| Time since last retrieval | − | Drives `potentially_forgotten` |
| Combined-concept performance | + | Boss and integration exercises are strongest signals |
| Debug performance | + | Fixing without full solution reveal indicates deep understanding |
| Prediction accuracy | + | Commit-before-run predictions *(future)*; today predict pass is binary Check only |

**Note:** Prediction accuracy is **not** a reliable mastery signal until commit-before-run records first answers separately from post-Run revision.

### Per-concept record (future schema)

```yaml
concept_id: for_loops
band: competent
last_success_at: 2026-08-01
last_retrieval_at: 2026-08-10
independent_successes: 4
hinted_successes: 1
recent_failures: 0
combined_successes: 2    # exercises where concept was "retrieved"
```

---

## 8. Boss challenge framework

### Purpose

Answer: **"Can the learner actually program with what they have learned?"**

Boss challenges introduce **no major new syntax**. They combine previously taught concepts with substantially less step-by-step scaffolding. Multiple valid implementations are accepted.

### Placement

| Checkpoint | After lessons | Combines (example) | Notes |
|------------|---------------|----------------------|-------|
| Boss 1 | 10 (end of Decisions section) | variables, if/else, elif, boolean logic, f-strings | May ship as final Lesson 10 capstone (`can_enter` + architecture) before a distinct `boss_challenge` type |
| Boss 2 | 15 (mid-Collections) | lists, loops, len/range, conditionals, dicts *(introduced by 13)* | |
| Boss 3 | 20 (end of Functions + nested data) | functions, dicts, nested data, loops, conditionals | |
| Boss 4 | 28 (Phase 2 capstone) | classes, methods, composition, cumulative skills | Lesson 28 composition capstone |

Phase 2 already defines Lesson 28 as a composition capstone; earlier bosses may be implemented as dedicated exercises or mini-project sequences within existing lesson slots until a distinct `boss_challenge` type exists. Label in UI as **Capstone**, not a separate game mode.

**Boss 1–3 are engagement targets**, not yet separate slots in `phase2-curriculum-plan.md`. Only **Lesson 28** is a committed multi-step capstone. Boss 1 may ship as the final exercise(s) in Lesson 10 (`can_enter` integrator) without waiting for a new exercise type.

### Assessment rules

- **Behavior only** — never require a specific variable name unless naming is the objective
- **Multi-test feedback:** Engine stops at first failure; `improve_function_feedback` may note earlier passing cases for the same function. **Full partial pass is not supported** until engine work lands — do not imply "3/4 tests passed" unlocks success
- **No punishment for failure** — retry freely; optional hint escalation
- **Explicit capability summary on success** — via `success_message`; no auto-aggregate until lesson-level UI ships

### Difficulty progression

| Element | Early boss | Late boss |
|---------|------------|-----------|
| Scaffolding | Requirements + one hint available | Requirements only |
| Starter code | Minimal skeleton | Empty or nearly empty |
| Test cases | 4–6 behavioral | 8–12 behavioral + edge cases |
| Valid solutions | 2–3 patterns acceptable | Many patterns acceptable |
| Time expectation | 10–20 minutes | 20–40 minutes |

---

## 9. Debugging framework

Debugging is **normal programming**, not a single chapter.

### Bug Hunt exercises (recurring)

Every **Phase 2 lesson (9–28)** should include at least one of:

- `debug` — fix broken starter code
- `predict_output` — trace before run
- `architecture` — identify error class or next debugging step

### Bug categories (rotate across lessons)

| Category | Example |
|----------|---------|
| Syntax errors | Missing colon, wrong indentation |
| Name errors | Undefined variable, typo |
| Type errors | Wrong operand types, missing `self` |
| Index/Key errors | Off-by-one, wrong dict key |
| Wrong conditions | `=` vs `==`, inverted logic |
| Loop bounds | Infinite while, wrong range |
| Mutation mistakes | Forgot reassignment after `.strip()` |
| Return behavior | Missing return → `None` |
| Reference/aliasing | Shared list mutated unexpectedly |
| Object state | Class-level list shared across instances |

### Debug workflow (encouraged in prompts and UI copy)

```
Observe → form hypothesis → change one thing → Run → evaluate
```

**Run/Check separation** (UI P0-3) is essential: learners must Run to see tracebacks and output; Check validates the fix.

After P0 ships, debug exercises should **not** embed static tracebacks in prompts — the learner reads real runner output.

**Pre-P0-3 fallback (historical):** Short embedded error description in prompt only until Run/Check separation shipped; remove once P0-3 is verified.

### Dedicated debugging lessons (Phase 2)

- **Lesson 22** — reading tracebacks (syntax vs runtime)
- **Lesson 23** — logic bugs (runs but wrong output)

These anchor the debugging spine; micro-debug exercises in every other lesson reinforce the habit.

---

## 10. Hint framework

### Progressive hint levels

| Level | Purpose | Example |
|-------|---------|---------|
| **Hint 1** | Point toward relevant concept | "Think about how elif chains choose exactly one branch." |
| **Hint 2** | Explain the needed concept | "Only the first true condition runs; later branches are skipped." |
| **Hint 3** | Show a similar example | Small worked example with different variable names |
| **Hint 4** | Walk toward the solution | Structural guidance without pasting the full answer |

Current lesson JSON supports `hints: []` as a flat list mapping to these levels. Future UI may label them explicitly.

**All lessons:** **3 progressive hints** per applicable exercise (concept → structure → near-solution). A fourth hint remains optional on short later exercises.

### Rules

- **Never punish hint use** — no XP loss, no streak break, no shame copy
- **Hint usage informs mastery** — heavy hint reliance suggests `developing`, not failure
- **Asking for help is not failure** — frame hints as "get unstuck and keep learning"
- **Hint 1 must not be the solution** — preserve reasoning space

Optional future metadata:

```json
{
  "hints": [
    {"level": 1, "type": "concept", "text": "..."},
    {"level": 2, "type": "explain", "text": "..."},
    {"level": 3, "type": "example", "text": "..."},
    {"level": 4, "type": "scaffold", "text": "..."}
  ]
}
```

---

## 11. Learner-choice framework

When the same learning objective can be assessed in multiple contexts, occasionally let the learner choose.

| Context | Same underlying objective |
|---------|---------------------------|
| RPG damage calculator | Arithmetic + conditionals |
| Shop checkout | Arithmetic + conditionals |
| Game dice mechanic | Random + conditionals |
| Data score analyzer | Loops + conditionals |

### Rules

1. **Same test contract** — all variants must be gradeable with equivalent behavioral tests (parameterized scenarios)
2. **Selective use** — at most 1 choice exercise per 5–8 lessons to limit curriculum maintenance
3. **Default variant** — one variant is always the default; choice is optional enrichment
4. **No fake choice** — variants must feel meaningfully different, not identical with renamed variables

**Until engine support:** Author the **default variant only** for Phase 2. Do not duplicate maintenance burden for the first batch.

Future metadata:

```json
{
  "type": "write_code",
  "choice_variants": [
    {"id": "rpg", "prompt": "...", "starter_code": "...", "tests": [...]},
    {"id": "shop", "prompt": "...", "starter_code": "...", "tests": [...]}
  ]
}
```

Until engine support exists, author one variant and document alternates in curriculum notes.

---

## 12. Mystery / discovery exercises

Occasionally present **understandable but unfamiliar** code before formal explanation.

Learner tasks:

1. Predict what it does
2. Run and experiment
3. Identify a pattern
4. State a hypothesis

Then teach the construct explicitly.

### When to use

- Introducing a construct that reads naturally before its name is known (e.g., seeing `.items()` in a loop before dict iteration lesson)
- Sparks curiosity without confusion

### When to avoid

- Syntax that cannot be understood without prior concepts
- More than ~1 discovery exercise per section
- Situations where confusion will feel like failure rather than intrigue

Label internally as `discovery: true` in metadata; do **not** show "mystery mode" chrome to the learner.

---

## 13. Skill-tree / concept-map concept

**Not implemented yet.** Future visualization of capabilities acquired.

### Concept areas (Phase 2 scope)

```
Python Fundamentals
├── Decisions (if/elif/else, boolean logic)
├── Collections (lists, dicts, nested data, iteration)
├── Functions (def, return, parameters, scope)
├── Debugging (tracebacks, logic bugs, value tracing)
└── Object-Oriented Programming (class, init, methods, composition)
```

### Display principles

- Show **dependencies** (dict iteration requires dicts + loops)
- Show **band** per concept (new → strong), not fake percentages
- Highlight **current development** — what you're working on now
- Never lock content behind arbitrary grind — unlock follows lesson completion, not XP

---

## 14. Difficulty and scaffolding progression

Deliberate arc across the course:

```
high scaffolding → partial scaffolding → independent implementation
```

| Stage | Explanation | Example | Exercise |
|-------|-------------|---------|----------|
| **Early** | Closely resembles exercise | Same variable names, similar structure | fill_blank, guided write |
| **Middle** | Teaches pieces, not exact solution | Same concept, different domain | predict → write with hints |
| **Late** | Requirements describe behavior | Spec only | write_code, boss, capstone |
| **Boss/Project** | Minimal implementation guidance | Empty or skeleton starter | behavioral tests only |

### Difficulty scale (aligns with Phase 2 plan)

- Phase 1 average: ~2
- Phase 2 ramp: 2 → 4–5 (capstone)
- Within-lesson: first exercise easiest, last most independent

The learner should **gradually need the course less** — late Phase 2 exercises should feel like real small programming tasks.

---

## 15. Completion feedback design

Replace generic "Lesson Complete!" with **competence summaries**.

### Good completion feedback

```
Challenge complete

You built a program combining:
  ✓ elif branch chains
  ✓ boundary comparisons
  ✓ f-string output

You traced 1 prediction correctly.
You fixed 1 logic bug without full guidance.
```

### Rules

- List **capabilities demonstrated**, not points earned
- Include metrics **only when meaningful** (debug count, concepts combined)
- Tie feedback to exercise metadata (`concepts.practiced`, `concepts.retrieved`)
- Success messages on individual exercises may already exist (`success_message` field) — use them
- No confetti, coins, loot boxes, streak pressure, or casino-like reinforcement

**Interim UI contract (Lessons 9–13):** Lesson-level capability summaries require §20B engine/UI work — **not available at launch**. Authors must carry competence narrative via per-exercise `success_message` / `failure_message`, especially on **architecture and final write_code** exercises. The **last exercise's** success message should summarize what the lesson combined.

### Failure feedback

- Name the **failing behavior**, not the learner
- Distinguish "syntax/runtime error" from "wrong output" from "wrong design choice"
- Offer retry and hints — never "Game Over"

---

## 16. Attention and session guidelines

Lessons should work in **relatively short sessions** (15–25 minutes target).

### Content rhythm

Prefer:

```
explanation → interaction → explanation → interaction
```

Not:

```
long reading block → finally code at the end
```

### Guidelines (flexible, not rigid caps)

| Element | Guideline | Notes |
|---------|-----------|-------|
| Explanation block | ≤150 words per section; 2–4 sections per lesson | Split with examples |
| Example size | ≤8–10 lines | Every line traceable |
| Exercises per lesson | 3–5 (target 4; Lesson 10 may reach 5) | At least 1 non-write |
| Predict/debug per lesson | ≥1 | Phase 2 debugging spine |
| Quick Challenge frequency | 1 per 5–8 lessons *(future)* | When mastery engine exists |
| Boss frequency | Every 4–6 lessons | May overlap with capstone lessons |
| Lesson duration | 15–25 min standard; up to 30 min for 5-exercise lessons with debug + multi-case write | Longer acceptable for boss/capstone |
| Session end | Natural stopping point after exercise 2–3 | Progress saves; no "finish or lose" |

### Cognitive load

- One major new concept per lesson when practical
- `common_mistakes` field surfaces 2–3 predictable errors — not exhaustive lists
- Avoid walls of text; use headings and short paragraphs (existing `parse_lesson_content` supports this)

---

## 17. Failure philosophy

Failure is **information**.

### Two failure modes

| Mode | Meaning | Response |
|------|---------|----------|
| **Concept not yet understood** | Repeated wrong predictions, architecture misses, same hint level exhausted | More explanation, similar example, optional micro-refresher |
| **Normal programming mistake** | Typo, off-by-one, wrong operator | Specific behavioral feedback; encourage debug workflow |

### Never

- Shame language ("Wrong!", "Failed!", "Try harder")
- Lost lives, broken streaks, XP deduction
- Artificial failure states that block progress
- Making exercises easier merely to preserve completion rate

### Repeated difficulty

Triggers **more appropriate scaffolding or review**, not punishment:

- Surface relevant hint level automatically after N attempts *(future)*
- Offer Quick Challenge on retrieved concept *(future)*
- Never reduce test rigor to inflate pass rate

---

## 18. Anti-patterns

Future agents and developers must **avoid** these engagement patterns:

| Anti-pattern | Why it hurts |
|--------------|--------------|
| Meaningless XP | Points without tied capability growth |
| Daily streak pressure | Extrinsic motivation; anxiety on missed days |
| Coins/currency without educational purpose | Distraction from learning |
| Achievements for trivial actions | "Opened the app" badges teach nothing |
| Excessive animations | Attention theft from code |
| Artificial time gates | "Wait 4 hours to continue" |
| Punishing hints | Discourages help-seeking |
| Leaderboard pressure | Compares learners; irrelevant for solo course |
| Social comparison / ranking | Peer pressure unrelated to solo learning |
| Constant reward interruption | Breaks flow state during coding |
| Easier tests to preserve completion rate | Fake progress |
| Predict exercises answerable only by running | Skips mental model; requires commit-before-run |
| Debug exercise with error only in prompt, not runnable code | Cannot Run → observe → fix |
| Boss introducing new syntax | Integration only, not new constructs |
| Parsons with multiple valid orderings | Busywork without transfer test |
| `source_uses` when behavior tests suffice | Over-constrains valid implementations |
| Duplicate choice UI (list + radios) | Split attention; unclear where to answer |
| "Run to check" on predict exercises | Run does not grade predictions; Check does |
| Prompt-embedded static tracebacks (post-P0) | Bypasses real Run/debug habit |
| "Review" labels on retrieval | Feels like remedial punishment |
| Fake precision ("87% master") | Misleading confidence |
| Large pasted starter code | Passive consumption, not construction |
| Gamification replacing progression | Lesson unlock must remain the real progression system |

Game-like **presentation** (RPG narrative, thematic examples) is fine. **Extrinsic reward systems** are not.

---

## 19. Proposed curriculum metadata changes

### Lesson-level (add to JSON schema)

```json
{
  "concepts_introduced": ["elif"],
  "concepts_practiced": ["conditionals", "comparisons"],
  "concepts_retrieved": ["f-strings", "variables"],
  "difficulty": 2,
  "project_artifact": "hero_stats",
  "project_action": "extend",
  "session_minutes_estimate": 20,
  "engagement": {
    "has_predict": true,
    "has_debug": true,
    "has_retrieval": true,
    "boss": false
  }
}
```

### Exercise-level

```json
{
  "concepts": {
    "introduced": [],
    "practiced": ["elif"],
    "retrieved": ["conditionals", "f-strings"]
  },
  "scaffolding": "guided",
  "cognitive_level": "apply",
  "hints": ["...", "...", "...", "..."],
  "success_message": "You chose the correct branch for every boundary.",
  "failure_message": "Check which tier runs when health equals a boundary value."
}
```

`scaffolding` values: `high` | `guided` | `partial` | `independent`  
`cognitive_level` values: `remember` | `understand` | `apply` | `analyze` | `evaluate` | `create`

### Catalog / engine (future)

- Concept registry: canonical IDs (`for_loops`, `dictionaries`, `elif`, …)
- Mastery store keyed by concept ID
- Retrieval scheduler reads `concepts_retrieved` + mastery bands
- Progress file extended with per-concept signals (backward compatible)

Existing fields (`topics`, `concepts`, `hints`, `success_message`) remain valid; new fields are additive.

### Metadata rollout (phased)

1. **Authoring notes** — concept roles, scaffolding (no schema change)
2. **JSON optional fields** — parse-tolerant; catalog validation tests
3. **Progress extension** — per-concept bands (backward compatible)
4. **Scheduler** — Quick Challenges

**Phase 2 batch minimum in JSON today:** existing fields only. Concept roles live in authoring notes until schema merge.

### Canonical concept IDs (starter registry)

Align with Phase 2 plan: `elif`, `boolean_logic`, `len_range`, `list_methods`, `dictionaries`, `dict_iteration`, `loops_while`, `nested_data`, `scope`, `debugging_logic`, `references`, `classes`, `composition`. Map legacy `topics` (e.g., `loops` → `for_loops`) consistently to avoid drift.

---

## 20. What should affect Lessons 9–13 RIGHT NOW

Lessons 9–13 are the first Phase 2 batch:

| # | ID | Title |
|---|-----|-------|
| 9 | `decisions_02_elif` | More Than Two Outcomes with elif |
| 10 | `decisions_03_boolean_logic` | Combining Conditions |
| 11 | `collections_04_len_range` | len and range |
| 12 | `collections_05_list_methods` | in, remove, pop |
| 13 | `collections_07_dictionaries` | Storing Labeled Data in Dictionaries |

Detailed specs exist in `docs/phase2-curriculum-plan.md`. This section separates engagement principles by implementation horizon.

**This document governs *why* and quality bar; `phase2-curriculum-plan.md` is the authoritative lesson blueprint** for exercise orderings, counts, and assessment details.

---

### PREREQUISITE — UI readiness (Appendix D)

Verify P0 acceptance criteria before authoring Lesson 9 JSON. See Appendix D status table.

---

### A. AUTHORING CHECKLIST (after P0 verified)

Use existing exercise types (`predict_output`, `fill_blank`, `write_code`, `debug`, `architecture`). **Follow per-lesson exercise progressions in `phase2-curriculum-plan.md` § Lessons 9–13** — do not invent alternate orderings.

#### Core learning loop

Every lesson follows the Phase 2 progression for that lesson ID. General pattern:

```
short explanation → example → predict → guided (fill_blank/debug) → independent write → architecture (where specified)
```

#### Exercise progressions (authoritative — from Phase 2 plan)

| Lesson | Progression |
|--------|-------------|
| 9 | predict → fill_blank → `wound_label` write_code → architecture |
| 10 | predict → fill_blank → debug (`=` vs `==`) → `can_enter` write_code → architecture |
| 11 | predict → fill_blank → debug (off-by-one) → `last_item` → `numbered_lines` *(add debug to Phase 2 plan if missing)* |
| 12 | predict → membership write_code → debug (wrong `remove`) → conditional remove |
| 13 | predict → fill_blank → `make_stats` write_code → purchase check write_code |

#### Minimum non-write coverage

| Lesson | Required non-write |
|--------|-------------------|
| 9 | predict + architecture *(no runnable debug required)* |
| 10 | predict + debug + architecture |
| 11 | predict + debug |
| 12 | predict + debug |
| 13 | predict + debug |

Rule: **≥1 of predict, debug, or architecture** per lesson — not necessarily all three.

#### Retrieval practice (metadata + authoring)

Tag concept roles in **authoring notes** until JSON schema lands:

- Lesson 9 retrieves: f-strings, variables, comparisons
- Lesson 10 retrieves: elif, if/else, comparisons; introduces boolean logic
- Lesson 11 retrieves: for loops, indexing, f-strings
- Lesson 12 retrieves: append, loops, len
- Lesson 13 retrieves: f-strings, comparisons, variables, strings

Do **not** label exercises as "review."

#### Persistent project thread

**Introduce** stable intake names in Lesson 9 — Phase 1 already builds cumulative Expedition 17 tools; Lessons 9+ grow the Expedition Intake System:

| Lesson | Project touch |
|--------|---------------|
| 9 | Expedition readiness tiers (`readiness_status(supplies)`) |
| 10 | Compound departure clearance (`can_depart(...)`) |
| 11 | Numbered roster / name length |
| 12 | Supply mutation + Quartermaster’s Update |
| 13 | Dictionary field records + Intake System v1 capstone |

Each function/structure gets a **stable name** reused later (`readiness_status`, `can_depart`, expedition records).

#### Progressive hints

**3 progressive hints** per applicable exercise (concept → structure → near-solution). Fourth hint optional on short later exercises.

#### Scaffolding curve (Lessons 9–13)

- Difficulty builds from Phase 1 into early intake work
- First exercise per lesson: predict or retrieval
- Last exercise: most independent construction or mini-project
- Examples resemble but do not duplicate exercise solutions

#### Prediction workflow

Use `predict_output` with `code_to_predict` early in each lesson.

**Today:** Learner reads snippet, types predicted output, **Check** compares to `expected_answer`. Run does **not** grade predictions.

Prompt copy: *"Decide your answer, then click Check."* Optionally: *"Copy the snippet into the editor and Run if you want to verify before checking."* **Do not** say "run to check."

Progression in Lessons 9–13: branch (9–10) → loop boundary (11) → mutation (12) → dict update (13).

#### Debugging as recurring activity

Follow the debug exercise contract on **code** exercises: broken starter, Run to observe, Check to validate fix. Lesson 9 includes threshold-order debugging; Boolean and mutation lessons continue the thread.

#### Assessment specifics (Lessons 9–13)

| Lesson | Critical test design |
|--------|---------------------|
| 10 | `can_depart`: multi-case matrix; **must fail** guide-only and supplies-only shortcuts |
| 11 | Roster numbering via `range`; distinguish `len` from last index |
| 12 | Mutation vs rebind; `append` must not be assigned back to the list |
| 13 | `build_expedition_record` returns dict with required keys; full denial/clearance matrix |

Every test needs explicit `message` naming failing **behavior**.

#### Meaningful completion feedback

Add `success_message` / `failure_message` on architecture and capstone write_code first; expand incrementally. Lesson-level summaries deferred to §20B.

#### Failure philosophy

Behavioral test `message` fields must explain **what failed** (e.g., "When health is exactly 25, the critical tier should run"). No shame language.

#### Attention / session design

- 3–5 exercises per lesson (Lesson 10: 5 is acceptable)
- Content blocks ≤150 words; use `common_mistakes` for 2–3 items
- Target 15–25 minutes; up to 30 for Lesson 10

#### Anti-patterns to avoid in authoring

- No three identical write_code exercises in a row
- No giant starter code paste
- No "copy this exactly" prompts
- No trivia architecture questions unrelated to the lesson

---

### B. IMPLEMENT SOON

High-value features after the first Phase 2 batch (Lessons 9–13) is validated.

| Feature | Layer | Unblocks |
|---------|-------|----------|
| **P1 UI: predict panel auto-height** | app | Longer predict snippets (while, scope) |
| **Formal concept metadata in JSON** | course | Retrieval tracking, feedback summaries |
| **Lesson completion capability summary** | app | Competence-based "what you combined" |
| **Boss challenge exercise type** | course + engine | Distinct boss UX (Boss 1 may ship as write_code first) |
| **Quick Challenge insertion** | engine + app | Spaced retrieval |
| **Mastery band storage** | engine | Adaptive review |
| **modify_existing / complete_partial types** | course + engine | Exercise variety beyond fill_blank |
| **Hint level labels in UI** | app | Clearer progressive help |
| **Project artifact tracking in progress** | engine | Persistent project continuity |
| **Commit-before-run prediction UI** | app + engine | Reliable prediction mastery signal |
| **Multi-line predict answer widget** | app | Multi-line output traces |
| **Single-surface choices UI** | app | Remove duplicate left-panel choice lists |
| **Extended `source_uses`** | engine | elif, while, boolean_op, dict_literal |
| **Hidden test flag** | course + engine | Boss edge cases without gotcha feel |

**P0 UI (choices, output panel, Run/Check separation) — shipped;** verify via `tests/test_ui_phase2_prerequisites.py` and Appendix D before authoring.

---

### C. FUTURE

Document now; do not delay Lessons 9–13.

| Idea | Notes |
|------|-------|
| Parsons problems (drag-and-drop) | Useful after predict, before write; needs new exercise type + UI |
| Learner choice variants | Engine support for parameterized equivalent tests |
| Skill-tree visualization | After mastery model validated |
| Mystery/discovery mode flag | Sparingly, per-section at most |
| Adaptive spacing scheduler | Requires mastery data from multiple lessons |
| Spaced Quick Challenges | "It's been a while since loops" — engine-driven |
| Save/load for persistent project | Phase 3+ |
| Gamified presentation layer | Thematic only; no XP/streaks |
| AI-generated hints | Only if quality-controlled; default to authored hints |
| Multi-line free-text predict answers | Nice-to-have for complex traces |

---

### D. Governing principles for Lessons 9–13

These five principles take precedence when authoring the first Phase 2 batch. When in doubt, choose the option that strengthens **reasoning and retrieval**, not completion speed.

1. **Interaction before independence** — Every lesson opens with prediction or guided practice before the hardest `write_code` exercise. No lesson is "read, then three writes."

2. **Retrieval without labeling** — Each lesson silently reuses 2–3 prior concepts (f-strings, conditionals, loops) in at least one exercise. Never prefix exercises with "review" or "reminder."

3. **Debug and predict every lesson** — At least one `predict_output`, `debug`, or `architecture` exercise per lesson. Debugging is habit formation, not a future topic.

4. **Competence feedback, not gamification** — Use behavioral `message` fields and `success_message` that name what the learner demonstrated. No XP, streaks, or shame framing.

5. **Persistent project continuity** — Phase 1 ends with the Expedition 17 Report; Lessons 9+ introduce stable intake functions/structures (`readiness_status`, `can_depart`, dictionary records) for later callback.

Supporting principles: 3–4 progressive hints per exercise; 4+ `function` test cases on write exercises; examples teach structure without duplicating solutions; difficulty stays in 2–3 range for this batch.

---

## Appendix A: Parsons problems evaluation

**Not implementing drag-and-drop in this phase.**

### Pedagogical progression

```
Predict → Arrange → Modify → Write → Debug → Build
```

| Stage | Learner activity |
|-------|------------------|
| Predict | What will shuffled code do? |
| Arrange | Order lines/blocks correctly |
| Modify | Change one line in arranged code |
| Write | Write from scratch |
| Debug | Fix arranged/written code |
| Build | Extend working program |

### Where Parsons helps

- First contact with multi-line structure (if/else blocks, loop bodies)
- Before first independent `write_code` for a new construct
- When learners can read code but struggle to **organize** it

### Where Parsons is busywork

- Single-line expressions
- After learner already writes multi-line code independently for that construct
- Late course / capstone work (use debug + write instead)

### Future spec (sketch)

```json
{
  "type": "parsons",
  "blocks": ["if health > 50:", "    print('healthy')", "else:", "    print('wounded')"],
  "distractors": ["elif health > 0:"]
}
```

Grading: run assembled code against behavioral tests.

---

## Appendix B: Quick Challenges (future)

Short retrieval tasks surfaced by spacing/mastery engine.

### Flow

1. Optional prompt: "Quick practice — loops" *(no "review" or "failed" framing)*
2. Tiny task (3–8 lines expected)
3. On success: strengthen concept band
4. On failure: retry → progressive hint → optional 60-second refresher link (not full lesson re-read)

### Rules

- Never block lesson unlock
- Never punish failure
- Draw from `concepts_retrieved` pools
- 2–4 minute target duration

**Defer until Phase 3/4:** Quick Challenges should not block Lessons 9–13 authoring. Until an adaptive engine exists, embedded retrieval exercises in forward lessons suffice.

---

## Appendix C: Prediction exercise progression

Train mental execution with increasing complexity:

| Level | Example concepts | Phase 2 placement |
|-------|------------------|-------------------|
| 1 | Simple expression, print | Phase 1 |
| 2 | Conditional branch | Lessons 9–10 |
| 3 | Loop iteration count | Lesson 11 |
| 4 | Mutation after method | Lesson 12 |
| 5 | Dict access/update | Lesson 13 |
| 6 | Function call + return | Lessons 16–18 |
| 7 | Object/reference behavior | Lessons 24–26 |

### Commit-before-run (ideal UX)

1. Learner enters/selects prediction
2. Prediction locked (or recorded)
3. Learner runs code
4. Actual output shown
5. Compare prediction vs reality

### Interim predict UX standard (until commit-lock ships)

**Supported path today:** Check-only grading on `expected_answer`.

1. **Prompt copy** — *"Decide your answer, then click Check."* Do not imply Run validates predictions.
2. **Optional self-verify** — *"Copy the snippet into the editor and Run if you want to verify before checking."*
3. **Compare step** — Feedback states match/mismatch; on mismatch show expected vs learner answer without revealing write-code solutions.
4. **Snippet length** — Keep `code_to_predict` ≤8 lines in Lessons 9–13 (P1 auto-height partial; max ~200px).

**Target (future):** Record prediction before Run; side-by-side comparison UI; optional override after 2 failed Checks (hint-equivalent, not penalized).

---

## Related documents

- `docs/phase2-curriculum-plan.md` — Lesson 9–28 specifications
- `course/lessons/README.md` — JSON authoring checklist
- `.cursor/rules/pedagogy.mdc` — Teaching principles
- `.cursor/rules/exercise-quality.mdc` — Assessment quality rules
- `course/exercise.py` — Exercise types and JSON models
- `engine/exercise_checker.py` — Grading behavior

---

## Appendix D: UI prerequisites for engagement patterns

Several engagement patterns depend on UI behavior documented in `docs/phase2-curriculum-plan.md`. Verify via `tests/test_ui_phase2_prerequisites.py` before authoring Lessons 9+.

### Status (2026-08-14)

| Prerequisite | Status | Authoring impact |
|--------------|--------|------------------|
| **P0-1** choices rendering | Shipped (`ide_panel` radios) | Architecture OK; **UX follow-up:** render choices in one surface only (right-panel radios) |
| **P0-2** output panel | Shipped (min ~140px + stretch) | Debug/traceback authoring OK |
| **P0-3** Run/Check separation | Shipped | Debug Run-first workflow OK |
| **P1-1** predict auto-height | Partial (max ~200px) | Keep predict snippets ≤8 lines in 9–13 |
| **Commit-before-run** | Not shipped | Check-only predict grading; see Appendix C |
| **Multi-line predict answer** | Not shipped | Prefer single-line or choice-based predicts |
| **Lesson completion summary** | Not shipped | Per-exercise `success_message` carries narrative |

### Pattern requirements

| Pattern | UI requirement |
|---------|----------------|
| Architecture / learner reasoning | Render `exercise.choices` as selectable options (**one authoritative location**) |
| Debug: Run → observe → fix | Run → Output only; Check/Hints → Feedback only |
| Multi-line output / tracebacks | Output panel min ~140px + vertical stretch |

**Lessons 9–10** include architecture exercises. **Debug exercises across 9–13** require authentic Run-first workflow (P0-3).

---

## Appendix E: Specialist review synthesis

This document was reviewed by [curriculum-designer](bc-285a2f6f-446b-56ba-aae2-e6c28cb5cf5e), [assessment-designer](bc-e7dd41f1-807f-5ed5-bb9a-ee310a6864f0), [learning-ux-reviewer](bc-93ee6544-e0f7-5383-a905-e348af502f7b), and post-review critiques from [Critique design doc curriculum](bc-85c4874c-7f1e-5ef4-90c9-6b0f611edfaa), [Critique design doc assessment](bc-c966280a-c6f4-5802-879e-e880399f28f8), and [Critique design doc UX](bc-6306799b-37f6-5107-b4f0-d093bc5eea95).

**§20A must not contradict Appendix D on P0 status or discovery avoidance in 9–13.**

Key integrated recommendations:

### Curriculum

- Treat `docs/phase2-curriculum-plan.md` as the **authoritative lesson spec** for 9–28; this document governs *why* and *how*, not duplicate per-lesson tables.
- **Do not implement the full engagement stack before Lessons 9–13 exist** — feature sprawl risks thin exercises and blocks curriculum on engine work.
- Persistent project naming must be **stable from Lesson 9** (`wound_label`, `can_enter`, `make_stats`) so Lesson 18–19 can reference prior artifacts.
- RPG thread = **shared vocabulary** through Lesson 18; cumulative project file deferred until nested data (Lesson 19) and capstone (Lesson 28).
- **Lesson 10 is the first section boss** — integrator `can_enter` with 5+ function cases; not a new exercise type yet.
- **Lesson 13 is the hardest jump** — keep 4 exercises, heavy scaffolding; no Parsons, mystery, or boss there.
- Reflection: use lightweight MCQ only (e.g., post-boss architecture); avoid open-ended journaling in Phase 2.
- Defer Parsons (6–8 total in Phase 2 max), Quick Challenges (Phase 3/4), context-choice variants, skill tree, and mastery UI.

### Assessment

- Prefer **behavioral tests** (`function`, `stdout_equals`, `expression`) over source comparison.
- **`write_code` minimum:** ≥3 visible cases + ≥1 hidden edge per exercise where generalization matters.
- Use `source_uses` only when construct use is the learning objective; extend features for Phase 2: `elif_branch`, `while_loop`, `boolean_op`, `dict_literal`.
- Debug exercises: `runs_successfully` + behavioral tests on fixed code; tag bug class in metadata (`logic|syntax|runtime`).
- **Hidden tests:** mark `tests[].hidden: true`; show first failing visible test only in feedback.
- Predict integrity requires **Check-only grading today**; commit-before-run is future — prompts must not say "run to check"
- Mastery: replace opaque floats with qualitative bands driven by weighted events; hints inform bands, never punish
- Failure taxonomy (future): distinguish `conceptual` vs `careless` vs `incomplete`
- Grading models: `course/exercise.py` (types), `engine/exercise_checker.py` (checks)

### Learning UX

- Short sessions require **interaction early** — first exercise should often be predict, not write.
- Failure copy must name the **behavior** that failed, never the learner.
- Hints are help, not penalty — UI should never show "hint penalty" or reduced score; never display hint count on success.
- Completion feedback should grow from per-exercise `success_message` toward lesson-level capability summaries.
- Avoid discovery/mystery exercises in 9–13 batch — focus on core loop establishment first.
- Run/Check separation (P0-3) shipped — verify before authoring
- Predict: **Check grades; Run is optional self-verify** for code learners write
- Remove duplicate architecture choice rendering (left list + right radios) before Lesson 9 ships
- Multi-line predict answer widget before complex loop traces.
- **Reflect step (future):** lightweight optional post-success consolidation ("What rule made this work?") — ungraded, one sentence; defer full implementation.
- **Retrieval naming:** in-world labels ("Field test," "Scout report") — never "Review homework" or "Spaced repetition."
- **Boss presentation:** same Run/Check/hints as normal exercises; label "Capstone," not a separate game mode.
- **Four loops need homes:** lesson → Lessons page; project → Dashboard card (defer until L18+); retrieval → optional Dashboard tile (L15+); playground → Experiment nav. Never stack more than two loops on one screen.
- **Quick Challenges:** opt-in from Dashboard only; no mid-lesson interruptions until Phase 3/4.
- **Persistent project UI:** defer editable game state until L18+; optional read-only "party log" card later.

### Engine compatibility matrix (what works today)

| Feature | Works now | Requires P0 UI | Requires engine extension |
|---------|-----------|----------------|---------------------------|
| predict_output, fill_blank, write_code, debug | ✓ | | |
| architecture with choices | ✓ | verify P0-1 | dedupe choice UI |
| Debug Run → observe | ✓ | verify P0-3 | |
| Multi-line output / tracebacks | ✓ | verify P0-2 | |
| Concept role tags | ✓ (authoring notes) | | schema validation |
| Hidden test differentiation | | | `tests[].hidden` |
| Commit-before-run | | UI lock | progress fields |
| Quick/Boss/Parsons types | | | new checkers |
| Hint-weighted mastery | | | progress schema |
| Partial pass on multi-test exercises | | | engine `CheckResult` |

---

## Document history

| Date | Change |
|------|--------|
| 2026-08-14 | Initial design document synthesized from engagement proposal, Phase 2 plan, and specialist review |
| 2026-08-14 | Post-review: exposure budgets, spacing rules, RPG vocabulary scope, assessment specs, anti-patterns, compatibility matrix |
| 2026-08-14 | UX review: Boss table fix, P0 acceptance criteria, interim predict UX standard, UX synthesis in Appendix E |
| 2026-08-14 | Critique pass: §20 restructure, P0 shipped status, Check-only predict, Phase 1 project baseline, assessment honesty |
