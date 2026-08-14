# Interactive Python Course

A self-paced desktop app that teaches Python through lessons, runnable examples,
behavior-checked exercises, progressive hints, and saved progress.

Phase 1 focuses on a working architecture: GUI shell, lesson loading, isolated
code execution with timeouts, exercise checking, unlocking, and progress
persistence — plus a beginner path from print through functions.

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

## Project structure

```
├── main.py                 # Entry point
├── requirements.txt        # PySide6
├── app/                    # PySide6 UI (IDE-style shell)
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
  "title": "Print and Comments",
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
- `source_uses` — require a construct (f-string, append, index, `if`, `for`, …) when that construct is the learning objective
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

The Tkinter UI runs Run/Check/Playground work on a background thread and marshals
results back with `after(...)`, so the interface stays responsive while waiting.

Tracebacks are filtered to learner code (`<student>` / `<playground>`), not the
application internals.

## Imports and modules

Learner code uses a guarded `__import__`. By default **no modules are importable**
(Phase 1 lessons do not need them). When the curriculum reaches modules, a lesson
or exercise may set:

```json
"allowed_modules": ["math", "json"]
```

Only names in the curated curriculum catalog can be enabled (`math`, `json`,
`random`, …). Requests for modules like `os` or `subprocess` are rejected even if
listed by mistake.

## Progress saving

Progress is stored in `data/progress.json`:

- completed lessons / exercises
- attempt counts and hints used
- draft code for unfinished exercises
- current lesson id
- mastery scores and mistake topic counts

It loads automatically on launch and saves after checks, hints, navigation, and
on quit. **File → Reset Progress…** clears everything after confirmation.

If the progress file is corrupt or malformed, the app quarantines it (renamed to
`progress.json.corrupt-<timestamp>`), starts fresh, and shows a warning instead of
crashing.

## How to add another lesson

1. Create `course/lessons/<id>.json` using an existing lesson as a template.
2. Set `section`, `section_order`, and `order` so it sorts where you want.
3. Add exercises with `tests` (or `expected_answer` / `choices`).
4. Optionally set `allowed_modules` on the lesson or exercise when imports are needed.
5. Restart the app (catalog loads at startup).
6. Optionally extend mastery topic names in `engine/progress.py` if you introduce
   a new major topic label.

No GUI code changes are required for ordinary new lessons.

## Unlocking

Lesson 1 is unlocked. Each following lesson unlocks when every exercise in the
previous lesson is marked complete.

## Playground

The Playground tab runs code in a persistent namespace. JSON/pickle-serializable
values remain until you click **Reset Environment**. Some objects (notably many
class definitions) may not persist across playground runs; recreate them if
needed.

## Phase roadmap

- **Phase 1 (this)**: architecture + beginner path from print through functions
- **Phase 2**: polished beginner curriculum (variables → basic classes)
- **Phase 3**: composition, inheritance, debugging, intermediate Python
- **Phase 4**: review/mastery adaptation + final RPG project milestones
