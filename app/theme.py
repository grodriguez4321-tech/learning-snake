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
    bg="#080B10",
    bg_sidebar="#0D1219",
    bg_card="#111823",
    bg_elevated="#172131",
    bg_input="#0D1219",
    bg_editor="#0D1219",
    bg_code_block="#111823",
    border="#223247",
    border_subtle="#151E2B",
    text="#E6EDF3",
    text_muted="#8B949E",
    text_dim="#6E7681",
    accent="#3B82F6",
    accent_hover="#60A5FA",
    accent_soft="#163A6B",
    success="#54D6A1",
    success_soft="#1B4332",
    warning="#D29922",
    warning_soft="#3D2E00",
    error="#F85149",
    error_soft="#3D1214",
    nav_active="#13233A",
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
        font-size: 14px;
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
        background: transparent;
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
        background: transparent;
        height: 10px;
    }}
    QScrollBar::handle:horizontal {{
        background: {theme.border};
        border-radius: 5px;
        min-width: 24px;
    }}
    QLabel#BrandTitle {{
        font-size: 17px;
        font-weight: 700;
        color: {theme.text};
        letter-spacing: 0.2px;
    }}
    QLabel#SectionHeading {{
        font-size: 11px;
        font-weight: 600;
        color: {theme.text_dim};
        letter-spacing: 0.9px;
    }}
    QLabel#LessonTitle {{
        font-size: 30px;
        font-weight: 700;
        color: {theme.text};
        padding-bottom: 2px;
    }}
    QLabel#PageTitle {{
        font-size: 26px;
        font-weight: 700;
        color: {theme.text};
    }}
    QLabel#CardTitle {{
        font-size: 14px;
        font-weight: 600;
        color: {theme.text};
    }}
    QLabel#ExerciseTitle {{
        font-size: 15px;
        font-weight: 600;
        color: {theme.text};
    }}
    QLabel#ExampleTitle {{
        font-size: 13px;
        font-weight: 600;
        color: {theme.text_muted};
    }}
    QLabel#LangBadge {{
        font-size: 11px;
        font-weight: 600;
        color: {theme.text_dim};
        background-color: {theme.bg_elevated};
        border: 1px solid {theme.border_subtle};
        border-radius: 6px;
        padding: 2px 8px;
    }}
    QLabel#BodyText {{
        color: {theme.text};
        font-size: 14px;
    }}
    QLabel#LeadText {{
        color: {theme.text_muted};
        font-size: 15px;
        padding-bottom: 4px;
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
        font-weight: 500;
    }}
    QLabel#FeedbackStrip {{
        color: {theme.text_muted};
        font-size: 13px;
        background-color: {theme.bg_elevated};
        border: 1px solid {theme.border_subtle};
        border-radius: 8px;
        padding: 10px 12px;
    }}
    QLabel#LessonRowIcon {{
        color: {theme.text_muted};
        font-size: 12px;
    }}
    QLabel#LessonRowLabel {{
        color: {theme.text_muted};
        font-size: 13px;
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
    QFrame#Card, QFrame#EditorCard {{
        background-color: {theme.bg_card};
        border: 1px solid {theme.border_subtle};
        border-radius: 10px;
    }}
    QFrame#ConceptCard {{
        background-color: {theme.bg_card};
        border: 1px solid {theme.accent_soft};
        border-radius: 10px;
    }}
    QFrame#MistakesCard {{
        background-color: {theme.bg_card};
        border: 1px solid {theme.warning_soft};
        border-radius: 10px;
    }}
    QLabel#SectionHeading {{
        color: {theme.text};
        font-weight: 600;
        font-size: 13px;
    }}
    QFrame#ExampleBlock {{
        background: transparent;
        border: none;
    }}
    QFrame#PanelSection {{
        background: transparent;
        border: none;
    }}
    QFrame#EditorChrome {{
        background-color: {theme.bg_elevated};
        border: none;
        border-bottom: 1px solid {theme.border_subtle};
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
    }}
    QFrame#ProgressPill {{
        background-color: {theme.bg_card};
        border: 1px solid {theme.border_subtle};
        border-radius: 16px;
    }}
    QFrame#LessonRow {{
        background: transparent;
        border: none;
        border-radius: 8px;
    }}
    QFrame#LessonRow:hover {{
        background-color: {theme.bg_elevated};
    }}
    QFrame#LessonRow[active="true"] {{
        background-color: {theme.nav_active};
        border-left: 3px solid {theme.accent};
        border-top-left-radius: 8px;
        border-bottom-left-radius: 8px;
    }}
    QFrame#LessonRow[active="true"] QLabel#LessonRowLabel {{
        color: {theme.text};
        font-weight: 600;
    }}
    QFrame#LessonRow[active="true"] QLabel#LessonRowIcon {{
        color: {theme.accent};
    }}
    QFrame#LessonRow[locked="true"] QLabel#LessonRowLabel {{
        color: {theme.text_dim};
    }}
    QFrame#LessonRow[locked="true"] QLabel#LessonRowIcon {{
        color: {theme.warning};
    }}
    QPushButton {{
        background-color: {theme.bg_elevated};
        color: {theme.text};
        border: 1px solid {theme.border};
        border-radius: 8px;
        padding: 7px 14px;
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
        padding: 8px 16px;
    }}
    QPushButton#PrimaryButton:hover {{
        background-color: {theme.accent_hover};
        border-color: {theme.accent_hover};
    }}
    QPushButton#ToolButton {{
        background-color: transparent;
        border: 1px solid {theme.border_subtle};
        border-radius: 7px;
        color: {theme.text_muted};
        padding: 5px 10px;
        font-size: 12px;
        font-weight: 500;
    }}
    QPushButton#ToolButton:hover {{
        background-color: {theme.bg_elevated};
        color: {theme.text};
        border-color: {theme.border};
    }}
    QPushButton#ToolButton:checked {{
        background-color: {theme.nav_active};
        color: {theme.text};
        border-color: {theme.accent_soft};
    }}
    QPushButton#GhostButton, QPushButton#SecondaryButton {{
        background-color: transparent;
        border: 1px solid {theme.border};
        color: {theme.text};
        padding: 7px 12px;
    }}
    QPushButton#GhostButton:hover, QPushButton#SecondaryButton:hover {{
        background-color: {theme.bg_elevated};
        border-color: {theme.border};
    }}
    QPushButton#IconButton {{
        background: transparent;
        border: 1px solid {theme.border_subtle};
        border-radius: 6px;
        padding: 0;
        color: {theme.text_muted};
        font-size: 16px;
    }}
    QPushButton#IconButton:hover {{
        background-color: {theme.bg_elevated};
        color: {theme.text};
    }}
    QPushButton#NavItem {{
        text-align: left;
        padding: 8px 12px;
        border: none;
        border-radius: 8px;
        background: transparent;
        color: {theme.text_muted};
        font-size: 13px;
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
    QLineEdit, QComboBox, QTextEdit#AnswerField {{
        background-color: {theme.bg_input};
        border: 1px solid {theme.border};
        border-radius: 8px;
        padding: 7px 10px;
        color: {theme.text};
        selection-background-color: {theme.select};
        font-size: 13px;
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
        padding: 6px;
    }}
    QPlainTextEdit#ExampleCode, QTextEdit#ExampleCode {{
        background-color: {theme.bg_code_block};
        color: {theme.text};
        border: 1px solid {theme.border_subtle};
        border-radius: 8px;
        font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
        font-size: 12px;
        padding: 10px 12px;
        selection-background-color: {theme.select};
    }}
    QPlainTextEdit#OutputView, QTextEdit#OutputView {{
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
        border: 1px solid {theme.border_subtle};
        border-radius: 8px;
        font-size: 13px;
        padding: 8px 10px;
    }}
    QRadioButton#ChoiceOption {{
        color: {theme.text};
        font-size: 13px;
        spacing: 8px;
    }}
    QRadioButton#ChoiceOption::indicator {{
        width: 14px;
        height: 14px;
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
        margin: 8px 0;
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
