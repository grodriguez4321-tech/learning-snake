from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.course_app import CourseApp
from app.theme import DARK, LIGHT, build_stylesheet
from main import build_controller


def _qt() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def _wait_idle(app: QApplication, timeout_ms: int = 4000) -> None:
    """Process events for a short window to allow async jobs to settle."""
    end = time.time() + timeout_ms / 1000.0
    while time.time() < end:
        app.processEvents()
        time.sleep(0.01)


def _grab(window) -> "QPixmap":
    app = QGuiApplication.instance()
    assert app is not None
    return window.grab()


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _sha_short() -> str:
    try:
        import subprocess

        sha = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=str(ROOT))
            .decode("utf-8")
            .strip()
        )
        return sha
    except Exception:
        return "unknown"


def find_choice_exercise(controller) -> tuple[str, int] | None:
    for lesson in controller.catalog.lessons:
        for idx, ex in enumerate(lesson.exercises):
            if getattr(ex, "is_choice_exercise", False) or getattr(ex, "uses_free_text_answer", False):
                return (lesson.id, idx)
    return None


def main() -> int:
    app = _qt()
    app.setStyleSheet(build_stylesheet(DARK))

    # Isolated progress/prefs
    tmp = ROOT / "docs" / "review-evidence" / "workspace-v9" / _sha_short()
    _ensure_dir(tmp)
    controller, runner, prefs = build_controller(ROOT, data_dir=tmp)

    course = CourseApp(controller, runner, prefs_store=prefs)
    course.show()
    app.processEvents()

    # 1440x900 dark — Learn
    course.resize(1440, 900)
    course.lessons_page.mode_bar._learn.click()
    app.processEvents()
    _grab(course).save(str(tmp / "1440x900-dark-learn.png"))

    # 1440x900 dark — Examples
    course.lessons_page.mode_bar._examples.click()
    app.processEvents()
    _grab(course).save(str(tmp / "1440x900-dark-examples.png"))

    # 1440x900 dark — Practice idle
    course.lessons_page.mode_bar._practice.click()
    course.show_editor()
    app.processEvents()
    _grab(course).save(str(tmp / "1440x900-dark-practice-idle.png"))

    # 1440x900 dark — Practice active (run to populate Output, then hint to populate Feedback)
    course._run_code()
    _wait_idle(app, 4000)
    course._show_hint()
    _wait_idle(app, 500)
    _grab(course).save(str(tmp / "1440x900-dark-practice-active.png"))

    # 1100x700 dark — Learn/Practice
    course.resize(1100, 700)
    course.lessons_page.mode_bar._learn.click()
    app.processEvents()
    _grab(course).save(str(tmp / "1100x700-dark-learn.png"))
    course.lessons_page.mode_bar._practice.click()
    course.show_editor()
    app.processEvents()
    _grab(course).save(str(tmp / "1100x700-dark-practice.png"))

    # 1440x900 light — Learn/Practice
    course.apply_theme(LIGHT)
    course.resize(1440, 900)
    course.lessons_page.mode_bar._learn.click()
    app.processEvents()
    _grab(course).save(str(tmp / "1440x900-light-learn.png"))
    course.lessons_page.mode_bar._practice.click()
    course.show_editor()
    app.processEvents()
    _grab(course).save(str(tmp / "1440x900-light-practice.png"))
    # switch back to dark for rest
    course.apply_theme(DARK)
    app.processEvents()

    # Rail expanded vs collapsed
    course.resize(1440, 900)
    if not course.sidebar._collapsed:
        _grab(course).save(str(tmp / "rail-expanded.png"))
    course.sidebar.set_collapsed(True)
    app.processEvents()
    _grab(course).save(str(tmp / "rail-collapsed.png"))
    course.sidebar.set_collapsed(False)
    app.processEvents()

    # Choice/answer exercise capture if available
    choice_ref = find_choice_exercise(controller)
    if choice_ref:
        lesson_id, ex_idx = choice_ref
        lesson = controller.set_current_lesson(lesson_id)
        if lesson:
            course._show_lesson(lesson, ex_idx)
            course.lessons_page.mode_bar._practice.click()
            course.show_editor()
            app.processEvents()
            _grab(course).save(str(tmp / "1440x900-dark-choice-or-answer.png"))

    print(f"Wrote screenshots to: {tmp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

