# AGENTS.md

## Cursor Cloud specific instructions

This repo is a single self-contained **PySide6 desktop app** (**Basilisk**).
There is no backend, database, or network service — everything runs locally in
one process. See `README.md` for the full architecture and command reference.

### Environment

- Python deps live in a virtualenv at `.venv` (created by the startup update script from `requirements.txt`). Activate it with `. .venv/bin/activate`, or call binaries directly (e.g. `.venv/bin/python`). The venv is NOT auto-activated in new shells.
- The GUI needs Qt/X11 system libraries (already installed in the environment snapshot): `libegl1`, `libgl1`, `libxkbcommon0`, `libxkbcommon-x11-0`, `libxcb-xkb1`, `libxcb-cursor0`, and related `libxcb-*` packages. If the `xcb` platform plugin fails to load, run `ldd .venv/lib/python*/site-packages/PySide6/Qt/plugins/platforms/libqxcb.so | grep 'not found'` to find any missing lib.

### Run / test / lint

- Run the app on the desktop: `DISPLAY=:1 python main.py` (an XFCE desktop is available on `DISPLAY=:1` for manual/GUI testing). Headless smoke check: `xvfb-run -a python main.py`.
- Automated tests (no display needed for engine tests; GUI tests use the offscreen platform): `QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v`.
- GUI smoke test: `xvfb-run -a python tests/smoke_gui.py`.
- There is no configured linter/formatter in this repo (no flake8/ruff/black config); "lint" is covered by the test suite.

#### Developer Preview

- Launch with isolated developer progress (does not change learner progress):
  - `py main.py --developer`
  - `py main.py --developer --lesson collections_19_nested_data`

### Gotchas

- Runtime state (`data/progress.json`, `data/ui_prefs.json`) is created on first run and is git-ignored. Delete these files to reset app state; the app also self-recovers from a corrupt progress file by quarantining it.
- Each code run spawns a subprocess (`python -m engine.execution_worker`) with a timeout, so tests and runs need the venv's `python` to be the one invoked.
