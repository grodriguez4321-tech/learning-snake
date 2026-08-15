"""Lightweight application-startup smoke (offscreen Qt).

Constructs QApplication + the main window, checks that import/startup does
not raise, then closes. Never calls QApplication.exec() or launch_app(), so
the test cannot sit in a GUI event loop waiting for a human.
"""

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


class AppStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def test_main_window_constructs_and_closes_without_hanging(self) -> None:
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
            self.app.processEvents()

            from PySide6.QtWidgets import QLabel

            self.assertEqual(course.windowTitle(), "Basilisk")
            brand_label = course.sidebar.findChild(QLabel, "BrandTitle")
            self.assertIsNotNone(brand_label)
            assert brand_label is not None
            self.assertEqual(brand_label.text(), "Basilisk")
            page_title = course.dashboard_page.findChild(QLabel, "PageTitle")
            self.assertIsNotNone(page_title)
            assert page_title is not None
            self.assertEqual(page_title.text(), "Basilisk")
            self.assertIsNotNone(course.lesson_view.lesson)
            self.assertFalse(course._busy)
            self.assertFalse(course._closing)

            course.close()
            self.app.processEvents()
            self.assertTrue(course._closing)


if __name__ == "__main__":
    unittest.main()
