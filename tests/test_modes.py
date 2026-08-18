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


class ModeBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def test_learn_examples_practice_toggle_and_visibility(self) -> None:
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

            # Default enters lessons and should start in Learn
            self.assertEqual(course.stack.currentIndex(), course._page_keys["lessons"])
            lp = course.lessons_page
            self.assertTrue(lp.mode_bar is not None)

            # Learn mode: editor should be temporarily hidden if Practice-only
            lp.set_mode("learn")
            self.app.processEvents()
            self.assertFalse(lp.ide.isVisible())

            # Examples mode hides editor too
            lp.set_mode("examples")
            self.app.processEvents()
            self.assertFalse(lp.ide.isVisible())

            # Practice shows the editor when editor preference is on
            lp.set_mode("practice")
            course.show_editor()
            # Apply again to reconcile temporary Learn/Examples hiding logic
            lp.set_mode("practice")
            self.app.processEvents()
            self.assertTrue(lp.ide.isVisible())

            # Switching away must not flip the saved preference (only temporary)
            lp.set_mode("learn")
            self.app.processEvents()
            # Preference unchanged; turning Practice back on should show editor again
            lp.set_mode("practice")
            self.app.processEvents()
            self.assertTrue(lp.ide.isVisible())

            course.close()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()

