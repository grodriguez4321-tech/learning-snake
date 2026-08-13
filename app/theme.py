"""IDE-inspired light/dark theme tokens for the course app.

Colors lean toward a VS Code / JetBrains feel: muted chrome, high-contrast
editor surfaces, and a distinct status bar — without decorative excess.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ThemeName = Literal["dark", "light"]


@dataclass(frozen=True)
class Theme:
    name: ThemeName
    # Chrome
    bg: str
    bg_elevated: str
    bg_sidebar: str
    bg_activity: str
    bg_status: str
    bg_input: str
    bg_code: str
    bg_output: str
    bg_exercise: str
    border: str
    # Text
    fg: str
    fg_muted: str
    fg_inverse: str
    # Accents
    accent: str
    accent_fg: str
    success: str
    error: str
    hint: str
    warning: str
    # Selection / tree
    select_bg: str
    select_fg: str
    # Fonts
    ui_font: tuple[str, int]
    ui_font_bold: tuple[str, int]
    ui_font_small: tuple[str, int]
    title_font: tuple[str, int, str]
    mono_font: tuple[str, int]
    mono_font_small: tuple[str, int]


DARK = Theme(
    name="dark",
    bg="#1e1e1e",
    bg_elevated="#252526",
    bg_sidebar="#252526",
    bg_activity="#333333",
    bg_status="#007acc",
    bg_input="#3c3c3c",
    bg_code="#1e1e1e",
    bg_output="#0d1117",
    bg_exercise="#2d2a1e",
    border="#3e3e42",
    fg="#cccccc",
    fg_muted="#858585",
    fg_inverse="#ffffff",
    accent="#0e639c",
    accent_fg="#ffffff",
    success="#89d185",
    error="#f48771",
    hint="#75beff",
    warning="#cca700",
    select_bg="#094771",
    select_fg="#ffffff",
    ui_font=("Segoe UI", 10),
    ui_font_bold=("Segoe UI", 10, "bold"),
    ui_font_small=("Segoe UI", 9),
    title_font=("Segoe UI", 16, "bold"),
    mono_font=("Consolas", 11),
    mono_font_small=("Consolas", 10),
)


LIGHT = Theme(
    name="light",
    bg="#ffffff",
    bg_elevated="#f3f3f3",
    bg_sidebar="#f3f3f3",
    bg_activity="#2c2c2c",
    bg_status="#007acc",
    bg_input="#ffffff",
    bg_code="#ffffff",
    bg_output="#1e1e1e",
    bg_exercise="#fff8e1",
    border="#e0e0e0",
    fg="#333333",
    fg_muted="#6e6e6e",
    fg_inverse="#ffffff",
    accent="#0e639c",
    accent_fg="#ffffff",
    success="#388a34",
    error="#a1260d",
    hint="#006ab1",
    warning="#bf8803",
    select_bg="#cce8ff",
    select_fg="#000000",
    ui_font=("Segoe UI", 10),
    ui_font_bold=("Segoe UI", 10, "bold"),
    ui_font_small=("Segoe UI", 9),
    title_font=("Segoe UI", 16, "bold"),
    mono_font=("Consolas", 11),
    mono_font_small=("Consolas", 10),
)


THEMES: dict[ThemeName, Theme] = {"dark": DARK, "light": LIGHT}


def get_theme(name: ThemeName) -> Theme:
    return THEMES.get(name, DARK)


def apply_ttk_theme(root: object, theme: Theme) -> None:
    """Configure ttk styles to match the active theme."""
    style = __import__("tkinter.ttk", fromlist=["Style"]).Style()
    try:
        style.theme_use("clam")
    except Exception:  # noqa: BLE001
        pass

    style.configure(".", background=theme.bg, foreground=theme.fg, font=theme.ui_font)
    style.configure("TFrame", background=theme.bg)
    style.configure("TLabel", background=theme.bg, foreground=theme.fg)
    style.configure("TLabelframe", background=theme.bg, foreground=theme.fg)
    style.configure("TLabelframe.Label", background=theme.bg, foreground=theme.fg_muted)
    style.configure(
        "TButton",
        background=theme.bg_input,
        foreground=theme.fg,
        bordercolor=theme.border,
        focuscolor=theme.accent,
        padding=(10, 4),
    )
    style.map(
        "TButton",
        background=[("active", theme.accent), ("disabled", theme.bg_elevated)],
        foreground=[("active", theme.accent_fg), ("disabled", theme.fg_muted)],
    )
    style.configure(
        "Accent.TButton",
        background=theme.accent,
        foreground=theme.accent_fg,
        padding=(10, 4),
    )
    style.map(
        "Accent.TButton",
        background=[("active", theme.select_bg)],
        foreground=[("active", theme.select_fg)],
    )
    style.configure(
        "Tool.TButton",
        background=theme.bg_activity,
        foreground=theme.fg_inverse,
        padding=(6, 8),
        font=theme.ui_font_small,
    )
    style.map(
        "Tool.TButton",
        background=[("active", theme.accent), ("pressed", theme.select_bg)],
    )
    style.configure(
        "ToolActive.TButton",
        background=theme.accent,
        foreground=theme.accent_fg,
        padding=(6, 8),
        font=theme.ui_font_small,
    )
    style.configure("TEntry", fieldbackground=theme.bg_input, foreground=theme.fg, insertcolor=theme.fg)
    style.configure("TNotebook", background=theme.bg, borderwidth=0)
    style.configure(
        "TNotebook.Tab",
        background=theme.bg_elevated,
        foreground=theme.fg_muted,
        padding=(12, 6),
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", theme.bg)],
        foreground=[("selected", theme.fg)],
    )
    style.configure(
        "Treeview",
        background=theme.bg_sidebar,
        foreground=theme.fg,
        fieldbackground=theme.bg_sidebar,
        borderwidth=0,
        rowheight=24,
    )
    style.map(
        "Treeview",
        background=[("selected", theme.select_bg)],
        foreground=[("selected", theme.select_fg)],
    )
    style.configure(
        "Vertical.TScrollbar",
        background=theme.bg_elevated,
        troughcolor=theme.bg,
        arrowcolor=theme.fg_muted,
    )
    style.configure(
        "Horizontal.TScrollbar",
        background=theme.bg_elevated,
        troughcolor=theme.bg,
        arrowcolor=theme.fg_muted,
    )
    style.configure("Status.TFrame", background=theme.bg_status)
    style.configure("Status.TLabel", background=theme.bg_status, foreground=theme.fg_inverse)
    style.configure("Sidebar.TFrame", background=theme.bg_sidebar)
    style.configure("Sidebar.TLabel", background=theme.bg_sidebar, foreground=theme.fg)
    style.configure("Activity.TFrame", background=theme.bg_activity)
    style.configure("PanelHeader.TFrame", background=theme.bg_elevated)
    style.configure(
        "PanelHeader.TLabel",
        background=theme.bg_elevated,
        foreground=theme.fg_muted,
        font=theme.ui_font_small,
    )
    style.configure("TPanedwindow", background=theme.border)
    style.configure("Sash", sashthickness=4)
