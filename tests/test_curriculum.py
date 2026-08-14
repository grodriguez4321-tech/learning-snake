"""Curriculum grading holes, content parsing, and catalog coverage."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from course.catalog import CourseCatalog
from course.lesson import parse_lesson_content
from engine.code_runner import CodeRunner
from engine.course_controller import CourseController
from engine.exercise_checker import ExerciseChecker
from engine.progress import DEFAULT_MASTERY_TOPICS, ProgressStore
from tests.exercise_solutions import SOLUTIONS, submit_solution

ROOT = Path(__file__).resolve().parents[1]


class ContentParsingTests(unittest.TestCase):
    def test_intro_and_sections_are_visible(self) -> None:
        catalog = CourseCatalog(ROOT / "course" / "lessons")
        catalog.load()
        for lesson in catalog.lessons:
            self.assertTrue(lesson.intro, msg=f"{lesson.id} has no intro")
            self.assertTrue(
                lesson.explanation_sections,
                msg=f"{lesson.id} hides the rest of its teaching text",
            )
            self.assertTrue(
                lesson.common_mistakes,
                msg=f"{lesson.id} has no common mistakes",
            )

    def test_parse_splits_problem_from_syntax(self) -> None:
        intro, sections = parse_lesson_content(
            "What problem does this solve?\n"
            "You need a way to see output.\n\n"
            "Basic syntax\n"
            "  print(value)\n\n"
            "Comments start with #. They do not run."
        )
        self.assertEqual(intro, "You need a way to see output.")
        headings = [section.heading for section in sections]
        self.assertIn("Basic syntax", headings)
        self.assertTrue(any("Comments start with #" in section.body for section in sections))


class MasteryTopicTests(unittest.TestCase):
    def test_print_and_strings_are_tracked(self) -> None:
        self.assertIn("print", DEFAULT_MASTERY_TOPICS)
        self.assertIn("strings", DEFAULT_MASTERY_TOPICS)
        self.assertIn("conditionals", DEFAULT_MASTERY_TOPICS)

        catalog = CourseCatalog(ROOT / "course" / "lessons")
        catalog.load()
        print_lesson = catalog.get("fundamentals_01_print")
        strings_lesson = catalog.get("fundamentals_03_fstrings")
        assert print_lesson is not None
        assert strings_lesson is not None
        self.assertEqual(print_lesson.topics, ["print"])
        self.assertEqual(strings_lesson.topics, ["strings"])


class GradingHoleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.checker = ExerciseChecker(CodeRunner(timeout=2.0))
        catalog = CourseCatalog(ROOT / "course" / "lessons")
        catalog.load()
        self.catalog = catalog

    def _exercise(self, lesson_id: str, exercise_id: str):
        lesson = self.catalog.get(lesson_id)
        assert lesson is not None
        return next(ex for ex in lesson.exercises if ex.id == exercise_id)

    def test_fstring_hardcoded_line_fails(self) -> None:
        exercise = self._exercise("fundamentals_03_fstrings", "fundamentals_03_ex1")
        starter = (
            'name = "Selene"\n'
            "health = 90\n"
            "level = 5\n"
        )
        hardcoded = self.checker.check(
            exercise, code=starter + 'print("Selene - Level 5 - HP 90")\n'
        )
        self.assertFalse(hardcoded.passed)
        concat = self.checker.check(
            exercise,
            code=starter
            + 'print(name + " - Level " + str(level) + " - HP " + str(health))\n',
        )
        self.assertFalse(concat.passed)
        valid = self.checker.check(
            exercise,
            code=starter + 'print(f"{name} - Level {level} - HP {health}")\n',
        )
        self.assertTrue(valid.passed, valid.message)
        single = self.checker.check(
            exercise,
            code=starter + "print(f'{name} - Level {level} - HP {health}')\n",
        )
        self.assertTrue(single.passed, single.message)

    def test_fstring_predict_does_not_use_multiarg_hint(self) -> None:
        exercise = self._exercise("fundamentals_03_fstrings", "fundamentals_03_ex2")
        wrong = self.checker.check(exercise, answer="Inventory:3x Potion")
        self.assertFalse(wrong.passed)
        self.assertNotIn("separates multiple arguments", wrong.message)

    def test_attack_hardcoded_number_fails(self) -> None:
        exercise = self._exercise("fundamentals_02_variables", "fundamentals_02_ex2")
        hardcoded = self.checker.check(
            exercise,
            code="strength = 12\nweapon_bonus = 3\nattack = 15\nprint(attack)\n",
        )
        self.assertFalse(hardcoded.passed)
        literals = self.checker.check(
            exercise,
            code="strength = 12\nweapon_bonus = 3\nattack = 12 + 3\nprint(attack)\n",
        )
        self.assertFalse(literals.passed)
        swapped = self.checker.check(
            exercise,
            code=(
                "strength = 12\n"
                "weapon_bonus = 3\n"
                "attack = weapon_bonus + strength\n"
                "print(attack)\n"
            ),
        )
        self.assertTrue(swapped.passed, swapped.message)

    def test_inventory_without_append_fails(self) -> None:
        exercise = self._exercise("collections_02_append", "collections_02_ex2")
        hardcoded = self.checker.check(
            exercise,
            code='inventory = ["sword", "shield", "potion", "torch"]\nprint("torch")\n',
        )
        self.assertFalse(hardcoded.passed)
        plus = self.checker.check(
            exercise,
            code=(
                'inventory = ["sword", "shield", "potion"] + ["torch"]\n'
                "print(inventory)\n"
            ),
        )
        self.assertTrue(plus.passed, plus.message)
        starred = self.checker.check(
            exercise,
            code=(
                'inventory = ["sword", "shield", "potion"]\n'
                'inventory.append("torch")\n'
                "print(*inventory)\n"
            ),
        )
        self.assertTrue(starred.passed, starred.message)

    def test_index_debug_rejects_hardcoded_name(self) -> None:
        exercise = self._exercise("collections_01_lists", "collections_01_ex2")
        hardcoded = self.checker.check(
            exercise,
            code='party = ["Aria", "Rook", "Mira"]\nprint("Aria")\n',
        )
        self.assertFalse(hardcoded.passed)
        fixed = self.checker.check(
            exercise,
            code='party = ["Aria", "Rook", "Mira"]\nprint(party[0])\n',
        )
        self.assertTrue(fixed.passed, fixed.message)

    def test_double_lookup_table_fails_hidden_input(self) -> None:
        exercise = self._exercise("functions_01_basics", "functions_01_ex1")
        table = self.checker.check(
            exercise,
            code=(
                "def double(number):\n"
                "    mapping = {2: 4, 7: 14, -3: -6, 0: 0}\n"
                "    return mapping[number]\n"
            ),
        )
        self.assertFalse(table.passed)

    def test_architecture_feedback_is_print_vs_return(self) -> None:
        exercise = self._exercise("functions_01_basics", "functions_01_ex2")
        wrong = self.checker.check(exercise, answer="1")
        self.assertFalse(wrong.passed)
        self.assertNotIn("is-a", wrong.message)
        self.assertNotIn("has-a", wrong.message)
        self.assertIn("return", wrong.message.lower())
        right = self.checker.check(exercise, answer="2")
        self.assertTrue(right.passed)

    def test_heal_accepts_if_equivalent_and_rejects_lookup(self) -> None:
        exercise = self._exercise("functions_01_basics", "functions_01_ex3")
        lookup = self.checker.check(
            exercise,
            code=(
                "def heal(health, amount):\n"
                "    if (health, amount) == (100, 20):\n"
                "        return 120\n"
                "    if (health, amount) == (50, 0):\n"
                "        return 50\n"
                "    if (health, amount) == (0, 10):\n"
                "        return 10\n"
            ),
        )
        self.assertFalse(lookup.passed)
        via_if = self.checker.check(
            exercise,
            code=(
                "def heal(health, amount):\n"
                "    total = health\n"
                "    total = total + amount\n"
                "    return total\n"
            ),
        )
        self.assertTrue(via_if.passed, via_if.message)

    def test_stdout_failure_does_not_spoiler_expected_line(self) -> None:
        exercise = self._exercise("fundamentals_01_print", "fundamentals_01_ex1")
        result = self.checker.check(exercise, code='print("nope")')
        self.assertFalse(result.passed)
        self.assertNotIn("Hello, Adventurer!", result.message)

    def test_gold_reassignment_rejects_hardcoded_sixty(self) -> None:
        exercise = self._exercise("fundamentals_02_variables", "fundamentals_02_ex3")
        hardcoded = self.checker.check(
            exercise, code="gold = 50\ngold = 60\nprint(gold)\n"
        )
        self.assertFalse(hardcoded.passed)
        plus_equals = self.checker.check(
            exercise, code="gold = 50\ngold += 10\nprint(gold)\n"
        )
        self.assertTrue(plus_equals.passed, plus_equals.message)


class FullCatalogLoopTests(unittest.TestCase):
    def test_every_exercise_has_a_recorded_solution(self) -> None:
        catalog = CourseCatalog(ROOT / "course" / "lessons")
        catalog.load()
        missing = []
        for lesson in catalog.lessons:
            for exercise in lesson.exercises:
                if exercise.id not in SOLUTIONS:
                    missing.append(exercise.id)
        self.assertEqual(missing, [])

    def test_recorded_solutions_pass_and_unlock_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            catalog = CourseCatalog(ROOT / "course" / "lessons")
            catalog.load()
            progress = ProgressStore(Path(tmp) / "progress.json")
            progress.load()
            controller = CourseController(
                catalog, progress, ExerciseChecker(CodeRunner(timeout=2.0))
            )
            previous = None
            for lesson in catalog.lessons:
                if previous is not None:
                    self.assertTrue(controller.is_unlocked(lesson), lesson.id)
                for exercise in lesson.exercises:
                    result = submit_solution(controller, lesson, exercise)
                    self.assertTrue(result.passed, f"{exercise.id}: {result.message}")
                previous = lesson
            nxt = catalog.next(catalog.lessons[-1].id)
            self.assertIsNone(nxt)
