"""Lesson content cards and left instructional column."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from course.exercise import Exercise
from course.lesson import CodeExample, Lesson


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _mono_font(point_size: int = 12) -> QFont:
    for family in ("Cascadia Code", "Consolas", "Courier New", "monospace"):
        font = QFont(family, point_size)
        font.setStyleHint(QFont.StyleHint.Monospace)
        return font
    return QFont("monospace", point_size)


def _intro_from_content(content: str) -> str:
    """First paragraph of lesson content as a concise description."""
    text = (content or "").strip()
    if not text:
        return ""
    parts = text.split("\n\n")
    return parts[0].replace("\n", " ").strip()


class ConceptCard(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ConceptCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

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
        lines = "".join(f"<li style='margin:4px 0;'>{_escape(c)}</li>" for c in concepts)
        self._body.setText(f"<ul style='margin:0; padding-left:18px;'>{lines}</ul>")


class ExampleCard(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        title = QLabel("Examples")
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        self._host = QVBoxLayout()
        self._host.setSpacing(12)
        layout.addLayout(self._host)

    def set_examples(self, examples: list[CodeExample]) -> None:
        while self._host.count():
            item = self._host.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        if not examples:
            empty = QLabel("No examples for this lesson.")
            empty.setObjectName("MutedLabel")
            self._host.addWidget(empty)
            return

        for ex in examples:
            block = QFrame()
            block.setObjectName("CodeBlock")
            bl = QVBoxLayout(block)
            bl.setContentsMargins(12, 10, 12, 10)
            bl.setSpacing(6)
            title = QLabel(ex.title or "Example")
            title.setObjectName("MutedLabel")
            bl.addWidget(title)
            code = QTextEdit()
            code.setObjectName("ExampleCode")
            code.setReadOnly(True)
            code.setPlainText(ex.code or "")
            code.setFont(_mono_font(12))
            doc_h = int(code.document().size().height()) + 28
            code.setFixedHeight(min(200, max(72, doc_h)))
            code.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            bl.addWidget(code)
            expl = (ex.explanation or "").strip()
            if expl:
                el = QLabel(expl)
                el.setWordWrap(True)
                el.setObjectName("MutedLabel")
                bl.addWidget(el)
            self._host.addWidget(block)


class ExerciseCard(QFrame):
    prevExercise = Signal()
    nextExercise = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
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
        self._prev_ex.setObjectName("SecondaryButton")
        self._prev_ex.setFixedWidth(36)
        self._prev_ex.clicked.connect(self.prevExercise.emit)
        self._next_ex = QPushButton("›")
        self._next_ex.setObjectName("SecondaryButton")
        self._next_ex.setFixedWidth(36)
        self._next_ex.clicked.connect(self.nextExercise.emit)
        header.addWidget(self._prev_ex)
        header.addWidget(self._next_ex)
        layout.addLayout(header)

        self._title = QLabel()
        self._title.setObjectName("CardTitle")
        layout.addWidget(self._title)

        self._prompt = QLabel()
        self._prompt.setWordWrap(True)
        self._prompt.setObjectName("BodyText")
        self._prompt.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self._prompt)

        self._predict_label = QLabel("Code to predict")
        self._predict_label.setObjectName("MutedLabel")
        layout.addWidget(self._predict_label)

        self._predict = QTextEdit()
        self._predict.setObjectName("ExampleCode")
        self._predict.setReadOnly(True)
        self._predict.setMaximumHeight(100)
        self._predict.setFont(_mono_font(11))
        layout.addWidget(self._predict)

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
            self._predict.setPlainText(exercise.code_to_predict)
        else:
            self._predict_label.setVisible(False)
            self._predict.setVisible(False)

        tips: list[str] = []
        if exercise.is_code_exercise:
            tips.append("Write your solution in the editor on the right.")
            tips.append("Use Run Code to try it, then Check Exercise to grade.")
        elif exercise.uses_free_text_answer or exercise.is_choice_exercise:
            tips.append("Enter your answer in the answer box above the action buttons.")
            tips.append("Then click Check Exercise.")
        if tips:
            items = "".join(f"<li style='margin:4px 0;'>{_escape(t)}</li>" for t in tips)
            self._instructions.setText(
                f"<b>Instructions</b><ul style='margin:6px 0; padding-left:18px;'>{items}</ul>"
            )
        else:
            self._instructions.setText("")


class LessonContent(QWidget):
    """Left instructional column for a lesson."""

    prevLesson = Signal()
    nextLesson = Signal()
    prevExercise = Signal()
    nextExercise = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.lesson: Lesson | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(24, 20, 20, 16)
        layout.setSpacing(16)

        self._title = QLabel()
        self._title.setObjectName("LessonTitle")
        self._title.setWordWrap(True)
        layout.addWidget(self._title)

        self._intro = QLabel()
        self._intro.setWordWrap(True)
        self._intro.setObjectName("BodyText")
        layout.addWidget(self._intro)

        self._concepts = ConceptCard()
        layout.addWidget(self._concepts)

        self._examples = ExampleCard()
        layout.addWidget(self._examples)

        self._exercise = ExerciseCard()
        self._exercise.prevExercise.connect(self.prevExercise.emit)
        self._exercise.nextExercise.connect(self.nextExercise.emit)
        layout.addWidget(self._exercise)

        layout.addStretch(1)

        nav = QHBoxLayout()
        nav.setSpacing(12)
        self._prev = QPushButton("← Previous")
        self._prev.setObjectName("SecondaryButton")
        self._prev.clicked.connect(self.prevLesson.emit)
        self._next = QPushButton("Next →")
        self._next.setObjectName("PrimaryButton")
        self._next.clicked.connect(self.nextLesson.emit)
        nav.addWidget(self._prev)
        nav.addStretch(1)
        nav.addWidget(self._next)
        layout.addLayout(nav)

        scroll.setWidget(body)
        outer.addWidget(scroll)

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
        self._intro.setText(_intro_from_content(lesson.content))
        self._concepts.set_concepts(list(lesson.concepts))
        self._examples.set_examples(list(lesson.examples))
        total = len(lesson.exercises)
        self._exercise.set_exercise(exercise, index=exercise_index, total=total)
        self._prev.setEnabled(prev_ok)
        self._next.setEnabled(True)  # always clickable; lock handled by controller
