from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QPushButton, QWidget


class ModeBar(QFrame):
    """Segmented control: Learn · Examples · Practice."""

    modeChanged = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TopBar")  # reuse top bar styling (thin chrome)
        self.setFixedHeight(40)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(6)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._learn = self._make_btn("Learn", "learn")
        self._examples = self._make_btn("Examples", "examples")
        self._practice = self._make_btn("Practice", "practice")
        for b in (self._learn, self._examples, self._practice):
            layout.addWidget(b)
        layout.addStretch(1)
        self.set_mode("learn")

    def _make_btn(self, label: str, mode: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setObjectName("ToolButton")
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self._emit(mode))
        self._group.addButton(btn)
        return btn

    def _emit(self, mode: str) -> None:
        self.modeChanged.emit(mode)

    def set_mode(self, mode: str) -> None:
        mapping = {"learn": self._learn, "examples": self._examples, "practice": self._practice}
        for key, btn in mapping.items():
            btn.blockSignals(True)
            btn.setChecked(key == mode)
            btn.blockSignals(False)
