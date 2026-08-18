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


class BrandAssetLoadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def test_sidebar_logo_loads_independent_of_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            progress_path = Path(tmp) / "progress.json"
            prefs = UiPrefsStore(Path(tmp) / "ui_prefs.json")
            prefs.load()
            controller, runner, _ignored_prefs = build_controller(ROOT)
            controller.progress = ProgressStore(progress_path)
            controller.progress.load()
            controller.progress.load_warning = None
            controller.progress.recovered_from_corrupt = False

            # Change working directory to a temp path to ensure no cwd-relative lookup is used
            cwd_before = os.getcwd()
            os.chdir("/tmp")
            try:
                course = CourseApp(controller, runner, prefs_store=prefs)
                course.show()
                self.app.processEvents()
                # Access the sidebar brand logo pixmap; it should be non-null
                pix = course.sidebar._brand_logo.pixmap()  # type: ignore[attr-defined]
                self.assertIsNotNone(pix)
                self.assertFalse(pix.isNull())
                course.close()
                self.app.processEvents()
            finally:
                os.chdir(cwd_before)


if __name__ == "__main__":
    unittest.main()

