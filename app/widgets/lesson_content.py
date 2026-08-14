"""Lesson content cards and left instructional column."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.theme import Theme
from app.widgets.code_editor import PythonHighlighter
from course.exercise import Exercise
from course.lesson import CodeExample, ContentSection, Lesson


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _mono_font(point_size: int = 12) -> QFont:
    font = QFont("Cascadia Code", point_size)
    if not font.exactMatch():
        font = QFont("Consolas", point_size)
    font.setStyleHint(QFont.StyleHint.Monospace)
    return font


def _fit_readonly_code_height(
    editor: QPlainTextEdit,
    *,
    min_height: int = 44,
    max_height: int = 200,
) -> None:
    """Size a read-only code panel to its content (used for predict snippets)."""
    editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    line_count = max(1, editor.blockCount())
    doc_h = int(editor.document().size().height()) + 18
    height = min(max_height, max(min_height, line_count * 20 + 16, doc_h))
    editor.setMinimumHeight(height)
    editor.setMaximumHeight(height)


def _format_body(text: str) -> str:
    stripped = (text or "").strip("\n")
    if not stripped:
        return ""
    escaped = _escape(stripped)
    if any(line.startswith("  ") for line in stripped.splitlines()):
        return (
            "<pre style='font-family: Consolas, \"Cascadia Code\", monospace; "
            "font-size: 12px; margin: 4px 0 0 0; white-space: pre-wrap;'>"
            f"{escaped}</pre>"
        )
    return escaped.replace("\n", "<br>")


class ConceptCard(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ConceptCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        header = QLabel("💡  Key Concepts")
        header.setObjectName("CardTitle")
        layout.addWidget(header)

        self._body = QLabel()
        self._body.setWordWrap(True)
        self._body.setObjectName("BodyText")
        self._body.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self._body)

    def set_concepts(self, concepts: list[str]) -> None:
        if not concepts:
            self._body.setText("—")
            return
        lines = "".join(
            f"<li style='margin:5px 0;'>{_escape(c)}</li>" for c in concepts
        )
        self._body.setText(f"<ul style='margin:0; padding-left:18px;'>{lines}</ul>")


class ExplanationCard(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 16)
        layout.setSpacing(12)

        header = QLabel("How it works")
        header.setObjectName("CardTitle")
        layout.addWidget(header)

        self._host = QVBoxLayout()
        self._host.setSpacing(12)
        layout.addLayout(self._host)

    def set_sections(self, sections: list[ContentSection]) -> None:
        while self._host.count():
            item = self._host.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

        if not sections:
            self.hide()
            return
        self.show()
        for section in sections:
            block = QFrame()
            block.setObjectName("ExampleBlock")
            inner = QVBoxLayout(block)
            inner.setContentsMargins(0, 0, 0, 0)
            inner.setSpacing(4)
            if section.heading:
                heading = QLabel(section.heading)
                heading.setObjectName("SectionHeading")
                heading.setWordWrap(True)
                inner.addWidget(heading)
            body = QLabel()
            body.setWordWrap(True)
            body.setObjectName("BodyText")
            body.setTextFormat(Qt.TextFormat.RichText)
            body.setText(_format_body(section.body))
            inner.addWidget(body)
            self._host.addWidget(block)


class MistakesCard(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("MistakesCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        header = QLabel("⚠  Common mistakes")
        header.setObjectName("CardTitle")
        layout.addWidget(header)

        self._body = QLabel()
        self._body.setWordWrap(True)
        self._body.setObjectName("BodyText")
        self._body.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self._body)

    def set_mistakes(self, mistakes: list[str]) -> None:
        if not mistakes:
            self.hide()
            return
        self.show()
        lines = "".join(
            f"<li style='margin:5px 0;'>{_escape(item)}</li>" for item in mistakes
        )
        self._body.setText(f"<ul style='margin:0; padding-left:18px;'>{lines}</ul>")


class ExampleBlock(QFrame):
    def __init__(self, example: CodeExample, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ExampleBlock")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        title = QLabel(example.title or "Example")
        title.setObjectName("ExampleTitle")
        head.addWidget(title)
        head.addStretch(1)
        lang = QLabel("Python")
        lang.setObjectName("LangBadge")
        head.addWidget(lang)
        layout.addLayout(head)

        code = QPlainTextEdit()
        code.setObjectName("ExampleCode")
        code.setReadOnly(True)
        code.setFrameShape(QFrame.Shape.NoFrame)
        code.setFont(_mono_font(12))
        code.setPlainText((example.code or "").rstrip() + "\n")
        code.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        code.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._highlighter = PythonHighlighter(code.document(), theme)
        # Fit height to content
        doc_h = int(code.document().size().height()) + 18
        line_count = max(1, code.blockCount())
        code.setFixedHeight(min(160, max(44, line_count * 20 + 16, doc_h)))
        layout.addWidget(code)

        expl = (example.explanation or "").strip()
        if expl:
            el = QLabel(expl)
            el.setWordWrap(True)
            el.setObjectName("MutedLabel")
            layout.addWidget(el)


class ExampleSection(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 16)
        layout.setSpacing(14)

        title = QLabel("Examples")
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        self._host = QVBoxLayout()
        self._host.setSpacing(16)
        layout.addLayout(self._host)

    def set_examples(self, examples: list[CodeExample], theme: Theme) -> None:
        while self._host.count():
            item = self._host.takeAt(0)
            w = item.widget()
            if w is not None:
                w.hide()
                w.setParent(None)
                w.deleteLater()

        if not examples:
            empty = QLabel("No examples for this lesson.")
            empty.setObjectName("MutedLabel")
            self._host.addWidget(empty)
            return

        for ex in examples:
            self._host.addWidget(ExampleBlock(ex, theme))


class ExerciseCard(QFrame):
    prevExercise = Signal()
    nextExercise = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Exercise")
        title.setObjectName("CardTitle")
        header.addWidget(title)
        header.addStretch(1)
        self._ex_meta = QLabel("")
        self._ex_meta.setObjectName("MutedLabel")
        header.addWidget(self._ex_meta)
        self._prev_ex = QPushButton("‹")
        self._prev_ex.setObjectName("IconButton")
        self._prev_ex.setFixedSize(32, 28)
        self._prev_ex.clicked.connect(self.prevExercise.emit)
        self._next_ex = QPushButton("›")
        self._next_ex.setObjectName("IconButton")
        self._next_ex.setFixedSize(32, 28)
        self._next_ex.clicked.connect(self.nextExercise.emit)
        header.addWidget(self._prev_ex)
        header.addWidget(self._next_ex)
        layout.addLayout(header)

        self._title = QLabel()
        self._title.setObjectName("ExerciseTitle")
        layout.addWidget(self._title)

        self._prompt = QLabel()
        self._prompt.setWordWrap(True)
        self._prompt.setObjectName("BodyText")
        self._prompt.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self._prompt)

        self._predict_label = QLabel("Code to predict")
        self._predict_label.setObjectName("MutedLabel")
        layout.addWidget(self._predict_label)

        self._predict = QPlainTextEdit()
        self._predict.setObjectName("ExampleCode")
        self._predict.setReadOnly(True)
        self._predict.setFrameShape(QFrame.Shape.NoFrame)
        self._predict.setFont(_mono_font(12))
        layout.addWidget(self._predict)

        self._choices_label = QLabel()
        self._choices_label.setWordWrap(True)
        self._choices_label.setObjectName("BodyText")
        self._choices_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self._choices_label)

        self._instructions = QLabel()
        self._instructions.setWordWrap(True)
        self._instructions.setObjectName("BodyText")
        self._instructions.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self._instructions)

    def set_exercise(
        self,
        exercise: Exercise | None,
        *,
        index: int = 0,
        total: int = 0,
    ) -> None:
        if exercise is None:
            self._title.setText("")
            self._prompt.setText("No exercise selected.")
            self._ex_meta.setText("")
            self._predict_label.setVisible(False)
            self._predict.setVisible(False)
            self._choices_label.setVisible(False)
            self._instructions.setText("")
            self._prev_ex.setEnabled(False)
            self._next_ex.setEnabled(False)
            return

        self._ex_meta.setText(f"{index + 1} / {total}")
        self._prev_ex.setEnabled(index > 0)
        self._next_ex.setEnabled(index < total - 1)
        self._title.setText(exercise.title)
        self._prompt.setText(exercise.prompt)

        if exercise.code_to_predict:
            self._predict_label.setVisible(True)
            self._predict.setVisible(True)
            self._predict.setPlainText(exercise.code_to_predict.strip())
            _fit_readonly_code_height(self._predict)
        else:
            self._predict_label.setVisible(False)
            self._predict.setVisible(False)

        if exercise.is_choice_exercise and exercise.choices:
            items = "".join(
                f"<li style='margin:5px 0;'>{index}. {_escape(choice)}</li>"
                for index, choice in enumerate(exercise.choices, start=1)
            )
            self._choices_label.setText(
                f"<b>Options</b><ol style='margin:6px 0; padding-left:22px;'>{items}</ol>"
            )
            self._choices_label.setVisible(True)
        else:
            self._choices_label.setVisible(False)

        tips: list[str] = []
        if exercise.is_code_exercise:
            tips.append("Write your solution in the editor on the right.")
            tips.append("Use Run Code to try it, then Check Exercise to grade.")
        elif exercise.is_choice_exercise:
            tips.append("Select an option on the right, then click Check.")
        elif exercise.uses_free_text_answer:
            tips.append("Type your predicted output in the answer box on the right.")
            tips.append("Then click Check.")
        if tips:
            items = "".join(f"<li style='margin:4px 0;'>{_escape(t)}</li>" for t in tips)
            self._instructions.setText(
                f"<b>Instructions</b><ul style='margin:6px 0; padding-left:18px;'>{items}</ul>"
            )
        else:
            self._instructions.setText("")


class LessonContent(QWidget):
    prevLesson = Signal()
    nextLesson = Signal()
    prevExercise = Signal()
    nextExercise = Signal()

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.lesson: Lesson | None = None
        self._theme = theme

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(28, 22, 20, 20)
        layout.setSpacing(18)

        self._title = QLabel()
        self._title.setObjectName("LessonTitle")
        self._title.setWordWrap(True)
        layout.addWidget(self._title)

        self._intro = QLabel()
        self._intro.setWordWrap(True)
        self._intro.setObjectName("LeadText")
        layout.addWidget(self._intro)

        self._explanation = ExplanationCard()
        layout.addWidget(self._explanation)

        self._concepts = ConceptCard()
        layout.addWidget(self._concepts)

        self._examples = ExampleSection()
        layout.addWidget(self._examples)

        self._mistakes = MistakesCard()
        layout.addWidget(self._mistakes)

        self._exercise = ExerciseCard()
        self._exercise.prevExercise.connect(self.prevExercise.emit)
        self._exercise.nextExercise.connect(self.nextExercise.emit)
        layout.addWidget(self._exercise)

        layout.addStretch(1)

        nav = QHBoxLayout()
        nav.setSpacing(12)
        nav.setContentsMargins(0, 8, 0, 0)
        self._prev = QPushButton("← Previous")
        self._prev.setObjectName("GhostButton")
        self._prev.setFixedHeight(36)
        self._prev.clicked.connect(self.prevLesson.emit)
        self._next = QPushButton("Next →")
        self._next.setObjectName("PrimaryButton")
        self._next.setFixedHeight(36)
        self._next.clicked.connect(self.nextLesson.emit)
        nav.addWidget(self._prev)
        nav.addStretch(1)
        nav.addWidget(self._next)
        layout.addLayout(nav)

        scroll.setWidget(body)
        outer.addWidget(scroll)

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        if self.lesson is not None:
            self._examples.set_examples(list(self.lesson.examples), theme)

    def show_lesson(
        self,
        lesson: Lesson,
        exercise: Exercise | None,
        *,
        exercise_index: int = 0,
        prev_ok: bool = False,
        next_ok: bool = False,
    ) -> None:
        self.lesson = lesson
        self._title.setText(lesson.title)
        intro = lesson.intro
        self._intro.setText(intro)
        self._intro.setVisible(bool(intro))
        self._explanation.set_sections(list(lesson.explanation_sections))
        self._concepts.set_concepts(list(lesson.concepts))
        self._examples.set_examples(list(lesson.examples), self._theme)
        self._mistakes.set_mistakes(list(lesson.common_mistakes))
        total = len(lesson.exercises)
        self._exercise.set_exercise(exercise, index=exercise_index, total=total)
        self._prev.setEnabled(prev_ok)
        self._next.setEnabled(True)
