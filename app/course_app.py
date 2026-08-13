"""Main Tkinter application — IDE-style shell.

Layout (inspired by VS Code / JetBrains):
  activity bar | explorer (TOC) | lesson document
                                 | editor + terminal

Panels (TOC / Editor) can be toggled from the activity bar, View menu, or
keyboard shortcuts. Dark/light theme is persisted in ui_prefs.json.
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable, Optional, TypeVar

from app.code_editor import CodeEditor
from app.lesson_view import LessonView
from app.playground import Playground
from app.sidebar import Sidebar
from app.theme import Theme, ThemeName, apply_ttk_theme, get_theme
from app.ui_prefs import UiPrefsStore
from course.exercise import Exercise
from course.lesson import Lesson
from engine.code_runner import CodeRunner
from engine.course_controller import CourseController
from engine.exercise_checker import CheckResult


T = TypeVar("T")


class CourseApp(ttk.Frame):
    def __init__(
        self,
        master: tk.Tk,
        controller: CourseController,
        runner: CodeRunner,
        prefs_store: Optional[UiPrefsStore] = None,
    ) -> None:
        super().__init__(master)
        self.master = master
        self.controller = controller
        self.runner = runner
        self.prefs_store = prefs_store or UiPrefsStore(
            Path(__file__).resolve().parents[1] / "data" / "ui_prefs.json"
        )
        self.prefs_store.load()

        self._current_lesson: Optional[Lesson] = None
        self._current_exercise: Optional[Exercise] = None
        self._loading_exercise = False
        self._busy = False
        self._closing = False
        self._result_queue: queue.Queue[tuple[Callable[[object], None], object]] = queue.Queue()
        self._theme = get_theme(self.prefs_store.prefs.theme)
        self._sidebar_visible = self.prefs_store.prefs.sidebar_visible
        self._editor_visible = self.prefs_store.prefs.editor_visible
        self._sidebar_pane_added = False
        self._editor_pane_added = False

        self.pack(fill="both", expand=True)
        self._build_menu()
        self._build_layout()
        self._apply_theme(self._theme)
        self._sync_panel_visibility(initial=True)
        self._bind_shortcuts()
        self._load_initial_lesson()
        self._maybe_warn_progress_recovery()
        self._poll_async_results()

    # --- chrome -------------------------------------------------------------

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.master)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Progress", command=self._save_progress, accelerator="Ctrl+S")
        file_menu.add_command(label="Reset Progress…", command=self._reset_progress)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self._on_close, accelerator="Ctrl+Q")
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(
            label="Toggle Explorer", command=self.toggle_sidebar, accelerator="Ctrl+B"
        )
        view_menu.add_command(
            label="Toggle Editor", command=self.toggle_editor, accelerator="Ctrl+J"
        )
        view_menu.add_separator()
        view_menu.add_command(
            label="Toggle Dark Mode", command=self.toggle_theme, accelerator="Ctrl+Shift+D"
        )
        menubar.add_cascade(label="View", menu=view_menu)

        go_menu = tk.Menu(menubar, tearoff=0)
        go_menu.add_command(label="Previous Lesson", command=self._prev_lesson)
        go_menu.add_command(label="Next Lesson", command=self._next_lesson)
        menubar.add_cascade(label="Go", menu=go_menu)

        self.master.config(menu=menubar)
        self._menubar = menubar
        self._file_menu = file_menu
        self._view_menu = view_menu
        self._go_menu = go_menu

    def _build_layout(self) -> None:
        # Root: body + status bar
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        # Activity bar (far left) — VS Code style
        self.activity = ttk.Frame(body, style="Activity.TFrame", width=48)
        self.activity.pack(side="left", fill="y")
        self.activity.pack_propagate(False)

        self.btn_explorer = ttk.Button(
            self.activity, text="TOC", style="ToolActive.TButton", command=self.toggle_sidebar
        )
        self.btn_explorer.pack(fill="x", padx=4, pady=(8, 4))
        self.btn_editor = ttk.Button(
            self.activity, text="ED", style="ToolActive.TButton", command=self.toggle_editor
        )
        self.btn_editor.pack(fill="x", padx=4, pady=4)
        self.btn_theme = ttk.Button(
            self.activity, text="◐", style="Tool.TButton", command=self.toggle_theme
        )
        self.btn_theme.pack(side="bottom", fill="x", padx=4, pady=8)

        # Main horizontal split: explorer | workspace
        self.h_paned = ttk.Panedwindow(body, orient="horizontal")
        self.h_paned.pack(side="left", fill="both", expand=True)

        self.sidebar = Sidebar(
            self.h_paned,
            self.controller,
            on_select=self._on_sidebar_select,
            on_close=self.hide_sidebar,
        )

        workspace = ttk.Frame(self.h_paned)
        self.h_paned.add(workspace, weight=4)

        # Top nav bar
        nav = ttk.Frame(workspace)
        nav.pack(fill="x", padx=4, pady=4)
        ttk.Button(nav, text="‹ Prev", command=self._prev_lesson, width=8).pack(side="left")
        ttk.Button(nav, text="Next ›", command=self._next_lesson, width=8).pack(side="left", padx=4)
        self.lesson_path_var = tk.StringVar(value="")
        ttk.Label(nav, textvariable=self.lesson_path_var).pack(side="left", padx=12)
        self.status_var = tk.StringVar(value="")
        ttk.Label(nav, textvariable=self.status_var).pack(side="right", padx=8)

        # Tabs: Lesson | Playground
        self.notebook = ttk.Notebook(workspace)
        self.notebook.pack(fill="both", expand=True)

        lesson_tab = ttk.Frame(self.notebook)
        self.notebook.add(lesson_tab, text="Lesson")

        # Vertical split inside Lesson: document | editor
        self.v_paned = ttk.Panedwindow(lesson_tab, orient="vertical")
        self.v_paned.pack(fill="both", expand=True)

        self.lesson_view = LessonView(self.v_paned, on_exercise_changed=self._on_exercise_changed)
        self.v_paned.add(self.lesson_view, weight=3)

        self.editor = CodeEditor(
            self.v_paned,
            on_run=self._run_code,
            on_check=self._check_answer,
            on_reset=self._reset_exercise,
            on_hint=self._show_hint,
            on_close=self.hide_editor,
        )

        playground_tab = Playground(
            self.notebook,
            on_run=self._run_playground,
            on_clear=lambda: None,
            on_reset_env=self.runner.reset_playground,
        )
        self.notebook.add(playground_tab, text="Playground")
        self.playground = playground_tab

        # Status bar
        status = ttk.Frame(self, style="Status.TFrame")
        status.pack(fill="x", side="bottom")
        self.status_left = tk.StringVar(value="Ready")
        self.status_right = tk.StringVar(value="Dark")
        ttk.Label(status, textvariable=self.status_left, style="Status.TLabel").pack(
            side="left", padx=10, pady=3
        )
        ttk.Label(status, textvariable=self.status_right, style="Status.TLabel").pack(
            side="right", padx=10, pady=3
        )

        self.master.protocol("WM_DELETE_WINDOW", self._on_close)

    def _bind_shortcuts(self) -> None:
        self.master.bind_all("<Control-b>", lambda e: self.toggle_sidebar())
        self.master.bind_all("<Control-B>", lambda e: self.toggle_sidebar())
        self.master.bind_all("<Control-j>", lambda e: self.toggle_editor())
        self.master.bind_all("<Control-J>", lambda e: self.toggle_editor())
        self.master.bind_all("<Control-Shift-D>", lambda e: self.toggle_theme())
        self.master.bind_all("<Control-s>", lambda e: self._save_progress())
        self.master.bind_all("<Control-q>", lambda e: self._on_close())

    # --- theme & panels -----------------------------------------------------

    def _apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        apply_ttk_theme(self.master, theme)
        try:
            self.master.configure(bg=theme.bg)
        except tk.TclError:
            pass
        self.configure(style="TFrame")
        self.sidebar.apply_theme(theme)
        self.lesson_view.apply_theme(theme)
        self.editor.apply_theme(theme)
        self.playground.apply_theme(theme)
        self._update_activity_buttons()
        self.status_right.set("Dark mode" if theme.name == "dark" else "Light mode")
        self._restyle_menus(theme)

    def _restyle_menus(self, theme: Theme) -> None:
        for menu in (self._menubar, self._file_menu, self._view_menu, self._go_menu):
            try:
                menu.configure(
                    background=theme.bg_elevated,
                    foreground=theme.fg,
                    activebackground=theme.select_bg,
                    activeforeground=theme.select_fg,
                    borderwidth=0,
                )
            except tk.TclError:
                pass

    def toggle_theme(self) -> None:
        next_name: ThemeName = "light" if self._theme.name == "dark" else "dark"
        self._apply_theme(get_theme(next_name))
        self.prefs_store.update(theme=next_name)

    def toggle_sidebar(self) -> None:
        if self._sidebar_visible:
            self.hide_sidebar()
        else:
            self.show_sidebar()

    def show_sidebar(self) -> None:
        if self._sidebar_visible and self._sidebar_pane_added:
            return
        self._sidebar_visible = True
        if not self._sidebar_pane_added:
            # Insert explorer as first pane.
            panes = list(self.h_paned.panes())
            self.h_paned.insert(panes[0] if panes else "end", self.sidebar, weight=1)
            self._sidebar_pane_added = True
        self._update_activity_buttons()
        self.prefs_store.update(sidebar_visible=True)
        self.status_left.set("Explorer shown")

    def hide_sidebar(self) -> None:
        if not self._sidebar_visible:
            return
        self._sidebar_visible = False
        if self._sidebar_pane_added:
            try:
                self.h_paned.forget(self.sidebar)
            except tk.TclError:
                pass
            self._sidebar_pane_added = False
        self._update_activity_buttons()
        self.prefs_store.update(sidebar_visible=False)
        self.status_left.set("Explorer hidden — Ctrl+B to show")

    def toggle_editor(self) -> None:
        if self._editor_visible:
            self.hide_editor()
        else:
            self.show_editor()

    def show_editor(self) -> None:
        if self._editor_visible and self._editor_pane_added:
            return
        self._editor_visible = True
        if not self._editor_pane_added:
            self.v_paned.add(self.editor, weight=3)
            self._editor_pane_added = True
        self._update_activity_buttons()
        self.prefs_store.update(editor_visible=True)
        self.status_left.set("Editor shown")
        self.editor.focus_editor()

    def hide_editor(self) -> None:
        if not self._editor_visible:
            return
        self._editor_visible = False
        if self._editor_pane_added:
            try:
                self.v_paned.forget(self.editor)
            except tk.TclError:
                pass
            self._editor_pane_added = False
        self._update_activity_buttons()
        self.prefs_store.update(editor_visible=False)
        self.status_left.set("Editor hidden — Ctrl+J to show")

    def _sync_panel_visibility(self, *, initial: bool = False) -> None:
        # Start with neither pane registered, then show per prefs.
        if self.prefs_store.prefs.sidebar_visible:
            self.show_sidebar()
        else:
            self.hide_sidebar()
        if self.prefs_store.prefs.editor_visible:
            self.show_editor()
        else:
            self.hide_editor()
        if initial:
            self.status_left.set("Ready")

    def _update_activity_buttons(self) -> None:
        self.btn_explorer.configure(
            style="ToolActive.TButton" if self._sidebar_visible else "Tool.TButton"
        )
        self.btn_editor.configure(
            style="ToolActive.TButton" if self._editor_visible else "Tool.TButton"
        )

    # --- async / progress warnings ------------------------------------------

    def _maybe_warn_progress_recovery(self) -> None:
        warning = self.controller.progress.load_warning
        if not warning:
            return

        def show() -> None:
            if not self._closing:
                messagebox.showwarning("Progress recovered", warning)

        try:
            self.master.after(200, show)
        except tk.TclError:
            pass

    def _poll_async_results(self) -> None:
        if self._closing:
            return
        try:
            while True:
                callback, payload = self._result_queue.get_nowait()
                try:
                    callback(payload)
                except Exception:  # noqa: BLE001
                    import traceback

                    traceback.print_exc()
        except queue.Empty:
            pass
        try:
            self.master.after(50, self._poll_async_results)
        except tk.TclError:
            pass

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
        self.editor.set_busy(True, message=busy_message)
        self.status_left.set(busy_message)

        def worker() -> None:
            try:
                result: object = work()
            except BaseException as exc:  # noqa: BLE001
                result = exc
            if self._closing:
                return
            self._result_queue.put(
                (lambda payload: self._finish_background(on_success, payload), result)
            )

        threading.Thread(target=worker, daemon=True).start()

    def _finish_background(
        self,
        on_success: Callable[[T], None],
        result: object,
    ) -> None:
        self._busy = False
        if self._closing:
            return
        self.editor.set_busy(False)
        self.status_left.set("Ready")
        if isinstance(result, BaseException):
            self.editor.set_output(f"{type(result).__name__}: {result}", kind="error")
            return
        on_success(result)  # type: ignore[arg-type]

    # --- navigation / lessons -----------------------------------------------

    def _load_initial_lesson(self) -> None:
        lesson = self.controller.current_lesson()
        if lesson is None:
            self.status_var.set("No lessons found.")
            return
        self._show_lesson(lesson)

    def _show_lesson(self, lesson: Lesson) -> None:
        self._persist_current_draft()
        self._current_lesson = lesson
        self.controller.progress.data.current_lesson_id = lesson.id
        self.controller.progress.save()
        self.lesson_view.show_lesson(lesson)
        self.sidebar.refresh(selected_lesson_id=lesson.id)
        self.lesson_path_var.set(f"{lesson.section}  /  {lesson.title}")
        self._update_status()
        if self._editor_visible:
            self.editor.focus_editor()

    def _update_status(self) -> None:
        lesson = self._current_lesson
        if lesson is None:
            self.status_var.set("")
            return
        unlocked_next = False
        nxt = self.controller.catalog.next(lesson.id)
        if nxt and self.controller.is_unlocked(nxt):
            unlocked_next = True
        complete = self.controller.progress.is_lesson_complete(lesson.id, lesson.exercise_ids)
        self.status_var.set(
            f"{'Complete' if complete else 'In progress'}"
            + (" · next unlocked" if unlocked_next else "")
        )

    def _on_sidebar_select(self, lesson_id: str) -> None:
        if self._busy:
            return
        if self._current_lesson is not None and self._current_lesson.id == lesson_id:
            return
        lesson = self.controller.set_current_lesson(lesson_id)
        if lesson:
            self._show_lesson(lesson)

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
            messagebox.showinfo(
                "Lesson locked",
                "Complete all exercises in the current lesson to unlock the next one.",
            )
            return
        lesson = self.controller.go_next()
        if lesson:
            self._show_lesson(lesson)

    def _on_exercise_changed(self, exercise: Exercise) -> None:
        self._persist_current_draft()
        self._loading_exercise = True
        self._current_exercise = exercise
        record = self.controller.progress.exercise(exercise.id)
        code = record.draft_code if record.draft_code else exercise.starter_code
        self.editor.set_starter(exercise.starter_code)
        self.editor.set_code(code)
        self.editor.set_answer(record.last_answer)
        if record.completed:
            self.editor.set_output(
                "This exercise is already complete. You can still experiment.",
                kind="success",
            )
        else:
            self.editor.clear_output()
        self._loading_exercise = False

    def _persist_current_draft(self) -> None:
        if self._loading_exercise or self._current_exercise is None:
            return
        self.controller.progress.save_draft(
            self._current_exercise.id,
            self.editor.get_code(),
            self.editor.get_answer(),
        )
        self.controller.progress.save()

    def _allowed_modules(self) -> list[str]:
        if self._current_exercise is None:
            return []
        return list(self._current_exercise.allowed_modules)

    # --- run / check --------------------------------------------------------

    def _run_code(self) -> None:
        if not self._editor_visible:
            self.show_editor()
        code = self.editor.get_code()
        modules = self._allowed_modules()

        def work():
            return self.runner.run(code, allowed_modules=modules)

        def done(result) -> None:
            if result.timed_out:
                self.editor.set_output(result.learner_message, kind="error")
            elif result.success:
                text = result.stdout if result.stdout else "(ran successfully — no output)"
                self.editor.set_output(text, kind="plain")
            else:
                self.editor.set_output(result.learner_message, kind="error")

        self._run_background(work, done, busy_message="Running code…")

    def _check_answer(self) -> None:
        if self._current_lesson is None or self._current_exercise is None:
            return
        if not self._editor_visible:
            self.show_editor()
        lesson = self._current_lesson
        exercise = self._current_exercise
        code = self.editor.get_code()
        answer = self.editor.get_answer()

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
            self.editor.set_output("\n".join(lines), kind=kind)
            self.sidebar.refresh(selected_lesson_id=lesson.id)
            self._update_status()
            if result.passed:
                nxt = self.controller.catalog.next(lesson.id)
                if nxt and self.controller.is_unlocked(nxt):
                    self.status_var.set("Exercise passed · next unlocked")
                    self.status_left.set("Exercise passed")

        self._run_background(work, done, busy_message="Checking answer…")

    def _reset_exercise(self) -> None:
        if self._busy or self._current_exercise is None:
            return
        if not messagebox.askyesno("Reset exercise", "Replace your code with the starter template?"):
            return
        self.editor.reset_to_starter()
        self.controller.progress.save_draft(self._current_exercise.id, self.editor.get_code(), "")
        self.controller.progress.save()
        self.editor.clear_output()

    def _show_hint(self) -> None:
        if self._busy or self._current_exercise is None:
            return
        if not self._editor_visible:
            self.show_editor()
        used, hint = self.controller.request_hint(self._current_exercise)
        if hint is None:
            self.editor.append_output(
                f"Hint {used}: No further hints. Re-read the lesson and try a smaller change.",
                kind="hint",
            )
        else:
            self.editor.append_output(f"Hint {used}: {hint}", kind="hint")

    def _run_playground(self, code: str, done: Callable[[str], None]) -> None:
        if self._closing:
            return

        def work():
            return self.runner.run_playground(code)

        def finish(result: object) -> None:
            if isinstance(result, BaseException):
                done(f"{type(result).__name__}: {result}")
                return
            if result.success:  # type: ignore[union-attr]
                text = result.stdout if result.stdout else "(ok — no output)"  # type: ignore[union-attr]
            else:
                text = result.learner_message  # type: ignore[union-attr]
            done(text)

        def worker() -> None:
            try:
                result: object = work()
            except BaseException as exc:  # noqa: BLE001
                result = exc
            if self._closing:
                return
            self._result_queue.put((finish, result))

        threading.Thread(target=worker, daemon=True).start()

    def _save_progress(self) -> None:
        self._persist_current_draft()
        self.controller.progress.save()
        self.prefs_store.save()
        self.status_left.set("Progress saved")

    def _reset_progress(self) -> None:
        if self._busy:
            return
        if not messagebox.askyesno(
            "Reset progress",
            "Erase all completed lessons, drafts, and mastery scores?",
        ):
            return
        self.controller.progress.reset()
        first = self.controller.catalog.first()
        if first:
            self.controller.progress.data.current_lesson_id = first.id
            self.controller.progress.save()
            self._current_exercise = None
            self._show_lesson(first)
        messagebox.showinfo("Reset", "Progress has been reset.")

    def _on_close(self) -> None:
        if self._closing:
            return
        self._closing = True
        self._persist_current_draft()
        self.controller.progress.save()
        self.prefs_store.save()
        self.master.destroy()


def launch_app(
    controller: CourseController,
    runner: CodeRunner,
    prefs_store: Optional[UiPrefsStore] = None,
) -> None:
    root = tk.Tk()
    root.title("Python Course — IDE")
    root.geometry("1280x840")
    root.minsize(960, 640)
    CourseApp(root, controller, runner, prefs_store=prefs_store)
    root.mainloop()
