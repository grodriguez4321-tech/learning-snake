"""Main Tkinter application window.

Composition over inheritance: the app owns sidebar, lesson view, editor, and
playground widgets, and coordinates them through CourseController.

Run/Check/Playground execution happens on a background thread so the Tk event
loop stays responsive while the subprocess runner waits (including timeouts).

Results are delivered through a thread-safe queue and applied on the Tk thread
via a periodic ``after`` poll — calling ``after`` directly from worker threads
is unreliable (and fails when mainloop is not running).
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional, TypeVar

from app.code_editor import CodeEditor
from app.lesson_view import LessonView
from app.playground import Playground
from app.sidebar import Sidebar
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
    ) -> None:
        super().__init__(master)
        self.master = master
        self.controller = controller
        self.runner = runner
        self._current_lesson: Optional[Lesson] = None
        self._current_exercise: Optional[Exercise] = None
        self._loading_exercise = False
        self._busy = False
        self._closing = False
        self._result_queue: queue.Queue[tuple[Callable[[object], None], object]] = queue.Queue()

        self.pack(fill="both", expand=True)
        self._build_menu()
        self._build_layout()
        self._load_initial_lesson()
        self._maybe_warn_progress_recovery()
        self._poll_async_results()

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.master)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Progress", command=self._save_progress)
        file_menu.add_command(label="Reset Progress…", command=self._reset_progress)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self._on_close)
        menubar.add_cascade(label="File", menu=file_menu)
        self.master.config(menu=menubar)

    def _build_layout(self) -> None:
        outer = ttk.Panedwindow(self, orient="horizontal")
        outer.pack(fill="both", expand=True)

        self.sidebar = Sidebar(outer, self.controller, on_select=self._on_sidebar_select)
        outer.add(self.sidebar, weight=1)

        right = ttk.Frame(outer)
        outer.add(right, weight=4)

        nav = ttk.Frame(right)
        nav.pack(fill="x", padx=4, pady=4)
        ttk.Button(nav, text="◀ Previous Lesson", command=self._prev_lesson).pack(side="left")
        ttk.Button(nav, text="Next Lesson ▶", command=self._next_lesson).pack(side="left", padx=6)
        self.status_var = tk.StringVar(value="")
        ttk.Label(nav, textvariable=self.status_var).pack(side="right")

        notebook = ttk.Notebook(right)
        notebook.pack(fill="both", expand=True)

        lesson_tab = ttk.Panedwindow(notebook, orient="vertical")
        notebook.add(lesson_tab, text="Lesson")

        self.lesson_view = LessonView(lesson_tab, on_exercise_changed=self._on_exercise_changed)
        lesson_tab.add(self.lesson_view, weight=3)

        self.editor = CodeEditor(
            lesson_tab,
            on_run=self._run_code,
            on_check=self._check_answer,
            on_reset=self._reset_exercise,
            on_hint=self._show_hint,
        )
        lesson_tab.add(self.editor, weight=3)

        playground_tab = Playground(
            notebook,
            on_run=self._run_playground,
            on_clear=lambda: None,
            on_reset_env=self.runner.reset_playground,
        )
        notebook.add(playground_tab, text="Playground")

        self.master.protocol("WM_DELETE_WINDOW", self._on_close)

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
                except Exception:  # noqa: BLE001 - never break the poll loop
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
        self._busy = True
        self.editor.set_busy(True, message=busy_message)

        def worker() -> None:
            try:
                result: object = work()
            except BaseException as exc:  # noqa: BLE001 - surface to UI
                result = exc
            if self._closing:
                return
            self._result_queue.put((lambda payload: self._finish_background(on_success, payload), result))

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
        if isinstance(result, BaseException):
            self.editor.set_output(f"{type(result).__name__}: {result}", kind="error")
            return
        on_success(result)  # type: ignore[arg-type]

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
        self._update_status()
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
            + (" · next lesson unlocked" if unlocked_next else "")
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

    def _run_code(self) -> None:
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
            # Refresh markers only; avoid selection churn inside event handlers.
            current_id = lesson.id
            self.sidebar.refresh(selected_lesson_id=current_id)
            self._update_status()
            if result.passed:
                nxt = self.controller.catalog.next(lesson.id)
                if nxt and self.controller.is_unlocked(nxt):
                    self.status_var.set("Exercise passed · next lesson unlocked")

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
        messagebox.showinfo("Saved", "Progress saved.")

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
        self.master.destroy()


def launch_app(controller: CourseController, runner: CodeRunner) -> None:
    root = tk.Tk()
    root.title("Interactive Python Course")
    root.geometry("1200x800")
    root.minsize(900, 600)
    CourseApp(root, controller, runner)
    root.mainloop()
