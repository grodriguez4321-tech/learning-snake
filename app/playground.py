"""Interactive Python playground with a persistent session namespace."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from app.theme import Theme


class Playground(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        on_run: Callable[[str, Callable[[str], None]], None],
        on_clear: Callable[[], None],
        on_reset_env: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self.on_run = on_run
        self.on_clear = on_clear
        self.on_reset_env = on_reset_env
        self._busy = False
        self._theme: Optional[Theme] = None

        header = ttk.Frame(self, style="PanelHeader.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text="PLAYGROUND", style="PanelHeader.TLabel").pack(
            side="left", padx=10, pady=4
        )
        ttk.Label(
            header,
            text="Variables persist until reset",
            style="PanelHeader.TLabel",
        ).pack(side="left", padx=8)

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=6, pady=4)
        self.run_button = ttk.Button(toolbar, text="▶ Run", command=self._run, style="Accent.TButton")
        self.run_button.pack(side="left")
        ttk.Button(toolbar, text="Clear Output", command=self._clear_output).pack(side="left", padx=4)
        self.reset_button = ttk.Button(toolbar, text="Reset Environment", command=self._reset_env)
        self.reset_button.pack(side="left")

        paned = ttk.Panedwindow(self, orient="vertical")
        paned.pack(fill="both", expand=True)

        input_frame = ttk.Frame(paned)
        tab = ttk.Frame(input_frame, style="PanelHeader.TFrame")
        tab.pack(fill="x")
        ttk.Label(tab, text="playground.py", style="PanelHeader.TLabel").pack(
            side="left", padx=10, pady=3
        )
        input_wrap = ttk.Frame(input_frame)
        input_wrap.pack(fill="both", expand=True)
        self.input = tk.Text(
            input_wrap,
            wrap="none",
            height=10,
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=8,
            highlightthickness=0,
            insertwidth=2,
        )
        y_scroll = ttk.Scrollbar(input_wrap, command=self.input.yview)
        self.input.configure(yscrollcommand=y_scroll.set)
        self.input.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        self.input.bind("<Tab>", self._insert_tab)
        self.input.bind("<Control-Return>", self._ctrl_enter)
        paned.add(input_frame, weight=2)

        output_frame = ttk.Frame(paned)
        out_tab = ttk.Frame(output_frame, style="PanelHeader.TFrame")
        out_tab.pack(fill="x")
        ttk.Label(out_tab, text="TERMINAL", style="PanelHeader.TLabel").pack(
            side="left", padx=10, pady=3
        )
        self.output = tk.Text(
            output_frame,
            wrap="word",
            height=10,
            state="disabled",
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=8,
            highlightthickness=0,
        )
        out_scroll = ttk.Scrollbar(output_frame, command=self.output.yview)
        self.output.configure(yscrollcommand=out_scroll.set)
        self.output.pack(side="left", fill="both", expand=True)
        out_scroll.pack(side="right", fill="y")
        paned.add(output_frame, weight=2)

        self.input.insert("1.0", "x = 2 + 2\nprint(x)\n")

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.input.configure(
            background=theme.bg_code,
            foreground=theme.fg,
            insertbackground=theme.fg,
            font=theme.mono_font,
            selectbackground=theme.select_bg,
            selectforeground=theme.select_fg,
        )
        self.output.configure(
            background=theme.bg_output,
            foreground="#d4d4d4",
            font=theme.mono_font_small,
        )
        self.output.tag_configure("error", foreground=theme.error)
        self.output.tag_configure("plain", foreground="#d4d4d4")
        self.output.tag_configure("hint", foreground=theme.hint)

    def _insert_tab(self, _event: object) -> str:
        self.input.insert("insert", "    ")
        return "break"

    def _ctrl_enter(self, _event: object) -> str:
        self._run()
        return "break"

    def _run(self) -> None:
        if self._busy:
            return
        code = self.input.get("1.0", "end-1c")
        self._set_busy(True)
        self._append("Running…", kind="hint")

        def done(text: str) -> None:
            self._set_busy(False)
            kind = (
                "error"
                if ("Error" in text or "Traceback" in text or "too long" in text)
                else "plain"
            )
            self._append(text, kind=kind)

        self.on_run(code, done)

    def _clear_output(self) -> None:
        self.on_clear()
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def _reset_env(self) -> None:
        if self._busy:
            return
        self.on_reset_env()
        self._append("[Playground environment reset — variables cleared]\n")

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        self.run_button.configure(state=state)
        self.reset_button.configure(state=state)
        self.input.configure(state=state)

    def _append(self, text: str, kind: str = "plain") -> None:
        tag = kind if kind in {"error", "plain", "hint"} else "plain"
        self.output.configure(state="normal")
        self.output.insert("end", text.rstrip() + "\n", tag)
        self.output.see("end")
        self.output.configure(state="disabled")
