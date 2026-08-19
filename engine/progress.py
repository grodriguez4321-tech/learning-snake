"""Local progress persistence.

Progress is stored as JSON beside the application so closing and reopening
the app restores completed lessons, drafts, hint usage, and mastery scores.

Corrupt or malformed files must never crash startup: they are quarantined and
replaced with a fresh ProgressData, with a warning retained for the UI.

Curriculum versioning
---------------------
``curriculum_version`` marks which curriculum a progress file matches.

Basilisk Curriculum V2 (version 2) reuses Phase 1 exercise IDs while changing
their meaning. Loading an older (or unversioned) file therefore:

* preserves mastery scores and mistake topic counts
* archives the raw file beside the progress path
* clears Phase 1 lesson completions and Phase 1 exercise records (including
  drafts), so old code never appears inside an unrelated new exercise
* requires Phase 1 to be retaken; later lesson IDs (9+) are left intact when
  present
* stamps the saved file with the current curriculum version
"""

from __future__ import annotations

import json
import time
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


CURRENT_CURRICULUM_VERSION = 3

# Lesson IDs rewritten in Basilisk Curriculum V2 (same IDs, new exercises).
PHASE1_REWRITTEN_LESSON_IDS = frozenset(
    {
        "fundamentals_01_print",
        "fundamentals_02_variables",
        "fundamentals_03_fstrings",
        "decisions_01_conditionals",
        "collections_01_lists",
        "collections_02_append",
        "collections_03_loops",
        "functions_01_basics",
    }
)

PHASE1_EXERCISE_PREFIXES = (
    "fundamentals_01_",
    "fundamentals_02_",
    "fundamentals_03_",
    "decisions_01_",
    "collections_01_",
    "collections_02_",
    "collections_03_",
    "functions_01_",
)

# Stable lesson IDs for Basilisk Curriculum V3.2 Production Core.
V32_LESSON_IDS = frozenset(
    {
        "fundamentals_01_print",
        "fundamentals_02_variables",
        "fundamentals_03_fstrings",
        "decisions_01_conditionals",
        "collections_01_lists",
        "collections_02_append",
        "collections_03_loops",
        "functions_01_basics",
        "decisions_09_elif",
        "decisions_10_boolean_logic",
        "collections_11_len_range",
        "collections_12_list_methods",
        "collections_13_dictionaries",
        "collections_14_dict_iteration",
        "collections_15_while",
        "functions_16_parameters",
        "functions_17_defaults",
        "functions_18_returning_data",
        "collections_19_nested_data",
        "functions_20_scope",
        "strings_21_methods",
        "errors_22_tracebacks",
        "errors_23_logic_debugging",
        "data_24_shared_references",
        "oop_25_classes_objects",
        "oop_26_init_self",
        "oop_27_methods",
        "oop_28_composition",
    }
)

def _v32_exercise_prefixes() -> tuple[str, ...]:
    prefixes: set[str] = set()
    for lid in V32_LESSON_IDS:
        parts = lid.split("_")
        if len(parts) >= 2:
            prefixes.add(f"{parts[0]}_{parts[1]}_")
    return tuple(sorted(prefixes))

V32_EXERCISE_PREFIXES = _v32_exercise_prefixes()


DEFAULT_MASTERY_TOPICS = [
    "print",
    "variables",
    "strings",
    "conditionals",
    "collections",
    "loops",
    "functions",
    "classes",
    "composition",
    "inheritance",
    "debugging",
]


def is_phase1_rewritten_exercise(exercise_id: str) -> bool:
    return any(str(exercise_id).startswith(prefix) for prefix in PHASE1_EXERCISE_PREFIXES)

def is_v32_exercise(exercise_id: str) -> bool:
    return any(str(exercise_id).startswith(prefix) for prefix in V32_EXERCISE_PREFIXES)


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
    curriculum_version: int = CURRENT_CURRICULUM_VERSION

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
        self.migrated_from_legacy: bool = False

    def load(self) -> ProgressData:
        self.load_warning = None
        self.recovered_from_corrupt = False
        self.migrated_from_legacy = False

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
        if self.migrated_from_legacy:
            # Persist the migrated shape so drafts do not reappear after quit.
            try:
                self.save()
            except OSError:
                pass
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

        try:
            version = int(raw.get("curriculum_version") or 0)
        except (TypeError, ValueError):
            version = 0

        data = ProgressData(
            completed_lessons=[str(item) for item in completed_raw],
            current_lesson_id=current,
            exercises=exercises,
            mastery=mastery,
            mistake_topics=mistakes,
            curriculum_version=version if version > 0 else 0,
        )

        # Stepwise migrations to preserve older test expectations and archive names.
        source_version = data.curriculum_version
        if source_version < 2:
            self._migrate_to_v2(data, raw)
            source_version = 2
        if source_version < 3:
            self._migrate_to_v32(data, raw)
            source_version = 3
        data.curriculum_version = CURRENT_CURRICULUM_VERSION

        return data

    def _migrate_to_v2(self, data: ProgressData, raw: dict[str, Any]) -> None:
        """Upgrade pre-V2 progress without silently mixing old drafts into new exercises."""
        archive = self._archive_legacy_file(raw)
        cleared_exercises = [
            exercise_id
            for exercise_id in list(data.exercises)
            if is_phase1_rewritten_exercise(exercise_id)
        ]
        for exercise_id in cleared_exercises:
            del data.exercises[exercise_id]

        data.completed_lessons = [
            lesson_id
            for lesson_id in data.completed_lessons
            if lesson_id not in PHASE1_REWRITTEN_LESSON_IDS
        ]

        if (
            data.current_lesson_id is not None
            and data.current_lesson_id in PHASE1_REWRITTEN_LESSON_IDS
        ):
            data.current_lesson_id = None

        data.curriculum_version = 2
        self.migrated_from_legacy = True

        archive_note = f" A backup was saved as {archive.name}." if archive else ""
        self.load_warning = (
            "Basilisk Curriculum V2 changed Phase 1 exercises while keeping the "
            "same exercise IDs. Prior Phase 1 completions and drafts were cleared "
            "so old solutions are not shown inside the new exercises. Mastery "
            "scores were kept. Please retake Lessons 1–8."
            f"{archive_note}"
        )

    def _migrate_to_v32(self, data: ProgressData, raw: dict[str, Any]) -> None:
        """Upgrade pre-V3.2 progress so drafts from older curricula do not attach to changed exercises."""
        archive = self._archive_legacy_file_v32(raw)
        # Clear all exercise progress for the V3.2 core so old drafts never appear inside rewritten tasks.
        cleared_exercises = [
            exercise_id for exercise_id in list(data.exercises) if is_v32_exercise(exercise_id)
        ]
        for exercise_id in cleared_exercises:
            del data.exercises[exercise_id]
        # Clear lesson completion flags for the V3.2 catalog.
        data.completed_lessons = [lid for lid in data.completed_lessons if lid not in V32_LESSON_IDS]
        # If current lesson points into the V3.2 set, unset it to avoid dropping into a mismatched exercise.
        if data.current_lesson_id in V32_LESSON_IDS:
            data.current_lesson_id = None
        # Reset mastery for tracked topics so the UI does not claim competence
        # based on replaced assessments.
        for topic in DEFAULT_MASTERY_TOPICS:
            data.mastery[topic] = 0.0
        data.curriculum_version = 3
        self.migrated_from_legacy = True
        archive_note = f" A backup was saved as {archive.name}." if archive else ""
        self.load_warning = (
            "Basilisk Curriculum V3.2 Production Core replaces the prior lessons. "
            "Prior completions and drafts for Lessons 1–28 were cleared so old work "
            "does not attach to rewritten exercises. Mastery indicators were reset "
            "for core topics to reflect the new curriculum."
            f"{archive_note}"
        )

    def _archive_legacy_file(self, raw: dict[str, Any]) -> Optional[Path]:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        backup = self.path.with_name(f"{self.path.name}.pre-basilisk-v2-{stamp}")
        try:
            backup.write_text(
                json.dumps(raw, indent=2) + "\n",
                encoding="utf-8",
            )
            return backup
        except OSError:
            return None

    def _archive_legacy_file_v32(self, raw: dict[str, Any]) -> Optional[Path]:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        backup = self.path.with_name(f"{self.path.name}.pre-basilisk-v3.2-{stamp}")
        try:
            backup.write_text(
                json.dumps(raw, indent=2) + "\n",
                encoding="utf-8",
            )
            return backup
        except OSError:
            return None

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
        self.data.curriculum_version = CURRENT_CURRICULUM_VERSION
        payload = {
            "curriculum_version": self.data.curriculum_version,
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
        self.migrated_from_legacy = False
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
                "curriculum_version": self.data.curriculum_version,
                "completed_lessons": self.data.completed_lessons,
                "current_lesson_id": self.data.current_lesson_id,
                "exercises": {
                    key: asdict(value) for key, value in self.data.exercises.items()
                },
                "mastery": self.data.mastery,
                "mistake_topics": self.data.mistake_topics,
            }
        )
