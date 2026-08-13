"""Right-hand IDE column: editor, actions, output, feedback."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.theme import Theme
from app.widgets.code_editor import CodeEditorWidget
from app.widgets.feedback_panel import FeedbackPanel
from app.widgets.output_panel import OutputPanel


class IdePanel(QFrame):
    runClicked = Signal()
    checkClicked = Signal()
    hintClicked = Signal()
    resetClicked = Signal()

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("EditorCard")
        self.setMinimumWidth(380)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        chrome = QFrame()
        chrome.setObjectName("EditorChrome")
        chrome.setFixedHeight(36)
        chrome_l = QHBoxLayout(chrome)
        chrome_l.setContentsMargins(14, 0, 12, 0)
        tab = QLabel("🐍  main.py")
        tab.setObjectName("TabLabel")
        chrome_l.addWidget(tab)
        chrome_l.addStretch(1)
        root.addWidget(chrome)

        body = QWidget()
        body_l = QVBoxLayout(body)
        body_l.setContentsMargins(12, 10, 12, 12)
        body_l.setSpacing(10)

        self.editor = CodeEditorWidget(theme)
        self.editor.setMinimumHeight(180)
        self.editor.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.editor.runRequested.connect(self.runClicked.emit)
        body_l.addWidget(self.editor, stretch=1)

        self._answer_label = QLabel("Your answer")
        self._answer_label.setObjectName("MutedLabel")
        body_l.addWidget(self._answer_label)
        self._answer = QLineEdit()
        self._answer.setObjectName("AnswerField")
        self._answer.setPlaceholderText("Type predicted output or choice here…")
        self._answer.setFixedHeight(34)
        body_l.addWidget(self._answer)
        self.set_answer_visible(False)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.setContentsMargins(0, 2, 0, 2)
        self._run = QPushButton("▶  Run Code")
        self._run.setObjectName("PrimaryButton")
        self._run.setFixedHeight(34)
        self._run.clicked.connect(self.runClicked.emit)
        self._check = QPushButton("✓  Check")
        self._check.setObjectName("GhostButton")
        self._check.setFixedHeight(34)
        self._check.clicked.connect(self.checkClicked.emit)
        self._hint = QPushButton("💡  Hint")
        self._hint.setObjectName("GhostButton")
        self._hint.setFixedHeight(34)
        self._hint.clicked.connect(self.hintClicked.emit)
        self._reset = QPushButton("↺  Reset")
        self._reset.setObjectName("GhostButton")
        self._reset.setFixedHeight(34)
        self._reset.clicked.connect(self.resetClicked.emit)
        for btn in (self._run, self._check, self._hint, self._reset):
            actions.addWidget(btn)
        actions.addStretch(1)
        body_l.addLayout(actions)

        self.output = OutputPanel(theme)
        body_l.addWidget(self.output)

        self.feedback = FeedbackPanel()
        body_l.addWidget(self.feedback)

        root.addWidget(body, stretch=1)
        self._starter = ""

    def apply_theme(self, theme: Theme) -> None:
        self.editor.apply_theme(theme)
        self.output.apply_theme(theme)

    def set_busy(self, busy: bool, message: str = "Running…") -> None:
        for btn in (self._run, self._check, self._hint, self._reset):
            btn.setEnabled(not busy)
        self.output.set_busy(busy, message)

    def set_hint_label(self, used: int, total: int) -> None:
        remaining = max(0, total - used)
        self._hint.setText(f"💡  Hint ({remaining})")

    def set_answer_visible(self, visible: bool) -> None:
        self._answer_label.setVisible(visible)
        self._answer.setVisible(visible)

    def get_code(self) -> str:
        return self.editor.get_text()

    def set_code(self, code: str) -> None:
        self.editor.set_text(code)

    def set_starter(self, starter: str) -> None:
        self._starter = starter

    def reset_to_starter(self) -> None:
        self.editor.set_text(self._starter)

    def get_answer(self) -> str:
        return self._answer.text()

    def set_answer(self, text: str) -> None:
        self._answer.setText(text)

    def clear_output(self) -> None:
        self.output.clear()

    def set_output(self, text: str, *, kind: str = "plain") -> None:
        self.output.set_text(text, kind=kind)

    def append_output(self, text: str, *, kind: str = "plain") -> None:
        self.output.append_text(text, kind=kind)

    def focus_editor(self) -> None:
        self.editor.setFocus()
