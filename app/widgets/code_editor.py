"""IDE-style code editor: line numbers, Python highlighting, Tab=4 spaces."""

from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextFormat,
)
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

from app.theme import Theme


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document, theme: Theme) -> None:
        super().__init__(document)
        self._theme = theme
        self._rules: list[tuple] = []
        self._rebuild()

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._rebuild()
        self.rehighlight()

    def _fmt(self, color: str, bold: bool = False) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(700)
        return fmt

    def _rebuild(self) -> None:
        import re

        t = self._theme
        keyword = self._fmt("#C586C0" if t.name == "dark" else "#AF00DB", bold=True)
        builtin = self._fmt("#DCDCAA" if t.name == "dark" else "#795E26")
        string = self._fmt("#CE9178" if t.name == "dark" else "#A31515")
        comment = self._fmt("#6A9955" if t.name == "dark" else "#008000")
        number = self._fmt("#B5CEA8" if t.name == "dark" else "#098658")
        self._rules = [
            (re.compile(r"\b(?:False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b"), keyword),
            (re.compile(r"\b(?:print|len|range|int|str|float|list|dict|set|tuple|bool|type|isinstance|enumerate|zip|map|min|max|sum|open|input)\b"), builtin),
            (re.compile(r"#[^\n]*"), comment),
            (re.compile(r"\"\"\".*?\"\"\"|'''.*?'''", re.DOTALL), string),
            (re.compile(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'"), string),
            (re.compile(r"\b\d+(?:\.\d+)?\b"), number),
        ]

    def highlightBlock(self, text: str) -> None:  # noqa: N802
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)


class LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditorWidget") -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:  # noqa: N802
        self._editor.paint_line_numbers(event)


class CodeEditorWidget(QPlainTextEdit):
    runRequested = Signal()

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CodeEditor")
        self._theme = theme
        font = QFont("Cascadia Code")
        if not font.exactMatch():
            font = QFont("Consolas")
        font.setStyleHint(QFont.Monospace)
        font.setPointSize(13)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setPlaceholderText("# Write your Python code here")

        self._line_area = LineNumberArea(self)
        self._highlighter = PythonHighlighter(self.document(), theme)

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        self._update_line_number_area_width(0)
        self._highlight_current_line()
        self.apply_theme(theme)

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._highlighter.set_theme(theme)
        self.setStyleSheet(
            f"""
            QPlainTextEdit#CodeEditor {{
                background-color: {theme.bg_editor};
                color: {theme.text};
                border: none;
                padding: 4px;
                selection-background-color: {theme.select};
            }}
            """
        )
        self._highlight_current_line()
        self._line_area.update()

    def line_number_area_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        return 16 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_number_area_width(self, _count: int = 0) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self._line_area.scroll(0, dy)
        else:
            self._line_area.update(0, rect.y(), self._line_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def paint_line_numbers(self, event) -> None:
        painter = QPainter(self._line_area)
        painter.fillRect(event.rect(), QColor(self._theme.bg_card))
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor(self._theme.text_dim))
                painter.drawText(
                    0,
                    top,
                    self._line_area.width() - 8,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(block_number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def _highlight_current_line(self) -> None:
        extra = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(self._theme.bg_elevated)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra.append(selection)
        self.setExtraSelections(extra)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key_Tab:
            self.insertPlainText("    ")
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and event.modifiers() & Qt.ControlModifier:
            self.runRequested.emit()
            return
        super().keyPressEvent(event)

    def get_text(self) -> str:
        return self.toPlainText()

    def set_text(self, text: str) -> None:
        self.setPlainText(text)
