"""Top bar breadcrumb eliding (offscreen Qt)."""

from __future__ import annotations

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QApplication

from app.theme import DARK, build_stylesheet
from app.widgets.top_bar import TopBar


def _qt() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setStyleSheet(build_stylesheet(DARK))
    return app


class TopBarBreadcrumbElideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def _shown_bar(self, text: str, *, width: int = 720) -> TopBar:
        bar = TopBar()
        bar.set_breadcrumb(text)
        bar.setFixedWidth(width)
        bar.show()
        self.app.processEvents()
        return bar

    def test_long_breadcrumb_elides_with_tooltip(self) -> None:
        text = "📖  Python Fundamentals  ›  Defining Functions and return"
        bar = self._shown_bar(text, width=720)
        displayed = bar._breadcrumb.text()
        self.assertTrue(
            displayed.endswith("…") or displayed.endswith("..."),
            f"expected ellipsis, got {displayed!r}",
        )
        self.assertLess(len(displayed), len(text))
        self.assertEqual(bar._breadcrumb.toolTip(), text)
        metrics = QFontMetrics(bar._breadcrumb.font())
        self.assertLessEqual(
            metrics.horizontalAdvance(displayed), bar._breadcrumb.width() or 720
        )

    def test_short_breadcrumb_is_not_elided(self) -> None:
        text = "Dashboard"
        bar = self._shown_bar(text, width=900)
        self.assertEqual(bar._breadcrumb.text(), text)
        self.assertEqual(bar._breadcrumb.toolTip(), text)

    def test_elide_updates_on_resize(self) -> None:
        text = "📖  Python Fundamentals  ›  Defining Functions and return"
        bar = self._shown_bar(text, width=900)
        self.assertEqual(bar._breadcrumb.text(), text)
        bar.setFixedWidth(720)
        self.app.processEvents()
        self.assertTrue(
            bar._breadcrumb.text().endswith("…")
            or bar._breadcrumb.text().endswith("...")
        )

    def test_very_narrow_bar_still_elides(self) -> None:
        text = "📖  Python Fundamentals  ›  Defining Functions and return"
        bar = self._shown_bar(text, width=480)
        displayed = bar._breadcrumb.text()
        self.assertTrue(
            displayed.endswith("…") or displayed.endswith("...") or displayed == "",
            f"expected ellipsis or empty, got {displayed!r}",
        )
        self.assertEqual(bar._breadcrumb.toolTip(), text)


if __name__ == "__main__":
    unittest.main()
