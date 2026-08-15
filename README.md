# Basilisk

An interactive Python learning program built around reasoning, debugging, and
progressively constructing real programs.

Basilisk teaches through lessons, runnable examples, behavior-checked exercises,
progressive hints, and saved progress. Learners predict output, repair broken
programs, and build small tools that grow across lessons.

## Curriculum overview

**Phase 1 (Lessons 1–8)** — Expedition 17 records. Twenty-eight exercises from
`print()` through functions, using the Basilisk teaching rhythm: observe or
recall → predict → repair → build → transfer or integrate. Stable lesson IDs
from earlier releases are preserved.

**Lessons 9–13** — Expedition Intake System. Extends the path with `elif`,
Boolean logic, `len`/`range`, list methods, and dictionaries, ending in a
capstone that builds a structured expedition record.

**Lessons 14–18** — Expedition Dispatch. Dictionary iteration and `.get`,
`while` loops, multiple parameters, defaults/keywords, and returning fresh
lists/dictionaries (Dispatch System v1). Catalog size after this batch:
18 lessons / 79 exercises.

Later curriculum batches (nested data, scope, strings/errors, references,
classes, and beyond) remain deferred as described in
`docs/phase2-curriculum-plan.md` and `docs/basilisk-master-curriculum-roadmap.md`.

## How to run

Requires Python 3.10+ and **PySide6**.

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

On Debian/Ubuntu you may also need Qt platform libraries (for example
`libxcb-cursor0`) if the window fails to open.

### IDE controls

| Action | Shortcut | Also |
| --- | --- | --- |
| Toggle sidebar | `Ctrl+B` | **Sidebar** in the top toolbar |
| Toggle editor column | `Ctrl+J` | **Editor** in the top toolbar |
| Toggle Dark/Light | `Ctrl+Shift+D` | **Theme · …** in the top toolbar |
| Save progress | `Ctrl+S` | **Save** in the top toolbar (also Settings) |
| Reset progress | — | **Reset…** in the top toolbar (also Settings) |
| Run code | `Ctrl+Enter` | **Run Code** button |

UI preferences (theme + panel visibility) are saved in `data/ui_prefs.json`.

On a headless machine (for smoke-testing the window):

```bash
xvfb-run -a python3 main.py
```

Run engine tests (no display required):

```bash
python3 -m unittest discover -s tests -v
```

GUI smoke test:

```bash
xvfb-run -a python3 tests/smoke_gui.py
```

On Windows, GitHub Actions (`.github/workflows/windows-ci.yml`) runs the same
checks on `windows-latest` with Python 3.12 and `QT_QPA_PLATFORM=offscreen`.
That job is **not** a visual review.

| Kind | What it covers |
| --- | --- |
| Unit tests | Engine, curriculum, progress, non-GUI learning loop, process timeout |
| Qt automated tests | Offscreen widgets: Phase 2 UI prerequisites, sidebar, top bar, startup |
| GUI smoke | Offscreen construct / run / check / timeout; closes itself |
| Learning-loop harness | `tests/e2e_learning_loop.py` — no manual interaction |

A human still needs to look at a real Windows desktop for layout, DPI/scaling,
fonts, native window chrome, hover/focus, and theme contrast.

## Project structure

```
├── main.py                 # Entry point
├── requirements.txt        # PySide6
├── app/                    # PySide6 UI (IDE-style shell)
│   ├── branding.py         # Visible product name constants
│   ├── course_app.py       # Main window, navigation, async run/check
│   ├── theme.py            # Dark/light tokens + QSS stylesheet
│   ├── ui_prefs.py         # Persist theme + panel visibility
│   ├── workers.py          # Background job host (non-blocking UI)
│   ├── pages/              # Dashboard, Lessons, Playground, Progress, Settings
│   └── widgets/            # Sidebar, TopBar, LessonContent, CodeEditor, …
├── course/                 # Curriculum models + lesson JSON
│   ├── catalog.py          # Loads/orders lessons
│   ├── lesson.py
│   ├── exercise.py
│   └── lessons/            # One JSON file per lesson
├── engine/                 # Non-UI logic
│   ├── code_runner.py      # Subprocess runner + timeout
│   ├── execution_worker.py # Isolated process that execs learner code
│   ├── import_policy.py    # Guarded allowlist for learner imports
│   ├── exercise_checker.py # Behavior-based tests + feedback
│   ├── progress.py         # JSON save/load with corrupt recovery
│   └── course_controller.py# Unlock rules and navigation
├── data/                   # progress.json created at runtime
└── tests/
```

Why this split exists: the GUI should not own curriculum content or grading
rules. Lessons live in JSON; checking lives in the engine; the app only
coordinates user actions.

## How lesson data works

Each file in `course/lessons/` is a lesson document, for example:

```json
{
  "id": "fundamentals_01_print",
  "section": "Python Fundamentals",
  "section_order": 1,
  "order": 1,
  "title": "Leave a Trace",
  "topics": ["print"],
  "content": "Explanation text...",
  "concepts": ["..."],
  "examples": [{"title": "...", "code": "...", "explanation": "..."}],
  "common_mistakes": ["..."],
  "exercises": [ ... ]
}
```

`CourseCatalog` loads every `*.json`, sorts by `(section_order, order, id)`,
and groups lessons into sections for the sidebar. See `course/lessons/README.md`
for the authoring checklist.

## How exercises are checked

Exercises are not graded by comparing source text when behavior can be tested.
Student code (and its tests) run in an isolated subprocess so infinite loops can
be stopped without freezing the GUI.

Supported checks include:

- `stdout_equals` / `stdout_contains` — inspect printed output
- `globals` — require names/types/values after execution
- `function` — call a student function with hidden arguments
- `expression` / `attribute` — evaluate expressions (objects, nested values)
- `class_defined` — require a class name
- `raises` — expect an exception type from an expression
- `runs_successfully` — require clean execution
- `source_uses` — require a construct (f-string, append, index, `if`, `elif`, `for`, …) when that construct is the learning objective
- Predict-output / architecture answers — compare the learner's response

Example function tests for `double(number)` call several inputs so a hardcoded
`return 4` fails. Feedback names which cases passed before the failure.

Hints are progressive: each Hint click reveals the next stored hint and records
`hints_used` in progress.

## Code execution safety

`engine/code_runner.py` launches `python -m engine.execution_worker` for each
run. The parent enforces a timeout (default 2 seconds) and terminates the worker
with OS-appropriate APIs:

- POSIX: process-group `SIGTERM` then `SIGKILL`
- Windows: `CREATE_NEW_PROCESS_GROUP` + `terminate()` / `kill()`

Timed-out programs show:

> Your program ran for too long and was stopped. Check for an infinite loop.

The UI runs Run/Check/Playground work on a background thread so the interface
stays responsive while waiting.

Tracebacks are filtered to learner code (`<student>` / `<playground>`), not the
application internals.

## Imports and modules

Learner code uses a guarded `__import__`. By default **no modules are importable**
(early lessons do not need them). When the curriculum reaches modules, a lesson
or exercise may set:

```json
"allowed_modules": ["math", "json"]
```

Only names in the curated curriculum catalog can be enabled (`math`, `json`,
`random`, …). Requests for modules like `os` or `subprocess` are rejected even if
listed by mistake.

## Progress saving

Progress is stored in `data/progress.json`:

- `curriculum_version` (currently **2** for Basilisk Curriculum V2)
- completed lessons / exercises
- attempt counts and hints used
- draft code for unfinished exercises
- current lesson id
- mastery scores and mistake topic counts

It loads automatically on launch and saves after checks, hints, navigation, and
on quit. **Reset…** in the toolbar (also Settings) clears everything after
confirmation.

If the progress file is corrupt or malformed, the app quarantines it (renamed to
`progress.json.corrupt-<timestamp>`), starts fresh, and shows a warning instead of
crashing.

### Curriculum V2 migration

Basilisk Curriculum V2 reuses Phase 1 exercise IDs while changing their meaning.
Loading an older or unversioned progress file:

- archives the prior file as `progress.json.pre-basilisk-v2-<timestamp>`
- keeps mastery scores and mistake topic counts
- clears Phase 1 lesson completions and Phase 1 exercise records (including drafts)
- requires Lessons 1–8 to be retaken
- never shows old draft code inside an unrelated new exercise

UI preferences in `data/ui_prefs.json` are unrelated and are left alone.

## How to add another lesson

1. Create `course/lessons/<id>.json` using an existing lesson as a template.
2. Set `section`, `section_order`, and `order` so it sorts where you want.
3. Add exercises with `tests` (or `expected_answer` / `choices`).
4. Optionally set `allowed_modules` on the lesson or exercise when imports are needed.
5. Restart the app (catalog loads at startup).
6. Optionally extend mastery topic names in `engine/progress.py` if you introduce
   a new major topic label.

No GUI code changes are required for ordinary new lessons. See
`course/lessons/README.md` for the check kinds and `source_uses` features.

## Unlocking

Lesson 1 is unlocked. Each following lesson unlocks when every exercise in the
previous lesson is marked complete. Sidebar section labels follow the same
linear order (Expedition Intake sections for Lessons 9–13).

## Playground

The Playground tab runs code in a persistent namespace. JSON/pickle-serializable
values remain until you click **Reset Environment**. Some objects (notably many
class definitions) may not persist across playground runs; recreate them if
needed.

## Phase roadmap

- **Phase 1 (Lessons 1–8)**: Basilisk foundation — `print` through functions (28 exercises)
- **Lessons 9–13**: Expedition Intake System — `elif`, Boolean logic, `len`/`range`, list methods, dictionaries
- **Later batches**: nested data, parsing, classes, composition, and beyond — see
  `docs/phase2-curriculum-plan.md`
- **Full arc (provisional after Lesson 28)**: Practical Python → notebooks/data → ML literacy → Build the Basilisk — see
  `docs/basilisk-master-curriculum-roadmap.md`

## Design docs

- `docs/basilisk-master-curriculum-roadmap.md` — master curriculum architecture through the capstone
- `docs/phase2-curriculum-plan.md` — later sequencing after Lessons 1–13
- `docs/engagement-retention-design.md` — teaching philosophy and retention
- `docs/basilisk-curriculum-implementation-plan.md` — implementation notes for this redesign
- `docs/basilisk-curriculum-reconciliation.md` — review findings and decisions
