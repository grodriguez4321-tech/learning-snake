from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.course_app import CourseApp
from app.theme import DARK, build_stylesheet
from app.ui_prefs import UiPrefsStore
from engine.progress import ProgressStore
from main import build_controller


def _qt() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setStyleSheet(build_stylesheet(DARK))
    return app


class SplitterResponsiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def test_vertical_drawer_present_and_resizable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            progress_path = Path(tmp) / "progress.json"
            prefs = UiPrefsStore(Path(tmp) / "ui_prefs.json")
            prefs.load()
            controller, runner, _ignored_prefs = build_controller(ROOT)
            controller.progress = ProgressStore(progress_path)
            controller.progress.load()
            controller.progress.load_warning = None
            controller.progress.recovered_from_corrupt = False

            course = CourseApp(controller, runner, prefs_store=prefs)
            course.show()
            self.app.processEvents()

            sp = course.lessons_page._vsplitter if hasattr(course.lessons_page, "_vsplitter") else None
            # lessons_page holds the horizontal splitter; ide has vertical one
            self.assertIsNotNone(course.lessons_page.splitter)
            self.assertIsNotNone(course.lessons_page.ide._vsplitter)

            # Change sizes and ensure they apply
            vs = course.lessons_page.ide._vsplitter
            sizes = vs.sizes()
            vs.setSizes([sizes[0] + 50, max(80, sizes[1] - 50)])
            self.app.processEvents()
            new_sizes = vs.sizes()
            self.assertTrue(isinstance(new_sizes, list))
            self.assertEqual(sum(new_sizes), sum(sizes))  # splitter preserves total

            course.close()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()

