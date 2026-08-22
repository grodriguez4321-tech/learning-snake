"""Submit embedded reference solutions/answers for catalog exercises."""

from __future__ import annotations

from course.exercise import Exercise
from course.lesson import Lesson
from engine.course_controller import CourseController
from engine.exercise_checker import CheckResult


def submit_solution(
    controller: CourseController,
    lesson: Lesson,
    exercise: Exercise,
) -> CheckResult:
    """Submit the exercise's embedded canonical reference solution or answer."""
    if exercise.is_code_exercise:
        code = exercise.reference_solution
        if not code or not code.strip():
            raise AssertionError(f"Missing reference_solution for {exercise.id}")
        return controller.submit_exercise(lesson, exercise, code=code)
    else:
        # Use expected_answer when provided, else fall back to first choice text/index.
        answer = exercise.expected_answer or (exercise.choices[0] if exercise.choices else "")
        if not str(answer).strip():
            raise AssertionError(f"Missing expected_answer for {exercise.id}")
        return controller.submit_exercise(lesson, exercise, answer=str(answer))
