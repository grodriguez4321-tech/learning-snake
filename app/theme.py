"""Central dark/light theme tokens and Qt stylesheets.

Palette targets a Cursor / VS Code / GitHub dark aesthetic — muted chrome,
subtle borders, blue accents — not pure black/white defaults.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ThemeName = Literal["dark", "light"]


@dataclass(frozen=True)
class Theme:
    name: ThemeName
    bg: str
    bg_sidebar: str
    bg_card: str
    bg_elevated: str
    bg_input: str
    bg_editor: str
    bg_code_block: str
    border: str
    border_subtle: str
    text: str
    text_muted: str
    text_dim: str
    accent: str
    accent_hover: str
    accent_soft: str
    success: str
    success_soft: str
    warning: str
    warning_soft: str
    error: str
    error_soft: str
    nav_active: str
    select: str


DARK = Theme(
    name="dark",
    bg="#0D1117",
    bg_sidebar="#11161D",
    bg_card="#161B22",
    bg_elevated="#1C2330",
    bg_input="#0D1117",
    bg_editor="#0D1117",
    bg_code_block="#0B0F14",
    border="#30363D",
    border_subtle="#21262D",
    text="#E6EDF3",
    text_muted="#8B949E",
    text_dim="#6E7681",
    accent="#2F81F7",
    accent_hover="#388BFD",
    accent_soft="#1F3A5F",
    success="#3FB950",
    success_soft="#1B4332",
    warning="#D29922",
    warning_soft="#3D2E00",
    error="#F85149",
    error_soft="#3D1214",
    nav_active="#1F3A5F",
    select="#264F78",
)


LIGHT = Theme(
    name="light",
    bg="#F6F8FA",
    bg_sidebar="#FFFFFF",
    bg_card="#FFFFFF",
    bg_elevated="#F6F8FA",
    bg_input="#FFFFFF",
    bg_editor="#FFFFFF",
    bg_code_block="#F6F8FA",
    border="#D0D7DE",
    border_subtle="#E6E8EB",
    text="#1F2328",
    text_muted="#656D76",
    text_dim="#8C959F",
    accent="#0969DA",
    accent_hover="#0860CA",
    accent_soft="#DDF4FF",
    success="#1A7F37",
    success_soft="#DAFBE1",
    warning="#9A6700",
    warning_soft="#FFF8C5",
    error="#CF222E",
    error_soft="#FFEBE9",
    nav_active="#DDF4FF",
    select="#B6E3FF",
)


def get_theme(name: ThemeName) -> Theme:
    return DARK if name == "dark" else LIGHT


def build_stylesheet(theme: Theme) -> str:
    """Application-wide QSS. Prefer this over per-widget color scattering."""
    return f"""
    * {{
        font-family: "Segoe UI", "Ubuntu", "Noto Sans", sans-serif;
        font-size: 13px;
    }}
    QMainWindow, QDialog {{
        background-color: {theme.bg};
        color: {theme.text};
    }}
    QWidget {{
        background-color: transparent;
        color: {theme.text};
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: {theme.bg};
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {theme.border};
        border-radius: 5px;
        min-height: 24px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: {theme.bg};
        height: 10px;
    }}
    QScrollBar::handle:horizontal {{
        background: {theme.border};
        border-radius: 5px;
        min-width: 24px;
    }}
    QLabel#BrandTitle {{
        font-size: 16px;
        font-weight: 700;
        color: {theme.text};
    }}
    QLabel#SectionHeading {{
        font-size: 11px;
        font-weight: 600;
        color: {theme.text_dim};
        letter-spacing: 0.8px;
    }}
    QLabel#LessonTitle {{
        font-size: 28px;
        font-weight: 700;
        color: {theme.text};
        padding-bottom: 4px;
    }}
    QLabel#PageTitle {{
        font-size: 24px;
        font-weight: 700;
        color: {theme.text};
    }}
    QLabel#CardTitle {{
        font-size: 14px;
        font-weight: 600;
        color: {theme.text};
    }}
    QLabel#BodyText {{
        color: {theme.text};
        font-size: 14px;
        line-height: 1.45;
    }}
    QLabel#MutedLabel {{
        color: {theme.text_muted};
        font-size: 13px;
    }}
    QLabel#Breadcrumb {{
        color: {theme.text_muted};
        font-size: 13px;
    }}
    QLabel#ProgressPct {{
        color: {theme.accent};
        font-weight: 700;
        font-size: 13px;
    }}
    QLabel#TabLabel {{
        color: {theme.text};
        font-size: 12px;
        padding: 6px 10px;
    }}
    QFrame#Sidebar {{
        background-color: {theme.bg_sidebar};
        border-right: 1px solid {theme.border_subtle};
    }}
    QFrame#SidebarFooter {{
        background-color: {theme.bg_card};
        border: 1px solid {theme.border_subtle};
        border-radius: 10px;
    }}
    QFrame#TopBar {{
        background-color: {theme.bg};
        border-bottom: 1px solid {theme.border_subtle};
    }}
    QFrame#Card, QFrame#EditorCard, QFrame#OutputCard, QFrame#FeedbackCard {{
        background-color: {theme.bg_card};
        border: 1px solid {theme.border_subtle};
        border-radius: 10px;
    }}
    QFrame#ConceptCard {{
        background-color: {theme.bg_card};
        border: 1px solid {theme.accent_soft};
        border-radius: 10px;
    }}
    QFrame#CodeBlock {{
        background-color: {theme.bg_code_block};
        border: 1px solid {theme.border_subtle};
        border-radius: 8px;
    }}
    QFrame#EditorChrome {{
        background-color: {theme.bg_elevated};
        border-bottom: 1px solid {theme.border_subtle};
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
    }}
    QFrame#ProgressPill {{
        background-color: {theme.bg_card};
        border: 1px solid {theme.border_subtle};
        border-radius: 16px;
    }}
    QPushButton {{
        background-color: {theme.bg_elevated};
        color: {theme.text};
        border: 1px solid {theme.border};
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {theme.border_subtle};
        border-color: {theme.border};
    }}
    QPushButton:pressed {{
        background-color: {theme.border};
    }}
    QPushButton:disabled {{
        color: {theme.text_dim};
        background-color: {theme.bg_card};
        border-color: {theme.border_subtle};
    }}
    QPushButton#PrimaryButton {{
        background-color: {theme.accent};
        color: #FFFFFF;
        border: 1px solid {theme.accent};
        font-weight: 600;
        padding: 9px 18px;
    }}
    QPushButton#PrimaryButton:hover {{
        background-color: {theme.accent_hover};
        border-color: {theme.accent_hover};
    }}
    QPushButton#SecondaryButton {{
        background-color: transparent;
        border: 1px solid {theme.border};
        color: {theme.text};
    }}
    QPushButton#LessonItem {{
        text-align: left;
        padding: 8px 12px;
        border: none;
        border-radius: 8px;
        background: transparent;
        color: {theme.text_muted};
        min-height: 20px;
    }}
    QPushButton#NavItem {{
        text-align: left;
        padding: 10px 12px;
        border: none;
        border-radius: 8px;
        background: transparent;
        color: {theme.text_muted};
        font-size: 13px;
        min-height: 18px;
    }}
    QPushButton#NavItem:hover {{
        background-color: {theme.bg_elevated};
        color: {theme.text};
    }}
    QPushButton#NavItem:checked {{
        background-color: {theme.nav_active};
        color: {theme.text};
        font-weight: 600;
    }}
    QPushButton#LessonItem:hover {{
        background-color: {theme.bg_elevated};
        color: {theme.text};
    }}
    QPushButton#LessonItem:checked {{
        background-color: {theme.nav_active};
        color: {theme.text};
        font-weight: 600;
    }}
    QPushButton#LessonItem:disabled {{
        color: {theme.text_dim};
        background: transparent;
    }}
    QLineEdit, QComboBox, QTextEdit#AnswerField {{
        background-color: {theme.bg_input};
        border: 1px solid {theme.border};
        border-radius: 8px;
        padding: 8px 10px;
        color: {theme.text};
        selection-background-color: {theme.select};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {theme.bg_card};
        color: {theme.text};
        border: 1px solid {theme.border};
        selection-background-color: {theme.select};
    }}
    QPlainTextEdit#CodeEditor, QTextEdit#CodeEditor {{
        background-color: {theme.bg_editor};
        color: {theme.text};
        border: none;
        font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
        font-size: 13px;
        selection-background-color: {theme.select};
        padding: 8px;
    }}
    QPlainTextEdit#OutputView, QTextEdit#OutputView, QTextEdit#ExampleCode {{
        background-color: {theme.bg_code_block};
        color: {theme.text};
        border: 1px solid {theme.border_subtle};
        border-radius: 8px;
        font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
        font-size: 12px;
        padding: 10px;
    }}
    QTextEdit#FeedbackView {{
        background-color: {theme.bg_elevated};
        color: {theme.text_muted};
        border: none;
        border-radius: 8px;
        font-size: 13px;
        padding: 10px;
    }}
    QProgressBar {{
        background-color: {theme.bg_elevated};
        border: none;
        border-radius: 4px;
        text-align: center;
        color: {theme.text_muted};
        max-height: 8px;
    }}
    QProgressBar::chunk {{
        background-color: {theme.accent};
        border-radius: 4px;
    }}
    QSplitter::handle {{
        background-color: {theme.border_subtle};
    }}
    QSplitter::handle:horizontal {{
        width: 1px;
    }}
    QToolTip {{
        background-color: {theme.bg_elevated};
        color: {theme.text};
        border: 1px solid {theme.border};
        padding: 6px;
    }}
    QMessageBox {{
        background-color: {theme.bg_card};
    }}
    """
