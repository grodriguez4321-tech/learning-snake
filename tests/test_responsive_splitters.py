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

    def test_vertical_drawer_present_and_resizable_and_responsive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            controller, runner, prefs = build_controller(ROOT, data_dir=data_dir)

            course = CourseApp(controller, runner, prefs_store=prefs)
            course.show()
            self.app.processEvents()

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

            # Both-pane policy at wide size: Practice + editor visible, editor >= ~520 px
            course.lessons_page.mode_bar._practice.click()
            course.show_editor()
            course.resize(1440, 900)
            self.app.processEvents()
            self.assertTrue(course.lessons_page.content.isVisible())
            self.assertTrue(course.lessons_page.ide.isVisible())
            self.assertGreaterEqual(course.lessons_page.ide.width(), 500)

            # Below-900 single-pane: Learn/Examples keep Prompt visible, Code disabled
            before_pref = course.prefs_store.prefs.editor_visible
            course.lessons_page.mode_bar._learn.click()
            course.resize(880, 800)
            self.app.processEvents()
            self.assertTrue(course.lessons_page.pane_bar.isVisible())
            # Attempt to switch to Code in non-Practice should be a no-op
            course.lessons_page.pane_bar._code.click()
            self.app.processEvents()
            self.assertTrue(course.lessons_page.content.isVisible())
            self.assertFalse(course.lessons_page.ide.isVisible())
            # Preference should remain unchanged by single-pane temporary policy
            self.assertEqual(course.prefs_store.prefs.editor_visible, before_pref)

            # Switch to Practice under 880px: Prompt/Code switch controls visibility without flipping prefs
            course.lessons_page.mode_bar._practice.click()
            self.app.processEvents()
            # Starts on Prompt
            self.assertTrue(course.lessons_page.content.isVisible())
            self.assertFalse(course.lessons_page.ide.isVisible())
            # Switch to Code
            course.lessons_page.pane_bar._code.click()
            self.app.processEvents()
            self.assertFalse(course.lessons_page.content.isVisible())
            self.assertTrue(course.lessons_page.ide.isVisible())
            self.assertEqual(course.prefs_store.prefs.editor_visible, before_pref)

            # Drawer states: collapsed ~40, idle ~140, active ~240 (platform deltas allowed)
            vs = course.lessons_page.ide._vsplitter
            # Give the layout some room to honor target sizes
            course.resize(1200, 800)
            self.app.processEvents()
            # Verify relative ordering collapsed < idle < active
            course.lessons_page.ide.set_drawer_active()
            self.app.processEvents()
            h_active = vs.sizes()[1]
            course.lessons_page.ide.set_drawer_idle()
            self.app.processEvents()
            h_idle = vs.sizes()[1]
            course.lessons_page.ide.set_drawer_collapsed()
            self.app.processEvents()
            h_collapsed = vs.sizes()[1]
            self.assertLessEqual(h_collapsed, h_idle)
            self.assertLessEqual(h_idle, h_active)
            # Ensure there is a meaningful range between collapsed and active
            self.assertGreaterEqual(h_active - h_collapsed, 10)
            course.lessons_page.ide.set_drawer_idle()
            self.app.processEvents()
            h = vs.sizes()[1]
            self.assertGreaterEqual(h, 120)
            course.lessons_page.ide.set_drawer_active()
            self.app.processEvents()
            h = vs.sizes()[1]
            self.assertGreaterEqual(h, 220)

            course.close()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()

