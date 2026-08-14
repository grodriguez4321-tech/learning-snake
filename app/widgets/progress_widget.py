"""Circular-ish progress pill for the top bar."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget


class ProgressWidget(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ProgressPill")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 14, 6)
        layout.setSpacing(10)

        self._pct = QLabel("0%")
        self._pct.setObjectName("ProgressPct")
        layout.addWidget(self._pct)

        self._label = QLabel("0 / 0 lessons")
        self._label.setObjectName("MutedLabel")
        layout.addWidget(self._label)

    def set_progress(self, completed: int, total: int) -> None:
        pct = int(round(100 * completed / total)) if total else 0
        self._pct.setText(f"{pct}%")
        self._label.setText(f"{completed} / {total} lessons")
