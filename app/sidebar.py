"""Left explorer/TOC panel — collapsible course outline."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from app.theme import Theme
from course.lesson import Lesson
from engine.course_controller import CourseController


class Sidebar(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        controller: CourseController,
        on_select: Callable[[str], None],
        on_close: Optional[Callable[[], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, style="Sidebar.TFrame", **kwargs)
        self.controller = controller
        self.on_select = on_select
        self.on_close = on_close
        self._theme: Optional[Theme] = None

        header = ttk.Frame(self, style="PanelHeader.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text="EXPLORER", style="PanelHeader.TLabel").pack(
            side="left", padx=10, pady=6
        )
        if on_close is not None:
            ttk.Button(header, text="✕", width=3, command=on_close, style="Tool.TButton").pack(
                side="right", padx=4, pady=2
            )

        meta = ttk.Frame(self, style="Sidebar.TFrame")
        meta.pack(fill="x", padx=8, pady=(8, 4))
        ttk.Label(meta, text="PYTHON COURSE", style="Sidebar.TLabel", font=("Segoe UI", 9, "bold")).pack(
            anchor="w"
        )
        self.progress_var = tk.StringVar(value="Progress: 0%")
        ttk.Label(meta, textvariable=self.progress_var, style="Sidebar.TLabel").pack(anchor="w")
        self.legend = ttk.Label(
            meta,
            text="✓ done   ○ open   [ ] locked",
            style="Sidebar.TLabel",
        )
        self.legend.pack(anchor="w", pady=(2, 0))

        tree_wrap = ttk.Frame(self, style="Sidebar.TFrame")
        tree_wrap.pack(fill="both", expand=True, padx=0, pady=0)
        self.tree = ttk.Treeview(tree_wrap, show="tree", selectmode="browse")
        scroll = ttk.Scrollbar(tree_wrap, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._on_tree_select)

        self._lesson_iids: dict[str, str] = {}
        self.refresh()

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.configure(style="Sidebar.TFrame")
        self.legend.configure(foreground=theme.fg_muted)

    def refresh(self, selected_lesson_id: Optional[str] = None) -> None:
        # Unbind while rebuilding: selection_set can deliver <<TreeviewSelect>>
        # after a suppress flag is cleared, which re-enters navigation and hangs.
        self.tree.unbind("<<TreeviewSelect>>")
        try:
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
                        marker = "[ ]"
                    elif complete:
                        marker = " ✓"
                    else:
                        marker = " ○"
                    label = f"{marker}  {lesson.title}"
                    iid = self.tree.insert(section_iid, "end", text=label, values=(lesson.id,))
                    self._lesson_iids[lesson.id] = iid

            if selected_lesson_id and selected_lesson_id in self._lesson_iids:
                iid = self._lesson_iids[selected_lesson_id]
                self.tree.selection_set(iid)
                self.tree.see(iid)
        finally:
            self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

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
