"""Local progress persistence.

Progress is stored as JSON beside the application so closing and reopening
the app restores completed lessons, drafts, hint usage, and mastery scores.
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


DEFAULT_MASTERY_TOPICS = [
    "variables",
    "collections",
    "loops",
    "functions",
    "classes",
    "composition",
    "inheritance",
    "debugging",
]


@dataclass
class ExerciseProgress:
    completed: bool = False
    attempts: int = 0
    hints_used: int = 0
    draft_code: str = ""
    last_answer: str = ""


@dataclass
class ProgressData:
    completed_lessons: list[str] = field(default_factory=list)
    current_lesson_id: Optional[str] = None
    exercises: dict[str, ExerciseProgress] = field(default_factory=dict)
    mastery: dict[str, float] = field(default_factory=dict)
    mistake_topics: dict[str, int] = field(default_factory=dict)

    def ensure_mastery_defaults(self) -> None:
        for topic in DEFAULT_MASTERY_TOPICS:
            self.mastery.setdefault(topic, 0.0)


class ProgressStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.data = ProgressData()
        self.data.ensure_mastery_defaults()

    def load(self) -> ProgressData:
        if not self.path.exists():
            self.data = ProgressData()
            self.data.ensure_mastery_defaults()
            return self.data

        with self.path.open(encoding="utf-8") as handle:
            raw = json.load(handle)

        exercises: dict[str, ExerciseProgress] = {}
        for exercise_id, payload in raw.get("exercises", {}).items():
            exercises[exercise_id] = ExerciseProgress(
                completed=bool(payload.get("completed", False)),
                attempts=int(payload.get("attempts", 0)),
                hints_used=int(payload.get("hints_used", 0)),
                draft_code=str(payload.get("draft_code", "")),
                last_answer=str(payload.get("last_answer", "")),
            )

        self.data = ProgressData(
            completed_lessons=list(raw.get("completed_lessons", [])),
            current_lesson_id=raw.get("current_lesson_id"),
            exercises=exercises,
            mastery={str(k): float(v) for k, v in raw.get("mastery", {}).items()},
            mistake_topics={str(k): int(v) for k, v in raw.get("mistake_topics", {}).items()},
        )
        self.data.ensure_mastery_defaults()
        return self.data

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "completed_lessons": self.data.completed_lessons,
            "current_lesson_id": self.data.current_lesson_id,
            "exercises": {
                exercise_id: asdict(progress)
                for exercise_id, progress in self.data.exercises.items()
            },
            "mastery": self.data.mastery,
            "mistake_topics": self.data.mistake_topics,
        }
        temporary = self.path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        temporary.replace(self.path)

    def reset(self) -> None:
        self.data = ProgressData()
        self.data.ensure_mastery_defaults()
        self.save()

    def exercise(self, exercise_id: str) -> ExerciseProgress:
        if exercise_id not in self.data.exercises:
            self.data.exercises[exercise_id] = ExerciseProgress()
        return self.data.exercises[exercise_id]

    def mark_exercise_result(
        self,
        exercise_id: str,
        *,
        passed: bool,
        topics: list[str] | None = None,
        answer: str = "",
        code: str = "",
    ) -> None:
        record = self.exercise(exercise_id)
        record.attempts += 1
        if answer:
            record.last_answer = answer
        if code:
            record.draft_code = code
        if passed:
            record.completed = True
            for topic in topics or []:
                self._bump_mastery(topic, 0.15)
        else:
            for topic in topics or []:
                self.data.mistake_topics[topic] = self.data.mistake_topics.get(topic, 0) + 1
                self._bump_mastery(topic, -0.05)

    def use_hint(self, exercise_id: str) -> int:
        record = self.exercise(exercise_id)
        record.hints_used += 1
        return record.hints_used

    def save_draft(self, exercise_id: str, code: str, answer: str | None = None) -> None:
        record = self.exercise(exercise_id)
        record.draft_code = code
        if answer is not None:
            record.last_answer = answer

    def is_exercise_complete(self, exercise_id: str) -> bool:
        return self.exercise(exercise_id).completed

    def is_lesson_complete(self, lesson_id: str, exercise_ids: list[str]) -> bool:
        if not exercise_ids:
            return lesson_id in self.data.completed_lessons
        return all(self.is_exercise_complete(exercise_id) for exercise_id in exercise_ids)

    def refresh_lesson_completion(self, lesson_id: str, exercise_ids: list[str]) -> bool:
        complete = self.is_lesson_complete(lesson_id, exercise_ids)
        if complete and lesson_id not in self.data.completed_lessons:
            self.data.completed_lessons.append(lesson_id)
        elif not complete and lesson_id in self.data.completed_lessons:
            self.data.completed_lessons.remove(lesson_id)
        return complete

    def overall_percent(self, all_exercise_ids: list[str]) -> float:
        if not all_exercise_ids:
            return 0.0
        done = sum(1 for exercise_id in all_exercise_ids if self.is_exercise_complete(exercise_id))
        return 100.0 * done / len(all_exercise_ids)

    def _bump_mastery(self, topic: str, delta: float) -> None:
        current = float(self.data.mastery.get(topic, 0.0))
        updated = max(0.0, min(1.0, current + delta))
        self.data.mastery[topic] = round(updated, 3)

    def snapshot(self) -> dict[str, Any]:
        return deepcopy(
            {
                "completed_lessons": self.data.completed_lessons,
                "current_lesson_id": self.data.current_lesson_id,
                "exercises": {
                    key: asdict(value) for key, value in self.data.exercises.items()
                },
                "mastery": self.data.mastery,
                "mistake_topics": self.data.mistake_topics,
            }
        )
