#!/usr/bin/env python3
"""Headless-friendly GUI smoke test for the PySide6 shell."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.course_app import CourseApp
from main import build_controller


def wait_until(app_qt: QApplication, course: CourseApp, timeout: float = 8.0) -> None:
    deadline = time.monotonic() + timeout
    while course._busy:
        if time.monotonic() >= deadline:
            raise TimeoutError("Timed out waiting for background work")
        app_qt.processEvents()
        time.sleep(0.05)
    app_qt.processEvents()


def main() -> None:
    print("building", flush=True)
    controller, runner = build_controller(ROOT)[:2]
    controller.progress.load_warning = None
    controller.progress.recovered_from_corrupt = False

    print("qt", flush=True)
    qt = QApplication.instance() or QApplication(sys.argv)
    print("app", flush=True)
    course = CourseApp(controller, runner)
    course.controller.progress.load_warning = None
    assert course.lesson_view.lesson is not None
    print("lesson", course.lesson_view.lesson.id, flush=True)

    print("toggle panels", flush=True)
    course.hide_sidebar()
    qt.processEvents()
    course.hide_editor()
    qt.processEvents()
    course.show_sidebar()
    qt.processEvents()
    course.show_editor()
    qt.processEvents()
    course.toggle_theme()
    qt.processEvents()
    course.toggle_theme()
    qt.processEvents()

    course.editor.set_code('print("Hello, Adventurer!")')
    print("run valid", flush=True)
    course._run_code()
    wait_until(qt, course)

    print("check", flush=True)
    course._check_answer()
    wait_until(qt, course)

    print("syntax", flush=True)
    course.editor.set_code("if True\n    print(1)")
    course._run_code()
    wait_until(qt, course)

    print("runtime", flush=True)
    course.editor.set_code("print(missing)")
    course._run_code()
    wait_until(qt, course)

    print("timeout begin", flush=True)
    course.runner.timeout = 0.5
    course.editor.set_code("while True:\n    pass\n")
    course._run_code()
    wait_until(qt, course, timeout=10.0)
    print("timeout done", flush=True)

    course.close()
    print("GUI smoke OK", flush=True)


if __name__ == "__main__":
    main()
