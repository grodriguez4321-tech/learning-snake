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

from app.course_app import CourseApp  # noqa: E402
from app.theme import DARK, build_stylesheet  # noqa: E402
from main import build_controller  # noqa: E402


def _qt() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setStyleSheet(build_stylesheet(DARK))
    return app


class SidebarCollapsedBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def test_collapsed_is_icon_only_and_accessible_and_prefs_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            controller, runner, prefs = build_controller(ROOT, data_dir=Path(tmp))
            course = CourseApp(controller, runner, prefs_store=prefs)
            course.show()
            self.app.processEvents()

            # Expanded by default
            self.assertGreaterEqual(course.sidebar.width(), 200)
            expanded_w = course.sidebar.width()
            self.assertEqual(expanded_w, 232)

            # Manual collapse to 64 px
            course.sidebar.set_collapsed(True)
            self.app.processEvents()
            self.assertEqual(course.sidebar.width(), 64)

            # Heading/footer/brand label hidden in collapsed state
            self.assertFalse(course.sidebar._brand_label.isVisible())
            self.assertFalse(course.sidebar._heading.isVisible())
            self.assertFalse(course.sidebar._footer.isVisible())

            # Nav buttons are icon-only (no route labels in text)
            for key, btn in course.sidebar._nav_buttons.items():  # type: ignore[attr-defined]
                txt = btn.text().strip()
                # Should not contain any route label words
                self.assertNotRegex(
                    txt.lower(), r"(dashboard|lessons|playground|progress|settings)"
                )
                # Keep text small (the emoji/icon)
                self.assertLessEqual(len(txt), 3, txt)
                # Tooltip remains informative
                self.assertRegex(
                    btn.toolTip().lower(), r"(dashboard|lessons|playground|progress|settings)"
                )

            # Lesson list rows: labels hidden, icons visible, accessible names preserved
            self.assertGreater(len(course.sidebar._lesson_rows), 0)  # type: ignore[attr-defined]
            any_row = next(iter(course.sidebar._lesson_rows.values()))  # type: ignore[attr-defined]
            self.assertFalse(any_row._label.isVisible())
            self.assertTrue(any_row._icon.isVisible())
            self.assertTrue(any_row.accessibleName() != "")
            self.assertIn(any_row.toolTip(), (any_row.accessibleName(), f"Locked — {any_row._full_title}"))

            # Routes remain activatable via icon-only buttons (e.g., Settings)
            course.sidebar._nav_buttons["settings"].click()  # type: ignore[attr-defined]
            self.app.processEvents()
            # Breadcrumb updates to Settings
            self.assertRegex(course.top_bar._breadcrumb.toolTip(), r"Settings|settings")  # type: ignore[attr-defined]

            # Expand and restore full layout
            course.sidebar.set_collapsed(False)
            self.app.processEvents()
            self.assertEqual(course.sidebar.width(), 232)
            self.assertTrue(course.sidebar._brand_label.isVisible())
            self.assertTrue(course.sidebar._heading.isVisible())
            self.assertTrue(course.sidebar._footer.isVisible())
            any_row = next(iter(course.sidebar._lesson_rows.values()))  # type: ignore[attr-defined]
            self.assertTrue(any_row._label.isVisible())

            # Responsive auto-collapse does not mutate sidebar_visible preference
            before_pref = course.prefs_store.prefs.sidebar_visible
            # Ensure visible and expanded before resize
            course.show_sidebar()
            course.resize(1000, 800)  # below threshold for auto-collapse
            self.app.processEvents()
            self.assertTrue(course.sidebar._collapsed)  # type: ignore[attr-defined]
            self.assertEqual(course.prefs_store.prefs.sidebar_visible, before_pref)
            # Widen to restore
            course.resize(1440, 900)
            self.app.processEvents()
            self.assertFalse(course.sidebar._collapsed)  # type: ignore[attr-defined]
            self.assertEqual(course.sidebar.width(), 232)

            course.close()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()

