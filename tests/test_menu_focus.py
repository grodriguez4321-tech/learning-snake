from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLineEdit

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


class MenuFocusRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def test_edit_actions_route_to_focused_widget(self) -> None:
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

            # Create a temporary line-edit and focus it
            line = QLineEdit()
            line.setText("hello")
            line.selectAll()
            line.show()
            line.setFocus()
            self.app.processEvents()

            # Trigger Cut via menu action and verify it affected the focused widget
            from PySide6.QtGui import QAction
            # Actions are parented to the Edit menu; search from the window
            cut_action = course.findChild(QAction, "edit.cut")
            self.assertIsNotNone(cut_action)
            assert cut_action is not None
            self.assertTrue(cut_action.isEnabled())
            cut_action.trigger()
            self.app.processEvents()
            self.assertEqual(line.text(), "")

            course.close()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()

