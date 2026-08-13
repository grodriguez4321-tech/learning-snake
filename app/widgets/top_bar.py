"""Top application bar: breadcrumb, progress, theme."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QWidget

from app.widgets.progress_widget import ProgressWidget


class TopBar(QFrame):
    themeChanged = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setFixedHeight(52)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 16, 0)
        layout.setSpacing(16)

        self._breadcrumb = QLabel("Python Fundamentals")
        self._breadcrumb.setObjectName("Breadcrumb")
        layout.addWidget(self._breadcrumb, stretch=1)

        self._progress = ProgressWidget()
        layout.addWidget(self._progress)

        theme_label = QLabel("Theme")
        theme_label.setObjectName("MutedLabel")
        layout.addWidget(theme_label)

        self._theme = QComboBox()
        self._theme.addItem("Dark", "dark")
        self._theme.addItem("Light", "light")
        self._theme.setMinimumWidth(110)
        self._theme.currentIndexChanged.connect(self._on_theme)
        layout.addWidget(self._theme)

    def set_breadcrumb(self, text: str) -> None:
        self._breadcrumb.setText(text)

    def set_progress(self, completed: int, total: int) -> None:
        self._progress.set_progress(completed, total)

    def set_theme(self, theme: str) -> None:
        idx = self._theme.findData(theme)
        if idx >= 0:
            self._theme.blockSignals(True)
            self._theme.setCurrentIndex(idx)
            self._theme.blockSignals(False)

    def _on_theme(self) -> None:
        data = self._theme.currentData()
        if data:
            self.themeChanged.emit(str(data))
