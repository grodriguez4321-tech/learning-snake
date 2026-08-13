"""Output strip for run/check results."""

from __future__ import annotations

from PySide6.QtGui import QColor, QTextCharFormat
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QTextEdit, QVBoxLayout, QWidget

from app.theme import Theme


class OutputPanel(QFrame):
    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PanelSection")
        self._theme = theme

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(10)
        title = QLabel("Output")
        title.setObjectName("CardTitle")
        header.addWidget(title)
        self._status = QLabel("Ready to run your code…")
        self._status.setObjectName("MutedLabel")
        header.addWidget(self._status, stretch=1)
        layout.addLayout(header)

        self._view = QTextEdit()
        self._view.setObjectName("OutputView")
        self._view.setReadOnly(True)
        self._view.setFixedHeight(96)
        layout.addWidget(self._view)

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme

    def set_busy(self, busy: bool, message: str = "Running…") -> None:
        self._status.setText(message if busy else "Ready to run your code…")

    def clear(self) -> None:
        self._view.clear()
        self._status.setText("Ready to run your code…")

    def set_text(self, text: str, *, kind: str = "plain") -> None:
        self._view.clear()
        self.append_text(text, kind=kind)

    def append_text(self, text: str, *, kind: str = "plain") -> None:
        color_map = {
            "plain": self._theme.text,
            "success": self._theme.success,
            "error": self._theme.error,
            "hint": self._theme.warning,
        }
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color_map.get(kind, self._theme.text)))
        cursor = self._view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        if self._view.toPlainText():
            cursor.insertText("\n")
        cursor.insertText(text, fmt)
        self._view.setTextCursor(cursor)
        self._view.ensureCursorVisible()
        labels = {
            "success": "Passed",
            "error": "Error",
            "hint": "Hint",
            "plain": "Output",
        }
        self._status.setText(labels.get(kind, "Output"))
