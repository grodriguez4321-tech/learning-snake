"""Course controller — unlock rules and navigation glue.

Keeps GUI widgets free of curriculum policy. Lessons unlock in catalog order
once the previous lesson's exercises are complete.
"""

from __future__ import annotations

from typing import Optional

from course.catalog import CourseCatalog
from course.exercise import Exercise
from course.lesson import Lesson
from engine.exercise_checker import CheckResult, ExerciseChecker
from engine.progress import ProgressStore


class CourseController:
    def __init__(
        self,
        catalog: CourseCatalog,
        progress: ProgressStore,
        checker: ExerciseChecker,
    ) -> None:
        self.catalog = catalog
        self.progress = progress
        self.checker = checker

    def all_exercise_ids(self) -> list[str]:
        ids: list[str] = []
        for lesson in self.catalog.lessons:
            ids.extend(lesson.exercise_ids)
        return ids

    def is_unlocked(self, lesson: Lesson) -> bool:
        index = self.catalog.index_of(lesson.id)
        if index <= 0:
            return True
        previous = self.catalog.lessons[index - 1]
        return self.progress.is_lesson_complete(previous.id, previous.exercise_ids)

    def current_lesson(self) -> Optional[Lesson]:
        lesson_id = self.progress.data.current_lesson_id
        if lesson_id:
            lesson = self.catalog.get(lesson_id)
            if lesson and self.is_unlocked(lesson):
                return lesson
        first = self.catalog.first()
        if first:
            self.progress.data.current_lesson_id = first.id
        return first

    def set_current_lesson(self, lesson_id: str) -> Optional[Lesson]:
        lesson = self.catalog.get(lesson_id)
        if lesson is None or not self.is_unlocked(lesson):
            return None
        self.progress.data.current_lesson_id = lesson_id
        self.progress.save()
        return lesson

    def go_previous(self) -> Optional[Lesson]:
        current = self.current_lesson()
        if current is None:
            return None
        previous = self.catalog.previous(current.id)
        if previous is None:
            return current
        return self.set_current_lesson(previous.id) or current

    def go_next(self) -> Optional[Lesson]:
        current = self.current_lesson()
        if current is None:
            return None
        nxt = self.catalog.next(current.id)
        if nxt is None:
            return current
        if not self.is_unlocked(nxt):
            return current
        return self.set_current_lesson(nxt.id) or current

    def submit_exercise(
        self,
        lesson: Lesson,
        exercise: Exercise,
        *,
        code: str = "",
        answer: str = "",
    ) -> CheckResult:
        result = self.checker.check(exercise, code=code, answer=answer)
        topics = exercise.topics or lesson.topics
        self.progress.mark_exercise_result(
            exercise.id,
            passed=result.passed,
            topics=topics,
            answer=answer,
            code=code,
        )
        self.progress.refresh_lesson_completion(lesson.id, lesson.exercise_ids)
        self.progress.save()
        return result

    def request_hint(self, exercise: Exercise) -> tuple[int, Optional[str]]:
        used = self.progress.use_hint(exercise.id)
        self.progress.save()
        if used > len(exercise.hints):
            return used, None
        return used, exercise.hints[used - 1]

    def overall_progress_percent(self) -> float:
        return self.progress.overall_percent(self.all_exercise_ids())
