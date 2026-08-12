"""Left sidebar: sections, lessons, locks, and overall progress."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from course.lesson import Lesson
from engine.course_controller import CourseController


class Sidebar(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        controller: CourseController,
        on_select: Callable[[str], None],
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self.controller = controller
        self.on_select = on_select

        ttk.Label(self, text="Python Course", font=("Segoe UI", 14, "bold")).pack(
            anchor="w", padx=8, pady=(8, 4)
        )
        self.progress_var = tk.StringVar(value="Progress: 0%")
        ttk.Label(self, textvariable=self.progress_var).pack(anchor="w", padx=8, pady=(0, 4))
        ttk.Label(
            self,
            text="✓ complete   ○ open   [locked] locked",
            foreground="#666",
            font=("Segoe UI", 8),
        ).pack(anchor="w", padx=8, pady=(0, 8))

        tree_wrap = ttk.Frame(self)
        tree_wrap.pack(fill="both", expand=True, padx=4, pady=4)
        self.tree = ttk.Treeview(tree_wrap, show="tree", selectmode="browse")
        scroll = ttk.Scrollbar(tree_wrap, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        self._lesson_iids: dict[str, str] = {}
        self.refresh()

    def refresh(self, selected_lesson_id: Optional[str] = None) -> None:
        self.tree.delete(*self.tree.get_children())
        self._lesson_iids.clear()

        percent = self.controller.overall_progress_percent()
        self.progress_var.set(f"Progress: {percent:.0f}%")

        for section in self.controller.catalog.sections:
            section_iid = self.tree.insert("", "end", text=section.name, open=True)
            for lesson in section.lessons:
                unlocked = self.controller.is_unlocked(lesson)
                complete = self.controller.progress.is_lesson_complete(
                    lesson.id, lesson.exercise_ids
                )
                if not unlocked:
                    marker = "[locked]"
                elif complete:
                    marker = "✓"
                else:
                    marker = "○"
                label = f"{marker}  {lesson.title}"
                iid = self.tree.insert(section_iid, "end", text=label, values=(lesson.id,))
                self._lesson_iids[lesson.id] = iid

        if selected_lesson_id and selected_lesson_id in self._lesson_iids:
            iid = self._lesson_iids[selected_lesson_id]
            self.tree.selection_set(iid)
            self.tree.see(iid)

    def _on_tree_select(self, _event: object) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        iid = selection[0]
        values = self.tree.item(iid, "values")
        if not values:
            return
        lesson_id = values[0]
        lesson = self.controller.catalog.get(lesson_id)
        if lesson is None:
            return
        if not self.controller.is_unlocked(lesson):
            messagebox.showinfo(
                "Lesson locked",
                "Complete the previous lesson's exercises to unlock this one.",
            )
            return
        self.on_select(lesson_id)

    def select_lesson(self, lesson: Lesson) -> None:
        iid = self._lesson_iids.get(lesson.id)
        if not iid:
            return
        self.tree.selection_set(iid)
        self.tree.see(iid)
