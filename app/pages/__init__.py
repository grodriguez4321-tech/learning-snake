"""Stacked content pages for the main shell."""

from __future__ import annotations

from PySide6.QtCore import Signal
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

from app.theme import Theme
from app.widgets.ide_panel import IdePanel
from app.widgets.lesson_content import LessonContent
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

        title = QLabel("Dashboard")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

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
                f"Welcome back. You are in {lesson.section}. "
                "Pick up where you left off or experiment in the playground."
            )
        else:
            self._lesson_label.setText("No lessons loaded")
            self._summary.setText("Add lesson JSON files under course/lessons to begin.")


class LessonsPage(QWidget):
    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.splitter = QSplitter()
        self.splitter.setChildrenCollapsible(False)
        self.content = LessonContent()
        self.ide = IdePanel(theme)
        self.splitter.addWidget(self.content)
        self.splitter.addWidget(self.ide)
        self.splitter.setStretchFactor(0, 5)
        self.splitter.setStretchFactor(1, 5)
        self.splitter.setSizes([640, 560])
        layout.addWidget(self.splitter)

    def apply_theme(self, theme: Theme) -> None:
        self.ide.apply_theme(theme)

    def set_editor_visible(self, visible: bool) -> None:
        self.ide.setVisible(visible)


class PlaygroundPage(QWidget):
    runRequested = Signal(str)
    resetEnvRequested = Signal()

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from app.widgets.code_editor import CodeEditorWidget
        from app.widgets.output_panel import OutputPanel

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

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
        ch = QHBoxLayout(chrome)
        ch.setContentsMargins(12, 8, 12, 8)
        ch.addWidget(QLabel("🐍  playground.py"))
        cl.addWidget(chrome)

        inner = QVBoxLayout()
        inner.setContentsMargins(12, 12, 12, 12)
        inner.setSpacing(12)
        self.editor = CodeEditorWidget(theme)
        self.editor.set_text("x = 2 + 2\nprint(x)\n")
        self.editor.runRequested.connect(self._emit_run)
        inner.addWidget(self.editor, stretch=3)

        actions = QHBoxLayout()
        run = QPushButton("▶  Run")
        run.setObjectName("PrimaryButton")
        run.clicked.connect(self._emit_run)
        clear = QPushButton("Clear Output")
        clear.setObjectName("SecondaryButton")
        clear.clicked.connect(lambda: self.output.clear())
        reset = QPushButton("Reset Environment")
        reset.setObjectName("SecondaryButton")
        reset.clicked.connect(self.resetEnvRequested.emit)
        actions.addWidget(run)
        actions.addWidget(clear)
        actions.addWidget(reset)
        actions.addStretch(1)
        inner.addLayout(actions)

        self.output = OutputPanel(theme)
        inner.addWidget(self.output)
        cl.addLayout(inner)
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        title = QLabel("Settings")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        body = QLabel(
            "Theme can be changed from the top bar. "
            "Progress and drafts are saved automatically when you leave an exercise "
            "or close the app."
        )
        body.setWordWrap(True)
        body.setObjectName("BodyText")
        layout.addWidget(body)

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
