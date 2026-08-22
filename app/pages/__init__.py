"""Stacked content pages for the main shell."""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.branding import APP_NAME, APP_TAGLINE
from app.theme import Theme
from app.widgets.ide_panel import IdePanel
from app.widgets.lesson_content import LessonContent
from app.widgets.mode_bar import ModeBar
from course.catalog import CourseCatalog
from engine.course_controller import CourseController


class DashboardPage(QWidget):
    continueClicked = Signal()
    playgroundClicked = Signal()

    def __init__(
        self,
        controller: CourseController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        title = QLabel(APP_NAME)
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        tagline = QLabel(APP_TAGLINE)
        tagline.setWordWrap(True)
        tagline.setObjectName("MutedLabel")
        layout.addWidget(tagline)

        self._summary = QLabel()
        self._summary.setWordWrap(True)
        self._summary.setObjectName("BodyText")
        layout.addWidget(self._summary)

        card = QFrame()
        card.setObjectName("Card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(12)
        self._lesson_label = QLabel()
        self._lesson_label.setObjectName("CardTitle")
        cl.addWidget(self._lesson_label)
        self._bar = QProgressBar()
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(8)
        cl.addWidget(self._bar)
        self._pct = QLabel()
        self._pct.setObjectName("MutedLabel")
        cl.addWidget(self._pct)
        row = QHBoxLayout()
        cont = QPushButton("Continue learning")
        cont.setObjectName("PrimaryButton")
        cont.clicked.connect(self.continueClicked.emit)
        play = QPushButton("Open playground")
        play.setObjectName("SecondaryButton")
        play.clicked.connect(self.playgroundClicked.emit)
        row.addWidget(cont)
        row.addWidget(play)
        row.addStretch(1)
        cl.addLayout(row)
        layout.addWidget(card)
        layout.addStretch(1)

    def refresh(self) -> None:
        lesson = self._controller.current_lesson()
        pct = self._controller.overall_progress_percent()
        self._bar.setValue(int(round(pct)))
        self._pct.setText(f"{pct:.0f}% of exercises complete")
        if lesson:
            self._lesson_label.setText(f"Current lesson: {lesson.title}")
            self._summary.setText(
                f"Welcome back to {APP_NAME}. You are in {lesson.section}. "
                "Pick up where you left off or experiment in the playground."
            )
        else:
            self._lesson_label.setText("No lessons loaded")
            self._summary.setText("Add lesson JSON files under course/lessons to begin.")


class PaneSwitch(QFrame):
    paneChanged = Signal(str)  # "prompt" | "code"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setFixedHeight(36)
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 0, 8, 0)
        row.setSpacing(6)
        self._prompt = QPushButton("Prompt")
        self._prompt.setObjectName("ToolButton")
        self._prompt.setCheckable(True)
        self._code = QPushButton("Code")
        self._code.setObjectName("ToolButton")
        self._code.setCheckable(True)
        self._prompt.clicked.connect(lambda: self._emit("prompt"))
        self._code.clicked.connect(lambda: self._emit("code"))
        row.addWidget(self._prompt)
        row.addWidget(self._code)
        row.addStretch(1)
        self.set_pane("prompt")

    def _emit(self, pane: str) -> None:
        self.set_pane(pane)
        self.paneChanged.emit(pane)

    def set_pane(self, pane: str) -> None:
        pane = pane if pane in {"prompt", "code"} else "prompt"
        for key, btn in (("prompt", self._prompt), ("code", self._code)):
            btn.blockSignals(True)
            btn.setChecked(key == pane)
            btn.blockSignals(False)

    def set_code_allowed(self, allowed: bool) -> None:
        """Enable/disable the Code button when single-pane is in a non-Practice mode."""
        self._code.setEnabled(allowed)
        if not allowed:
            # Ensure Prompt remains selected when Code is not allowed
            self.set_pane("prompt")


class LessonsPage(QWidget):
    editorToggleAllowed = Signal(bool)

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 12, 12)
        outer.setSpacing(0)

        self.mode_bar = ModeBar()
        outer.addWidget(self.mode_bar)

        # Single-pane switch (visible under narrow width)
        self.pane_bar = PaneSwitch()
        self.pane_bar.hide()
        outer.addWidget(self.pane_bar)

        host = QHBoxLayout()
        host.setContentsMargins(0, 0, 0, 0)
        host.setSpacing(0)
        outer.addLayout(host, stretch=1)

        self.splitter = QSplitter()
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(12)
        self.content = LessonContent(theme)
        self.ide = IdePanel(theme)
        self.splitter.addWidget(self.content)
        self.splitter.addWidget(self.ide)
        self.splitter.setStretchFactor(0, 5)
        self.splitter.setStretchFactor(1, 5)
        self.splitter.setSizes([620, 580])
        host.addWidget(self.splitter)

        self._theme = theme
        self._editor_pref_visible = True
        self._mode: str = "learn"
        self._per_lesson_state: dict[str, tuple[str, int]] = {}
        self.mode_bar.modeChanged.connect(self._on_mode_changed)
        self.pane_bar.paneChanged.connect(self._on_pane_changed)
        self._single_pane: bool = False
        self._active_pane: str = "prompt"
        self.pane_bar.set_pane("prompt")

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.content.apply_theme(theme)
        self.ide.apply_theme(theme)

    def set_editor_visible(self, visible: bool) -> None:
        self._editor_pref_visible = visible
        self._apply_editor_visibility()

    def _apply_editor_visibility(self) -> None:
        # Single-pane policy overrides editor visibility
        if self._single_pane:
            allow_code = self._mode == "practice"
            # In Learn/Examples, always show Prompt; Code is unavailable.
            self.pane_bar.set_code_allowed(allow_code)
            if not allow_code:
                self._active_pane = "prompt"
            show_code = allow_code and self._active_pane == "code"
            self.content.setVisible(not show_code)
            self.ide.setVisible(show_code)
            # Editor toggle is a no-op while single-pane policy is active
            self.editorToggleAllowed.emit(False)
            return
        # Both panes visible; only Practice shows IDE; disable toggle otherwise
        self.content.setVisible(True)
        allow_toggle = self._mode == "practice"
        self.ide.setVisible(self._editor_pref_visible and allow_toggle)
        self.editorToggleAllowed.emit(allow_toggle)

    # Session-only lesson state ------------------------------------------------
    def present_lesson(
        self,
        *,
        lesson,
        exercise,
        exercise_index: int,
        prev_ok: bool,
        next_ok: bool,
    ) -> None:
        # Restore per-lesson state where available
        mode, saved_index = self._per_lesson_state.get(lesson.id, ("learn", exercise_index))
        ex_index = saved_index if saved_index is not None else exercise_index
        self.content.show_lesson(
            lesson,
            exercise,
            exercise_index=ex_index,
            prev_ok=prev_ok,
            next_ok=next_ok,
        )
        # Restore per-lesson mode (default Learn)
        self.set_mode(mode, lesson_id=lesson.id, exercise_index=ex_index)

    def set_mode(self, mode: str, *, lesson_id: str | None = None, exercise_index: int | None = None) -> None:
        self._mode = mode
        self.mode_bar.set_mode(mode)
        self.content.set_mode(mode)
        self._apply_editor_visibility()
        if lesson_id is not None:
            current = self._per_lesson_state.get(lesson_id, (mode, exercise_index or 0))
            ex_index = current[1] if exercise_index is None else exercise_index
            self._per_lesson_state[lesson_id] = (mode, ex_index or 0)

    def _on_mode_changed(self, mode: str) -> None:
        # Update UI and remember for the current lesson if present
        lesson = getattr(self.content, "lesson", None)
        lid = getattr(lesson, "id", None)
        self.set_mode(mode, lesson_id=lid)

    def remember_exercise_index(self, lesson_id: str, index: int) -> None:
        mode, _ = self._per_lesson_state.get(lesson_id, (self._mode, index))
        self._per_lesson_state[lesson_id] = (mode, index)

    def get_saved_exercise_index(self, lesson_id: str, default: int = 0) -> int:
        return self._per_lesson_state.get(lesson_id, (self._mode, default))[1]

    # --- responsive policy ---------------------------------------------------
    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._apply_layout_policy()

    def _apply_layout_policy(self) -> None:
        # Enter single-pane mode when width is narrow enough that both panes would crush usability.
        threshold = 900
        wants_single = self.width() < threshold
        if wants_single != self._single_pane:
            self._single_pane = wants_single
            self.pane_bar.setVisible(self._single_pane)
        self._apply_editor_visibility()

    def _on_pane_changed(self, pane: str) -> None:
        # Do not allow switching to Code outside Practice in single-pane mode
        if self._single_pane and self._mode != "practice" and pane == "code":
            self.pane_bar.set_pane("prompt")
            self._active_pane = "prompt"
            self._apply_editor_visibility()
            return
        self._active_pane = pane if pane in {"prompt", "code"} else "prompt"
        self._apply_editor_visibility()


class PlaygroundPage(QWidget):
    runRequested = Signal(str)
    resetEnvRequested = Signal()

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from app.widgets.code_editor import CodeEditorWidget
        from app.widgets.output_panel import OutputPanel

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 24, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Playground")
        title.setObjectName("PageTitle")
        header.addWidget(title)
        header.addStretch(1)
        tip = QLabel("Variables persist until you reset the environment")
        tip.setObjectName("MutedLabel")
        header.addWidget(tip)
        layout.addLayout(header)

        card = QFrame()
        card.setObjectName("EditorCard")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        chrome = QFrame()
        chrome.setObjectName("EditorChrome")
        chrome.setFixedHeight(36)
        ch = QHBoxLayout(chrome)
        ch.setContentsMargins(14, 0, 12, 0)
        tab = QLabel("🐍  playground.py")
        tab.setObjectName("TabLabel")
        ch.addWidget(tab)
        cl.addWidget(chrome)

        inner_host = QWidget()
        inner = QVBoxLayout(inner_host)
        inner.setContentsMargins(12, 10, 12, 12)
        inner.setSpacing(10)
        self.editor = CodeEditorWidget(theme)
        self.editor.set_text("x = 2 + 2\nprint(x)\n")
        self.editor.runRequested.connect(self._emit_run)
        inner.addWidget(self.editor, stretch=1)

        actions = QHBoxLayout()
        run = QPushButton("▶  Run")
        run.setObjectName("PrimaryButton")
        run.setFixedHeight(34)
        run.clicked.connect(self._emit_run)
        clear = QPushButton("Clear Output")
        clear.setObjectName("GhostButton")
        clear.setFixedHeight(34)
        clear.clicked.connect(lambda: self.output.clear())
        reset = QPushButton("Reset Environment")
        reset.setObjectName("GhostButton")
        reset.setFixedHeight(34)
        reset.clicked.connect(self.resetEnvRequested.emit)
        actions.addWidget(run)
        actions.addWidget(clear)
        actions.addWidget(reset)
        actions.addStretch(1)
        inner.addLayout(actions)

        self.output = OutputPanel(theme)
        inner.addWidget(self.output)
        cl.addWidget(inner_host, stretch=1)
        layout.addWidget(card, stretch=1)
        self._theme = theme

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.editor.apply_theme(theme)
        self.output.apply_theme(theme)

    def _emit_run(self) -> None:
        self.runRequested.emit(self.editor.get_text())

    def set_busy(self, busy: bool) -> None:
        self.output.set_busy(busy, "Running playground…")


class ProgressPage(QWidget):
    def __init__(
        self,
        controller: CourseController,
        catalog: CourseCatalog,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._catalog = catalog
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        title = QLabel("Progress")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        self._overall = QLabel()
        self._overall.setObjectName("BodyText")
        layout.addWidget(self._overall)

        self._bar = QProgressBar()
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(10)
        layout.addWidget(self._bar)

        from PySide6.QtCore import Qt

        self._list = QLabel()
        self._list.setWordWrap(True)
        self._list.setObjectName("MutedLabel")
        self._list.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self._list)
        layout.addStretch(1)

    def refresh(self) -> None:
        pct = self._controller.overall_progress_percent()
        self._bar.setValue(int(round(pct)))
        self._overall.setText(f"Overall completion: {pct:.0f}%")
        rows = []
        for lesson in self._catalog.lessons:
            done = self._controller.progress.is_lesson_complete(
                lesson.id, lesson.exercise_ids
            )
            unlocked = self._controller.is_unlocked(lesson)
            if done:
                mark = "✓"
            elif unlocked:
                mark = "○"
            else:
                mark = "🔒"
            rows.append(f"<li>{mark} {lesson.title}</li>")
        self._list.setText("<ul>" + "".join(rows) + "</ul>")


class SettingsPage(QWidget):
    resetProgressClicked = Signal()
    saveClicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from PySide6.QtCore import Qt

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        title = QLabel("Settings")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        body = QLabel(
            f"{APP_NAME} saves theme and panel visibility from the top toolbar. "
            "Progress and drafts are saved automatically when you leave an exercise "
            "or close the app — use Save for an explicit checkpoint."
        )
        body.setWordWrap(True)
        body.setObjectName("BodyText")
        layout.addWidget(body)

        shortcuts = QLabel(
            "<b>Keyboard shortcuts</b><br>"
            "Ctrl+B — toggle sidebar<br>"
            "Ctrl+J — toggle editor column<br>"
            "Ctrl+Shift+D — toggle dark/light theme<br>"
            "Ctrl+Enter — run code<br>"
            "Ctrl+S — save progress<br>"
            "Ctrl+Q — quit"
        )
        shortcuts.setObjectName("MutedLabel")
        shortcuts.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(shortcuts)

        row = QHBoxLayout()
        save = QPushButton("Save progress now")
        save.setObjectName("PrimaryButton")
        save.clicked.connect(self.saveClicked.emit)
        reset = QPushButton("Reset all progress…")
        reset.setObjectName("SecondaryButton")
        reset.clicked.connect(self.resetProgressClicked.emit)
        row.addWidget(save)
        row.addWidget(reset)
        row.addStretch(1)
        layout.addLayout(row)
        layout.addStretch(1)
