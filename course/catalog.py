"""Load and order the course curriculum from JSON lesson files.

The catalog is the single source of truth for which lessons exist and the
order they unlock. The GUI only renders whatever the catalog returns.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from course.lesson import Lesson, Section, lesson_from_dict


class CourseCatalog:
    def __init__(self, lessons_dir: Path) -> None:
        self.lessons_dir = Path(lessons_dir)
        self._lessons: list[Lesson] = []
        self._by_id: dict[str, Lesson] = {}
        self._sections: list[Section] = []

    def load(self) -> None:
        paths = sorted(self.lessons_dir.glob("*.json"))
        lessons: list[Lesson] = []
        for path in paths:
            with path.open(encoding="utf-8") as handle:
                data = json.load(handle)
            lessons.append(lesson_from_dict(data))

        lessons.sort(key=lambda lesson: (lesson.section_order, lesson.order, lesson.id))
        self._lessons = lessons
        self._by_id = {lesson.id: lesson for lesson in lessons}
        self._sections = self._build_sections(lessons)

    @staticmethod
    def _build_sections(lessons: list[Lesson]) -> list[Section]:
        sections: dict[str, Section] = {}
        ordered: list[Section] = []
        for lesson in lessons:
            if lesson.section not in sections:
                section = Section(name=lesson.section, order=lesson.section_order)
                sections[lesson.section] = section
                ordered.append(section)
            sections[lesson.section].lessons.append(lesson)
        ordered.sort(key=lambda section: section.order)
        return ordered

    @property
    def lessons(self) -> list[Lesson]:
        return list(self._lessons)

    @property
    def sections(self) -> list[Section]:
        return list(self._sections)

    def get(self, lesson_id: str) -> Optional[Lesson]:
        return self._by_id.get(lesson_id)

    def index_of(self, lesson_id: str) -> int:
        for index, lesson in enumerate(self._lessons):
            if lesson.id == lesson_id:
                return index
        return -1

    def previous(self, lesson_id: str) -> Optional[Lesson]:
        index = self.index_of(lesson_id)
        if index > 0:
            return self._lessons[index - 1]
        return None

    def next(self, lesson_id: str) -> Optional[Lesson]:
        index = self.index_of(lesson_id)
        if 0 <= index < len(self._lessons) - 1:
            return self._lessons[index + 1]
        return None

    def first(self) -> Optional[Lesson]:
        return self._lessons[0] if self._lessons else None
