"""Feedback strip for learner guidance and check results."""

from __future__ import annotations

from PySide6.QtGui import QColor, QTextCharFormat
from PySide6.QtWidgets import QFrame, QLabel, QTextEdit, QVBoxLayout, QWidget

from app.theme import Theme


class FeedbackPanel(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PanelSection")
        self._theme: Theme | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)

        title = QLabel("Feedback")
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        self._view = QTextEdit()
        self._view.setObjectName("FeedbackView")
        self._view.setReadOnly(True)
        self._view.setMinimumHeight(48)
        self._view.setMaximumHeight(160)
        layout.addWidget(self._view)

        self.reset()

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme

    def reset(self) -> None:
        self.set_message("Run your code and check your solution!", kind="plain")

    def set_message(self, text: str, *, kind: str = "plain") -> None:
        self._view.clear()
        if not text:
            text = "Run your code and check your solution!"
        self._append(text, kind=kind)

    def append_message(self, text: str, *, kind: str = "plain") -> None:
        self._append(text, kind=kind)

    def _append(self, text: str, *, kind: str = "plain") -> None:
        if self._theme is None:
            self._view.setPlainText(text)
            return
        color_map = {
            "plain": self._theme.text_muted,
            "success": self._theme.success,
            "error": self._theme.error,
            "hint": self._theme.warning,
        }
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color_map.get(kind, self._theme.text_muted)))
        cursor = self._view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        if self._view.toPlainText():
            cursor.insertText("\n")
        cursor.insertText(text, fmt)
        self._view.setTextCursor(cursor)
        self._view.ensureCursorVisible()
