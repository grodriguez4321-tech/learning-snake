"""Feedback panel for learner guidance."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QTextEdit, QVBoxLayout, QWidget


class FeedbackPanel(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("FeedbackCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        header = QLabel("Feedback")
        header.setObjectName("CardTitle")
        layout.addWidget(header)

        self._view = QTextEdit()
        self._view.setObjectName("FeedbackView")
        self._view.setReadOnly(True)
        self._view.setMaximumHeight(90)
        self._view.setPlainText("Run your code and check your solution!")
        layout.addWidget(self._view)

    def set_message(self, text: str) -> None:
        self._view.setPlainText(text)

    def reset(self) -> None:
        self.set_message("Run your code and check your solution!")
