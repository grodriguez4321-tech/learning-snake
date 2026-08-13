"""Left sidebar: navigation + lesson list."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
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
        self.setFixedWidth(260)
        self._catalog = catalog
        self._controller = controller
        self._nav_buttons: dict[str, QPushButton] = {}
        self._lesson_buttons: dict[str, QPushButton] = {}
        self._active_nav = "lessons"
        self._active_lesson_id: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 16, 12, 12)
        root.setSpacing(8)

        title_row = QHBoxLayout()
        brand = QLabel("Python Course")
        brand.setObjectName("BrandTitle")
        title_row.addWidget(brand)
        title_row.addStretch(1)
        root.addLayout(title_row)

        for key, label, icon in NAV_ITEMS:
            btn = QPushButton(f"  {icon}   {label}")
            btn.setObjectName("NavItem")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, k=key: self._on_nav(k))
            self._nav_buttons[key] = btn
            root.addWidget(btn)

        heading = QLabel("LESSONS")
        heading.setObjectName("SectionHeading")
        heading.setContentsMargins(8, 16, 0, 4)
        root.addWidget(heading)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._lesson_host = QWidget()
        self._lesson_layout = QVBoxLayout(self._lesson_host)
        self._lesson_layout.setContentsMargins(0, 0, 0, 0)
        self._lesson_layout.setSpacing(2)
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

        while self._lesson_layout.count() > 1:
            item = self._lesson_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._lesson_buttons.clear()

        for index, lesson in enumerate(self._catalog.lessons, start=1):
            unlocked = self._controller.is_unlocked(lesson)
            completed = self._controller.progress.is_lesson_complete(
                lesson.id, lesson.exercise_ids
            )
            if completed:
                icon = "✓"
            elif not unlocked:
                icon = "🔒"
            else:
                icon = "○"
            label = f"{icon}  {index}. {lesson.title}"
            btn = QPushButton(label)
            btn.setObjectName("LessonItem")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setEnabled(unlocked)
            btn.setMinimumHeight(36)
            btn.setToolTip(
                lesson.title if unlocked else "Complete the previous lesson to unlock"
            )
            lid = lesson.id
            btn.clicked.connect(lambda checked=False, i=lid: self._on_lesson(i))
            self._lesson_buttons[lid] = btn
            self._lesson_layout.insertWidget(self._lesson_layout.count() - 1, btn)

        if self._active_lesson_id:
            self.set_active_lesson(self._active_lesson_id)

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
        for lid, btn in self._lesson_buttons.items():
            btn.setChecked(lid == lesson_id)
