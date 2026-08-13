"""Top application bar: breadcrumb, progress, theme toggle."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from app.widgets.progress_widget import ProgressWidget


class TopBar(QFrame):
    themeChanged = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setFixedHeight(48)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 16, 0)
        layout.setSpacing(12)

        self._breadcrumb = QLabel("Python Fundamentals")
        self._breadcrumb.setObjectName("Breadcrumb")
        layout.addWidget(self._breadcrumb, stretch=1)

        self._progress = ProgressWidget()
        layout.addWidget(self._progress)

        self._theme_btn = QPushButton("Theme · Dark")
        self._theme_btn.setObjectName("GhostButton")
        self._theme_btn.setFixedHeight(30)
        self._theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self._theme_btn)
        self._theme = "dark"

    def set_breadcrumb(self, text: str) -> None:
        self._breadcrumb.setText(text)

    def set_progress(self, completed: int, total: int) -> None:
        self._progress.set_progress(completed, total)

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        label = "Dark" if theme == "dark" else "Light"
        self._theme_btn.setText(f"Theme · {label}")

    def _toggle_theme(self) -> None:
        nxt = "light" if self._theme == "dark" else "dark"
        self.set_theme(nxt)
        self.themeChanged.emit(nxt)
