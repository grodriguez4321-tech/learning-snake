"""Local progress persistence.

Progress is stored as JSON beside the application so closing and reopening
the app restores completed lessons, drafts, hint usage, and mastery scores.

Corrupt or malformed files must never crash startup: they are quarantined and
replaced with a fresh ProgressData, with a warning retained for the UI.
"""

from __future__ import annotations

import json
import time
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
        self.load_warning: Optional[str] = None
        self.recovered_from_corrupt: bool = False

    def load(self) -> ProgressData:
        self.load_warning = None
        self.recovered_from_corrupt = False

        if not self.path.exists():
            self.data = ProgressData()
            self.data.ensure_mastery_defaults()
            return self.data

        try:
            text = self.path.read_text(encoding="utf-8")
        except OSError as exc:
            self._recover(f"Could not read progress file ({exc}).")
            return self.data

        if not text.strip():
            self._recover("Progress file was empty.")
            return self.data

        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            self._quarantine_and_recover(f"Progress JSON was invalid ({exc}).")
            return self.data

        if not isinstance(raw, dict):
            self._quarantine_and_recover("Progress JSON root was not an object.")
            return self.data

        try:
            self.data = self._parse(raw)
        except Exception as exc:  # noqa: BLE001 - never crash on progress shape bugs
            self._quarantine_and_recover(f"Progress data was malformed ({exc}).")
            return self.data

        self.data.ensure_mastery_defaults()
        return self.data

    def _parse(self, raw: dict[str, Any]) -> ProgressData:
        exercises: dict[str, ExerciseProgress] = {}
        raw_exercises = raw.get("exercises", {})
        if raw_exercises is None:
            raw_exercises = {}
        if not isinstance(raw_exercises, dict):
            raise ValueError("exercises must be an object")

        for exercise_id, payload in raw_exercises.items():
            if not isinstance(payload, dict):
                continue
            try:
                exercises[str(exercise_id)] = ExerciseProgress(
                    completed=bool(payload.get("completed", False)),
                    attempts=int(payload.get("attempts", 0) or 0),
                    hints_used=int(payload.get("hints_used", 0) or 0),
                    draft_code=str(payload.get("draft_code", "") or ""),
                    last_answer=str(payload.get("last_answer", "") or ""),
                )
            except (TypeError, ValueError):
                continue

        completed_raw = raw.get("completed_lessons", [])
        if completed_raw is None:
            completed_raw = []
        if not isinstance(completed_raw, list):
            completed_raw = []

        mastery_raw = raw.get("mastery", {})
        if not isinstance(mastery_raw, dict):
            mastery_raw = {}
        mastery: dict[str, float] = {}
        for key, value in mastery_raw.items():
            try:
                mastery[str(key)] = float(value)
            except (TypeError, ValueError):
                continue

        mistakes_raw = raw.get("mistake_topics", {})
        if not isinstance(mistakes_raw, dict):
            mistakes_raw = {}
        mistakes: dict[str, int] = {}
        for key, value in mistakes_raw.items():
            try:
                mistakes[str(key)] = int(value)
            except (TypeError, ValueError):
                continue

        current = raw.get("current_lesson_id")
        if current is not None:
            current = str(current)

        return ProgressData(
            completed_lessons=[str(item) for item in completed_raw],
            current_lesson_id=current,
            exercises=exercises,
            mastery=mastery,
            mistake_topics=mistakes,
        )

    def _quarantine_and_recover(self, reason: str) -> None:
        backup = self._quarantine_corrupt_file()
        detail = reason
        if backup is not None:
            detail = f"{reason} A backup was saved as {backup.name}."
        self._recover(detail)

    def _recover(self, reason: str) -> None:
        self.data = ProgressData()
        self.data.ensure_mastery_defaults()
        self.recovered_from_corrupt = True
        self.load_warning = (
            f"{reason} Starting with a fresh progress file. "
            "Previous completion state may have been lost."
        )

    def _quarantine_corrupt_file(self) -> Optional[Path]:
        if not self.path.exists():
            return None
        stamp = time.strftime("%Y%m%d-%H%M%S")
        backup = self.path.with_name(f"{self.path.name}.corrupt-{stamp}")
        try:
            self.path.replace(backup)
            return backup
        except OSError:
            try:
                backup.write_bytes(self.path.read_bytes())
                return backup
            except OSError:
                return None

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
        self.load_warning = None
        self.recovered_from_corrupt = False
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
