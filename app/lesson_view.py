"""Lesson document panel — explanation, examples, and current exercise."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from app.theme import Theme
from course.exercise import Exercise
from course.lesson import Lesson


class LessonView(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        on_exercise_changed: Callable[[Exercise], None],
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self.on_exercise_changed = on_exercise_changed
        self.lesson: Optional[Lesson] = None
        self.exercise_index = 0
        self._theme: Optional[Theme] = None

        self.title_var = tk.StringVar(value="Select a lesson")
        self.section_var = tk.StringVar(value="")
        self.exercise_title_var = tk.StringVar(value="")

        header = ttk.Frame(self)
        header.pack(fill="x", padx=12, pady=(10, 4))
        self.section_label = ttk.Label(header, textvariable=self.section_var)
        self.section_label.pack(anchor="w")
        self.title_label = ttk.Label(header, textvariable=self.title_var)
        self.title_label.pack(anchor="w")

        body_header = ttk.Frame(self, style="PanelHeader.TFrame")
        body_header.pack(fill="x", padx=0, pady=(4, 0))
        ttk.Label(body_header, text="LESSON", style="PanelHeader.TLabel").pack(
            side="left", padx=10, pady=4
        )

        body_wrap = ttk.Frame(self)
        body_wrap.pack(fill="both", expand=True, padx=0, pady=0)
        self.body = tk.Text(
            body_wrap,
            wrap="word",
            height=14,
            state="disabled",
            relief="flat",
            borderwidth=0,
            padx=14,
            pady=10,
            highlightthickness=0,
        )
        body_scroll = ttk.Scrollbar(body_wrap, command=self.body.yview)
        self.body.configure(yscrollcommand=body_scroll.set)
        self.body.pack(side="left", fill="both", expand=True)
        body_scroll.pack(side="right", fill="y")

        exercise_header = ttk.Frame(self, style="PanelHeader.TFrame")
        exercise_header.pack(fill="x", pady=(1, 0))
        ttk.Label(exercise_header, text="EXERCISE", style="PanelHeader.TLabel").pack(
            side="left", padx=10, pady=4
        )
        ttk.Button(exercise_header, text="Next ›", command=self.next_exercise, width=8).pack(
            side="right", padx=(0, 8), pady=2
        )
        ttk.Button(exercise_header, text="‹ Prev", command=self.prev_exercise, width=8).pack(
            side="right", pady=2
        )
        ttk.Label(exercise_header, textvariable=self.exercise_title_var, style="PanelHeader.TLabel").pack(
            side="right", padx=8
        )

        prompt_wrap = ttk.Frame(self)
        prompt_wrap.pack(fill="x", padx=0, pady=0)
        self.prompt = tk.Text(
            prompt_wrap,
            wrap="word",
            height=7,
            state="disabled",
            relief="flat",
            borderwidth=0,
            padx=14,
            pady=8,
            highlightthickness=0,
        )
        prompt_scroll = ttk.Scrollbar(prompt_wrap, command=self.prompt.yview)
        self.prompt.configure(yscrollcommand=prompt_scroll.set)
        self.prompt.pack(side="left", fill="both", expand=True)
        prompt_scroll.pack(side="right", fill="y")

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.section_label.configure(foreground=theme.fg_muted, font=theme.ui_font_small)
        self.title_label.configure(foreground=theme.fg, font=theme.title_font)
        self.body.configure(
            background=theme.bg,
            foreground=theme.fg,
            font=theme.ui_font,
            insertbackground=theme.fg,
        )
        self.prompt.configure(
            background=theme.bg_exercise,
            foreground=theme.fg,
            font=theme.ui_font,
            insertbackground=theme.fg,
        )
        self.body.tag_configure(
            "heading",
            font=theme.ui_font_bold,
            foreground=theme.fg,
            spacing1=10,
            spacing3=4,
        )
        self.body.tag_configure("body", font=theme.ui_font, foreground=theme.fg, spacing3=2)
        self.body.tag_configure(
            "code",
            font=theme.mono_font_small,
            background=theme.bg_elevated,
            foreground=theme.fg,
            lmargin1=12,
            lmargin2=12,
        )
        self.body.tag_configure(
            "bullet",
            font=theme.ui_font,
            foreground=theme.fg,
            lmargin1=12,
            lmargin2=24,
        )
        self.prompt.tag_configure(
            "code",
            font=theme.mono_font_small,
            background=theme.bg_code,
            foreground=theme.fg,
        )

    def show_lesson(self, lesson: Lesson, exercise_index: int = 0) -> None:
        self.lesson = lesson
        self.exercise_index = max(0, min(exercise_index, max(0, len(lesson.exercises) - 1)))
        self.section_var.set(lesson.section.upper())
        self.title_var.set(lesson.title)
        self._render_body()
        self._render_exercise()

    def current_exercise(self) -> Optional[Exercise]:
        if not self.lesson or not self.lesson.exercises:
            return None
        return self.lesson.exercises[self.exercise_index]

    def prev_exercise(self) -> None:
        if not self.lesson or self.exercise_index <= 0:
            return
        self.exercise_index -= 1
        self._render_exercise()

    def next_exercise(self) -> None:
        if not self.lesson or self.exercise_index >= len(self.lesson.exercises) - 1:
            return
        self.exercise_index += 1
        self._render_exercise()

    def _render_body(self) -> None:
        assert self.lesson is not None
        lesson = self.lesson
        self.body.configure(state="normal")
        self.body.delete("1.0", "end")

        self.body.insert("end", lesson.content.strip() + "\n\n", "body")

        if lesson.concepts:
            self.body.insert("end", "Important concepts\n", "heading")
            for concept in lesson.concepts:
                self.body.insert("end", f"• {concept}\n", "bullet")
            self.body.insert("end", "\n")

        if lesson.examples:
            self.body.insert("end", "Examples\n", "heading")
            for example in lesson.examples:
                self.body.insert("end", f"{example.title}\n", "body")
                self.body.insert("end", example.code.rstrip() + "\n", "code")
                if example.explanation:
                    self.body.insert("end", example.explanation + "\n", "body")
                self.body.insert("end", "\n")

        if lesson.common_mistakes:
            self.body.insert("end", "Common mistakes\n", "heading")
            for mistake in lesson.common_mistakes:
                self.body.insert("end", f"• {mistake}\n", "bullet")

        self.body.configure(state="disabled")
        self.body.see("1.0")

    def _render_exercise(self) -> None:
        exercise = self.current_exercise()
        self.prompt.configure(state="normal")
        self.prompt.delete("1.0", "end")
        if exercise is None:
            self.exercise_title_var.set("(none)")
            self.prompt.insert("1.0", "This lesson has no exercises yet.")
            self.prompt.configure(state="disabled")
            return

        total = len(self.lesson.exercises) if self.lesson else 1
        self.exercise_title_var.set(f"{exercise.title}  ({self.exercise_index + 1}/{total})")
        self.prompt.insert("end", exercise.prompt.strip() + "\n\n")
        if exercise.code_to_predict:
            self.prompt.insert("end", "Code:\n")
            self.prompt.insert("end", exercise.code_to_predict.rstrip() + "\n\n", "code")
        if exercise.choices:
            self.prompt.insert("end", "Choices:\n")
            for index, choice in enumerate(exercise.choices, start=1):
                self.prompt.insert("end", f"  {index}. {choice}\n")
            self.prompt.insert("end", "\nEnter the choice number or the full text in the answer box.\n")
        self.prompt.configure(state="disabled")
        self.prompt.see("1.0")
        self.on_exercise_changed(exercise)
