"""Sidebar lesson-row title eliding (offscreen Qt)."""

from __future__ import annotations

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSize
from PySide6.QtGui import QFontMetrics, QResizeEvent
from PySide6.QtWidgets import QApplication

from app.theme import DARK, build_stylesheet
from app.widgets.sidebar import LessonRow


def _qt() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setStyleSheet(build_stylesheet(DARK))
    return app


def _is_elided(displayed: str, full: str) -> bool:
    return (
        len(displayed) < len(full)
        or displayed.endswith("…")
        or displayed.endswith("...")
    )


class LessonRowElideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def _shown_row(
        self,
        text: str,
        *,
        row_width: int = 228,
        label_width: int = 184,
        enabled: bool = True,
    ) -> LessonRow:
        row = LessonRow("functions_01_basics")
        row.set_row(icon="○", text=text, enabled=enabled, active=False)
        row.setFixedWidth(row_width)
        row.show()
        self.app.processEvents()
        row._label.setFixedWidth(label_width)
        row.resizeEvent(QResizeEvent(QSize(row_width, 34), QSize(row_width, 34)))
        self.app.processEvents()
        return row

    def test_long_title_elides_and_keeps_full_tooltip(self) -> None:
        title = "8. Defining Functions and return"
        row = self._shown_row(title, label_width=120)
        displayed = row._label.text()
        self.assertTrue(_is_elided(displayed, title), f"expected elision, got {displayed!r}")
        self.assertEqual(row.toolTip(), title)
        self.assertEqual(row._label.toolTip(), title)
        metrics = QFontMetrics(row._label.font())
        self.assertLessEqual(metrics.horizontalAdvance(displayed), row._label.width())

    def test_short_title_is_not_elided(self) -> None:
        title = "1. Print and Comments"
        row = self._shown_row(title, label_width=200)
        self.assertEqual(row._label.text(), title)
        self.assertEqual(row.toolTip(), title)

    def test_locked_tooltip_includes_full_title(self) -> None:
        title = "8. Defining Functions and return"
        row = self._shown_row(title, label_width=120, enabled=False)
        self.assertEqual(row.toolTip(), f"Locked — {title}")
        self.assertTrue(_is_elided(row._label.text(), title))

    def test_displayed_text_never_exceeds_label_width(self) -> None:
        title = "99. " + ("Very Long Lesson Title Word " * 8)
        row = self._shown_row(title, row_width=180, label_width=120)
        displayed = row._label.text()
        self.assertTrue(_is_elided(displayed, title))
        metrics = QFontMetrics(row._label.font())
        self.assertLessEqual(metrics.horizontalAdvance(displayed), row._label.width())
        self.assertEqual(row.toolTip(), title)


if __name__ == "__main__":
    unittest.main()
