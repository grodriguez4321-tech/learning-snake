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


class ViewTogglePrefsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def test_view_menu_checkmarks_sync_with_prefs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            progress_path = Path(tmp) / "progress.json"
            prefs_path = Path(tmp) / "ui_prefs.json"
            prefs = UiPrefsStore(prefs_path)
            prefs.load()
            controller, runner, _ignored_prefs = build_controller(ROOT)
            controller.progress = ProgressStore(progress_path)
            controller.progress.load()
            controller.progress.load_warning = None
            controller.progress.recovered_from_corrupt = False

            course = CourseApp(controller, runner, prefs_store=prefs)
            self.app.processEvents()

            # Sidebar visible by default per prefs; toggle off
            course.toggle_sidebar()
            self.app.processEvents()
            self.assertFalse(course.sidebar.isVisible())
            self.assertFalse(course.prefs_store.prefs.sidebar_visible)
            # Top bar controls mirror the View menu checkmarks
            self.assertFalse(course.top_bar._sidebar_btn.isChecked())

            # Toggle editor off then on
            course.toggle_editor()
            self.app.processEvents()
            self.assertFalse(course.prefs_store.prefs.editor_visible)
            self.assertFalse(course.top_bar._editor_btn.isChecked())
            course.toggle_editor()
            self.app.processEvents()
            self.assertTrue(course.prefs_store.prefs.editor_visible)
            self.assertTrue(course.top_bar._editor_btn.isChecked())

            course.close()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()

