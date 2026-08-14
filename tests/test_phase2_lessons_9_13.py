"""Automated tests for Phase 2 Lessons 9–13 (curriculum + grading)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from course.catalog import CourseCatalog
from course.exercise import EXERCISE_TYPES
from engine.code_runner import CodeRunner
from engine.course_controller import CourseController
from engine.exercise_checker import ExerciseChecker
from engine.progress import ProgressStore
from tests.exercise_solutions import SOLUTIONS, submit_solution

ROOT = Path(__file__).resolve().parents[1]

PHASE1_IDS = [
    "fundamentals_01_print",
    "fundamentals_02_variables",
    "fundamentals_03_fstrings",
    "decisions_01_conditionals",
    "collections_01_lists",
    "collections_02_append",
    "collections_03_loops",
    "functions_01_basics",
]

PHASE2_BATCH_IDS = [
    "decisions_02_elif",
    "decisions_03_boolean_logic",
    "collections_04_len_range",
    "collections_05_list_methods",
    "collections_07_dictionaries",
]

LESSON9_13_EXERCISE_TYPES = {
    "decisions_02_elif": {"predict_output", "fill_blank", "write_code", "architecture"},
    "decisions_03_boolean_logic": {
        "predict_output",
        "fill_blank",
        "debug",
        "write_code",
        "architecture",
    },
    "collections_04_len_range": {"predict_output", "fill_blank", "debug", "write_code"},
    "collections_05_list_methods": {"predict_output", "write_code", "debug"},
    "collections_07_dictionaries": {"predict_output", "fill_blank", "debug", "write_code"},
}


class Phase2CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = CourseCatalog(ROOT / "course" / "lessons")
        cls.catalog.load()

    def test_phase1_order_unchanged_at_front(self) -> None:
        ids = [lesson.id for lesson in self.catalog.lessons]
        self.assertEqual(ids[:8], PHASE1_IDS)

    def test_phase2_batch_follows_phase1(self) -> None:
        ids = [lesson.id for lesson in self.catalog.lessons]
        self.assertEqual(ids[8:13], PHASE2_BATCH_IDS)

    def test_lessons_load_valid_json(self) -> None:
        for lesson_id in PHASE2_BATCH_IDS:
            lesson = self.catalog.get(lesson_id)
            self.assertIsNotNone(lesson, lesson_id)
            assert lesson is not None
            self.assertTrue(lesson.intro, msg=f"{lesson_id} missing intro")
            self.assertTrue(lesson.common_mistakes, msg=f"{lesson_id} missing mistakes")
            self.assertGreaterEqual(len(lesson.exercises), 4, lesson_id)

    def test_exercise_type_variety_per_lesson(self) -> None:
        for lesson_id, required_types in LESSON9_13_EXERCISE_TYPES.items():
            lesson = self.catalog.get(lesson_id)
            assert lesson is not None
            seen = {ex.type for ex in lesson.exercises}
            for kind in required_types:
                self.assertIn(kind, seen, f"{lesson_id} missing {kind}")
            non_write = seen - {"write_code", "fill_blank", "mini_project"}
            self.assertTrue(non_write, f"{lesson_id} needs predict/debug/architecture")

    def test_all_exercises_have_solutions(self) -> None:
        missing = []
        for lesson_id in PHASE2_BATCH_IDS:
            lesson = self.catalog.get(lesson_id)
            assert lesson is not None
            for exercise in lesson.exercises:
                if exercise.id not in SOLUTIONS:
                    missing.append(exercise.id)
                self.assertIn(exercise.type, EXERCISE_TYPES)
        self.assertEqual(missing, [])


class Phase2GradingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.checker = ExerciseChecker(CodeRunner(timeout=2.0))
        catalog = CourseCatalog(ROOT / "course" / "lessons")
        catalog.load()
        self.catalog = catalog

    def _exercise(self, lesson_id: str, exercise_id: str):
        lesson = self.catalog.get(lesson_id)
        assert lesson is not None
        return next(ex for ex in lesson.exercises if ex.id == exercise_id)

    def test_numbered_lines_rejects_len_two_hardcode(self) -> None:
        exercise = self._exercise("collections_04_len_range", "collections_04_ex5")
        hardcoded = self.checker.check(
            exercise,
            code=(
                "def numbered_lines(items):\n"
                "    if len(items) == 2:\n"
                "        return ['1. sword', '2. shield']\n"
                "    if len(items) == 1:\n"
                "        return [f'1. {items[0]}']\n"
                "    return []\n"
            ),
        )
        self.assertFalse(hardcoded.passed)

    def test_debug_exercises_reject_hardcoded_stdout(self) -> None:
        gate = self._exercise("decisions_03_boolean_logic", "decisions_03_ex4")
        self.assertFalse(
            self.checker.check(
                gate,
                code='passphrase = "open"\nentered = "open"\nprint("enter")\n',
            ).passed
        )
        hero = self._exercise("collections_07_dictionaries", "collections_07_ex3")
        self.assertFalse(
            self.checker.check(
                hero,
                code='hero = {"name": "Mira", "health": 42, "gold": 10}\nprint(42)\n',
            ).passed
        )
        remove = self._exercise("collections_05_list_methods", "collections_05_ex3")
        self.assertFalse(
            self.checker.check(
                remove,
                code=(
                    'inventory = ["sword", "potion", "key"]\n'
                    'inventory = ["sword", "key"]\n'
                    "print(inventory)\n"
                ),
            ).passed
        )

    def test_can_enter_rejects_tuple_lookup(self) -> None:
        exercise = self._exercise("decisions_03_boolean_logic", "decisions_03_ex5")
        cheat = self.checker.check(
            exercise,
            code=(
                "def can_enter(has_key, gold):\n"
                "    return (has_key, gold) in {(True, 15), (True, 10), (True, 100)}\n"
            ),
        )
        self.assertFalse(cheat.passed)

    def test_wound_label_rejects_lookup_table(self) -> None:
        exercise = self._exercise("decisions_02_elif", "decisions_02_ex3")
        lookup = self.checker.check(
            exercise,
            code=(
                "def wound_label(health):\n"
                "    table = {80: 'healthy', 50: 'wounded', 25: 'wounded', 0: 'critical', -3: 'critical'}\n"
                "    return table[health]\n"
            ),
        )
        self.assertFalse(lookup.passed)
        missing_key = self.checker.check(
            exercise,
            code=(
                "def wound_label(health):\n"
                "    if health == 80:\n"
                "        return 'healthy'\n"
                "    return 'wounded'\n"
            ),
        )
        self.assertFalse(missing_key.passed)

    def test_wound_label_accepts_elif_chain(self) -> None:
        exercise = self._exercise("decisions_02_elif", "decisions_02_ex3")
        result = self.checker.check(
            exercise,
            code=(
                "def wound_label(health):\n"
                "    if health > 50:\n"
                "        return 'healthy'\n"
                "    if health > 0:\n"
                "        return 'wounded'\n"
                "    return 'critical'\n"
            ),
        )
        self.assertTrue(result.passed, result.message)

    def test_can_enter_rejects_key_only_and_gold_only(self) -> None:
        exercise = self._exercise("decisions_03_boolean_logic", "decisions_03_ex5")
        key_only = self.checker.check(
            exercise,
            code="def can_enter(has_key, gold):\n    return has_key\n",
        )
        self.assertFalse(key_only.passed)
        gold_only = self.checker.check(
            exercise,
            code="def can_enter(has_key, gold):\n    return gold >= 10\n",
        )
        self.assertFalse(gold_only.passed)

    def test_can_enter_accepts_equivalent_boolean_form(self) -> None:
        exercise = self._exercise("decisions_03_boolean_logic", "decisions_03_ex5")
        result = self.checker.check(
            exercise,
            code=(
                "def can_enter(has_key, gold):\n"
                "    if has_key:\n"
                "        return gold >= 10\n"
                "    return False\n"
            ),
        )
        self.assertTrue(result.passed, result.message)

    def test_last_item_accepts_indexing_and_handles_empty(self) -> None:
        exercise = self._exercise("collections_04_len_range", "collections_04_ex4")
        via_index = self.checker.check(
            exercise,
            code=(
                "def last_item(items):\n"
                "    if not items:\n"
                "        return None\n"
                "    return items[len(items) - 1]\n"
            ),
        )
        self.assertTrue(via_index.passed, via_index.message)
        hardcoded = self.checker.check(
            exercise,
            code=(
                "def last_item(items):\n"
                "    if items == ['sword', 'shield', 'potion']:\n"
                "        return 'potion'\n"
                "    return None\n"
            ),
        )
        self.assertFalse(hardcoded.passed)

    def test_numbered_lines_rejects_hardcoded_list(self) -> None:
        exercise = self._exercise("collections_04_len_range", "collections_04_ex5")
        hardcoded = self.checker.check(
            exercise,
            code=(
                "def numbered_lines(items):\n"
                "    if items == ['sword', 'shield']:\n"
                "        return ['1. sword', '2. shield']\n"
                "    return []\n"
            ),
        )
        self.assertFalse(hardcoded.passed)

    def test_drop_item_skips_missing_without_error(self) -> None:
        exercise = self._exercise("collections_05_list_methods", "collections_05_ex4")
        result = self.checker.check(
            exercise,
            code=(
                "def drop_item(inventory, item):\n"
                "    if item in inventory:\n"
                "        inventory.remove(item)\n"
                "    return inventory\n"
            ),
        )
        self.assertTrue(result.passed, result.message)
        blind_remove = self.checker.check(
            exercise,
            code=(
                "def drop_item(inventory, item):\n"
                "    inventory.remove(item)\n"
                "    return inventory\n"
            ),
        )
        self.assertFalse(blind_remove.passed)

    def test_make_stats_rejects_hardcoded_mira(self) -> None:
        exercise = self._exercise("collections_07_dictionaries", "collections_07_ex4")
        hardcoded = self.checker.check(
            exercise,
            code=(
                "def make_stats(name, hp, gold):\n"
                '    return {"name": "Mira", "health": 42, "gold": 10}\n'
            ),
        )
        self.assertFalse(hardcoded.passed)

    def test_can_afford_uses_dict_lookup(self) -> None:
        exercise = self._exercise("collections_07_dictionaries", "collections_07_ex5")
        hardcoded = self.checker.check(
            exercise,
            code=(
                "def can_afford(stats, price):\n"
                "    if price <= 10:\n"
                "        return True\n"
                "    return False\n"
            ),
        )
        self.assertFalse(hardcoded.passed)

    def test_architecture_choices_present(self) -> None:
        for lesson_id, ex_id in (
            ("decisions_02_elif", "decisions_02_ex4"),
            ("decisions_03_boolean_logic", "decisions_03_ex7"),
        ):
            exercise = self._exercise(lesson_id, ex_id)
            self.assertGreaterEqual(len(exercise.choices), 2)
            self.assertTrue(exercise.expected_answer)


class Phase2UnlockTests(unittest.TestCase):
    def test_phase2_unlocks_after_phase1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            catalog = CourseCatalog(ROOT / "course" / "lessons")
            catalog.load()
            progress = ProgressStore(Path(tmp) / "progress.json")
            progress.load()
            controller = CourseController(
                catalog, progress, ExerciseChecker(CodeRunner(timeout=2.0))
            )
            first_phase2 = catalog.get(PHASE2_BATCH_IDS[0])
            assert first_phase2 is not None
            self.assertFalse(controller.is_unlocked(first_phase2))

            for lesson in catalog.lessons[:8]:
                for exercise in lesson.exercises:
                    result = submit_solution(controller, lesson, exercise)
                    self.assertTrue(result.passed, f"{exercise.id}: {result.message}")

            self.assertTrue(controller.is_unlocked(first_phase2))

    def test_full_batch_solutions_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            catalog = CourseCatalog(ROOT / "course" / "lessons")
            catalog.load()
            progress = ProgressStore(Path(tmp) / "progress.json")
            progress.load()
            controller = CourseController(
                catalog, progress, ExerciseChecker(CodeRunner(timeout=2.0))
            )
            for lesson_id in PHASE2_BATCH_IDS:
                lesson = catalog.get(lesson_id)
                assert lesson is not None
                for exercise in lesson.exercises:
                    result = submit_solution(controller, lesson, exercise)
                    self.assertTrue(result.passed, f"{exercise.id}: {result.message}")


class Phase2ContentQualityTests(unittest.TestCase):
    def test_hints_are_progressive_not_generic(self) -> None:
        catalog = CourseCatalog(ROOT / "course" / "lessons")
        catalog.load()
        banned = ("think carefully", "review the lesson", "try again")
        for lesson_id in PHASE2_BATCH_IDS:
            lesson = catalog.get(lesson_id)
            assert lesson is not None
            for exercise in lesson.exercises:
                self.assertGreaterEqual(
                    len(exercise.hints),
                    3,
                    f"{exercise.id} should have at least 3 hints",
                )
                for hint in exercise.hints:
                    lower = hint.lower()
                    for phrase in banned:
                        self.assertNotIn(phrase, lower, exercise.id)

    def test_write_code_exercises_have_behavior_messages(self) -> None:
        catalog = CourseCatalog(ROOT / "course" / "lessons")
        catalog.load()
        for lesson_id in PHASE2_BATCH_IDS:
            lesson = catalog.get(lesson_id)
            assert lesson is not None
            for exercise in lesson.exercises:
                if exercise.type != "write_code":
                    continue
                for test in exercise.tests:
                    if test.kind == "function":
                        self.assertTrue(
                            test.message,
                            f"{exercise.id} function test missing message",
                        )


if __name__ == "__main__":
    unittest.main()
