"""Non-GUI verification of the full Phase 1 learning loop."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from course.catalog import CourseCatalog
from engine.code_runner import CodeRunner
from engine.course_controller import CourseController
from engine.exercise_checker import ExerciseChecker
from engine.progress import ProgressStore


ROOT = Path(__file__).resolve().parents[1]


class LearningLoopTests(unittest.TestCase):
    def test_incorrect_hint_pass_unlock_reload_reset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            progress_path = Path(tmp) / "progress.json"
            catalog = CourseCatalog(ROOT / "course" / "lessons")
            catalog.load()
            progress = ProgressStore(progress_path)
            progress.load()
            runner = CodeRunner(timeout=2.0)
            controller = CourseController(catalog, progress, ExerciseChecker(runner))

            lesson = catalog.first()
            assert lesson is not None
            nxt = catalog.next(lesson.id)
            assert nxt is not None
            exercise = lesson.exercises[0]

            # Incorrect
            bad = controller.submit_exercise(lesson, exercise, code="print('nope')")
            self.assertFalse(bad.passed)
            self.assertTrue(bad.message)

            # Hints one at a time
            seen: list[str] = []
            for _ in range(len(exercise.hints)):
                _, hint = controller.request_hint(exercise)
                assert hint is not None
                seen.append(hint)
            self.assertEqual(seen, exercise.hints)
            _, exhausted = controller.request_hint(exercise)
            self.assertIsNone(exhausted)

            # Draft persistence across reload
            progress.save_draft(exercise.id, "# still working\nprint('draft')\n", "")
            progress.data.current_lesson_id = lesson.id
            progress.save()

            reloaded = ProgressStore(progress_path)
            reloaded.load()
            self.assertEqual(reloaded.exercise(exercise.id).attempts, 1)
            self.assertEqual(reloaded.exercise(exercise.id).hints_used, len(exercise.hints) + 1)
            self.assertIn("draft", reloaded.exercise(exercise.id).draft_code)
            self.assertEqual(reloaded.data.current_lesson_id, lesson.id)

            controller = CourseController(catalog, reloaded, ExerciseChecker(runner))
            self.assertFalse(controller.is_unlocked(nxt))

            # Alternative valid solution (single quotes)
            good = controller.submit_exercise(
                lesson, exercise, code="print('Hello, Adventurer!')"
            )
            self.assertTrue(good.passed)

            # Finish lesson
            for remaining in lesson.exercises[1:]:
                if remaining.is_code_exercise:
                    result = controller.submit_exercise(
                        lesson, remaining, code="print('Hello, Adventurer!')"
                    )
                else:
                    result = controller.submit_exercise(
                        lesson, remaining, answer=remaining.expected_answer
                    )
                self.assertTrue(result.passed, result.message)

            self.assertTrue(controller.is_unlocked(nxt))
            self.assertTrue(reloaded.is_lesson_complete(lesson.id, lesson.exercise_ids))

            # Navigate helpers
            controller.set_current_lesson(nxt.id)
            self.assertEqual(controller.current_lesson().id, nxt.id)
            previous = controller.go_previous()
            assert previous is not None
            self.assertEqual(previous.id, lesson.id)

            # Reset clears unlocks and drafts
            reloaded.reset()
            controller = CourseController(catalog, reloaded, ExerciseChecker(runner))
            self.assertFalse(controller.is_unlocked(nxt))
            self.assertFalse(reloaded.is_exercise_complete(exercise.id))
            self.assertEqual(reloaded.exercise(exercise.id).draft_code, "")


if __name__ == "__main__":
    unittest.main()
