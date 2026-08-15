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
        exercise = self._exercise("fundamentals_03_fstrings", "fundamentals_03_ex3")
        starter = (
            "expedition = 17\n"
            "registered = 4\n"
            "days_overdue = 3\n"
        )
        hardcoded = self.checker.check(
            exercise,
            code=starter + 'print("Expedition 17 | Party 4 | 3 days overdue")\n',
        )
        self.assertFalse(hardcoded.passed)
        valid = self.checker.check(
            exercise,
            code=starter
            + 'print(f"Expedition {expedition} | Party {registered} | {days_overdue} days overdue")\n',
        )
        self.assertTrue(valid.passed, valid.message)

    def test_fstring_debug_predict_feedback(self) -> None:
        exercise = self._exercise("fundamentals_03_fstrings", "fundamentals_03_ex1")
        wrong = self.checker.check(exercise, answer="Party registered:4")
        self.assertFalse(wrong.passed)
        self.assertNotIn("Party registered: 4", wrong.message)

    def test_evidence_count_hardcoded_number_fails(self) -> None:
        exercise = self._exercise("fundamentals_02_variables", "fundamentals_02_ex2")
        hardcoded = self.checker.check(
            exercise,
            code=(
                "tracks_found = 2\n"
                "damaged_items = 3\n"
                "evidence_count = 5\n"
                "print(evidence_count)\n"
            ),
        )
        self.assertFalse(hardcoded.passed)
        literals = self.checker.check(
            exercise,
            code=(
                "tracks_found = 2\n"
                "damaged_items = 3\n"
                "evidence_count = 2 + 3\n"
                "print(evidence_count)\n"
            ),
        )
        self.assertFalse(literals.passed)
        swapped = self.checker.check(
            exercise,
            code=(
                "tracks_found = 2\n"
                "damaged_items = 3\n"
                "evidence_count = damaged_items + tracks_found\n"
                "print(evidence_count)\n"
            ),
        )
        self.assertTrue(swapped.passed, swapped.message)

    def test_evidence_without_append_fails(self) -> None:
        exercise = self._exercise("collections_02_append", "collections_02_ex2")
        hardcoded = self.checker.check(
            exercise,
            code=(
                'evidence = ["broken lantern", "drag marks", "gray dust"]\n'
                "print(evidence)\n"
            ),
        )
        self.assertFalse(hardcoded.passed)
        plus = self.checker.check(
            exercise,
            code=(
                'evidence = ["broken lantern", "drag marks"] + ["gray dust"]\n'
                "print(evidence)\n"
            ),
        )
        self.assertTrue(plus.passed, plus.message)
        append = self.checker.check(
            exercise,
            code=(
                'evidence = ["broken lantern", "drag marks"]\n'
                'evidence.append("gray dust")\n'
                "print(evidence)\n"
            ),
        )
        self.assertTrue(append.passed, append.message)

    def test_index_debug_rejects_hardcoded_name(self) -> None:
        exercise = self._exercise("collections_01_lists", "collections_01_ex2")
        hardcoded = self.checker.check(
            exercise,
            code='party = ["Aria", "Rook", "Mira", "Selene"]\nprint("Rook")\n',
        )
        self.assertFalse(hardcoded.passed)
        fixed = self.checker.check(
            exercise,
            code='party = ["Aria", "Rook", "Mira", "Selene"]\nprint(party[1])\n',
        )
        self.assertTrue(fixed.passed, fixed.message)

    def test_inspect_clue_lookup_table_fails_hidden_input(self) -> None:
        exercise = self._exercise("functions_01_basics", "functions_01_ex3")
        table = self.checker.check(
            exercise,
            code=(
                "def inspect_clue(clue):\n"
                "    mapping = {\n"
                '        "gray dust": "FLAG: gray dust",\n'
                '        "broken lantern": "logged: broken lantern",\n'
                "    }\n"
                "    return mapping[clue]\n"
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

    def test_inspect_clue_accepts_equivalent_and_rejects_print_only(self) -> None:
        exercise = self._exercise("functions_01_basics", "functions_01_ex3")
        printed = self.checker.check(
            exercise,
            code=(
                "def inspect_clue(clue):\n"
                '    if clue == "gray dust":\n'
                '        print(f"FLAG: {clue}")\n'
                "    else:\n"
                '        print(f"logged: {clue}")\n'
            ),
        )
        self.assertFalse(printed.passed)
        via_if = self.checker.check(
            exercise,
            code=(
                "def inspect_clue(clue):\n"
                '    if clue == "gray dust":\n'
                '        return f"FLAG: {clue}"\n'
                '    return f"logged: {clue}"\n'
            ),
        )
        self.assertTrue(via_if.passed, via_if.message)

    def test_stdout_failure_does_not_spoiler_expected_line(self) -> None:
        exercise = self._exercise("fundamentals_01_print", "fundamentals_01_ex3")
        result = self.checker.check(exercise, code='print("nope")')
        self.assertFalse(result.passed)
        self.assertNotIn("SEARCH DISPATCH", result.message)

    def test_status_debug_requires_quoted_string(self) -> None:
        exercise = self._exercise("fundamentals_02_variables", "fundamentals_02_ex3")
        broken = self.checker.check(exercise, code="status = OVERDUE\nprint(status)\n")
        self.assertFalse(broken.passed)
        fixed = self.checker.check(
            exercise, code='status = "OVERDUE"\nprint(status)\n'
        )
        self.assertTrue(fixed.passed, fixed.message)

    def test_elif_branch_required_for_readiness(self) -> None:
        exercise = self._exercise("decisions_09_elif", "decisions_09_ex3")
        separate_ifs = self.checker.check(
            exercise,
            code=(
                "def readiness_status(supplies):\n"
                "    if supplies >= 10:\n"
                '        return "Cleared"\n'
                "    if supplies >= 5:\n"
                '        return "Review"\n'
                '    return "Denied"\n'
            ),
        )
        self.assertFalse(separate_ifs.passed)
        with_elif = self.checker.check(
            exercise,
            code=(
                "def readiness_status(supplies):\n"
                "    if supplies >= 10:\n"
                '        return "Cleared"\n'
                "    elif supplies >= 5:\n"
                '        return "Review"\n'
                "    else:\n"
                '        return "Denied"\n'
            ),
        )
        self.assertTrue(with_elif.passed, with_elif.message)

    def test_capstone_denies_without_guide(self) -> None:
        exercise = self._exercise(
            "collections_13_dictionaries", "collections_13_ex6"
        )
        always_clear = self.checker.check(
            exercise,
            code=(
                "def build_expedition_record(destination, party, supplies, has_guide, warning_active):\n"
                "    return {\n"
                '        "destination": destination,\n'
                '        "party": party,\n'
                '        "supplies": supplies,\n'
                '        "has_guide": has_guide,\n'
                '        "warning_active": warning_active,\n'
                '        "member_count": len(party),\n'
                '        "supply_count": len(supplies),\n'
                '        "status": "Cleared",\n'
                "    }\n"
            ),
        )
        self.assertFalse(always_clear.passed)


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
