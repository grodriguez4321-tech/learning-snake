#!/usr/bin/env python3
from __future__ import annotations

import sys
import time
import tkinter as tk
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.course_app import CourseApp
from main import build_controller


def wait_until(root: tk.Tk, app: CourseApp, timeout: float = 8.0) -> None:
    """Pump Tk events until background work finishes (no nested mainloop)."""
    deadline = time.monotonic() + timeout
    while app._busy:
        if time.monotonic() >= deadline:
            raise TimeoutError("Timed out waiting for background work")
        root.update()
        time.sleep(0.05)
    root.update_idletasks()


def main() -> None:
    print("building", flush=True)
    controller, runner = build_controller(ROOT)[:2]
    # Avoid modal recovery dialogs during automated smoke.
    controller.progress.load_warning = None
    controller.progress.recovered_from_corrupt = False

    print("tk", flush=True)
    root = tk.Tk()
    root.withdraw()
    root.title("Interactive Python Course — smoke")
    root.geometry("1100x750")
    print("app", flush=True)
    app = CourseApp(root, controller, runner)
    app.controller.progress.load_warning = None
    assert app.lesson_view.lesson is not None
    print("lesson", app.lesson_view.lesson.id, flush=True)

    print("toggle panels", flush=True)
    app.hide_sidebar()
    root.update()
    app.hide_editor()
    root.update()
    app.show_sidebar()
    root.update()
    app.show_editor()
    root.update()
    app.toggle_theme()
    root.update()
    app.toggle_theme()
    root.update()

    app.editor.set_code('print("Hello, Adventurer!")')
    print("run valid", flush=True)
    app._run_code()
    wait_until(root, app)

    print("check", flush=True)
    app._check_answer()
    wait_until(root, app)

    print("syntax", flush=True)
    app.editor.set_code("if True\n    print(1)")
    app._run_code()
    wait_until(root, app)

    print("runtime", flush=True)
    app.editor.set_code("print(missing)")
    app._run_code()
    wait_until(root, app)

    print("timeout begin", flush=True)
    app.runner.timeout = 0.5
    app.editor.set_code("while True:\n    pass\n")
    app._run_code()
    wait_until(root, app, timeout=10.0)
    print("timeout done", flush=True)

    try:
        root.destroy()
    except tk.TclError:
        pass
    print("GUI smoke OK", flush=True)


if __name__ == "__main__":
    main()
