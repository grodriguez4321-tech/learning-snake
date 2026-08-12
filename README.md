# Interactive Python Course

A self-paced desktop app that teaches Python through lessons, runnable examples,
behavior-checked exercises, progressive hints, and saved progress.

Phase 1 focuses on a working architecture: GUI shell, lesson loading, isolated
code execution with timeouts, exercise checking, unlocking, and progress
persistence — with a small set of sample lessons to prove the loop.

## How to run

Requires Python 3.10+ and Tkinter (`python3-tk` on Debian/Ubuntu).

```bash
python3 main.py
```

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
├── app/                    # Tkinter UI (composition of widgets)
│   ├── course_app.py       # Window layout and event wiring
│   ├── sidebar.py          # Sections, locks, progress
│   ├── lesson_view.py      # Lesson text + current exercise
│   ├── code_editor.py      # Editor, run/check/reset/hint, feedback
│   └── playground.py       # Free experimentation console
├── course/                 # Curriculum models + lesson JSON
│   ├── catalog.py          # Loads/orders lessons
│   ├── lesson.py
│   ├── exercise.py
│   └── lessons/            # One JSON file per lesson
├── engine/                 # Non-UI logic
│   ├── code_runner.py      # Subprocess runner + timeout
│   ├── execution_worker.py # Isolated process that execs learner code
│   ├── exercise_checker.py # Behavior-based tests + feedback
│   ├── progress.py         # JSON save/load
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
  "topics": ["variables"],
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
- Predict-output / architecture answers — compare the learner's response

Example function tests for `double(number)` call several inputs so a hardcoded
`return 4` fails. Feedback names which cases passed before the failure.

Hints are progressive: each Hint click reveals the next stored hint and records
`hints_used` in progress.

## Code execution safety

`engine/code_runner.py` launches `python -m engine.execution_worker` for each
run. The parent enforces a timeout (default 2 seconds). Timed-out programs show:

> Your program ran for too long and was stopped. Check for an infinite loop.

Tracebacks are filtered to learner code (`<student>` / `<playground>`), not the
application internals.

## How to add another lesson

1. Create `course/lessons/<id>.json` using an existing lesson as a template.
2. Set `section`, `section_order`, and `order` so it sorts where you want.
3. Add exercises with `tests` (or `expected_answer` / `choices`).
4. Restart the app (catalog loads at startup).
5. Optionally extend mastery topic names in `engine/progress.py` if you introduce
   a new major topic label.

No GUI code changes are required for ordinary new lessons.

## Progress saving

Progress is stored in `data/progress.json`:

- completed lessons / exercises
- attempt counts and hints used
- draft code for unfinished exercises
- current lesson id
- mastery scores and mistake topic counts

It loads automatically on launch and saves after checks, hints, navigation, and
on quit. **File → Reset Progress…** clears everything after confirmation.

## Unlocking

Lesson 1 is unlocked. Each following lesson unlocks when every exercise in the
previous lesson is marked complete.

## Playground

The Playground tab runs code in a persistent namespace. JSON/pickle-serializable
values remain until you click **Reset Environment**. Some objects (notably many
class definitions) may not persist across playground runs; recreate them if
needed.

## Phase roadmap

- **Phase 1 (this)**: architecture + 5 sample lessons proving the learning loop
- **Phase 2**: polished beginner curriculum (variables → basic classes)
- **Phase 3**: composition, inheritance, debugging, intermediate Python
- **Phase 4**: review/mastery adaptation + final RPG project milestones
