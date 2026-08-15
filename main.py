#!/usr/bin/env python3
"""Entry point for Basilisk — an interactive Python learning program."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
    developer_mode: bool = False,
    initial_lesson_id: str | None = None,
) -> tuple[CourseController, CodeRunner, UiPrefsStore]:
    base = Path(root) if root is not None else ROOT
    catalog = CourseCatalog(base / "course" / "lessons")
    catalog.load()
    runtime = Path(data_dir) if data_dir is not None else base / "data"
    progress_path = runtime / ("developer_progress.json" if developer_mode else "progress.json")
    progress = ProgressStore(progress_path)
    progress.load()
    prefs = UiPrefsStore(runtime / "ui_prefs.json")
    prefs.load()
    runner = CodeRunner()
    checker = ExerciseChecker(runner)
    controller = CourseController(catalog, progress, checker, developer_mode=developer_mode)
    # Select initial lesson id when provided (developer mode only).
    if initial_lesson_id and not developer_mode:
        raise ValueError("--lesson requires --developer mode")
    if initial_lesson_id:
        selected = catalog.get(initial_lesson_id)
        if selected is None:
            raise ValueError(f"Unknown lesson id: {initial_lesson_id}")
        progress.data.current_lesson_id = initial_lesson_id
        progress.save()
    elif progress.data.current_lesson_id is None and catalog.first():
        progress.data.current_lesson_id = catalog.first().id
        progress.save()
    return controller, runner, prefs


def main() -> None:
    import argparse
    from app.course_app import launch_app

    parser = argparse.ArgumentParser(description="Basilisk — interactive Python learning")
    parser.add_argument("--developer", "--dev", action="store_true", dest="developer_mode", help="Enable Developer Preview Mode")
    parser.add_argument("--lesson", dest="initial_lesson_id", help="Open a specific lesson id (requires --developer)")
    args = parser.parse_args()
    try:
        controller, runner, prefs = build_controller(
            developer_mode=bool(args.developer_mode),
            initial_lesson_id=args.initial_lesson_id,
        )
    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
        sys.exit(2)
    launch_app(controller, runner, prefs_store=prefs)


if __name__ == "__main__":
    main()
