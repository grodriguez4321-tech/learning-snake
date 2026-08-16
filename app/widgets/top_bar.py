"""Top application bar: breadcrumb, panel toggles, progress, theme."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget

from app.widgets.progress_widget import ProgressWidget


class TopBar(QFrame):
    themeChanged = Signal(str)
    toggleSidebarClicked = Signal()
    toggleEditorClicked = Signal()
    saveClicked = Signal()
    resetProgressClicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setFixedHeight(48)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 12, 0)
        layout.setSpacing(8)

        self._breadcrumb = QLabel("Python Fundamentals")
        self._breadcrumb.setObjectName("Breadcrumb")
        self._breadcrumb.setWordWrap(False)
        self._breadcrumb.setMinimumWidth(0)
        self._breadcrumb.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        layout.addWidget(self._breadcrumb, stretch=1)
        self._full_breadcrumb = "Python Fundamentals"

        self._progress = ProgressWidget()
        layout.addWidget(self._progress)

        self._sidebar_btn = self._tool_button("Sidebar", "Ctrl+B")
        self._sidebar_btn.setCheckable(True)
        self._sidebar_btn.setChecked(True)
        self._sidebar_btn.clicked.connect(self.toggleSidebarClicked.emit)
        layout.addWidget(self._sidebar_btn)

        self._editor_btn = self._tool_button("Editor", "Ctrl+J")
        self._editor_btn.setCheckable(True)
        self._editor_btn.setChecked(True)
        self._editor_btn.clicked.connect(self.toggleEditorClicked.emit)
        layout.addWidget(self._editor_btn)

        self._save_btn = self._tool_button("Save", "Ctrl+S")
        self._save_btn.clicked.connect(self.saveClicked.emit)
        layout.addWidget(self._save_btn)

        self._reset_btn = self._tool_button("Reset…", None)
        self._reset_btn.setToolTip("Reset all progress")
        self._reset_btn.clicked.connect(self.resetProgressClicked.emit)
        layout.addWidget(self._reset_btn)

        self._theme_btn = self._tool_button("Theme · Dark", "Ctrl+Shift+D")
        self._theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self._theme_btn)
        self._theme = "dark"

    @staticmethod
    def _tool_button(label: str, shortcut: str | None) -> QPushButton:
        btn = QPushButton(label)
        btn.setObjectName("ToolButton")
        btn.setFixedHeight(30)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if shortcut:
            btn.setToolTip(f"{label} ({shortcut})")
        return btn

    def set_breadcrumb(self, text: str) -> None:
        self._full_breadcrumb = text
        self._breadcrumb.setToolTip(text)
        self._apply_breadcrumb_elide()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._apply_breadcrumb_elide()

    def _apply_breadcrumb_elide(self) -> None:
        text = self._full_breadcrumb
        width = self._breadcrumb.width()
        if width <= 1:
            layout = self.layout()
            margins = layout.contentsMargins() if layout is not None else None
            margin_w = (margins.left() + margins.right()) if margins is not None else 28
            spacing = layout.spacing() if layout is not None else 8
            trailing = (
                self._progress.width()
                + self._sidebar_btn.width()
                + self._editor_btn.width()
                + self._save_btn.width()
                + self._reset_btn.width()
                + self._theme_btn.width()
                + spacing * 5
            )
            width = max(0, self.width() - margin_w - trailing)
        if width <= 1:
            self._breadcrumb.setText("")
            return
        metrics = QFontMetrics(self._breadcrumb.font())
        self._breadcrumb.setText(
            metrics.elidedText(text, Qt.TextElideMode.ElideRight, width)
        )

    def set_progress(self, completed: int, total: int) -> None:
        self._progress.set_progress(completed, total)

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        label = "Dark" if theme == "dark" else "Light"
        self._theme_btn.setText(f"Theme · {label}")
        self._theme_btn.setToolTip(f"Theme · {label} (Ctrl+Shift+D)")

    def set_sidebar_visible(self, visible: bool) -> None:
        self._sidebar_btn.blockSignals(True)
        self._sidebar_btn.setChecked(visible)
        self._sidebar_btn.blockSignals(False)

    def set_editor_visible(self, visible: bool) -> None:
        self._editor_btn.blockSignals(True)
        self._editor_btn.setChecked(visible)
        self._editor_btn.blockSignals(False)

    def set_editor_enabled(self, enabled: bool) -> None:
        self._editor_btn.setEnabled(enabled)

    def flash_saved(self) -> None:
        self._save_btn.setText("Saved")
        from PySide6.QtCore import QTimer

        QTimer.singleShot(1200, lambda: self._save_btn.setText("Save"))

    def _toggle_theme(self) -> None:
        nxt = "light" if self._theme == "dark" else "dark"
        self.set_theme(nxt)
        self.themeChanged.emit(nxt)
