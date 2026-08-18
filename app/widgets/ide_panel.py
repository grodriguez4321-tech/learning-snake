"""Right-hand IDE column: editor, actions, output, feedback."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTabWidget,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSplitter,
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
        self.setMinimumWidth(520)
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
        body_l.setContentsMargins(0, 0, 0, 0)
        body_l.setSpacing(0)

        # Vertical splitter: top (work area), bottom (drawer tabs)
        self._vsplitter = QSplitter(Qt.Orientation.Vertical)
        self._vsplitter.setChildrenCollapsible(False)
        self._vsplitter.setHandleWidth(10)
        body_l.addWidget(self._vsplitter, stretch=1)

        work_host = QWidget()
        work = QVBoxLayout(work_host)
        work.setContentsMargins(12, 10, 12, 12)
        work.setSpacing(10)

        self.editor = CodeEditorWidget(theme)
        self.editor.setMinimumHeight(180)
        self.editor.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.editor.runRequested.connect(self.runClicked.emit)
        work.addWidget(self.editor, stretch=3)

        self._answer_label = QLabel("Your answer")
        self._answer_label.setObjectName("MutedLabel")
        work.addWidget(self._answer_label)

        self._answer = QLineEdit()
        self._answer.setObjectName("AnswerField")
        self._answer.setPlaceholderText("Type predicted output here…")
        self._answer.setFixedHeight(34)
        work.addWidget(self._answer)

        self._choice_host = QWidget()
        self._choice_layout = QVBoxLayout(self._choice_host)
        self._choice_layout.setContentsMargins(0, 0, 0, 0)
        self._choice_layout.setSpacing(6)
        self._choice_group = QButtonGroup(self)
        self._choice_buttons: list[QRadioButton] = []
        work.addWidget(self._choice_host)
        self._choice_host.hide()

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
        work.addLayout(actions)

        # Bottom drawer: tabbed Output / Feedback
        drawer_host = QWidget()
        drawer_l = QVBoxLayout(drawer_host)
        drawer_l.setContentsMargins(12, 6, 12, 12)
        drawer_l.setSpacing(8)
        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.output = OutputPanel(theme)
        self.feedback = FeedbackPanel()
        self._tabs.addTab(self.output, "Output")
        self._tabs.addTab(self.feedback, "Feedback")
        drawer_l.addWidget(self._tabs)

        self._vsplitter.addWidget(work_host)
        self._vsplitter.addWidget(drawer_host)
        # Target sizes: editor area dominant; drawer ~180 px initially
        self._vsplitter.setSizes([520, 180])

        root.addWidget(body, stretch=1)
        self._starter = ""
        self.set_answer_visible(False)

    def apply_theme(self, theme: Theme) -> None:
        self.editor.apply_theme(theme)
        self.output.apply_theme(theme)
        self.feedback.apply_theme(theme)

    def set_busy(self, busy: bool, message: str = "Running…") -> None:
        for btn in (self._run, self._check, self._hint, self._reset):
            btn.setEnabled(not busy)
        # Show Output tab and enlarge drawer during busy to surface status
        self._tabs.setCurrentWidget(self.output)
        self.set_drawer_active() if busy else self.set_drawer_idle()
        self.output.set_busy(busy, message)

    def set_hint_label(self, used: int, total: int) -> None:
        remaining = max(0, total - used)
        self._hint.setText(f"💡  Hint ({remaining})")

    def set_answer_visible(self, visible: bool) -> None:
        self._answer_label.setVisible(visible and not self._choice_buttons)
        self._answer.setVisible(visible and not self._choice_buttons)

    def set_choices(self, choices: list[str]) -> None:
        self._clear_choices()
        if not choices:
            self._choice_host.hide()
            return
        for index, choice in enumerate(choices, start=1):
            label = f"{index}. {choice}"
            button = QRadioButton(label)
            button.setObjectName("ChoiceOption")
            self._choice_group.addButton(button, index)
            self._choice_layout.addWidget(button)
            self._choice_buttons.append(button)
        self._answer_label.setText("Choose an option")
        self._answer_label.setVisible(True)
        self._answer.setVisible(False)
        self._choice_host.show()

    def _clear_choices(self) -> None:
        for button in self._choice_buttons:
            self._choice_group.removeButton(button)
            button.deleteLater()
        self._choice_buttons.clear()
        while self._choice_layout.count():
            item = self._choice_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def clear_choices(self) -> None:
        self._clear_choices()
        self._choice_host.hide()
        self._answer_label.setText("Your answer")

    def get_code(self) -> str:
        return self.editor.get_text()

    def set_code(self, code: str) -> None:
        self.editor.set_text(code)

    def set_starter(self, starter: str) -> None:
        self._starter = starter

    def reset_to_starter(self) -> None:
        self.editor.set_text(self._starter)

    def get_answer(self) -> str:
        if self._choice_buttons:
            checked_id = self._choice_group.checkedId()
            if checked_id >= 1:
                return str(checked_id)
            return ""
        return self._answer.text()

    def set_answer(self, text: str) -> None:
        cleaned = (text or "").strip()
        if self._choice_buttons:
            for index, button in enumerate(self._choice_buttons, start=1):
                choice_text = button.text().split(". ", 1)[-1]
                if cleaned == str(index) or cleaned == choice_text:
                    button.setChecked(True)
                    return
            for button in self._choice_buttons:
                button.setAutoExclusive(False)
                button.setChecked(False)
                button.setAutoExclusive(True)
            return
        self._answer.setText(text)

    def clear_output(self) -> None:
        self.output.clear()

    def set_output(self, text: str, *, kind: str = "plain") -> None:
        self.output.set_text(text, kind=kind)
        self.activate_output()

    def output_text(self) -> str:
        return self.output.plain_text

    def focus_editor(self) -> None:
        self.editor.setFocus()

    # --- drawer / tabs helpers ----------------------------------------------
    def set_drawer_collapsed(self) -> None:
        sizes = self._vsplitter.sizes()
        total = max(1, sum(sizes))
        self._vsplitter.setSizes([total - 40, 40])

    def set_drawer_idle(self) -> None:
        sizes = self._vsplitter.sizes()
        total = max(1, sum(sizes))
        idle = 140
        self._vsplitter.setSizes([max(200, total - idle), idle])

    def set_drawer_active(self) -> None:
        sizes = self._vsplitter.sizes()
        total = max(1, sum(sizes))
        active = 240
        self._vsplitter.setSizes([max(160, total - active), active])

    def activate_output(self) -> None:
        self._tabs.setCurrentWidget(self.output)
        self.set_drawer_active()

    def activate_feedback(self) -> None:
        self._tabs.setCurrentWidget(self.feedback)
        self.set_drawer_active()
