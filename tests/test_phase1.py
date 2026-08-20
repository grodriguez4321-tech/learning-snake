"""Automated tests for Phase 1 engine behavior (no GUI required)."""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from course.catalog import CourseCatalog
from course.exercise import Exercise, TestCase
from engine.code_runner import TIMEOUT_MESSAGE, CodeRunner
from engine.course_controller import CourseController
from engine.exercise_checker import ExerciseChecker
from engine.progress import ProgressStore
from main import build_controller


ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def test_loads_ordered_lessons(self) -> None:
        catalog = CourseCatalog(ROOT / "course" / "lessons")
        catalog.load()
        # V3.2: exact 28 lessons total; spot-check first few and ordering.
        self.assertEqual(len(catalog.lessons), 28)
        ids = [lesson.id for lesson in catalog.lessons]
        self.assertEqual(
            ids[:8],
            [
                "fundamentals_01_print",
                "fundamentals_02_variables",
                "fundamentals_03_fstrings",
                "decisions_01_conditionals",
                "collections_01_lists",
                "collections_02_append",
                "collections_03_loops",
                "functions_01_basics",
            ],
        )
        # Ordering is stable by section_order then order.
        for left, right in zip(catalog.lessons, catalog.lessons[1:]):
            self.assertLessEqual(
                (left.section_order, left.order),
                (right.section_order, right.order),
            )

    def test_catalog_counts_match_contract(self) -> None:
        catalog = CourseCatalog(ROOT / "course" / "lessons")
        catalog.load()
        total_exercises = sum(len(lesson.exercises) for lesson in catalog.lessons)
        total_projects = sum(
            1 for lesson in catalog.lessons for ex in lesson.exercises if ex.type == "mini_project"
        )
        self.assertEqual(len(catalog.lessons), 28)
        self.assertEqual(total_exercises, 214)
        self.assertEqual(total_projects, 23)

    def test_lesson_ids_are_unique(self) -> None:
        catalog = CourseCatalog(ROOT / "course" / "lessons")
        catalog.load()
        ids = [lesson.id for lesson in catalog.lessons]
        self.assertEqual(len(ids), len(set(ids)))
        exercise_ids = [
            exercise.id for lesson in catalog.lessons for exercise in lesson.exercises
        ]
        self.assertEqual(len(exercise_ids), len(set(exercise_ids)))
        self.assertEqual(len(exercise_ids), 214)


class RunnerTests(unittest.TestCase):
    def test_captures_stdout(self) -> None:
        runner = CodeRunner(timeout=2.0)
        ok = runner.run("print('hi')")
        self.assertTrue(ok.success)
        self.assertEqual(ok.stdout.strip(), "hi")

    def test_runtime_error_is_student_facing(self) -> None:
        runner = CodeRunner(timeout=2.0)
        bad = runner.run("print(undefined_variable)")
        self.assertFalse(bad.success)
        self.assertIn("NameError", bad.error or "")
        self.assertNotIn("code_runner.py", bad.error or "")
        self.assertNotIn("execution_worker.py", bad.error or "")

    def test_syntax_error(self) -> None:
        runner = CodeRunner(timeout=2.0)
        bad = runner.run("if True\n    print('broken')")
        self.assertFalse(bad.success)
        self.assertIn("SyntaxError", bad.error or "")

    def test_timeout_stops_infinite_loop(self) -> None:
        runner = CodeRunner(timeout=0.5)
        started = time.monotonic()
        result = runner.run("while True:\n    pass\n")
        elapsed = time.monotonic() - started
        self.assertFalse(result.success)
        self.assertTrue(result.timed_out)
        self.assertIn("too long", result.error or "")
        self.assertLess(elapsed, 3.0)

    def test_playground_persists_until_reset(self) -> None:
        runner = CodeRunner(timeout=2.0)
        first = runner.run_playground("score = 10")
        self.assertTrue(first.success)
        second = runner.run_playground("print(score)")
        self.assertTrue(second.success)
        self.assertEqual(second.stdout.strip(), "10")
        runner.reset_playground()
        third = runner.run_playground("print(score)")
        self.assertFalse(third.success)
        self.assertIn("NameError", third.error or "")


class CheckerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.checker = ExerciseChecker(CodeRunner(timeout=2.0))
        catalog = CourseCatalog(ROOT / "course" / "lessons")
        catalog.load()
        self.catalog = catalog

    def test_stdout_grading(self) -> None:
        exercise = Exercise(
            id="t_stdout",
            type="write_code",
            title="stdout",
            prompt="print hello",
            tests=[TestCase(kind="stdout_equals", expected="hello\n")],
        )
        self.assertTrue(self.checker.check(exercise, code="print('hello')").passed)
        self.assertFalse(self.checker.check(exercise, code="print('bye')").passed)

    def test_variable_grading(self) -> None:
        exercise = Exercise(
            id="t_globals",
            type="write_code",
            title="vars",
            prompt="set x",
            tests=[
                TestCase(kind="globals", name="x", type_name="int", expected=7),
            ],
        )
        self.assertTrue(self.checker.check(exercise, code="x = 7").passed)
        self.assertFalse(self.checker.check(exercise, code="x = '7'").passed)

    def test_function_checks_multiple_cases_and_feedback(self) -> None:
        lesson = self.catalog.get("functions_01_basics")
        assert lesson is not None
        # V3.2: inspect_clue lives at functions_01_ex7
        exercise = next(ex for ex in lesson.exercises if ex.id == "functions_01_ex7")

        wrong = self.checker.check(
            exercise,
            code=(
                "def inspect_clue(clue):\n"
                '    if clue == "gray dust":\n'
                '        return f"FLAG: {clue}"\n'
                '    return f"logged: broken lantern"\n'
            ),
        )
        self.assertFalse(wrong.passed)
        self.assertIn("inspect_clue(", wrong.message)
        self.assertIn("worked for", wrong.message)

        right = self.checker.check(
            exercise,
            code=(
                "def inspect_clue(clue):\n"
                '    if clue == "gray dust":\n'
                '        return f"FLAG: {clue}"\n'
                "    else:\n"
                '        return f"logged: {clue}"\n'
            ),
        )
        self.assertTrue(right.passed)

    def test_failed_function_without_spoiling_full_solution(self) -> None:
        exercise = Exercise(
            id="t_fn",
            type="write_code",
            title="fn",
            prompt="triple",
            tests=[
                TestCase(kind="function", function="triple", args=[2], expected=6),
                TestCase(kind="function", function="triple", args=[3], expected=9),
            ],
        )
        result = self.checker.check(exercise, code="def triple(n):\n    return n\n")
        self.assertFalse(result.passed)
        self.assertNotIn("return n * 3", result.message)

    def test_class_and_attribute_checks(self) -> None:
        exercise = Exercise(
            id="t_class",
            type="write_code",
            title="class",
            prompt="Character",
            tests=[
                TestCase(kind="class_defined", name="Character"),
                TestCase(kind="expression", expression="Character('A', 10).health", expected=10),
                TestCase(kind="attribute", expression="Character('B', 3).name", expected="B"),
            ],
        )
        code = (
            "class Character:\n"
            "    def __init__(self, name, health):\n"
            "        self.name = name\n"
            "        self.health = health\n"
        )
        self.assertTrue(self.checker.check(exercise, code=code).passed)

    def test_raises_check(self) -> None:
        exercise = Exercise(
            id="t_raises",
            type="write_code",
            title="raises",
            prompt="boom",
            tests=[TestCase(kind="raises", expression="boom()", expected="ValueError")],
        )
        code = "def boom():\n    raise ValueError('nope')\n"
        self.assertTrue(self.checker.check(exercise, code=code).passed)

    def test_predict_output_does_not_reveal_answer(self) -> None:
        lesson = self.catalog.get("fundamentals_01_print")
        assert lesson is not None
        exercise = next(ex for ex in lesson.exercises if ex.id == "fundamentals_01_ex1")
        # V3.2: expected is "hello"
        wrong = self.checker.check(exercise, answer="HELLO")
        self.assertFalse(wrong.passed)
        self.assertNotIn("hello", (wrong.message or "").lower())
        self.assertTrue(
            self.checker.check(
                exercise, answer="hello"
            ).passed
        )

    def test_timeout_during_check(self) -> None:
        exercise = Exercise(
            id="t_loop",
            type="write_code",
            title="loop",
            prompt="don't loop",
            tests=[TestCase(kind="stdout_equals", expected="hi\n")],
        )
        checker = ExerciseChecker(CodeRunner(timeout=0.4))
        result = checker.check(exercise, code="while True:\n    pass\n")
        self.assertFalse(result.passed)
        self.assertEqual(result.message, TIMEOUT_MESSAGE)


class ProgressTests(unittest.TestCase):
    def test_save_load_unlock_and_reset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            store = ProgressStore(path)
            store.load()
            catalog = CourseCatalog(ROOT / "course" / "lessons")
            catalog.load()
            controller = CourseController(catalog, store, ExerciseChecker())

            first = catalog.lessons[0]
            second = catalog.lessons[1]
            self.assertTrue(controller.is_unlocked(first))
            self.assertFalse(controller.is_unlocked(second))

            for exercise in first.exercises:
                if exercise.is_code_exercise:
                    code = exercise.reference_solution
                    self.assertTrue(code.strip(), f"missing reference_solution for {exercise.id}")
                    result = controller.submit_exercise(first, exercise, code=code)
                else:
                    answer = exercise.expected_answer or (exercise.choices[0] if exercise.choices else "")
                    self.assertTrue(str(answer).strip(), f"missing expected_answer for {exercise.id}")
                    result = controller.submit_exercise(first, exercise, answer=str(answer))
                self.assertTrue(result.passed, f"{exercise.id}: {result.message}")

            record = store.exercise(first.exercises[0].id)
            self.assertGreaterEqual(record.attempts, 1)
            self.assertTrue(controller.is_unlocked(second))

            store2 = ProgressStore(path)
            store2.load()
            controller2 = CourseController(catalog, store2, ExerciseChecker())
            self.assertTrue(controller2.is_unlocked(second))
            self.assertTrue(store2.is_lesson_complete(first.id, first.exercise_ids))
            self.assertGreaterEqual(store2.exercise(first.exercises[0].id).attempts, 1)

            store2.reset()
            controller3 = CourseController(catalog, store2, ExerciseChecker())
            self.assertFalse(controller3.is_unlocked(second))
            self.assertFalse(store2.is_exercise_complete(first.exercises[0].id))


class EndToEndLessonFlowTests(unittest.TestCase):
    def test_complete_learning_loop_with_drafts_hints_and_reload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            lessons_src = ROOT / "course" / "lessons"
            lessons_dst = tmp_path / "course" / "lessons"
            lessons_dst.mkdir(parents=True)
            for path in lessons_src.glob("*.json"):
                lessons_dst.joinpath(path.name).write_text(
                    path.read_text(encoding="utf-8"), encoding="utf-8"
                )

            data_dir = tmp_path / "data"
            data_dir.mkdir()
            catalog = CourseCatalog(lessons_dst)
            catalog.load()
            progress = ProgressStore(data_dir / "progress.json")
            progress.load()
            controller = CourseController(catalog, progress, ExerciseChecker())
            lesson = catalog.first()
            assert lesson is not None
            second = catalog.lessons[1]

            exercise = lesson.exercises[0]
            if exercise.is_code_exercise:
                bad = controller.submit_exercise(lesson, exercise, code="print('Nope')")
            else:
                bad = controller.submit_exercise(lesson, exercise, answer="Nope")
            self.assertFalse(bad.passed)

            used1, hint1 = controller.request_hint(exercise)
            used2, hint2 = controller.request_hint(exercise)
            self.assertEqual(used1, 1)
            self.assertEqual(used2, 2)
            self.assertIsNotNone(hint1)
            self.assertIsNotNone(hint2)
            self.assertNotEqual(hint1, hint2)

            progress.save_draft(exercise.id, "print('unfinished draft')", "")
            progress.data.current_lesson_id = lesson.id
            progress.save()

            # Simulate close/reopen before finishing.
            progress_reopen = ProgressStore(data_dir / "progress.json")
            progress_reopen.load()
            self.assertIn("unfinished draft", progress_reopen.exercise(exercise.id).draft_code)
            self.assertEqual(progress_reopen.exercise(exercise.id).hints_used, 2)
            self.assertEqual(progress_reopen.exercise(exercise.id).attempts, 1)
            self.assertFalse(controller.is_unlocked(second))

            controller = CourseController(catalog, progress_reopen, ExerciseChecker())
            if exercise.is_code_exercise:
                code = exercise.reference_solution
                self.assertTrue(code.strip(), f"missing reference_solution for {exercise.id}")
                good = controller.submit_exercise(lesson, exercise, code=code)
            else:
                answer = exercise.expected_answer or (exercise.choices[0] if exercise.choices else "")
                self.assertTrue(str(answer).strip(), f"missing expected_answer for {exercise.id}")
                good = controller.submit_exercise(lesson, exercise, answer=str(answer))
            self.assertTrue(good.passed, good.message)

            for remaining in lesson.exercises[1:]:
                if remaining.is_code_exercise:
                    code = remaining.reference_solution
                    self.assertTrue(code.strip(), f"missing reference_solution for {remaining.id}")
                    result = controller.submit_exercise(lesson, remaining, code=code)
                else:
                    answer = remaining.expected_answer or (remaining.choices[0] if remaining.choices else "")
                    self.assertTrue(str(answer).strip(), f"missing expected_answer for {remaining.id}")
                    result = controller.submit_exercise(lesson, remaining, answer=str(answer))
                self.assertTrue(result.passed, f"{remaining.id}: {result.message}")

            self.assertTrue(controller.is_unlocked(second))
            self.assertTrue(
                progress_reopen.is_lesson_complete(lesson.id, lesson.exercise_ids)
            )


class BuildControllerTests(unittest.TestCase):
    def test_build_controller(self) -> None:
        controller, runner = build_controller(ROOT)[:2]
        self.assertGreaterEqual(len(controller.catalog.lessons), 8)
        self.assertIsInstance(runner, CodeRunner)


if __name__ == "__main__":
    unittest.main()
