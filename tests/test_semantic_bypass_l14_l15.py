from __future__ import annotations

import unittest

from course.exercise import Exercise, TestCase
from engine.code_runner import CodeRunner
from engine.exercise_checker import ExerciseChecker


class SemanticValidatorsLessons14And15(unittest.TestCase):
    def setUp(self) -> None:
        self.checker = ExerciseChecker(CodeRunner(timeout=2.0))

    def test_14_2_print_outside_items_loop_fails(self) -> None:
        exercise = Exercise(
            id="tmp_14_2",
            type="write_code",
            title="Pairs must print inside loop",
            prompt="Print item: count inside a .items() loop.",
            tests=[
                TestCase(kind="source_uses", feature="print_pair_from_items_loop", name="stock"),
            ],
        )
        bypass = (
            'stock = {"rope": 2, "torch": 1}\n'
            "for item, count in stock.items():\n"
            "    print(end=\"\")\n"
            'print("rope: 2")\n'
            'print("torch: 1")\n'
        )
        blocked = self.checker.check(exercise, code=bypass)
        self.assertFalse(blocked.passed)
        good = (
            'stock = {"rope": 2, "torch": 1}\n'
            "for item, count in stock.items():\n"
            '    print(f"{item}: {count}")\n'
        )
        ok = self.checker.check(exercise, code=good)
        self.assertTrue(ok.passed, ok.message)

    def test_14_5_items_and_get_semantics(self) -> None:
        exercise = Exercise(
            id="tmp_14_5",
            type="write_code",
            title="Field ledger must use items + get",
            prompt="Return lines built from .items() and status from .get().",
            tests=[
                TestCase(kind="source_uses", feature="append_pair_from_items_loop", names=["lines"], name="stock", in_function="field_ledger"),
                TestCase(kind="source_uses", feature="return_name", name="lines", in_function="field_ledger"),
                TestCase(kind="source_uses", feature="ban_reassign", name="lines", in_function="field_ledger"),
                TestCase(kind="source_uses", feature="ban_list_methods", names=["lines", "pop"], in_function="field_ledger"),
                TestCase(kind="source_uses", feature="dict_get_on", name="stock", in_function="field_ledger"),
                TestCase(kind="source_uses", feature="ban_subscript_on", name="stock", in_function="field_ledger"),
                TestCase(kind="source_uses", feature="ban_membership_on", name="stock", in_function="field_ledger"),
            ],
        )
        discard_items_then_rebuild = (
            "def field_ledger(stock):\n"
            "    lines = []\n"
            "    for item, count in stock.items():\n"
            '        lines.append("")\n'
            "    lines = []\n"
            "    for item in stock:\n"
            '        lines.append(f"{item}: {stock[item]}")\n'
            "    if stock.get(\"antidote\", 0) > 0:\n"
            '        lines.append("Antidote ready")\n'
            "    else:\n"
            '        lines.append("Antidote missing")\n'
            "    return lines\n"
        )
        blocked = self.checker.check(exercise, code=discard_items_then_rebuild)
        self.assertFalse(blocked.passed)
        pop_then_status = (
            "def field_ledger(stock):\n"
            "    lines = []\n"
            "    for item, count in stock.items():\n"
            '        lines.append(f"{item}: {count}")\n'
            "    if stock.get(\"antidote\", 0) > 0:\n"
            '        lines.append("")\n'
            "    else:\n"
            '        lines.append("")\n'
            "    lines.pop()\n"
            "    if \"antidote\" in stock and stock[\"antidote\"] > 0:\n"
            '        lines.append("Antidote ready")\n'
            "    else:\n"
            '        lines.append("Antidote missing")\n'
            "    return lines\n"
        )
        blocked2 = self.checker.check(exercise, code=pop_then_status)
        self.assertFalse(blocked2.passed)
        valid = (
            "def field_ledger(stock):\n"
            "    lines = []\n"
            "    for item, count in stock.items():\n"
            '        lines.append(f"{item}: {count}")\n'
            "    if stock.get(\"antidote\", 0) > 0:\n"
            '        status = "Antidote ready"\n'
            "    else:\n"
            '        status = "Antidote missing"\n'
            "    lines.append(status)\n"
            "    return lines\n"
        )
        ok = self.checker.check(exercise, code=valid)
        self.assertTrue(ok.passed, ok.message)

    def test_15_2_steps_must_be_computed_in_while(self) -> None:
        exercise = Exercise(
            id="tmp_15_2",
            type="write_code",
            title="Compute steps in loop",
            prompt="Use while to decrement distance and count steps.",
            tests=[
                TestCase(kind="source_uses", feature="while_updates", name="steps"),
            ],
        )
        bypass = (
            "steps = 3\n"
            "distance = 3\n"
            "while distance > 0:\n"
            "    distance -= 1\n"
            "print(steps)\n"
        )
        blocked = self.checker.check(exercise, code=bypass)
        self.assertFalse(blocked.passed)
        valid = (
            "steps = 0\n"
            "distance = 3\n"
            "while distance > 0:\n"
            "    distance -= 1\n"
            "    steps += 1\n"
            "print(steps)\n"
        )
        ok = self.checker.check(exercise, code=valid)
        self.assertTrue(ok.passed, ok.message)

    def test_15_3_loop_must_print_signal_inside(self) -> None:
        exercise = Exercise(
            id="tmp_15_3",
            type="write_code",
            title="Countdown prints in loop",
            prompt="Print signal countdown in while loop.",
            tests=[
                TestCase(kind="source_uses", feature="print_inside_while", name="signal"),
            ],
        )
        bypass = (
            "signal = 3\n"
            "while signal > 0:\n"
            "    print(end=\"\")\n"
            "    signal -= 1\n"
            "print(3)\n"
            "print(2)\n"
            "print(1)\n"
            "print('clear')\n"
        )
        blocked = self.checker.check(exercise, code=bypass)
        self.assertFalse(blocked.passed)
        valid = (
            "signal = 3\n"
            "while signal > 0:\n"
            "    print(signal)\n"
            "    signal -= 1\n"
            "print('clear')\n"
        )
        ok = self.checker.check(exercise, code=valid)
        self.assertTrue(ok.passed, ok.message)

    def test_15_5_require_index_accumulator_and_ban_shortcuts(self) -> None:
        exercise = Exercise(
            id="tmp_15_5",
            type="write_code",
            title="Trail total must use while with index/accumulator",
            prompt="Implement trail_total(distances) using a while index/accumulator.",
            tests=[
                TestCase(kind="source_uses", feature="index_accumulator_while", names=["distances"], name="total", in_function="trail_total"),
                TestCase(kind="source_uses", feature="ban_calls", names=["sum"], in_function="trail_total"),
                TestCase(kind="source_uses", feature="ban_listcomp", in_function="trail_total"),
                TestCase(kind="source_uses", feature="ban_recursion", in_function="trail_total"),
                TestCase(kind="source_uses", feature="ban_builtins_get_sum", in_function="trail_total"),
            ],
        )
        listcomp = (
            "def trail_total(distances):\n"
            "    index = 0\n"
            "    total = 0\n"
            "    while index < len(distances):\n"
            "        total += distances[index] * 0\n"
            "        index += 1\n"
            "    [total := total + value for value in distances]\n"
            "    return total\n"
        )
        self.assertFalse(self.checker.check(exercise, code=listcomp).passed)
        recursion_alias = (
            "def trail_total(distances):\n"
            "    index = 0\n"
            "    total = 0\n"
            "    while index < len(distances):\n"
            "        total += distances[index] * 0\n"
            "        index += 1\n"
            "    if not distances:\n"
            "        return 0\n"
            "    return distances[0] + again(distances[1:])\n"
            "again = trail_total\n"
        )
        self.assertFalse(self.checker.check(exercise, code=recursion_alias).passed)
        wrapped_sum = (
            "totaler = lambda values: sum(values)\n"
            "def trail_total(distances):\n"
            "    index = 0\n"
            "    total = 0\n"
            "    while index < len(distances):\n"
            "        total += distances[index] * 0\n"
            "        index += 1\n"
            "    return totaler(distances)\n"
        )
        self.assertFalse(self.checker.check(exercise, code=wrapped_sum).passed)
        builtins_get = (
            "def trail_total(distances):\n"
            "    index = 0\n"
            "    total = 0\n"
            "    while index < len(distances):\n"
            "        total += distances[index] * 0\n"
            "        index += 1\n"
            "    return __builtins__.get('sum')(distances)\n"
        )
        self.assertFalse(self.checker.check(exercise, code=builtins_get).passed)
        valid = (
            "def trail_total(distances):\n"
            "    index = 0\n"
            "    total = 0\n"
            "    while index < len(distances):\n"
            "        total += distances[index]\n"
            "        index += 1\n"
            "    return total\n"
        )
        ok = self.checker.check(exercise, code=valid)
        self.assertTrue(ok.passed, ok.message)


if __name__ == '__main__':
    unittest.main()

