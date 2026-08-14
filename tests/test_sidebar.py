"""Sidebar lesson-row title eliding (offscreen Qt)."""

from __future__ import annotations

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.widgets.sidebar import LessonRow


def _qt() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


class LessonRowElideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def _shown_row(self, text: str, *, width: int = 228, enabled: bool = True) -> LessonRow:
        row = LessonRow("functions_01_basics")
        row.set_row(icon="○", text=text, enabled=enabled, active=False)
        row.setFixedWidth(width)
        row.show()
        self.app.processEvents()
        return row

    def test_long_title_elides_and_keeps_full_tooltip(self) -> None:
        title = "8. Defining Functions and return"
        row = self._shown_row(title)
        displayed = row._label.text()
        self.assertTrue(
            displayed.endswith("…") or displayed.endswith("..."),
            f"expected ellipsis, got {displayed!r}",
        )
        self.assertLess(len(displayed), len(title))
        self.assertEqual(row.toolTip(), title)
        self.assertEqual(row._label.toolTip(), title)

    def test_short_title_is_not_elided(self) -> None:
        title = "1. Print and Comments"
        row = self._shown_row(title)
        self.assertEqual(row._label.text(), title)
        self.assertEqual(row.toolTip(), title)

    def test_locked_tooltip_includes_full_title(self) -> None:
        title = "8. Defining Functions and return"
        row = self._shown_row(title, enabled=False)
        self.assertEqual(row.toolTip(), f"Locked — {title}")
        self.assertTrue(
            row._label.text().endswith("…") or row._label.text().endswith("..."),
            f"expected ellipsis, got {row._label.text()!r}",
        )


if __name__ == "__main__":
    unittest.main()
