#!/usr/bin/env python3
"""Headless-friendly GUI smoke test specifically for Developer Preview Mode."""

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
    print("building developer", flush=True)
    controller, runner = build_controller(
        ROOT, developer_mode=True, initial_lesson_id="collections_19_nested_data"
    )[:2]
    controller.progress.load_warning = None
    controller.progress.recovered_from_corrupt = False

    print("qt", flush=True)
    qt = QApplication.instance() or QApplication(sys.argv)
    print("app", flush=True)
    course = CourseApp(controller, runner)
    assert "Developer Preview" in course.windowTitle()
    assert course.lesson_view.lesson is not None
    print("lesson", course.lesson_view.lesson.id, flush=True)
    course.close()
    print("Developer Preview GUI smoke OK", flush=True)


if __name__ == "__main__":
    main()

