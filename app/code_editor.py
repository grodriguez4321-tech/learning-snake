"""Code editor + output console panel (IDE-style workspace)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from app.theme import Theme


class CodeEditor(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        on_run: Callable[[], None],
        on_check: Callable[[], None],
        on_reset: Callable[[], None],
        on_hint: Callable[[], None],
        on_close: Optional[Callable[[], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_run = on_run
        self._theme: Optional[Theme] = None
        self.on_close = on_close

        header = ttk.Frame(self, style="PanelHeader.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text="EDITOR", style="PanelHeader.TLabel").pack(
            side="left", padx=10, pady=4
        )
        if on_close is not None:
            ttk.Button(header, text="✕", width=3, command=on_close, style="Tool.TButton").pack(
                side="right", padx=4, pady=2
            )

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=6, pady=4)
        self.run_btn = ttk.Button(toolbar, text="▶ Run", command=on_run, style="Accent.TButton")
        self.run_btn.pack(side="left")
        self.check_btn = ttk.Button(toolbar, text="Check Answer", command=on_check)
        self.check_btn.pack(side="left", padx=4)
        self.reset_btn = ttk.Button(toolbar, text="Reset", command=on_reset)
        self.reset_btn.pack(side="left")
        self.hint_btn = ttk.Button(toolbar, text="Hint", command=on_hint)
        self.hint_btn.pack(side="left", padx=4)
        self.shortcut_label = ttk.Label(toolbar, text="Ctrl+Enter Run")
        self.shortcut_label.pack(side="right")

        self._buttons = [self.run_btn, self.check_btn, self.reset_btn, self.hint_btn]

        paned = ttk.Panedwindow(self, orient="vertical")
        paned.pack(fill="both", expand=True)

        editor_frame = ttk.Frame(paned)
        tab_bar = ttk.Frame(editor_frame, style="PanelHeader.TFrame")
        tab_bar.pack(fill="x")
        ttk.Label(tab_bar, text="exercise.py", style="PanelHeader.TLabel").pack(
            side="left", padx=10, pady=3
        )
        editor_wrap = ttk.Frame(editor_frame)
        editor_wrap.pack(fill="both", expand=True)
        self.editor = tk.Text(
            editor_wrap,
            wrap="none",
            undo=True,
            height=10,
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=8,
            highlightthickness=0,
            insertwidth=2,
        )
        y_scroll = ttk.Scrollbar(editor_wrap, command=self.editor.yview)
        x_scroll = ttk.Scrollbar(editor_wrap, orient="horizontal", command=self.editor.xview)
        self.editor.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.editor.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        editor_wrap.rowconfigure(0, weight=1)
        editor_wrap.columnconfigure(0, weight=1)
        paned.add(editor_frame, weight=3)

        self.editor.bind("<Tab>", self._insert_tab)
        self.editor.bind("<Control-Return>", self._ctrl_enter)
        self.editor.bind("<Control-KP_Enter>", self._ctrl_enter)

        answer_frame = ttk.Frame(paned)
        answer_header = ttk.Frame(answer_frame, style="PanelHeader.TFrame")
        answer_header.pack(fill="x")
        ttk.Label(answer_header, text="ANSWER / PREDICTION", style="PanelHeader.TLabel").pack(
            side="left", padx=10, pady=3
        )
        self.answer = ttk.Entry(answer_frame)
        self.answer.pack(fill="x", padx=8, pady=6)
        paned.add(answer_frame, weight=0)

        output_frame = ttk.Frame(paned)
        output_header = ttk.Frame(output_frame, style="PanelHeader.TFrame")
        output_header.pack(fill="x")
        ttk.Label(output_header, text="TERMINAL", style="PanelHeader.TLabel").pack(
            side="left", padx=10, pady=3
        )
        output_wrap = ttk.Frame(output_frame)
        output_wrap.pack(fill="both", expand=True)
        self.output = tk.Text(
            output_wrap,
            wrap="word",
            height=8,
            state="disabled",
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=8,
            highlightthickness=0,
        )
        out_scroll = ttk.Scrollbar(output_wrap, command=self.output.yview)
        self.output.configure(yscrollcommand=out_scroll.set)
        self.output.pack(side="left", fill="both", expand=True)
        out_scroll.pack(side="right", fill="y")
        paned.add(output_frame, weight=2)

        self._starter: str = ""

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.shortcut_label.configure(foreground=theme.fg_muted, font=theme.ui_font_small)
        self.editor.configure(
            background=theme.bg_code,
            foreground=theme.fg,
            insertbackground=theme.fg,
            font=theme.mono_font,
            selectbackground=theme.select_bg,
            selectforeground=theme.select_fg,
        )
        # Terminal stays dark in both themes (IDE convention).
        self.output.configure(
            background=theme.bg_output,
            foreground="#d4d4d4",
            font=theme.mono_font_small,
        )
        self.output.tag_configure("error", foreground=theme.error)
        self.output.tag_configure("success", foreground=theme.success)
        self.output.tag_configure("hint", foreground=theme.hint)
        self.output.tag_configure("plain", foreground="#d4d4d4")

    def _insert_tab(self, _event: object) -> str:
        self.editor.insert("insert", "    ")
        return "break"

    def _ctrl_enter(self, _event: object) -> str:
        self._on_run()
        return "break"

    def set_code(self, code: str) -> None:
        was_disabled = str(self.editor.cget("state")) == "disabled"
        if was_disabled:
            self.editor.configure(state="normal")
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", code)
        if was_disabled:
            self.editor.configure(state="disabled")

    def get_code(self) -> str:
        return self.editor.get("1.0", "end-1c")

    def set_starter(self, starter: str) -> None:
        self._starter = starter

    def reset_to_starter(self) -> None:
        self.set_code(self._starter)
        self.answer.delete(0, "end")

    def get_answer(self) -> str:
        return self.answer.get()

    def set_answer(self, value: str) -> None:
        self.answer.delete(0, "end")
        self.answer.insert(0, value)

    def focus_editor(self) -> None:
        self.editor.focus_set()

    def append_output(self, text: str, kind: str = "plain") -> None:
        self.output.configure(state="normal")
        tag = kind if kind in {"error", "success", "hint", "plain"} else "plain"
        self.output.insert("end", text.rstrip() + "\n", tag)
        self.output.see("end")
        self.output.configure(state="disabled")

    def set_output(self, text: str, kind: str = "plain") -> None:
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        tag = kind if kind in {"error", "success", "hint", "plain"} else "plain"
        self.output.insert("1.0", text.rstrip() + "\n", tag)
        self.output.configure(state="disabled")

    def clear_output(self) -> None:
        self.set_output("")

    def set_busy(self, busy: bool, message: str = "Running…") -> None:
        state = "disabled" if busy else "normal"
        for button in self._buttons:
            button.configure(state=state)
        self.editor.configure(state=state)
        self.answer.configure(state=state)
        if busy:
            self.set_output(message, kind="hint")
