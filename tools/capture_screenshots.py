#!/usr/bin/env python3
"""Capture Learn/Examples/Practice screenshots for the Basilisk UI."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.course_app import CourseApp  # noqa: E402
from main import build_controller  # noqa: E402


def ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def main() -> None:
    controller, runner, prefs = build_controller(ROOT)
    app = QApplication.instance() or QApplication(sys.argv)
    course = CourseApp(controller, runner, prefs_store=prefs)
    course.show()
    app.processEvents()

    lesson = controller.current_lesson()
    if lesson:
        course._show_lesson(lesson)
        app.processEvents()

    out_dir = ROOT / "docs" / "screenshots" / "three-stage-ui"
    sizes = [(1100, 700), (1400, 900)]
    for w, h in sizes:
        course.resize(w, h)
        app.processEvents()
        # Learn
        course.lessons_page.content.set_stage("learn")
        app.processEvents()
        p = course.grab()
        path = out_dir / f"lesson-learn-{w}x{h}.png"
        ensure_dir(path)
        p.save(str(path))
        # Examples
        course.lessons_page.content.set_stage("examples")
        app.processEvents()
        p = course.grab()
        path = out_dir / f"lesson-examples-{w}x{h}.png"
        p.save(str(path))
        # Practice
        course.lessons_page.content.set_stage("practice")
        app.processEvents()
        p = course.grab()
        path = out_dir / f"lesson-practice-{w}x{h}.png"
        p.save(str(path))

    course.close()


if __name__ == "__main__":
    main()

