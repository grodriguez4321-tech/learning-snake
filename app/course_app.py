"""Main PySide6 application — IDE-style course shell.

Presentation only: grading, unlocking, and execution stay in engine/.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Optional, TypeVar

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.branding import WINDOW_TITLE
from app.pages import (
    DashboardPage,
    LessonsPage,
    PlaygroundPage,
    ProgressPage,
    SettingsPage,
)
from app.theme import Theme, ThemeName, build_stylesheet, get_theme
from app.ui_prefs import UiPrefsStore
from app.widgets.sidebar import Sidebar
from app.widgets.top_bar import TopBar
from app.workers import AsyncJobHost
from course.exercise import Exercise
from course.lesson import Lesson
from engine.code_runner import CodeRunner
from engine.course_controller import CourseController
from engine.exercise_checker import CheckResult


T = TypeVar("T")


class CourseApp(QMainWindow):
    """Primary window. Also exposes a small API used by smoke_gui."""

    def __init__(
        self,
        controller: CourseController,
        runner: CodeRunner,
        prefs_store: Optional[UiPrefsStore] = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.controller = controller
        self.runner = runner
        self.prefs_store = prefs_store or UiPrefsStore(
            Path(__file__).resolve().parents[1] / "data" / "ui_prefs.json"
        )
        self.prefs_store.load()

        self._theme = get_theme(self.prefs_store.prefs.theme)
        self._current_lesson: Optional[Lesson] = None
        self._current_exercise: Optional[Exercise] = None
        self._exercise_index = 0
        self._loading_exercise = False
        self._busy = False
        self._closing = False
        self._sidebar_visible = self.prefs_store.prefs.sidebar_visible
        self._editor_visible = self.prefs_store.prefs.editor_visible
        self._jobs = AsyncJobHost(self)

        self.setWindowTitle(WINDOW_TITLE)
        self.resize(1400, 900)
        self.setMinimumSize(1100, 700)

        self._build_ui()
        self._bind_shortcuts()
        self.apply_theme(self._theme)
        self._sync_panel_visibility()
        self._load_initial_lesson()
        self._maybe_warn_progress_recovery()

    # Compatibility aliases for smoke tests / older call sites
    @property
    def lesson_view(self) -> LessonsPage:
        return self.lessons_page

    @property
    def editor(self):
        return self.lessons_page.ide

    @property
    def playground(self):
        return self.playground_page

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = Sidebar(self.controller.catalog, self.controller)
        self.sidebar.navChanged.connect(self._on_nav)
        self.sidebar.lessonSelected.connect(self._on_sidebar_select)
        root.addWidget(self.sidebar)

        right = QWidget()
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.setSpacing(0)

        self.top_bar = TopBar()
        self.top_bar.themeChanged.connect(self._on_theme_changed)
        self.top_bar.toggleSidebarClicked.connect(self.toggle_sidebar)
        self.top_bar.toggleEditorClicked.connect(self.toggle_editor)
        self.top_bar.saveClicked.connect(self._save_progress)
        self.top_bar.resetProgressClicked.connect(self._reset_progress)
        self.top_bar.set_theme(self._theme.name)
        right_l.addWidget(self.top_bar)

        self.stack = QStackedWidget()
        self.dashboard_page = DashboardPage(self.controller)
        self.dashboard_page.continueClicked.connect(lambda: self._on_nav("lessons"))
        self.dashboard_page.playgroundClicked.connect(lambda: self._on_nav("playground"))

        self.lessons_page = LessonsPage(self._theme)
        # smoke: lesson_view.lesson
        self.lessons_page.lesson = None  # type: ignore[attr-defined]
        content = self.lessons_page.content
        content.prevLesson.connect(self._prev_lesson)
        content.nextLesson.connect(self._next_lesson)
        content.prevExercise.connect(self._prev_exercise)
        content.nextExercise.connect(self._next_exercise)
        ide = self.lessons_page.ide
        ide.runClicked.connect(self._run_code)
        ide.checkClicked.connect(self._check_answer)
        ide.hintClicked.connect(self._show_hint)
        ide.resetClicked.connect(self._reset_exercise)

        self.playground_page = PlaygroundPage(self._theme)
        self.playground_page.runRequested.connect(self._run_playground)
        self.playground_page.resetEnvRequested.connect(self._reset_playground_env)

        self.progress_page = ProgressPage(self.controller, self.controller.catalog)
        self.settings_page = SettingsPage()
        self.settings_page.resetProgressClicked.connect(self._reset_progress)
        self.settings_page.saveClicked.connect(self._save_progress)

        self._page_keys = {
            "dashboard": 0,
            "lessons": 1,
            "playground": 2,
            "progress": 3,
            "settings": 4,
        }
        for page in (
            self.dashboard_page,
            self.lessons_page,
            self.playground_page,
            self.progress_page,
            self.settings_page,
        ):
            self.stack.addWidget(page)

        right_l.addWidget(self.stack, stretch=1)
        root.addWidget(right, stretch=1)

    def _bind_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+B"), self, self.toggle_sidebar)
        QShortcut(QKeySequence("Ctrl+J"), self, self.toggle_editor)
        QShortcut(QKeySequence("Ctrl+Shift+D"), self, self.toggle_theme)
        QShortcut(QKeySequence("Ctrl+S"), self, self._save_progress)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)

    # --- theme / panels -----------------------------------------------------

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(build_stylesheet(theme))
        self.lessons_page.apply_theme(theme)
        self.playground_page.apply_theme(theme)
        self.top_bar.set_theme(theme.name)

    def toggle_theme(self) -> None:
        next_name: ThemeName = "light" if self._theme.name == "dark" else "dark"
        self.apply_theme(get_theme(next_name))
        self.prefs_store.update(theme=next_name)

    def _on_theme_changed(self, name: str) -> None:
        if name not in {"dark", "light"}:
            return
        self.apply_theme(get_theme(name))  # type: ignore[arg-type]
        self.prefs_store.update(theme=name)  # type: ignore[arg-type]

    def toggle_sidebar(self) -> None:
        if self._sidebar_visible:
            self.hide_sidebar()
        else:
            self.show_sidebar()

    def show_sidebar(self) -> None:
        self._sidebar_visible = True
        self.sidebar.setVisible(True)
        self.top_bar.set_sidebar_visible(True)
        self.prefs_store.update(sidebar_visible=True)

    def hide_sidebar(self) -> None:
        self._sidebar_visible = False
        self.sidebar.setVisible(False)
        self.top_bar.set_sidebar_visible(False)
        self.prefs_store.update(sidebar_visible=False)

    def toggle_editor(self) -> None:
        if self._editor_visible:
            self.hide_editor()
        else:
            self.show_editor()

    def show_editor(self) -> None:
        self._editor_visible = True
        self.lessons_page.set_editor_visible(True)
        self.top_bar.set_editor_visible(True)
        self.prefs_store.update(editor_visible=True)
        self.lessons_page.ide.focus_editor()

    def hide_editor(self) -> None:
        self._editor_visible = False
        self.lessons_page.set_editor_visible(False)
        self.top_bar.set_editor_visible(False)
        self.prefs_store.update(editor_visible=False)

    def _sync_panel_visibility(self) -> None:
        if self.prefs_store.prefs.sidebar_visible:
            self.show_sidebar()
        else:
            self.hide_sidebar()
        if self.prefs_store.prefs.editor_visible:
            self.show_editor()
        else:
            self.hide_editor()

    # --- navigation ---------------------------------------------------------

    def _on_nav(self, key: str) -> None:
        idx = self._page_keys.get(key)
        if idx is None:
            return
        self.sidebar.set_active_nav(key)
        self.stack.setCurrentIndex(idx)
        if key == "dashboard":
            self.dashboard_page.refresh()
            self.top_bar.set_breadcrumb("Dashboard")
        elif key == "lessons":
            lesson = self._current_lesson or self.controller.current_lesson()
            if lesson:
                self.top_bar.set_breadcrumb(f"📖  {lesson.section}  ›  {lesson.title}")
        elif key == "playground":
            self.top_bar.set_breadcrumb("Playground")
        elif key == "progress":
            self.progress_page.refresh()
            self.top_bar.set_breadcrumb("Progress")
        elif key == "settings":
            self.top_bar.set_breadcrumb("Settings")
        self._refresh_progress_pill()

    def _refresh_progress_pill(self) -> None:
        lessons = self.controller.catalog.lessons
        completed = sum(
            1
            for lesson in lessons
            if self.controller.progress.is_lesson_complete(lesson.id, lesson.exercise_ids)
        )
        self.top_bar.set_progress(completed, len(lessons))

    def _load_initial_lesson(self) -> None:
        lesson = self.controller.current_lesson()
        if lesson is None:
            self.top_bar.set_breadcrumb("No lessons found")
            return
        self._show_lesson(lesson)
        self._on_nav("lessons")

    def _show_lesson(self, lesson: Lesson, exercise_index: int = 0) -> None:
        self._persist_current_draft()
        self._current_lesson = lesson
        self.lessons_page.lesson = lesson  # smoke compat
        self.controller.progress.data.current_lesson_id = lesson.id
        self.controller.progress.save()
        self._exercise_index = max(0, min(exercise_index, max(0, len(lesson.exercises) - 1)))
        exercise = lesson.exercises[self._exercise_index] if lesson.exercises else None

        prev_ok = self.controller.catalog.previous(lesson.id) is not None
        next_lesson = self.controller.catalog.next(lesson.id)
        next_ok = next_lesson is not None and self.controller.is_unlocked(next_lesson)

        self.lessons_page.content.show_lesson(
            lesson,
            exercise,
            exercise_index=self._exercise_index,
            prev_ok=prev_ok,
            next_ok=next_ok,
        )
        self.sidebar.refresh_lessons(selected_lesson_id=lesson.id)
        self.top_bar.set_breadcrumb(f"📖  {lesson.section}  ›  {lesson.title}")
        self._refresh_progress_pill()
        if exercise is not None:
            self._on_exercise_changed(exercise)
        if self._editor_visible:
            self.lessons_page.ide.focus_editor()

    def _on_sidebar_select(self, lesson_id: str) -> None:
        if self._busy:
            return
        if self._current_lesson is not None and self._current_lesson.id == lesson_id:
            self._on_nav("lessons")
            return
        lesson = self.controller.set_current_lesson(lesson_id)
        if lesson:
            self._show_lesson(lesson)
            self._on_nav("lessons")

    def _prev_lesson(self) -> None:
        if self._busy:
            return
        lesson = self.controller.go_previous()
        if lesson:
            self._show_lesson(lesson)

    def _next_lesson(self) -> None:
        if self._busy:
            return
        current = self._current_lesson
        if current is None:
            return
        nxt = self.controller.catalog.next(current.id)
        if nxt and not self.controller.is_unlocked(nxt):
            QMessageBox.information(
                self,
                "Lesson locked",
                "Complete all exercises in the current lesson to unlock the next one.",
            )
            return
        lesson = self.controller.go_next()
        if lesson:
            self._show_lesson(lesson)

    def _prev_exercise(self) -> None:
        if self._busy or self._current_lesson is None or self._exercise_index <= 0:
            return
        self._show_lesson(self._current_lesson, self._exercise_index - 1)

    def _next_exercise(self) -> None:
        if self._busy or self._current_lesson is None:
            return
        if self._exercise_index >= len(self._current_lesson.exercises) - 1:
            return
        self._show_lesson(self._current_lesson, self._exercise_index + 1)

    def _on_exercise_changed(self, exercise: Exercise) -> None:
        self._persist_current_draft()
        self._loading_exercise = True
        self._current_exercise = exercise
        record = self.controller.progress.exercise(exercise.id)
        code = record.draft_code if record.draft_code else exercise.starter_code
        ide = self.lessons_page.ide
        ide.set_starter(exercise.starter_code)
        ide.set_code(code)
        if exercise.is_choice_exercise:
            ide.clear_choices()
            ide.set_choices(list(exercise.choices))
        else:
            ide.clear_choices()
            ide.set_answer_visible(exercise.uses_free_text_answer)
        ide.set_answer(record.last_answer)
        used = record.hints_used
        ide.set_hint_label(used, len(exercise.hints))
        if record.completed:
            ide.clear_output()
            ide.feedback.set_message(
                "Nice work — this exercise is complete.",
                kind="success",
            )
        else:
            ide.clear_output()
            ide.feedback.reset()
        self._loading_exercise = False

    def _persist_current_draft(self) -> None:
        if self._loading_exercise or self._current_exercise is None:
            return
        ide = self.lessons_page.ide
        self.controller.progress.save_draft(
            self._current_exercise.id,
            ide.get_code(),
            ide.get_answer(),
        )
        self.controller.progress.save()

    def _allowed_modules(self) -> list[str]:
        if self._current_exercise is None:
            return []
        return list(self._current_exercise.allowed_modules)

    # --- async run / check --------------------------------------------------

    def _run_background(
        self,
        work: Callable[[], T],
        on_success: Callable[[T], None],
        *,
        busy_message: str = "Running…",
    ) -> None:
        if self._busy or self._closing:
            return
        if not self._editor_visible:
            self.show_editor()
        self._busy = True
        self.lessons_page.ide.set_busy(True, message=busy_message)

        def done(result: object) -> None:
            self._busy = False
            if self._closing:
                return
            self.lessons_page.ide.set_busy(False)
            if isinstance(result, BaseException):
                self.lessons_page.ide.set_output(
                    f"{type(result).__name__}: {result}", kind="error"
                )
                return
            on_success(result)  # type: ignore[arg-type]

        self._jobs.run(work, done)

    def _run_code(self) -> None:
        if not self._editor_visible:
            self.show_editor()
        code = self.lessons_page.ide.get_code()
        modules = self._allowed_modules()

        def work():
            return self.runner.run(code, allowed_modules=modules)

        def done(result) -> None:
            if result.timed_out:
                self.lessons_page.ide.set_output(result.learner_message, kind="error")
                self.lessons_page.ide.feedback.set_message(
                    "Your program timed out. Check for infinite loops."
                )
            elif result.success:
                text = result.stdout if result.stdout else "(ran successfully — no output)"
                self.lessons_page.ide.set_output(text, kind="plain")
                self.lessons_page.ide.feedback.set_message(
                    "Code ran. Use Check Exercise when you are ready to grade."
                )
            else:
                self.lessons_page.ide.set_output(result.learner_message, kind="error")
                self.lessons_page.ide.feedback.set_message(
                    "There was an error. Read the Output panel and try again."
                )

        self._run_background(work, done, busy_message="Running code…")

    def _check_answer(self) -> None:
        if self._current_lesson is None or self._current_exercise is None:
            return
        if not self._editor_visible:
            self.show_editor()
        lesson = self._current_lesson
        exercise = self._current_exercise
        code = self.lessons_page.ide.get_code()
        answer = self.lessons_page.ide.get_answer()

        def work() -> CheckResult:
            return self.controller.submit_exercise(
                lesson,
                exercise,
                code=code,
                answer=answer,
            )

        def done(result: CheckResult) -> None:
            lines = [result.message]
            for detail in result.details:
                if detail and detail != result.message:
                    lines.append(detail)
            if result.run and result.run.error and not result.passed:
                if result.run.error not in lines:
                    lines.append("")
                    lines.append(result.run.error)
            kind = "success" if result.passed else "error"
            self.lessons_page.ide.feedback.set_message("\n".join(lines), kind=kind)
            self.sidebar.refresh_lessons(selected_lesson_id=lesson.id)
            self._refresh_progress_pill()
            record = self.controller.progress.exercise(exercise.id)
            self.lessons_page.ide.set_hint_label(record.hints_used, len(exercise.hints))

        self._run_background(work, done, busy_message="Checking answer…")

    def _reset_exercise(self) -> None:
        if self._busy or self._current_exercise is None:
            return
        reply = QMessageBox.question(
            self,
            "Reset exercise",
            "Replace your code with the starter template?",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        ide = self.lessons_page.ide
        ide.reset_to_starter()
        ide.set_answer("")
        self.controller.progress.save_draft(self._current_exercise.id, ide.get_code(), "")
        self.controller.progress.save()
        ide.clear_output()
        ide.feedback.reset()

    def _show_hint(self) -> None:
        if self._busy or self._current_exercise is None:
            return
        if not self._editor_visible:
            self.show_editor()
        used, hint = self.controller.request_hint(self._current_exercise)
        ide = self.lessons_page.ide
        if hint is None:
            text = (
                f"Hint {used}: No further hints. "
                "Re-read the lesson and try a smaller change."
            )
        else:
            text = f"Hint {used}: {hint}"
        ide.feedback.set_message(text, kind="hint")
        ide.set_hint_label(used, len(self._current_exercise.hints))

    def _run_playground(self, code: str) -> None:
        if self._closing or self._busy:
            return
        self._busy = True
        self.playground_page.set_busy(True)

        def work():
            return self.runner.run_playground(code)

        def done(result: object) -> None:
            self._busy = False
            self.playground_page.set_busy(False)
            if isinstance(result, BaseException):
                self.playground_page.output.set_text(
                    f"{type(result).__name__}: {result}", kind="error"
                )
                return
            if result.success:  # type: ignore[union-attr]
                text = result.stdout if result.stdout else "(ok — no output)"  # type: ignore[union-attr]
                self.playground_page.output.set_text(text, kind="plain")
            else:
                self.playground_page.output.set_text(
                    result.learner_message, kind="error"  # type: ignore[union-attr]
                )

        self._jobs.run(work, done)

    def _reset_playground_env(self) -> None:
        self.runner.reset_playground()
        self.playground_page.output.set_text("Playground environment reset.", kind="hint")

    def _save_progress(self) -> None:
        self._persist_current_draft()
        self.controller.progress.save()
        self.prefs_store.save()
        self.top_bar.flash_saved()

    def _reset_progress(self) -> None:
        if self._busy:
            return
        reply = QMessageBox.question(
            self,
            "Reset progress",
            "Erase all completed lessons, drafts, and mastery scores?",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.controller.progress.reset()
        first = self.controller.catalog.first()
        if first:
            self.controller.progress.data.current_lesson_id = first.id
            self.controller.progress.save()
            self._current_exercise = None
            self._show_lesson(first)
            self._on_nav("lessons")
        self._refresh_progress_pill()
        self.progress_page.refresh()
        self.sidebar.refresh_lessons(
            selected_lesson_id=first.id if first else None
        )
        QMessageBox.information(self, "Reset", "Progress has been reset.")

    def _maybe_warn_progress_recovery(self) -> None:
        warning = self.controller.progress.load_warning
        if not warning:
            return

        def show() -> None:
            if not self._closing:
                QMessageBox.warning(self, "Progress recovered", warning)

        from PySide6.QtCore import QTimer

        QTimer.singleShot(200, show)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._closing = True
        self._jobs.stop()
        self._persist_current_draft()
        self.controller.progress.save()
        self.prefs_store.save()
        super().closeEvent(event)


def launch_app(
    controller: CourseController,
    runner: CodeRunner,
    prefs_store: Optional[UiPrefsStore] = None,
) -> None:
    app = QApplication.instance()
    created = False
    if app is None:
        app = QApplication(sys.argv)
        created = True
    window = CourseApp(controller, runner, prefs_store=prefs_store)
    window.show()
    if created:
        app.exec()
