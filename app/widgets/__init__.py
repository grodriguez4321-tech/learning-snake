"""Reusable Qt UI widgets for the course shell."""

from __future__ import annotations

from app.widgets.code_editor import CodeEditorWidget
from app.widgets.feedback_panel import FeedbackPanel
from app.widgets.ide_panel import IdePanel
from app.widgets.lesson_content import LessonContent
from app.widgets.output_panel import OutputPanel
from app.widgets.progress_widget import ProgressWidget
from app.widgets.sidebar import Sidebar
from app.widgets.top_bar import TopBar

# Alias used by older imports / docs
ProgressPill = ProgressWidget

__all__ = [
    "CodeEditorWidget",
    "FeedbackPanel",
    "IdePanel",
    "LessonContent",
    "OutputPanel",
    "ProgressPill",
    "ProgressWidget",
    "Sidebar",
    "TopBar",
]
