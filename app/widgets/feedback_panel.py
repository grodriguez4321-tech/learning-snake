"""Feedback strip for learner guidance."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class FeedbackPanel(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PanelSection")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)

        title = QLabel("Feedback")
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        self._view = QLabel("Run your code and check your solution!")
        self._view.setObjectName("FeedbackStrip")
        self._view.setWordWrap(True)
        self._view.setMinimumHeight(40)
        layout.addWidget(self._view)

    def set_message(self, text: str) -> None:
        self._view.setText(text)

    def reset(self) -> None:
        self.set_message("Run your code and check your solution!")
