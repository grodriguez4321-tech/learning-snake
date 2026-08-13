"""Lesson and section data models.

Lessons are loaded from JSON files under course/lessons/ so the GUI never
hardcodes curriculum content. Adding a lesson means dropping in a new JSON
file and listing it in the catalog — no UI changes required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from course.exercise import Exercise, exercise_from_dict


@dataclass
class CodeExample:
    title: str
    code: str
    explanation: str = ""


@dataclass
class Lesson:
    id: str
    section: str
    title: str
    content: str
    order: int = 0
    section_order: int = 0
    topics: list[str] = field(default_factory=list)
    examples: list[CodeExample] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)
    exercises: list[Exercise] = field(default_factory=list)
    common_mistakes: list[str] = field(default_factory=list)

    @property
    def exercise_ids(self) -> list[str]:
        return [ex.id for ex in self.exercises]


def lesson_from_dict(data: dict[str, Any]) -> Lesson:
    examples = [
        CodeExample(
            title=item.get("title", "Example"),
            code=item.get("code", ""),
            explanation=item.get("explanation", ""),
        )
        for item in data.get("examples", [])
    ]
    exercises = []
    lesson_modules = list(data.get("allowed_modules", []))
    for item in data.get("exercises", []):
        exercise = exercise_from_dict(item)
        if not exercise.allowed_modules and lesson_modules:
            exercise.allowed_modules = list(lesson_modules)
        exercises.append(exercise)
    return Lesson(
        id=data["id"],
        section=data["section"],
        title=data["title"],
        content=data.get("content", ""),
        order=int(data.get("order", 0)),
        section_order=int(data.get("section_order", 0)),
        topics=list(data.get("topics", [])),
        examples=examples,
        concepts=list(data.get("concepts", [])),
        exercises=exercises,
        common_mistakes=list(data.get("common_mistakes", [])),
    )


@dataclass
class Section:
    name: str
    order: int
    lessons: list[Lesson] = field(default_factory=list)

    @property
    def lesson_count(self) -> int:
        return len(self.lessons)
