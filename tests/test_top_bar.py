"""Top bar breadcrumb eliding (offscreen Qt)."""

from __future__ import annotations

import os
import sys
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSize
from PySide6.QtGui import QFontMetrics, QResizeEvent
from PySide6.QtWidgets import QApplication

from app.theme import DARK, build_stylesheet
from app.widgets.top_bar import TopBar


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


class TopBarBreadcrumbElideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def _shown_bar(
        self,
        text: str,
        *,
        width: int = 720,
        breadcrumb_width: int | None = None,
    ) -> TopBar:
        bar = TopBar()
        bar.setFixedWidth(width)
        bar.show()
        self.app.processEvents()
        if breadcrumb_width is not None:
            bar._breadcrumb.setFixedWidth(breadcrumb_width)
        bar.set_breadcrumb(text)
        bar.resizeEvent(QResizeEvent(QSize(width, 48), QSize(width, 48)))
        self.app.processEvents()
        return bar

    def test_long_breadcrumb_elides_with_tooltip(self) -> None:
        text = "📖  Python Fundamentals  ›  Defining Functions and return"
        bar = self._shown_bar(text, width=720, breadcrumb_width=160)
        displayed = bar._breadcrumb.text()
        self.assertTrue(_is_elided(displayed, text), f"expected elision, got {displayed!r}")
        self.assertEqual(bar._breadcrumb.toolTip(), text)
        metrics = QFontMetrics(bar._breadcrumb.font())
        self.assertLessEqual(metrics.horizontalAdvance(displayed), bar._breadcrumb.width())

    def test_short_breadcrumb_is_not_elided(self) -> None:
        text = "Dashboard"
        bar = self._shown_bar(text, width=900, breadcrumb_width=240)
        self.assertEqual(bar._breadcrumb.text(), text)
        self.assertEqual(bar._breadcrumb.toolTip(), text)

    def test_elide_updates_on_resize(self) -> None:
        text = "📖  Python Fundamentals  ›  Defining Functions and return"
        bar = self._shown_bar(text, width=900, breadcrumb_width=600)
        self.assertFalse(_is_elided(bar._breadcrumb.text(), text), bar._breadcrumb.text())
        self.assertEqual(bar._breadcrumb.text(), text)
        bar._breadcrumb.setFixedWidth(140)
        bar.resizeEvent(QResizeEvent(QSize(720, 48), QSize(720, 48)))
        self.app.processEvents()
        self.assertTrue(_is_elided(bar._breadcrumb.text(), text))

    def test_very_narrow_bar_still_elides(self) -> None:
        text = "📖  Python Fundamentals  ›  Defining Functions and return"
        bar = self._shown_bar(text, width=480, breadcrumb_width=60)
        displayed = bar._breadcrumb.text()
        self.assertTrue(
            _is_elided(displayed, text) or displayed == "",
            f"expected elision or empty, got {displayed!r}",
        )
        self.assertEqual(bar._breadcrumb.toolTip(), text)


if __name__ == "__main__":
    unittest.main()
