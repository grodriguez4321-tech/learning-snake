"""Automated tests for Lessons 14–18 and required validator features."""

from __future__ import annotations

import unittest
from pathlib import Path

from course.catalog import CourseCatalog
from course.exercise import Exercise, TestCase
from engine.code_runner import CodeRunner
from engine.course_controller import CourseController
from engine.exercise_checker import ExerciseChecker
from engine.progress import ProgressStore
from tests.exercise_solutions import SOLUTIONS, submit_solution

ROOT = Path(__file__).resolve().parents[1]


class CatalogAndContentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = CourseCatalog(ROOT / "course" / "lessons")
        self.catalog.load()

    def test_catalog_order_and_counts(self) -> None:
        ids = [lesson.id for lesson in self.catalog.lessons]
        # New lessons must be present and in section 7/8 order.
        expected_tail = [
            "collections_14_dict_iteration",
            "collections_15_while",
            "functions_16_parameters",
            "functions_17_defaults",
            "functions_18_returning_data",
        ]
        self.assertGreaterEqual(len(ids), 18)
        self.assertEqual(ids[-5:], expected_tail)

        # Exactly five exercises in each new lesson.
        for lid in expected_tail:
            lesson = self.catalog.get(lid)
            assert lesson is not None
            self.assertEqual(len(lesson.exercises), 5, lid)

        # Overall counts after this batch.
        all_exercises = [ex for lesson in self.catalog.lessons for ex in lesson.exercises]
        self.assertEqual(len(self.catalog.lessons), 18)
        self.assertEqual(len(all_exercises), 79)

    def test_new_exercise_metadata(self) -> None:
        for lid in [
            "collections_14_dict_iteration",
            "collections_15_while",
            "functions_16_parameters",
            "functions_17_defaults",
            "functions_18_returning_data",
        ]:
            lesson = self.catalog.get(lid)
            assert lesson is not None

            # Predict answers must be single-line (no newline).
            for ex in lesson.exercises:
                if ex.type == "predict_output":
                    self.assertNotIn("\n", ex.expected_answer.strip(), ex.id)

            # Runnable exercises should have at least three progressive hints.
            for ex in lesson.exercises:
                if ex.is_code_exercise:
                    self.assertGreaterEqual(len(ex.hints), 3, ex.id)


class ValidatorFeatureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.checker = ExerciseChecker(CodeRunner(timeout=2.0))

    def _check_source_uses(self, code: str, test: TestCase) -> bool:
        ex = Exercise(id="src_uses", type="write_code", title="tmp", prompt="tmp", tests=[test])
        result = self.checker.check(exercise=ex, code=code)
        return result.passed

    def test_while_loop_scoped_to_function(self) -> None:
        # Dummy while outside target function must not satisfy in_function requirement.
        test = TestCase(kind="source_uses", feature="while_loop", in_function="trail_total")
        code = (
            "while True:\n"
            "    break\n"
            "def trail_total(distances):\n"
            "    return 0\n"
        )
        self.assertFalse(self._check_source_uses(code, test))
        good = (
            "def trail_total(distances):\n"
            "    i=0\n"
            "    s=0\n"
            "    while i < len(distances):\n"
            "        s+=distances[i]\n"
            "        i+=1\n"
            "    return s\n"
        )
        self.assertTrue(self._check_source_uses(good, test))

    def test_items_call_must_drive_loop(self) -> None:
        test = TestCase(
            kind="source_uses",
            feature="method_call",
            method="items",
            name="stock",
            inside="for_iter",
            in_function="ledger",
        )
        dummy = (
            "def ledger(stock):\n"
            "    stock.items()\n"
            "    for k in stock:\n"
            "        pass\n"
        )
        self.assertFalse(self._check_source_uses(dummy, test))
        good = (
            "def ledger(stock):\n"
            "    for k,v in stock.items():\n"
            "        pass\n"
        )
        self.assertTrue(self._check_source_uses(good, test))

    def test_get_requires_explicit_default_and_receiver(self) -> None:
        # Must have at least 2 positional args and the receiver name must match.
        test = TestCase(
            kind="source_uses",
            feature="method_call",
            method="get",
            name="stock",
            min_args=2,
            in_function="f",
        )
        no_default = "def f(stock):\n    return stock.get('antidote')\n"
        wrong_receiver = "def f(mapping):\n    return mapping.get('antidote', 0)\n"
        good = "def f(stock):\n    return stock.get('antidote', 0)\n"
        self.assertFalse(self._check_source_uses(no_default, test))
        self.assertFalse(self._check_source_uses(wrong_receiver, test))
        self.assertTrue(self._check_source_uses(good, test))

    def test_function_signature_parameter_order_and_defaults(self) -> None:
        want = TestCase(
            kind="source_uses",
            feature="function_signature",
            name="log_entry",
            names=[],
            # JSON loader maps these to custom fields; here we set them directly.
        )
        # Attach via asdict path — but ExerciseChecker uses dataclass->dict; emulate payload fields:
        want.parameters = ["message", "level", "source"]  # type: ignore[attr-defined]
        want.kwargs = {}  # silence dataclass conversion path
        # We don't have a first-class field on TestCase for defaults; inject via .__dict__ for clarity in test
        setattr(want, "defaults", {"level": "NOTICE", "source": "field"})

        wrong_order = "def log_entry(level='NOTICE', message='', source='field'):\n    pass\n"
        body_fallback = (
            "def log_entry(message, level, source):\n"
            "    if level is None:\n"
            "        level = 'NOTICE'\n"
            "    if source is None:\n"
            "        source = 'field'\n"
            "    return f'[{level}][{source}] {message}'\n"
        )
        wrong_default = "def log_entry(message, level='INFO', source='field'):\n    pass\n"
        correct = "def log_entry(message, level='NOTICE', source='field'):\n    pass\n"

        self.assertFalse(self._check_source_uses(wrong_order, want))
        self.assertFalse(self._check_source_uses(body_fallback, want))
        self.assertFalse(self._check_source_uses(wrong_default, want))
        self.assertTrue(self._check_source_uses(correct, want))


class SolutionsAndUnlockingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = CourseCatalog(ROOT / "course" / "lessons")
        self.catalog.load()
        self.progress = ProgressStore(Path(ROOT / "data" / "progress.json").with_name("test-progress.json"))
        self.progress.load()
        self.controller = CourseController(self.catalog, self.progress, ExerciseChecker(CodeRunner(timeout=2.0)))

    def test_every_new_exercise_has_solution_and_passes(self) -> None:
        missing: list[str] = []
        for lid in [
            "collections_14_dict_iteration",
            "collections_15_while",
            "functions_16_parameters",
            "functions_17_defaults",
            "functions_18_returning_data",
        ]:
            lesson = self.catalog.get(lid)
            assert lesson is not None
            for ex in lesson.exercises:
                if ex.id not in SOLUTIONS:
                    missing.append(ex.id)
        self.assertEqual(missing, [])

        # Run and pass all new exercises in order.
        for lid in [
            "collections_14_dict_iteration",
            "collections_15_while",
            "functions_16_parameters",
            "functions_17_defaults",
            "functions_18_returning_data",
        ]:
            lesson = self.catalog.get(lid)
            assert lesson is not None
            for exercise in lesson.exercises:
                result = submit_solution(self.controller, lesson, exercise)
                self.assertTrue(result.passed, f"{exercise.id}: {result.message}")

    def test_lesson_18_unlocks_only_after_17_complete(self) -> None:
        lesson17 = self.catalog.get("functions_17_defaults")
        lesson18 = self.catalog.get("functions_18_returning_data")
        assert lesson17 and lesson18
        # Reset progress
        self.progress.reset()
        # Before completion, 18 should be locked.
        self.assertFalse(self.controller.is_unlocked(lesson18))
        # Complete lesson 17
        for exercise in lesson17.exercises:
            result = submit_solution(self.controller, lesson17, exercise)
            self.assertTrue(result.passed, result.message)
        # Now 18 unlocks.
        self.assertTrue(self.controller.is_unlocked(lesson18))


if __name__ == "__main__":
    unittest.main()

