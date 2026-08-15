"""Regression coverage for Basilisk Lessons 19–23 (Issue #24)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from course.catalog import CourseCatalog
from engine.code_runner import CodeRunner
from engine.course_controller import CourseController
from engine.exercise_checker import ExerciseChecker
from engine.progress import ProgressStore
from tests.exercise_solutions import SOLUTIONS, submit_solution

ROOT = Path(__file__).resolve().parents[1]

BATCH_IDS = [
    "collections_19_nested_data",
    "functions_20_scope",
    "strings_21_methods",
    "errors_22_tracebacks",
    "errors_23_logic_debugging",
]

EXPECTED_CATALOG_IDS = [
    # 1–13 (existing)
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
    # 14–18 (implemented earlier)
    "collections_14_dict_iteration",
    "collections_15_while",
    "functions_16_parameters",
    "functions_17_defaults",
    "functions_18_returning_data",
    # 19–23 (this batch)
    *BATCH_IDS,
]


class Lessons1923CatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = CourseCatalog(ROOT / "course" / "lessons")
        self.catalog.load()

    def test_catalog_order_and_counts(self) -> None:
        ids = [lesson.id for lesson in self.catalog.lessons]
        self.assertEqual(ids, EXPECTED_CATALOG_IDS)
        self.assertEqual(len(self.catalog.lessons), 23)
        exercise_ids = [
            exercise.id for lesson in self.catalog.lessons for exercise in lesson.exercises
        ]
        self.assertEqual(len(exercise_ids), 104)
        self.assertEqual(len(exercise_ids), len(set(exercise_ids)))

    def test_batch_lessons_have_five_exercises_each(self) -> None:
        for lesson_id in BATCH_IDS:
            lesson = self.catalog.get(lesson_id)
            assert lesson is not None
            self.assertEqual(len(lesson.exercises), 5, lesson_id)
            self.assertEqual(lesson.section_order, 9)

    def test_runnable_exercises_have_three_hints_and_single_line_predictions(self) -> None:
        for lesson_id in BATCH_IDS:
            lesson = self.catalog.get(lesson_id)
            assert lesson is not None
            for exercise in lesson.exercises:
                if exercise.is_code_exercise or exercise.type in {"predict_output", "architecture"}:
                    self.assertEqual(len(exercise.hints), 3, exercise.id)
                if exercise.type == "predict_output":
                    self.assertNotIn("\n", exercise.expected_answer, exercise.id)

    def test_behavioral_tests_have_messages(self) -> None:
        behavioral = {"stdout_equals", "stdout_contains", "function", "expression", "globals"}
        missing: list[str] = []
        for lesson_id in BATCH_IDS:
            lesson = self.catalog.get(lesson_id)
            assert lesson is not None
            for exercise in lesson.exercises:
                for test in exercise.tests:
                    if test.kind in behavioral and not (test.message or "").strip():
                        missing.append(f"{exercise.id}:{test.kind}")
        self.assertEqual(missing, [])

    def test_examples_do_not_duplicate_prediction_code_or_disclose_known_solution(self) -> None:
        for lesson_id in BATCH_IDS:
            lesson = self.catalog.get(lesson_id)
            assert lesson is not None
            example_blobs = [ex.code for ex in lesson.examples]
            for exercise in lesson.exercises:
                if exercise.type == "predict_output":
                    for blob in example_blobs:
                        self.assertNotEqual(
                            blob.strip(), exercise.code_to_predict.strip(), f"{lesson_id} duplicates predict code"
                        )
                        self.assertNotIn(
                            exercise.code_to_predict.strip(),
                            blob,
                            f"{lesson_id} embeds predict code inside example",
                        )
        # Lesson 23 example must not reveal the repaired signal_level solution
        l23 = self.catalog.get("errors_23_logic_debugging")
        assert l23 is not None
        text = "\n".join(ex.code for ex in l23.examples)
        self.assertNotIn("def signal_level(", text)
        self.assertFalse(">=" in text and "80" in text and "50" in text and "Elite" in text and "Ready" in text)


class Lessons1923GradingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.checker = ExerciseChecker(CodeRunner(timeout=2.0))
        self.catalog = CourseCatalog(ROOT / "course" / "lessons")
        self.catalog.load()

    def _exercise(self, lesson_id: str, exercise_id: str):
        lesson = self.catalog.get(lesson_id)
        assert lesson is not None
        return next(ex for ex in lesson.exercises if ex.id == exercise_id)

    def test_all_reference_solutions_pass(self) -> None:
        for lesson_id in BATCH_IDS:
            lesson = self.catalog.get(lesson_id)
            assert lesson is not None
            for exercise in lesson.exercises:
                spec = SOLUTIONS[exercise.id]
                result = self.checker.check(
                    exercise,
                    code=spec.get("code", ""),
                    answer=spec.get("answer", ""),
                )
                self.assertTrue(result.passed, f"{exercise.id}: {result.message}")

    def test_nested_path_and_totals_and_roster(self) -> None:
        # Lesson 19 matrices
        total = self._exercise("collections_19_nested_data", "collections_19_ex4")
        roster = self._exercise("collections_19_nested_data", "collections_19_ex5")
        # Totals
        code = SOLUTIONS[total.id]["code"]
        self.assertTrue(self.checker.check(total, code=code).passed)
        # Numbered roster behavior
        code = SOLUTIONS[roster.id]["code"]
        self.assertTrue(self.checker.check(roster, code=code).passed)

    def test_use_supply_does_not_mutate_global(self) -> None:
        exercise = self._exercise("functions_20_scope", "functions_20_ex3")
        mutating = self.checker.check(
            exercise,
            code=(
                "supplies = 3\n"
                "def use_supply():\n"
                "    global supplies\n"
                "    supplies = supplies - 1\n"
                "    return supplies\n"
                "print(use_supply())\n"
            ),
        )
        self.assertFalse(mutating.passed)

    def test_normalization_and_log_line_parsing(self) -> None:
        norm = self._exercise("strings_21_methods", "strings_21_ex4")
        parse = self._exercise("strings_21_methods", "strings_21_ex5")
        # Accept chained or reassigned methods
        reassigned = self.checker.check(
            norm,
            code=("def normalize_username(text):\n" "    text = text.strip()\n" "    return text.lower()\n"),
        )
        self.assertTrue(reassigned.passed, reassigned.message)
        chain = self.checker.check(
            norm, code=("def normalize_username(text):\n" "    return text.lower().strip()\n")
        )
        self.assertTrue(chain.passed, chain.message)
        # Parse variants
        self.assertTrue(self.checker.check(parse, code=SOLUTIONS[parse.id]["code"]).passed)

    def test_required_function_signatures_and_methods_are_enforced(self) -> None:
        lesson = self.catalog.get("strings_21_methods")
        assert lesson is not None
        ex4 = next(ex for ex in lesson.exercises if ex.id == "strings_21_ex4")
        sig_tests = [t for t in ex4.tests if t.kind == "source_uses" and t.feature == "function_signature"]
        self.assertTrue(any(t.name == "normalize_username" and t.parameters == ["text"] for t in sig_tests))
        ex5 = next(ex for ex in lesson.exercises if ex.id == "strings_21_ex5")
        methods = [t for t in ex5.tests if t.kind == "source_uses" and t.feature == "method_call"]
        names = {t.method for t in methods}
        self.assertTrue({"split", "strip", "lower"} <= names)

    def test_deferred_syntax_absent_in_new_lessons_and_solutions(self) -> None:
        import re
        comp_list = re.compile(r"\\[[^\\]]*\\bfor\\b[^\\]]*\\]")
        comp_dict = re.compile(r"\\{[^\\}]*\\bfor\\b[^\\}]*\\}")
        # Lesson examples/starters
        for lesson_id in BATCH_IDS:
            lesson = self.catalog.get(lesson_id)
            assert lesson is not None
            for example in lesson.examples:
                self.assertIsNone(comp_list.search(example.code))
                self.assertIsNone(comp_dict.search(example.code))
            for exercise in lesson.exercises:
                if exercise.starter_code:
                    self.assertIsNone(comp_list.search(exercise.starter_code))
                    self.assertIsNone(comp_dict.search(exercise.starter_code))
        # Recorded solutions for this batch
        batch_ex_ids = [ex.id for lid in BATCH_IDS for ex in self.catalog.get(lid).exercises]  # type: ignore[union-attr]
        for ex_id in batch_ex_ids:
            code = SOLUTIONS.get(ex_id, {}).get("code", "")
            if code:
                self.assertIsNone(comp_list.search(code), ex_id)
                self.assertIsNone(comp_dict.search(code), ex_id)

    def test_broken_starters_raise_intended_error_families(self) -> None:
        # Lesson 22 debug starters: SyntaxError, NameError, TypeError, IndexError/KeyError progression
        cases = [
            ("errors_22_tracebacks", "errors_22_ex2", "SyntaxError"),
            ("errors_22_tracebacks", "errors_22_ex3", "NameError"),
            ("errors_22_tracebacks", "errors_22_ex4", "TypeError"),
            ("errors_22_tracebacks", "errors_22_ex5", "IndexError"),
        ]
        for lesson_id, ex_id, family in cases:
            exercise = self._exercise(lesson_id, ex_id)
            # Run exactly the starter code; checker should report a pre-test error with a learner-facing traceback.
            result = self.checker.check(exercise, code=exercise.starter_code)
            self.assertFalse(result.passed, ex_id)
            detail = (result.details[0] if result.details else (result.run.error if result.run else "")) or ""
            self.assertIn(family, detail, f"{ex_id}: expected {family} in {detail!r}")

    def test_branch_order_and_off_by_one_fail(self) -> None:
        branch = self._exercise("errors_23_logic_debugging", "errors_23_ex3")
        wrong_order = self.checker.check(
            branch,
            code=("def signal_level(score):\n" '    if score >= 50:\n' '        return "Ready"\n'
                  '    elif score >= 80:\n' '        return "Elite"\n' '    return "Hold"\n'),
        )
        self.assertFalse(wrong_order.passed)

        cd = self._exercise("errors_23_logic_debugging", "errors_23_ex4")
        off_by_one = self.checker.check(
            cd,
            code=("def countdown(start):\n" "    values = []\n" "    while start > 0:\n"
                  "        start -= 1\n" "        values.append(start)\n" "    return values\n"),
        )
        self.assertFalse(off_by_one.passed)

    def test_examples_do_not_disclose_solutions(self) -> None:
        forbidden_snippets = [
            "def total_party_health(",
            "def numbered_roster(",
            "def use_supply(",
            "def normalize_username(",
            "def parse_log_line(",
            "def signal_level(",
            "def countdown(",
            "def expedition_report(",
        ]
        for lesson_id in BATCH_IDS:
            lesson = self.catalog.get(lesson_id)
            assert lesson is not None
            blob = "\n\n".join(example.code for example in lesson.examples)
            for snippet in forbidden_snippets:
                self.assertNotIn(snippet, blob, msg=f"{lesson_id} discloses {snippet!r}")

    def test_lesson_unlocks_linear_after_18(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            progress = Path(tmp) / "progress.json"
            catalog = CourseCatalog(ROOT / "course" / "lessons")
            catalog.load()
            store = ProgressStore(progress)
            store.load()
            controller = CourseController(catalog, store, ExerciseChecker(CodeRunner(timeout=2.0)))

            lesson18 = catalog.get("functions_18_returning_data")
            lesson19 = catalog.get("collections_19_nested_data")
            assert lesson18 is not None and lesson19 is not None

            # Complete everything before lesson 18.
            for lesson in catalog.lessons:
                if lesson.id == "functions_18_returning_data":
                    break
                for exercise in lesson.exercises:
                    result = submit_solution(controller, lesson, exercise)
                    self.assertTrue(result.passed, f"{exercise.id}: {result.message}")

            self.assertTrue(controller.is_unlocked(lesson18))
            self.assertFalse(controller.is_unlocked(lesson19))
            for exercise in lesson18.exercises:
                result = submit_solution(controller, lesson18, exercise)
                self.assertTrue(result.passed, f"{exercise.id}: {result.message}")
            self.assertTrue(controller.is_unlocked(lesson19))

            # Now step through 19 → 23 linearly
            prev = lesson19
            for next_id in BATCH_IDS[1:]:
                nxt = catalog.get(next_id)
                assert nxt is not None
                self.assertFalse(controller.is_unlocked(nxt))
                for exercise in prev.exercises:
                    result = submit_solution(controller, prev, exercise)
                    self.assertTrue(result.passed, f"{exercise.id}: {result.message}")
                self.assertTrue(controller.is_unlocked(nxt))
                prev = nxt


if __name__ == "__main__":
    unittest.main()

