"""Regression coverage for Basilisk Lessons 14–18 (Issue #18)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from course.catalog import CourseCatalog
from engine.code_runner import CodeRunner
from engine.course_controller import CourseController
from engine.exercise_checker import ExerciseChecker
from engine.execution_worker import apply_source_uses
from engine.progress import ProgressStore
from tests.exercise_solutions import SOLUTIONS, submit_solution

ROOT = Path(__file__).resolve().parents[1]

BATCH_IDS = [
    "collections_14_dict_iteration",
    "collections_15_while",
    "functions_16_parameters",
    "functions_17_defaults",
    "functions_18_returning_data",
]

EXPECTED_CATALOG_IDS = [
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
    *BATCH_IDS,
]


class SourceUsesFeatureTests(unittest.TestCase):
    def test_while_loop_respects_in_function(self) -> None:
        ok, _ = apply_source_uses(
            {"feature": "while_loop", "in_function": "trail_total"},
            "def trail_total(distances):\n    while False:\n        break\n",
        )
        self.assertTrue(ok)
        bad, message = apply_source_uses(
            {"feature": "while_loop", "in_function": "trail_total"},
            "while False:\n    pass\n\ndef trail_total(distances):\n    return 0\n",
        )
        self.assertFalse(bad)
        self.assertIn("while", message.lower())

    def test_while_loop_nonconstant_rejects_while_false(self) -> None:
        ok, _ = apply_source_uses(
            {"feature": "while_loop", "nonconstant": True},
            "n = 2\nwhile n > 0:\n    n -= 1\n",
        )
        self.assertTrue(ok)
        bad, message = apply_source_uses(
            {"feature": "while_loop", "nonconstant": True},
            "while False:\n    pass\n",
        )
        self.assertFalse(bad)
        never, message2 = apply_source_uses(
            {"feature": "while_loop", "nonconstant": True},
            "n = 3\nwhile n < 0:\n    n -= 1\n",
        )
        self.assertFalse(never)
        self.assertTrue(message.strip() and message2.strip())

    def test_forbidden_call_rejects_sum(self) -> None:
        ok, _ = apply_source_uses(
            {"feature": "forbidden_call", "name": "sum", "in_function": "trail_total"},
            "def trail_total(distances):\n    total = 0\n    return total\n",
        )
        self.assertTrue(ok)
        bad, message = apply_source_uses(
            {"feature": "forbidden_call", "name": "sum", "in_function": "trail_total"},
            "def trail_total(distances):\n    return sum(distances)\n",
        )
        self.assertFalse(bad)
        self.assertIn("sum", message.lower())
        indirect, _ = apply_source_uses(
            {"feature": "forbidden_call", "name": "sum", "in_function": "trail_total"},
            'def trail_total(distances):\n    return __builtins__["sum"](distances)\n',
        )
        self.assertFalse(indirect)

    def test_method_call_items_must_drive_for_iter(self) -> None:
        ok, _ = apply_source_uses(
            {
                "feature": "method_call",
                "method": "items",
                "name": "stock",
                "inside": "for_iter",
            },
            'stock = {"rope": 1}\nfor item, count in stock.items():\n    print(item)\n',
        )
        self.assertTrue(ok)
        dummy, _ = apply_source_uses(
            {
                "feature": "method_call",
                "method": "items",
                "name": "stock",
                "inside": "for_iter",
            },
            'stock = {"rope": 1}\nstock.items()\nfor item in stock:\n    print(item)\n',
        )
        self.assertFalse(dummy)

    def test_method_call_items_outside_target_function_fails(self) -> None:
        bad, _ = apply_source_uses(
            {
                "feature": "method_call",
                "method": "items",
                "name": "stock",
                "inside": "for_iter",
                "in_function": "field_ledger",
            },
            'stock = {"rope": 1}\n'
            "for item, count in stock.items():\n"
            "    pass\n"
            "\n"
            "def field_ledger(stock):\n"
            "    return []\n",
        )
        self.assertFalse(bad)

    def test_method_call_get_requires_min_args_and_receiver(self) -> None:
        ok, _ = apply_source_uses(
            {
                "feature": "method_call",
                "method": "get",
                "name": "stock",
                "min_args": 2,
                "in_function": "antidote_count",
            },
            'def antidote_count(stock):\n    return stock.get("antidote", 0)\n',
        )
        self.assertTrue(ok)
        no_default, _ = apply_source_uses(
            {
                "feature": "method_call",
                "method": "get",
                "name": "stock",
                "min_args": 2,
                "in_function": "antidote_count",
            },
            'def antidote_count(stock):\n    return stock.get("antidote")\n',
        )
        self.assertFalse(no_default)
        wrong_receiver, _ = apply_source_uses(
            {
                "feature": "method_call",
                "method": "get",
                "name": "stock",
                "min_args": 2,
                "in_function": "antidote_count",
            },
            'def antidote_count(stock):\n    other = {}\n    return other.get("antidote", 0)\n',
        )
        self.assertFalse(wrong_receiver)

    def test_function_signature_rejects_args_order_and_body_defaults(self) -> None:
        ok, _ = apply_source_uses(
            {
                "feature": "function_signature",
                "name": "log_entry",
                "parameters": ["message", "level", "source"],
                "defaults": {"level": "NOTICE", "source": "field"},
            },
            'def log_entry(message, level="NOTICE", source="field"):\n    return message\n',
        )
        self.assertTrue(ok)

        star_args, message = apply_source_uses(
            {
                "feature": "function_signature",
                "name": "supply_cost",
                "parameters": ["price", "quantity"],
            },
            "def supply_cost(*args):\n    return args[0] * args[1]\n",
        )
        self.assertFalse(star_args)
        self.assertIn("supply_cost", message)

        wrong_order, _ = apply_source_uses(
            {
                "feature": "function_signature",
                "name": "mark_dispatch",
                "parameters": ["destination", "status"],
                "defaults": {"status": "Review"},
            },
            'def mark_dispatch(status="Review", destination="x"):\n    return destination\n',
        )
        self.assertFalse(wrong_order)

        body_only, _ = apply_source_uses(
            {
                "feature": "function_signature",
                "name": "format_supply",
                "parameters": ["item", "quantity"],
                "defaults": {"quantity": 1},
            },
            "def format_supply(item, quantity):\n"
            "    if quantity is None:\n"
            "        quantity = 1\n"
            "    return quantity\n",
        )
        self.assertFalse(body_only)

        wrong_default, _ = apply_source_uses(
            {
                "feature": "function_signature",
                "name": "log_entry",
                "parameters": ["message", "level", "source"],
                "defaults": {"level": "NOTICE", "source": "field"},
            },
            'def log_entry(message, level="ALERT", source="field"):\n    return message\n',
        )
        self.assertFalse(wrong_default)

    def test_existing_source_uses_features_remain_green(self) -> None:
        cases = [
            ({"feature": "for_loop"}, "for item in []:\n    pass\n"),
            ({"feature": "len_call", "names": ["party"]}, "len(party)\n"),
            (
                {"feature": "fstring", "names": ["item"]},
                'item = "rope"\nprint(f"{item}")\n',
            ),
            (
                {"feature": "range_call"},
                "for i in range(3):\n    print(i)\n",
            ),
            (
                {"feature": "calls_name", "name": "print", "inside": "for_loop"},
                "for item in [1]:\n    print(item)\n",
            ),
            (
                {"feature": "rebind_self", "name": "signal", "inside": "while_loop"},
                "signal = 3\nwhile signal > 0:\n    signal -= 1\n",
            ),
        ]
        for test, source in cases:
            ok, message = apply_source_uses(test, source)
            self.assertTrue(ok, f"{test}: {message}")


class Lessons1418CatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = CourseCatalog(ROOT / "course" / "lessons")
        self.catalog.load()

    def test_catalog_order_and_counts(self) -> None:
        ids = [lesson.id for lesson in self.catalog.lessons]
        # Preserve exact order for the first 18 lessons; later lessons may exist.
        self.assertGreaterEqual(len(ids), 18)
        self.assertEqual(ids[:18], EXPECTED_CATALOG_IDS)
        # Count only the first 18 lessons here (batch 14–18 regression scope).
        first_eighteen = self.catalog.lessons[:18]
        exercise_ids = [ex.id for lesson in first_eighteen for ex in lesson.exercises]
        self.assertEqual(len(exercise_ids), 79)
        self.assertEqual(len(exercise_ids), len(set(exercise_ids)))

    def test_batch_lessons_have_five_exercises_each(self) -> None:
        for lesson_id in BATCH_IDS:
            lesson = self.catalog.get(lesson_id)
            assert lesson is not None
            self.assertEqual(len(lesson.exercises), 5, lesson_id)
            self.assertEqual(lesson.section_order, 7 if "collections" in lesson_id else 8)

    def test_runnable_exercises_have_three_hints_and_single_line_predictions(self) -> None:
        for lesson_id in BATCH_IDS:
            lesson = self.catalog.get(lesson_id)
            assert lesson is not None
            for exercise in lesson.exercises:
                if exercise.is_code_exercise or exercise.type in {
                    "predict_output",
                    "architecture",
                }:
                    self.assertEqual(len(exercise.hints), 3, exercise.id)
                if exercise.type == "predict_output":
                    self.assertNotIn("\n", exercise.expected_answer, exercise.id)

    def test_new_source_uses_features_are_referenced(self) -> None:
        features = {
            test.feature
            for lesson_id in BATCH_IDS
            for exercise in self.catalog.get(lesson_id).exercises  # type: ignore[union-attr]
            for test in exercise.tests
            if test.kind == "source_uses"
        }
        self.assertIn("while_loop", features)
        self.assertIn("method_call", features)
        self.assertIn("function_signature", features)


class Lessons1418GradingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.checker = ExerciseChecker(CodeRunner(timeout=2.0))
        self.catalog = CourseCatalog(ROOT / "course" / "lessons")
        self.catalog.load()

    def _exercise(self, lesson_id: str, exercise_id: str):
        lesson = self.catalog.get(lesson_id)
        assert lesson is not None
        return next(ex for ex in lesson.exercises if ex.id == exercise_id)

    def test_empty_list_expected_is_preserved(self) -> None:
        from course.exercise import TestCase
        from engine.exercise_checker import test_case_to_dict

        payload = test_case_to_dict(
            TestCase(kind="function", function="label_supplies", args=[[]], expected=[])
        )
        self.assertEqual(payload["expected"], [])

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

    def test_issue22_six_deceptive_bypasses_fail(self) -> None:
        cases = [
            (
                "collections_14_dict_iteration",
                "collections_14_ex2",
                (
                    'stock = {"rope": 2, "torch": 1}\n'
                    "for item, count in stock.items():\n"
                    "    break\n"
                    'print("rope: 2")\n'
                    'print("torch: 1")\n'
                ),
            ),
            (
                "collections_14_dict_iteration",
                "collections_14_ex4",
                (
                    "def antidote_count(stock):\n"
                    '    stock.get("rope", 99)\n'
                    '    return stock["antidote"] if "antidote" in stock else 0\n'
                ),
            ),
            (
                "collections_14_dict_iteration",
                "collections_14_ex5",
                (
                    "def field_ledger(stock):\n"
                    "    stock.items()\n"
                    '    stock.get("antidote", 0)\n'
                    "    lines = []\n"
                    "    for item in stock:\n"
                    '        lines.append(f"{item}: {stock[item]}")\n'
                    '    if "antidote" in stock and stock["antidote"] > 0:\n'
                    '        lines.append("Antidote ready")\n'
                    "    else:\n"
                    '        lines.append("Antidote missing")\n'
                    "    return lines\n"
                ),
            ),
            (
                "collections_15_while",
                "collections_15_ex2",
                (
                    "steps = 0\n"
                    "distance = 3\n"
                    "while False:\n"
                    "    distance -= 1\n"
                    "print(3)\n"
                ),
            ),
            (
                "collections_15_while",
                "collections_15_ex3",
                (
                    "signal = 3\n"
                    "while False:\n"
                    "    print(signal)\n"
                    "    signal -= 1\n"
                    "print(3)\n"
                    "print(2)\n"
                    "print(1)\n"
                    'print("clear")\n'
                ),
            ),
            (
                "collections_15_while",
                "collections_15_ex5",
                (
                    "def trail_total(distances):\n"
                    "    while False:\n"
                    "        index = 0\n"
                    "        total = 0\n"
                    "    if False:\n"
                    "        len(distances)\n"
                    "        distances[0]\n"
                    "    return sum(distances)\n"
                ),
            ),
        ]
        for lesson_id, exercise_id, code in cases:
            exercise = self._exercise(lesson_id, exercise_id)
            result = self.checker.check(exercise, code=code)
            self.assertFalse(result.passed, exercise_id)
            self.assertTrue(result.message.strip(), exercise_id)
            lowered = result.message.lower()
            self.assertNotIn("lambda", lowered, exercise_id)

    def test_issue22_live_path_bypass_variants_fail(self) -> None:
        """Variants that coexist with related AST nodes but never do live work."""
        cases = [
            (
                "collections_14_dict_iteration",
                "collections_14_ex2",
                (
                    'stock = {"rope": 2, "torch": 1}\n'
                    "for item, count in stock.items():\n"
                    "    break\n"
                    '    print(f"{item}: {count}")\n'
                    'print("rope: 2")\n'
                    'print("torch: 1")\n'
                ),
            ),
            (
                "collections_14_dict_iteration",
                "collections_14_ex4",
                (
                    "def antidote_count(stock):\n"
                    '    return stock.get("antidote", 0) if False else (\n'
                    '        stock["antidote"] if "antidote" in stock else 0\n'
                    "    )\n"
                ),
            ),
            (
                "collections_14_dict_iteration",
                "collections_14_ex5",
                (
                    "def field_ledger(stock):\n"
                    "    lines = []\n"
                    "    for item, count in stock.items():\n"
                    "        break\n"
                    '        lines.append(f"{item}: {count}")\n'
                    "    for item in stock:\n"
                    '        lines.append(f"{item}: {stock[item]}")\n'
                    '    if stock.get("antidote", 0) < -1:\n'
                    "        pass\n"
                    '    if "antidote" in stock and stock["antidote"] > 0:\n'
                    '        lines.append("Antidote ready")\n'
                    "    else:\n"
                    '        lines.append("Antidote missing")\n'
                    "    return lines\n"
                ),
            ),
            (
                "collections_15_while",
                "collections_15_ex2",
                (
                    "steps = 0\n"
                    "distance = 3\n"
                    "while distance < 0:\n"
                    "    steps += 1\n"
                    "    distance -= 1\n"
                    "steps = 3\n"
                    "print(steps)\n"
                ),
            ),
            (
                "collections_15_while",
                "collections_15_ex3",
                (
                    "signal = 3\n"
                    "while signal < 0:\n"
                    "    print(signal)\n"
                    "    signal -= 1\n"
                    "print(3)\n"
                    "print(2)\n"
                    "print(1)\n"
                    'print("clear")\n'
                ),
            ),
            (
                "collections_15_while",
                "collections_15_ex5",
                (
                    "def trail_total(distances):\n"
                    "    index = 0\n"
                    "    total = 0\n"
                    "    while index < 0:\n"
                    "        total += distances[index]\n"
                    "        index += 1\n"
                    "    len(distances)\n"
                    "    for value in distances:\n"
                    "        total += value\n"
                    "    return total\n"
                ),
            ),
            (
                "collections_15_while",
                "collections_15_ex5",
                (
                    "def trail_total(distances):\n"
                    "    index = 0\n"
                    "    total = 0\n"
                    "    while index < 0:\n"
                    "        total += distances[index]\n"
                    "        index += 1\n"
                    "    len(distances)\n"
                    '    return __builtins__["sum"](distances)\n'
                ),
            ),
        ]
        for lesson_id, exercise_id, code in cases:
            exercise = self._exercise(lesson_id, exercise_id)
            result = self.checker.check(exercise, code=code)
            self.assertFalse(
                result.passed,
                f"{exercise_id} unexpectedly passed: {result.message}",
            )
            self.assertTrue(result.message.strip(), exercise_id)

    def test_issue22_semantic_live_path_bypasses_fail(self) -> None:
        """Deceptive submissions from the Issue #22 semantic re-review must fail."""
        cases = [
            (
                "collections_14_dict_iteration",
                "collections_14_ex2",
                (
                    'stock = {"rope": 2, "torch": 1}\n'
                    "for item, count in stock.items():\n"
                    "    if False:\n"
                    '        print(f"{item}: {count}")\n'
                    'print("rope: 2")\n'
                    'print("torch: 1")\n'
                ),
            ),
            (
                "collections_14_dict_iteration",
                "collections_14_ex4",
                (
                    "def antidote_count(stock):\n"
                    '    count = stock.get("antidote", 0)\n'
                    '    count = stock["antidote"] if "antidote" in stock else 0\n'
                    "    return count\n"
                ),
            ),
            (
                "collections_14_dict_iteration",
                "collections_14_ex5",
                (
                    "def field_ledger(stock):\n"
                    "    lines = []\n"
                    "    scratch = []\n"
                    "    for item, count in stock.items():\n"
                    "        scratch.append(count)\n"
                    "    for item in stock:\n"
                    '        lines.append(f"{item}: {stock[item]}")\n'
                    '    if stock.get("antidote", 0) > 0:\n'
                    '        scratch.append("ready")\n'
                    "    else:\n"
                    '        scratch.append("missing")\n'
                    '    if "antidote" in stock and stock["antidote"] > 0:\n'
                    '        lines.append("Antidote ready")\n'
                    "    else:\n"
                    '        lines.append("Antidote missing")\n'
                    "    return lines\n"
                ),
            ),
            (
                "collections_15_while",
                "collections_15_ex2",
                (
                    "steps = 3\n"
                    "distance = 3\n"
                    "while distance > 0 and False:\n"
                    "    distance -= 1\n"
                    "print(steps)\n"
                ),
            ),
            (
                "collections_15_while",
                "collections_15_ex2",
                (
                    "steps = 0\n"
                    "distance = 3\n"
                    "while distance > 0:\n"
                    "    steps += 1\n"
                    "    distance -= 1\n"
                    "steps = 1 + 2\n"
                    "print(steps)\n"
                ),
            ),
            (
                "collections_15_while",
                "collections_15_ex3",
                (
                    "signal = 3\n"
                    "while signal > 0 and False:\n"
                    "    print(signal)\n"
                    "    signal -= 1\n"
                    "print(3)\n"
                    "print(2)\n"
                    "print(1)\n"
                    'print("clear")\n'
                ),
            ),
            (
                "collections_15_while",
                "collections_15_ex5",
                (
                    "totaler = sum\n"
                    "\n"
                    "def trail_total(distances):\n"
                    "    index = 0\n"
                    "    total = 0\n"
                    "    while index >= 0 and False:\n"
                    "        total += distances[index]\n"
                    "        index += 1\n"
                    "    len(distances)\n"
                    "    return totaler(distances)\n"
                ),
            ),
            (
                "collections_15_while",
                "collections_15_ex5",
                (
                    "def trail_total(distances):\n"
                    "    index = 0\n"
                    "    total = 0\n"
                    "    while index >= 0 and False:\n"
                    "        total += distances[index]\n"
                    "        index += 1\n"
                    "    len(distances)\n"
                    "    if not distances:\n"
                    "        return 0\n"
                    "    return distances[0] + trail_total(distances[1:])\n"
                ),
            ),
            (
                "collections_15_while",
                "collections_15_ex5",
                (
                    "totaler = sum\n"
                    "\n"
                    "def trail_total(distances):\n"
                    "    index = 0\n"
                    "    total = 0\n"
                    "    while index < len(distances):\n"
                    "        total += distances[index]\n"
                    "        index += 1\n"
                    "    return totaler(distances)\n"
                ),
            ),
            (
                "collections_15_while",
                "collections_15_ex5",
                (
                    "def trail_total(distances):\n"
                    "    index = 0\n"
                    "    total = 0\n"
                    "    while index < len(distances):\n"
                    "        total += distances[index]\n"
                    "        index += 1\n"
                    "    if not distances:\n"
                    "        return 0\n"
                    "    return distances[0] + trail_total(distances[1:])\n"
                ),
            ),
        ]
        for lesson_id, exercise_id, code in cases:
            exercise = self._exercise(lesson_id, exercise_id)
            result = self.checker.check(exercise, code=code)
            self.assertFalse(
                result.passed,
                f"{exercise_id} unexpectedly passed: {result.message}",
            )
            self.assertTrue(result.message.strip(), exercise_id)

    def test_issue22_semantic_correct_alternatives_pass(self) -> None:
        """Behaviorally correct alternatives must still pass after live-path hardening."""
        cases = [
            (
                "collections_14_dict_iteration",
                "collections_14_ex5",
                (
                    "def field_ledger(stock):\n"
                    "    lines = []\n"
                    "    for item, count in stock.items():\n"
                    '        lines.append(f"{item}: {count}")\n'
                    '    if stock.get("antidote", 0) > 0:\n'
                    '        status = "Antidote ready"\n'
                    "    else:\n"
                    '        status = "Antidote missing"\n'
                    "    lines.append(status)\n"
                    "    return lines\n"
                ),
            ),
            (
                "collections_15_while",
                "collections_15_ex2",
                (
                    "steps = 0\n"
                    "distance = 3\n"
                    "if distance > 0:\n"
                    "    while distance > 0:\n"
                    "        steps += 1\n"
                    "        distance -= 1\n"
                    "print(steps)\n"
                ),
            ),
            (
                "collections_15_while",
                "collections_15_ex5",
                (
                    "def trail_total(distances):\n"
                    "    index = 0\n"
                    "    total = 0\n"
                    "    if distances:\n"
                    "        while index < len(distances):\n"
                    "            total += distances[index]\n"
                    "            index += 1\n"
                    "    return total\n"
                ),
            ),
        ]
        for lesson_id, exercise_id, code in cases:
            exercise = self._exercise(lesson_id, exercise_id)
            result = self.checker.check(exercise, code=code)
            self.assertTrue(
                result.passed,
                f"{exercise_id} unexpectedly failed: {result.message}",
            )

    def test_dispatch_status_accepts_loop_counting_without_len(self) -> None:
        exercise = self._exercise("functions_16_parameters", "functions_16_ex5")
        loop_only = (
            "def dispatch_status(party, supplies, warning_active):\n"
            "    if warning_active:\n"
            '        return "Denied"\n'
            "    members = 0\n"
            "    for _person in party:\n"
            "        members += 1\n"
            "    if members == 0:\n"
            '        return "Denied"\n'
            "    supply_count = 0\n"
            "    for _item in supplies:\n"
            "        supply_count += 1\n"
            "    if supply_count >= 2 * members:\n"
            '        return "Ready"\n'
            '    return "Review"\n'
        )
        result = self.checker.check(exercise, code=loop_only)
        self.assertTrue(result.passed, result.message)

    def test_expression_failures_use_configured_message(self) -> None:
        exercise = self._exercise("functions_18_returning_data", "functions_18_ex5")
        aliased = self.checker.check(
            exercise,
            code=(
                'def build_dispatch(destination, party, supplies, status="Review"):\n'
                "    return {\n"
                '        "destination": destination,\n'
                '        "party": party,\n'
                '        "supplies": supplies,\n'
                '        "member_count": len(party),\n'
                '        "supply_count": len(supplies),\n'
                '        "status": status,\n'
                "    }\n"
            ),
        )
        self.assertFalse(aliased.passed)
        self.assertTrue(aliased.message.strip())
        lowered = aliased.message.lower()
        self.assertNotIn("lambda", lowered)
        self.assertNotIn("expression (", lowered)
        self.assertIn("new list", lowered)

    def test_batch_behavioral_tests_have_nonempty_messages(self) -> None:
        behavioral = {
            "stdout_equals",
            "stdout_contains",
            "function",
            "expression",
            "globals",
        }
        missing: list[str] = []
        for lesson_id in BATCH_IDS:
            lesson = self.catalog.get(lesson_id)
            assert lesson is not None
            for exercise in lesson.exercises:
                for test in exercise.tests:
                    if test.kind in behavioral and not (test.message or "").strip():
                        missing.append(f"{exercise.id}:{test.kind}")
        self.assertEqual(missing, [])

    def test_examples_do_not_disclose_prediction_or_solutions(self) -> None:
        forbidden_snippets = [
            'stock = {"rope": 2}\n\nfor item in stock:\n    print(item)',
            "fuel = 3\n\nwhile fuel > 0:\n    fuel -= 1\n\nprint(fuel)",
            'def route_label(destination, status):\n    return f"{destination}: {status}"\n\nprint(route_label("Gloamfen", "Review"))',
            'def mark_route(destination, status="Review"):\n    return f"{destination}: {status}"\n\nprint(mark_route("Gloamfen"))',
            'def log_entry(message, level="NOTICE", source="field"):\n    return f"[{level}][{source}] {message}"',
            'def pack(item):\n    result = [item]\n\nprint(pack("rope"))',
            "def trail_total(distances):",
            "def build_dispatch(",
            "def antidote_count(",
            "def field_ledger(",
        ]
        for lesson_id in BATCH_IDS:
            lesson = self.catalog.get(lesson_id)
            assert lesson is not None
            blob = "\n\n".join(example.code for example in lesson.examples)
            for snippet in forbidden_snippets:
                self.assertNotIn(snippet, blob, msg=f"{lesson_id} discloses {snippet!r}")

    def test_items_dummy_call_fails_fill_blank(self) -> None:
        exercise = self._exercise("collections_14_dict_iteration", "collections_14_ex2")
        result = self.checker.check(
            exercise,
            code=(
                'stock = {"rope": 2, "torch": 1}\n'
                "stock.items()\n"
                "for item in stock:\n"
                '    print(f"{item}: {stock[item]}")\n'
            ),
        )
        self.assertFalse(result.passed)

    def test_get_without_default_fails(self) -> None:
        exercise = self._exercise("collections_14_dict_iteration", "collections_14_ex4")
        result = self.checker.check(
            exercise,
            code=(
                "def antidote_count(stock):\n"
                '    return stock["antidote"] if "antidote" in stock else 0\n'
            ),
        )
        self.assertFalse(result.passed)

    def test_trail_total_rejects_hardcoded_and_sum(self) -> None:
        exercise = self._exercise("collections_15_while", "collections_15_ex5")
        hardcoded = self.checker.check(
            exercise,
            code="def trail_total(distances):\n    return 9\n",
        )
        self.assertFalse(hardcoded.passed)
        with_sum = self.checker.check(
            exercise,
            code="def trail_total(distances):\n    return sum(distances)\n",
        )
        self.assertFalse(with_sum.passed)
        dummy_while = self.checker.check(
            exercise,
            code=(
                "while False:\n"
                "    pass\n"
                "\n"
                "def trail_total(distances):\n"
                "    return sum(distances)\n"
            ),
        )
        self.assertFalse(dummy_while.passed)

    def test_signal_debug_rejects_dummy_while_hardcoded_prints(self) -> None:
        exercise = self._exercise("collections_15_while", "collections_15_ex3")
        bypass = self.checker.check(
            exercise,
            code=(
                "while False:\n"
                "    pass\n"
                "print(3)\n"
                "print(2)\n"
                "print(1)\n"
                'print("clear")\n'
            ),
        )
        self.assertFalse(bypass.passed)

    def test_dispatch_status_boundary_matrix(self) -> None:
        exercise = self._exercise("functions_16_parameters", "functions_16_ex5")
        good = SOLUTIONS["functions_16_ex5"]["code"]
        self.assertTrue(self.checker.check(exercise, code=good).passed)
        always_ready = self.checker.check(
            exercise,
            code=(
                "def dispatch_status(party, supplies, warning_active):\n"
                '    return "Ready"\n'
            ),
        )
        self.assertFalse(always_ready.passed)

    def test_star_args_rejected_for_supply_cost(self) -> None:
        exercise = self._exercise("functions_16_parameters", "functions_16_ex2")
        result = self.checker.check(
            exercise,
            code=(
                "def supply_cost(*args):\n"
                "    return args[0] * args[1]\n"
                "\n"
                "print(supply_cost(5, 3))\n"
            ),
        )
        self.assertFalse(result.passed)

    def test_defaults_require_signature_not_body_fallback(self) -> None:
        exercise = self._exercise("functions_17_defaults", "functions_17_ex3")
        result = self.checker.check(
            exercise,
            code=(
                "def format_supply(item, quantity=None):\n"
                "    if quantity is None:\n"
                "        quantity = 1\n"
                '    return f"{quantity} x {item}"\n'
                "\n"
                'print(format_supply("rope"))\n'
            ),
        )
        self.assertFalse(result.passed)

    def test_keyword_and_positional_binding_for_log_entry(self) -> None:
        exercise = self._exercise("functions_17_defaults", "functions_17_ex5")
        result = self.checker.check(exercise, code=SOLUTIONS["functions_17_ex5"]["code"])
        self.assertTrue(result.passed, result.message)

    def test_add_item_preserves_caller_list(self) -> None:
        exercise = self._exercise("functions_18_returning_data", "functions_18_ex4")
        mutating = self.checker.check(
            exercise,
            code=(
                "def add_item(supplies, item):\n"
                "    supplies.append(item)\n"
                "    return supplies\n"
            ),
        )
        self.assertFalse(mutating.passed)
        copying = self.checker.check(
            exercise,
            code=(
                "def add_item(supplies, item):\n"
                "    packed = supplies[:]\n"
                "    packed.append(item)\n"
                "    return packed\n"
            ),
        )
        self.assertTrue(copying.passed, copying.message)

    def test_build_dispatch_copies_and_preserves(self) -> None:
        exercise = self._exercise("functions_18_returning_data", "functions_18_ex5")
        aliased = self.checker.check(
            exercise,
            code=(
                'def build_dispatch(destination, party, supplies, status="Review"):\n'
                "    return {\n"
                '        "destination": destination,\n'
                '        "party": party,\n'
                '        "supplies": supplies,\n'
                '        "member_count": len(party),\n'
                '        "supply_count": len(supplies),\n'
                '        "status": status,\n'
                "    }\n"
            ),
        )
        self.assertFalse(aliased.passed)
        good = self.checker.check(
            exercise, code=SOLUTIONS["functions_18_ex5"]["code"]
        )
        self.assertTrue(good.passed, good.message)

    def test_lesson_18_unlocks_after_lesson_17(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            progress = ProgressStore(Path(tmp) / "progress.json")
            progress.load()
            controller = CourseController(
                self.catalog, progress, ExerciseChecker(CodeRunner(timeout=2.0))
            )
            lesson_17 = self.catalog.get("functions_17_defaults")
            lesson_18 = self.catalog.get("functions_18_returning_data")
            assert lesson_17 is not None and lesson_18 is not None

            # Complete everything before lesson 17.
            for lesson in self.catalog.lessons:
                if lesson.id == "functions_17_defaults":
                    break
                for exercise in lesson.exercises:
                    result = submit_solution(controller, lesson, exercise)
                    self.assertTrue(result.passed, f"{exercise.id}: {result.message}")

            self.assertTrue(controller.is_unlocked(lesson_17))
            self.assertFalse(controller.is_unlocked(lesson_18))
            for exercise in lesson_17.exercises:
                result = submit_solution(controller, lesson_17, exercise)
                self.assertTrue(result.passed, f"{exercise.id}: {result.message}")
            self.assertTrue(controller.is_unlocked(lesson_18))


if __name__ == "__main__":
    unittest.main()
