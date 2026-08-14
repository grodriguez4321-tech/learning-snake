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
class ContentSection:
    heading: str
    body: str


def _looks_like_heading(line: str) -> bool:
    text = line.strip()
    if not text or len(text) > 60:
        return False
    if text.endswith("?"):
        return True
    if any(char in text for char in ".{}()[]"):
        return False
    return True


def parse_lesson_content(content: str) -> tuple[str, list[ContentSection]]:
    """Split lesson content into a lead intro plus titled explanation sections."""
    text = (content or "").strip()
    if not text:
        return "", []

    blocks = [part.strip() for part in text.split("\n\n") if part.strip()]
    intro = ""
    sections: list[ContentSection] = []

    for index, block in enumerate(blocks):
        lines = [line.rstrip() for line in block.split("\n") if line.strip() or line.startswith(" ")]
        if not lines:
            continue
        first = lines[0].strip()
        rest = "\n".join(lines[1:]).strip()
        if _looks_like_heading(first) and rest:
            heading = first
            body = rest
            if index == 0 and heading.lower().startswith("what problem"):
                intro = body
                continue
            sections.append(ContentSection(heading=heading, body=body))
            continue
        if index == 0 and not intro:
            intro = block.replace("\n", " ")
        else:
            sections.append(ContentSection(heading="", body=block))

    return intro, sections


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

    @property
    def intro(self) -> str:
        lead, _ = parse_lesson_content(self.content)
        return lead

    @property
    def explanation_sections(self) -> list[ContentSection]:
        _, sections = parse_lesson_content(self.content)
        return sections


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
