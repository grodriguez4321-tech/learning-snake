#!/usr/bin/env python3
from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.course_app import CourseApp
from main import build_controller


def main() -> None:
    print("building", flush=True)
    controller, runner = build_controller(ROOT)
    print("tk", flush=True)
    root = tk.Tk()
    root.withdraw()  # headless-friendly; still constructs widgets
    root.title("Interactive Python Course — smoke")
    root.geometry("1100x750")
    print("app", flush=True)
    app = CourseApp(root, controller, runner)
    assert app.lesson_view.lesson is not None
    print("lesson", app.lesson_view.lesson.id, flush=True)

    app.editor.set_code('print("Hello, Adventurer!")')
    print("run valid", flush=True)
    app._run_code()
    print("check", flush=True)
    app._check_answer()

    print("syntax", flush=True)
    app.editor.set_code("if True\n    print(1)")
    app._run_code()

    print("runtime", flush=True)
    app.editor.set_code("print(missing)")
    app._run_code()

    print("timeout begin", flush=True)
    app.runner.timeout = 0.5
    app.editor.set_code("while True:\n    pass\n")
    app._run_code()
    print("timeout done", flush=True)

    # Avoid update()/mainloop; destroy widgets directly.
    try:
        root.destroy()
    except tk.TclError:
        pass
    print("GUI smoke OK", flush=True)


if __name__ == "__main__":
    main()
