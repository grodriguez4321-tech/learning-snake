"""Left sidebar: navigation + lesson list."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from course.catalog import CourseCatalog
from engine.course_controller import CourseController


NAV_ITEMS = (
    ("dashboard", "Dashboard", "⌂"),
    ("lessons", "Lessons", "☰"),
    ("playground", "Playground", "▷"),
    ("progress", "Progress", "◉"),
    ("settings", "Settings", "⚙"),
)


class LessonRow(QFrame):
    """Single-line lesson row — avoids QPushButton emoji/wrap painting bugs."""

    clicked = Signal(str)

    def __init__(self, lesson_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.lesson_id = lesson_id
        self.setObjectName("LessonRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(34)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._active = False
        self._enabled = True

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)

        self._icon = QLabel("○")
        self._icon.setObjectName("LessonRowIcon")
        self._icon.setFixedWidth(16)
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._icon)

        self._label = QLabel()
        self._label.setObjectName("LessonRowLabel")
        self._label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        layout.addWidget(self._label, stretch=1)

    def set_row(self, *, icon: str, text: str, enabled: bool, active: bool) -> None:
        self._enabled = enabled
        self._active = active
        self._icon.setText(icon)
        self.setEnabled(enabled)
        self.setProperty("active", "true" if active else "false")
        self.setProperty("locked", "true" if not enabled else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        # Elide inside available width (~sidebar 260 - padding - icon)
        metrics = QFontMetrics(self._label.font())
        self._label.setText(metrics.elidedText(text, Qt.TextElideMode.ElideRight, 190))
        self.setToolTip(text if enabled else f"Locked — {text}")

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if self._enabled and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.lesson_id)
        super().mousePressEvent(event)


class Sidebar(QFrame):
    navChanged = Signal(str)
    lessonSelected = Signal(str)

    def __init__(
        self,
        catalog: CourseCatalog,
        controller: CourseController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(256)
        self._catalog = catalog
        self._controller = controller
        self._nav_buttons: dict[str, QPushButton] = {}
        self._lesson_rows: dict[str, LessonRow] = {}
        self._active_nav = "lessons"
        self._active_lesson_id: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 18, 14, 14)
        root.setSpacing(4)

        brand = QLabel("Python Course")
        brand.setObjectName("BrandTitle")
        brand.setContentsMargins(6, 0, 0, 8)
        root.addWidget(brand)

        for key, label, icon in NAV_ITEMS:
            btn = QPushButton(f"  {icon}   {label}")
            btn.setObjectName("NavItem")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setFixedHeight(36)
            btn.clicked.connect(lambda checked=False, k=key: self._on_nav(k))
            self._nav_buttons[key] = btn
            root.addWidget(btn)

        heading = QLabel("LESSONS")
        heading.setObjectName("SectionHeading")
        heading.setContentsMargins(8, 18, 0, 6)
        root.addWidget(heading)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._lesson_host = QWidget()
        self._lesson_layout = QVBoxLayout(self._lesson_host)
        self._lesson_layout.setContentsMargins(0, 0, 0, 0)
        self._lesson_layout.setSpacing(3)
        self._lesson_layout.addStretch(1)
        scroll.setWidget(self._lesson_host)
        root.addWidget(scroll, stretch=1)

        footer = QFrame()
        footer.setObjectName("SidebarFooter")
        fl = QVBoxLayout(footer)
        fl.setContentsMargins(12, 12, 12, 12)
        tip = QLabel("Ready to learn Python?\nWork through lessons at your own pace.")
        tip.setWordWrap(True)
        tip.setObjectName("MutedLabel")
        fl.addWidget(tip)
        root.addWidget(footer)

        self.refresh_lessons()
        self.set_active_nav("lessons")

    def _on_nav(self, key: str) -> None:
        self.set_active_nav(key)
        self.navChanged.emit(key)

    def set_active_nav(self, key: str) -> None:
        self._active_nav = key
        for k, btn in self._nav_buttons.items():
            btn.setChecked(k == key)

    def refresh_lessons(self, selected_lesson_id: str | None = None) -> None:
        if selected_lesson_id is not None:
            self._active_lesson_id = selected_lesson_id

        # Immediate remove to avoid ghost-overlap with deleteLater.
        while self._lesson_layout.count() > 1:
            item = self._lesson_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.hide()
                w.setParent(None)
                w.deleteLater()
        self._lesson_rows.clear()

        for index, lesson in enumerate(self._catalog.lessons, start=1):
            unlocked = self._controller.is_unlocked(lesson)
            completed = self._controller.progress.is_lesson_complete(
                lesson.id, lesson.exercise_ids
            )
            if completed:
                icon = "✓"
            elif not unlocked:
                icon = "⊘"
            else:
                icon = "○"
            row = LessonRow(lesson.id)
            row.set_row(
                icon=icon,
                text=f"{index}. {lesson.title}",
                enabled=unlocked,
                active=lesson.id == self._active_lesson_id,
            )
            row.clicked.connect(self._on_lesson)
            self._lesson_rows[lesson.id] = row
            self._lesson_layout.insertWidget(self._lesson_layout.count() - 1, row)

    def _on_lesson(self, lesson_id: str) -> None:
        lesson = self._catalog.get(lesson_id)
        if lesson is None or not self._controller.is_unlocked(lesson):
            return
        self.set_active_lesson(lesson_id)
        self.set_active_nav("lessons")
        self.navChanged.emit("lessons")
        self.lessonSelected.emit(lesson_id)

    def set_active_lesson(self, lesson_id: str | None) -> None:
        self._active_lesson_id = lesson_id
        for lid, row in self._lesson_rows.items():
            active = lid == lesson_id
            row.setProperty("active", "true" if active else "false")
            row.style().unpolish(row)
            row.style().polish(row)
            row.update()
            # keep internal flag in sync for click gating
            row._active = active  # noqa: SLF001
