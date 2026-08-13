"""Code editor and output panel for exercises."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


MONO = ("Consolas", 11)
MONO_SMALL = ("Consolas", 10)


class CodeEditor(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        on_run: Callable[[], None],
        on_check: Callable[[], None],
        on_reset: Callable[[], None],
        on_hint: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_run = on_run

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=4, pady=4)
        ttk.Button(toolbar, text="Run Code", command=on_run).pack(side="left")
        ttk.Button(toolbar, text="Check Answer", command=on_check).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Reset Exercise", command=on_reset).pack(side="left")
        ttk.Button(toolbar, text="Hint", command=on_hint).pack(side="left", padx=4)
        ttk.Label(toolbar, text="Ctrl+Enter runs code", foreground="#666").pack(side="right")

        self._buttons: list[ttk.Button] = []
        for child in toolbar.winfo_children():
            if isinstance(child, ttk.Button):
                self._buttons.append(child)

        paned = ttk.Panedwindow(self, orient="vertical")
        paned.pack(fill="both", expand=True, padx=4, pady=4)

        editor_frame = ttk.LabelFrame(paned, text="3. Code Editor")
        editor_wrap = ttk.Frame(editor_frame)
        editor_wrap.pack(fill="both", expand=True)
        self.editor = tk.Text(
            editor_wrap,
            wrap="none",
            font=MONO,
            undo=True,
            height=12,
            insertbackground="#111",
            background="#fafafa",
            relief="solid",
            borderwidth=1,
            padx=6,
            pady=6,
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

        answer_frame = ttk.LabelFrame(paned, text="Answer / Prediction (for non-code questions)")
        self.answer = ttk.Entry(answer_frame, font=("Segoe UI", 11))
        self.answer.pack(fill="x", padx=6, pady=6)
        paned.add(answer_frame, weight=0)

        output_frame = ttk.LabelFrame(paned, text="4. Output / Feedback")
        output_wrap = ttk.Frame(output_frame)
        output_wrap.pack(fill="both", expand=True)
        self.output = tk.Text(
            output_wrap,
            wrap="word",
            height=10,
            font=MONO_SMALL,
            state="disabled",
            background="#111827",
            foreground="#e5e7eb",
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=8,
        )
        out_scroll = ttk.Scrollbar(output_wrap, command=self.output.yview)
        self.output.configure(yscrollcommand=out_scroll.set)
        self.output.pack(side="left", fill="both", expand=True)
        out_scroll.pack(side="right", fill="y")
        self.output.tag_configure("error", foreground="#fca5a5")
        self.output.tag_configure("success", foreground="#86efac")
        self.output.tag_configure("hint", foreground="#93c5fd")
        self.output.tag_configure("plain", foreground="#e5e7eb")
        paned.add(output_frame, weight=2)

        self._starter: str = ""

    def _insert_tab(self, _event: object) -> str:
        self.editor.insert("insert", "    ")
        return "break"

    def _ctrl_enter(self, _event: object) -> str:
        self._on_run()
        return "break"

    def set_code(self, code: str) -> None:
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", code)

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
