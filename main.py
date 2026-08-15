#!/usr/bin/env python3
"""Entry point for Basilisk — an interactive Python learning program."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.course_app import launch_app
from app.ui_prefs import UiPrefsStore
from course.catalog import CourseCatalog
from engine.code_runner import CodeRunner
from engine.course_controller import CourseController
from engine.exercise_checker import ExerciseChecker
from engine.progress import ProgressStore


def build_controller(
    root: Path | None = None,
    *,
    data_dir: Path | None = None,
) -> tuple[CourseController, CodeRunner, UiPrefsStore]:
    base = Path(root) if root is not None else ROOT
    catalog = CourseCatalog(base / "course" / "lessons")
    catalog.load()
    runtime = Path(data_dir) if data_dir is not None else base / "data"
    progress = ProgressStore(runtime / "progress.json")
    progress.load()
    prefs = UiPrefsStore(runtime / "ui_prefs.json")
    prefs.load()
    runner = CodeRunner()
    checker = ExerciseChecker(runner)
    controller = CourseController(catalog, progress, checker)
    if progress.data.current_lesson_id is None and catalog.first():
        progress.data.current_lesson_id = catalog.first().id
        progress.save()
    return controller, runner, prefs


def main() -> None:
    controller, runner, prefs = build_controller()
    launch_app(controller, runner, prefs_store=prefs)


if __name__ == "__main__":
    main()
