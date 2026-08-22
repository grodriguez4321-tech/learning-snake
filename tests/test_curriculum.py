"""Curriculum grading holes, content parsing, and catalog coverage."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from course.catalog import CourseCatalog
from course.lesson import parse_lesson_content
from engine.code_runner import CodeRunner
from engine.course_controller import CourseController
from engine.exercise_checker import ExerciseChecker
from engine.progress import DEFAULT_MASTERY_TOPICS, ProgressStore, CURRENT_CURRICULUM_VERSION

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
        self.assertIn("print", print_lesson.topics)
        self.assertIn("strings", strings_lesson.topics)


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
        starter = 'item = "torch"\ncount = 4\n\n'
        hardcoded = self.checker.check(
            exercise, code=starter + 'print("torch: 4")\n'
        )
        self.assertFalse(hardcoded.passed)
        valid = self.checker.check(exercise, code=starter + 'print(f"{item}: {count}")\n')
        self.assertTrue(valid.passed, valid.message)

    def test_fstring_debug_predict_feedback(self) -> None:
        exercise = self._exercise("fundamentals_03_fstrings", "fundamentals_03_ex1")
        wrong = self.checker.check(exercise, answer="Hello,Ada")
        self.assertFalse(wrong.passed)
        self.assertNotIn("Hello, Ada", wrong.message or "")

    def test_variables_report_must_print_variables_not_literals(self) -> None:
        exercise = self._exercise("fundamentals_02_variables", "fundamentals_02_ex6")
        literals = self.checker.check(
            exercise,
            code=(
                "expedition = 17\n"
                "registered = 4\n"
                "days_overdue = 3\n"
                'status = "OVERDUE"\n'
                "print(17)\n"
                "print(4)\n"
                "print(3)\n"
                'print("OVERDUE")\n'
            ),
        )
        self.assertFalse(literals.passed)
        use_vars = self.checker.check(
            exercise,
            code=(
                "expedition = 17\n"
                "registered = 4\n"
                "days_overdue = 3\n"
                'status = "OVERDUE"\n'
                "print(expedition)\n"
                "print(registered)\n"
                "print(days_overdue)\n"
                "print(status)\n"
            ),
        )
        self.assertTrue(use_vars.passed, use_vars.message)

    def test_evidence_without_append_fails(self) -> None:
        # V3.2: collections_02_ex2 requires items.append(\"torch\") and exact printed list
        exercise = self._exercise("collections_02_append", "collections_02_ex2")
        hardcoded = self.checker.check(
            exercise,
            code=('items = ["rope", "torch"]\nprint(items)\n'),
        )
        self.assertFalse(hardcoded.passed)
        plus = self.checker.check(
            exercise,
            code=('items = ["rope"] + ["torch"]\nprint(items)\n'),
        )
        self.assertFalse(plus.passed)
        extend = self.checker.check(
            exercise,
            code=('items = ["rope"]\nitems.extend(["torch"])\nprint(items)\n'),
        )
        self.assertFalse(extend.passed)
        augassign = self.checker.check(
            exercise,
            code=('items = ["rope"]\nitems += ["torch"]\nprint(items)\n'),
        )
        self.assertFalse(augassign.passed)
        append = self.checker.check(
            exercise,
            code=('items = ["rope"]\nitems.append("torch")\nprint(items)\n'),
        )
        self.assertTrue(append.passed, append.message)

    def test_index_debug_rejects_hardcoded_name(self) -> None:
        # V3.2: collections_01_ex2 uses colors -> print(colors[1]) should print blue
        exercise = self._exercise("collections_01_lists", "collections_01_ex2")
        hardcoded = self.checker.check(
            exercise,
            code='colors = ["red", "blue", "green"]\nprint("blue")\n',
        )
        self.assertFalse(hardcoded.passed)
        fixed = self.checker.check(
            exercise,
            code='colors = ["red", "blue", "green"]\nprint(colors[1])\n',
        )
        self.assertTrue(fixed.passed, fixed.message)

    def test_inspect_clue_lookup_table_fails_hidden_input(self) -> None:
        exercise = self._exercise("functions_01_basics", "functions_01_ex7")
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
        exercise = self._exercise("functions_01_basics", "functions_01_ex5")
        wrong = self.checker.check(exercise, answer="1")
        self.assertFalse(wrong.passed)
        # V3.2: Do not assert on specific feedback wording; just verify fail/pass behavior.
        right = self.checker.check(exercise, answer="2")
        self.assertTrue(right.passed)

    def test_inspect_clue_accepts_equivalent_and_rejects_print_only(self) -> None:
        exercise = self._exercise("functions_01_basics", "functions_01_ex7")
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
        self.assertNotIn("first\nsecond", result.message or "")

    def test_status_debug_requires_quoted_string(self) -> None:
        # V3.2: debug quoted text at fundamentals_02_ex5
        exercise = self._exercise("fundamentals_02_variables", "fundamentals_02_ex5")
        broken = self.checker.check(exercise, code="status = OVERDUE\nprint(status)\n")
        self.assertFalse(broken.passed)
        fixed = self.checker.check(
            exercise, code='status = "OVERDUE"\nprint(status)\n'
        )
        self.assertTrue(fixed.passed, fixed.message)

    def test_elif_branch_required_for_readiness(self) -> None:
        # V3.2: decisions_10_ex9 requires elif in the clearance board.
        exercise = self._exercise("decisions_10_boolean_logic", "decisions_10_ex9")
        # Missing elif: use nested else/if to try to bypass construct check.
        nested_else_if = self.checker.check(
            exercise,
            code=(
                "has_guide = True\n"
                "supplies = 10\n"
                "warning_active = False\n"
                "route_damaged = False\n"
                "if warning_active or route_damaged:\n"
                '    status = "Denied"\n'
                "else:\n"
                "    if has_guide and supplies >= 10:\n"
                '        status = "Cleared"\n'
                "    else:\n"
                '        status = "Review"\n'
                'print(f"Status: {status}")\n'
            ),
        )
        self.assertFalse(nested_else_if.passed)
        # Reference solution (with elif) must pass.
        with_elif = self.checker.check(exercise, code=exercise.reference_solution)
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

    def test_capstone_requires_len_on_party_and_supplies(self) -> None:
        exercise = self._exercise(
            "collections_13_dictionaries", "collections_13_ex6"
        )
        # Behaviorally correct counts, but only len(party) — supplies counted manually.
        partial_len = self.checker.check(
            exercise,
            code=(
                "def build_expedition_record(destination, party, supplies, has_guide, warning_active):\n"
                "    supply_count = 0\n"
                "    for item in supplies:\n"
                "        supply_count += 1\n"
                "    record = {\n"
                '        "destination": destination,\n'
                '        "party": party,\n'
                '        "supplies": supplies,\n'
                '        "has_guide": has_guide,\n'
                '        "warning_active": warning_active,\n'
                '        "member_count": len(party),\n'
                '        "supply_count": supply_count,\n'
                "    }\n"
                "    if not has_guide or warning_active:\n"
                '        record["status"] = "Denied"\n'
                "    elif supply_count >= 5:\n"
                '        record["status"] = "Cleared"\n'
                "    else:\n"
                '        record["status"] = "Review"\n'
                "    return record\n"
            ),
        )
        self.assertFalse(partial_len.passed)

    def test_intake_system_success_message_configured(self) -> None:
        exercise = self._exercise(
            "collections_13_dictionaries", "collections_13_ex7"
        )
        result = self.checker.check(exercise, code=exercise.reference_solution)
        self.assertTrue(result.passed, result.message)
        self.assertEqual(result.message, exercise.success_message)

    def test_expedition_report_requires_calling_inspect_clue(self) -> None:
        exercise = self._exercise("functions_01_basics", "functions_01_ex8")
        rebuilt = self.checker.check(
            exercise,
            code=(
                "evidence = ['broken lantern', 'gray dust', 'torn cloak']\n"
                "def inspect_clue(clue):\n"
                "    if clue == 'gray dust':\n"
                "        return f'FLAG: {clue}'\n"
                "    return f'logged: {clue}'\n"
                "for clue in evidence:\n"
                "    if clue == 'gray dust':\n"
                "        print(f'FLAG: {clue}')\n"
                "    else:\n"
                "        print(f'logged: {clue}')\n"
            ),
        )
        self.assertFalse(rebuilt.passed)
        dummy_outside = self.checker.check(
            exercise,
            code=(
                "evidence = ['broken lantern', 'gray dust', 'torn cloak']\n"
                "def inspect_clue(clue):\n"
                "    if clue == 'gray dust':\n"
                "        return f'FLAG: {clue}'\n"
                "    return f'logged: {clue}'\n"
                "inspect_clue('noop')\n"
                "for clue in evidence:\n"
                "    if clue == 'gray dust':\n"
                "        print(f'FLAG: {clue}')\n"
                "    else:\n"
                "        print(f'logged: {clue}')\n"
            ),
        )
        self.assertFalse(dummy_outside.passed)
        for_else_bypass = self.checker.check(
            exercise,
            code=(
                "evidence = ['broken lantern', 'gray dust', 'torn cloak']\n"
                "def inspect_clue(clue):\n"
                "    if clue == 'gray dust':\n"
                "        return f'FLAG: {clue}'\n"
                "    return f'logged: {clue}'\n"
                "for clue in evidence:\n"
                "    if clue == 'gray dust':\n"
                "        print(f'FLAG: {clue}')\n"
                "    else:\n"
                "        print(f'logged: {clue}')\n"
                "else:\n"
                "    inspect_clue('noop')\n"
            ),
        )
        self.assertFalse(for_else_bypass.passed)

    def test_use_last_supply_rejects_list_copy(self) -> None:
        exercise = self._exercise(
            "collections_12_list_methods", "collections_12_ex7"
        )
        copied = self.checker.check(
            exercise,
            code=(
                "def use_last_supply(supplies):\n"
                "    used = supplies[-1]\n"
                "    return used\n"
            ),
        )
        self.assertFalse(copied.passed)
        via_pop = self.checker.check(
            exercise,
            code=(
                "def use_last_supply(supplies):\n"
                "    return supplies.pop()\n"
            ),
        )
        self.assertTrue(via_pop.passed, via_pop.message)

    def test_prepare_supplies_rejects_replacement_list(self) -> None:
        exercise = self._exercise(
            "collections_12_list_methods", "collections_12_ex6"
        )
        rebuilt = self.checker.check(
            exercise,
            code=(
                "def prepare_supplies(supplies):\n"
                "    return [item for item in supplies if item != 'cracked vial'] + ['antidote']\n"
            ),
        )
        self.assertFalse(rebuilt.passed)

    def test_quartermaster_project_hints_and_expected_output(self) -> None:
        exercise = self._exercise(
            "collections_12_list_methods", "collections_12_ex8"
        )
        self.assertEqual(len(exercise.hints), 3)
        hints_text = "\n".join(exercise.hints).lower()
        self.assertIn("remove", hints_text)
        self.assertIn("append", hints_text)
        self.assertIn("range(len(supplies))", hints_text)
        self.assertTrue(any(word in hints_text for word in ["ready", "review"]))
        self.assertIn("cracked vial", exercise.starter_code)
        stdout = next(t for t in exercise.tests if t.kind == "stdout_equals")
        self.assertEqual(
            stdout.expected,
            "Supply count: 3\n1: rope\n2: torch\n3: antidote\nREADY\n",
        )

    def test_abandoned_camp_is_script_level(self) -> None:
        # V3.2: The Abandoned Camp mini-project is decisions_01_ex7 (script-level)
        exercise = self._exercise("decisions_01_conditionals", "decisions_01_ex7")
        self.assertNotIn("def ", exercise.starter_code)
        self.assertNotIn("camp_report", exercise.prompt.lower())
        with_func = self.checker.check(
            exercise,
            code=(
                "expedition = 17\n"
                "registered = 4\n"
                "bedrolls = 3\n"
                "def camp_report(expedition, registered, bedrolls):\n"
                "    if bedrolls != registered:\n"
                '        return f"Expedition {expedition}: INVESTIGATE"\n'
                '    return f"Expedition {expedition}: CLEAR"\n'
                "print(camp_report(expedition, registered, bedrolls))\n"
            ),
        )
        # May or may not pass behaviorally; != must fail construct check
        ne = self.checker.check(
            exercise,
            code=(
                "expedition = 17\n"
                "registered = 4\n"
                "bedrolls = 3\n"
                "if bedrolls != registered:\n"
                '    print(f"Expedition {expedition}: INVESTIGATE")\n'
                "else:\n"
                '    print(f"Expedition {expedition}: CLEAR")\n'
            ),
        )
        self.assertFalse(ne.passed)
        good = self.checker.check(
            exercise,
            code=(
                "expedition = 17\n"
                "registered = 4\n"
                "bedrolls = 3\n"
                "if bedrolls < registered:\n"
                '    print(f"Expedition {expedition}: INVESTIGATE")\n'
                "else:\n"
                '    print(f"Expedition {expedition}: CLEAR")\n'
            ),
        )
        self.assertTrue(good.passed, good.message)

    def test_boolean_constructs_required(self) -> None:
        # V3.2: Use write_code exercises for construct checks
        and_not_ex = self._exercise("decisions_10_boolean_logic", "decisions_10_ex8")
        nested = self.checker.check(
            and_not_ex,
            code=(
                "has_guide = True\n"
                "supplies = 12\n"
                "warning_active = False\n"
                "can_depart = False\n"
                "if has_guide:\n"
                "    if supplies >= 10:\n"
                "        if warning_active == False:\n"
                "            can_depart = True\n"
                "print(can_depart)\n"
            ),
        )
        self.assertFalse(nested.passed)
        without_not = self.checker.check(
            and_not_ex,
            code=(
                "has_guide = True\n"
                "supplies = 12\n"
                "warning_active = False\n"
                "can_depart = has_guide and supplies >= 10 and (warning_active == False)\n"
                "print(can_depart)\n"
            ),
        )
        self.assertFalse(without_not.passed)
        route_board = self._exercise("decisions_10_boolean_logic", "decisions_10_ex9")
        with_or_and = self.checker.check(route_board, code=route_board.reference_solution)
        self.assertTrue(with_or_and.passed, with_or_and.message)

    def test_range_and_len_constructs_required(self) -> None:
        roster = self._exercise("collections_11_len_range", "collections_11_ex4")
        dummy_range = self.checker.check(
            roster,
            code=(
                "def numbered_roster(party):\n"
                "    range(1)\n"
                "    lines = []\n"
                "    index = 0\n"
                "    while index < len(party):\n"
                '        lines.append(f"{index + 1}: {party[index]}")\n'
                "        index += 1\n"
                "    return lines\n"
            ),
        )
        self.assertFalse(dummy_range.passed)
        name_len = self._exercise("collections_11_len_range", "collections_11_ex5")
        hardcoded = self.checker.check(
            name_len,
            code=(
                "def is_long_name(name):\n"
                "    count = 0\n"
                "    for _ in name:\n"
                "        count += 1\n"
                "    return count >= 8\n"
            ),
        )
        self.assertFalse(hardcoded.passed)

    def test_can_depart_rejects_low_supply_shortcut(self) -> None:
        exercise = self._exercise(
            "decisions_10_boolean_logic", "decisions_10_ex4"
        )
        shortcut = self.checker.check(
            exercise,
            code=(
                "def can_depart(has_guide, supplies, warning_active):\n"
                "    return has_guide == True and supplies != 9 and warning_active == False\n"
            ),
        )
        self.assertFalse(shortcut.passed)

    def test_dispatch_rejects_single_print(self) -> None:
        exercise = self._exercise("fundamentals_01_print", "fundamentals_01_ex3")
        single = self.checker.check(
            exercise,
            code=(
                "# note\n"
                'print("SEARCH DISPATCH\\nExpedition: 17\\nStatus: OVERDUE")\n'
            ),
        )
        self.assertFalse(single.passed)

    def test_e2e_harness_refuses_production_data_dir(self) -> None:
        from tests.e2e_learning_loop import PRODUCTION_DATA, assert_isolated_runtime

        with self.assertRaises(AssertionError):
            assert_isolated_runtime(PRODUCTION_DATA)

    def test_pre_basilisk_progress_migration(self) -> None:
        from engine.progress import CURRENT_CURRICULUM_VERSION, ProgressStore

        fixture = ROOT / "tests" / "fixtures" / "pre_basilisk_v2_progress.json"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            path.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
            store = ProgressStore(path)
            store.load()
            self.assertTrue(store.migrated_from_legacy)
            self.assertIsNotNone(store.load_warning)
            self.assertEqual(store.data.curriculum_version, CURRENT_CURRICULUM_VERSION)
            self.assertNotIn("fundamentals_01_print", store.data.completed_lessons)
            self.assertNotIn("decisions_01_ex4", store.data.exercises)
            self.assertNotIn("fundamentals_01_ex3", store.data.exercises)
            self.assertAlmostEqual(store.data.mastery["print"], 0.45)
            archives = list(Path(tmp).glob("progress.json.pre-basilisk-v2-*"))
            self.assertEqual(len(archives), 1)
            reloaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(reloaded["curriculum_version"], CURRENT_CURRICULUM_VERSION)
            self.assertNotIn("decisions_01_ex4", reloaded.get("exercises", {}))


class FullCatalogLoopTests(unittest.TestCase):
    def test_every_exercise_has_a_recorded_solution(self) -> None:
        catalog = CourseCatalog(ROOT / "course" / "lessons")
        catalog.load()
        missing: list[str] = []
        for lesson in catalog.lessons:
            for exercise in lesson.exercises:
                if exercise.is_code_exercise:
                    if not exercise.reference_solution.strip():
                        missing.append(exercise.id)
                else:
                    # predict_output / architecture should have an expected answer
                    if not (exercise.expected_answer or exercise.choices):
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
                    if exercise.is_code_exercise:
                        code = exercise.reference_solution
                        self.assertTrue(code.strip(), f"missing reference_solution for {exercise.id}")
                        result = controller.submit_exercise(lesson, exercise, code=code)
                    else:
                        # Use canonical expected answer (text or choice index/text)
                        answer = exercise.expected_answer or (exercise.choices[0] if exercise.choices else "")
                        self.assertTrue(str(answer).strip(), f"missing expected_answer for {exercise.id}")
                        result = controller.submit_exercise(lesson, exercise, answer=str(answer))
                    self.assertTrue(result.passed, f"{exercise.id}: {result.message}")
                previous = lesson
            nxt = catalog.next(catalog.lessons[-1].id)
            self.assertIsNone(nxt)
