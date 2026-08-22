from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from course.catalog import CourseCatalog
from engine.code_runner import CodeRunner
from engine.course_controller import CourseController
from engine.exercise_checker import ExerciseChecker
from engine.progress import CURRENT_CURRICULUM_VERSION, ProgressStore

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(CURRENT_CURRICULUM_VERSION < 3, "V3.2 contract tests only run on curriculum v3+")
class V32ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = CourseCatalog(ROOT / "course" / "lessons")
        self.catalog.load()

    def test_exact_catalog_order_and_counts(self) -> None:
        expected_ids = [
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
            "collections_14_dict_iteration",
            "collections_15_while",
            "functions_16_parameters",
            "functions_17_defaults",
            "functions_18_returning_data",
            "collections_19_nested_data",
            "functions_20_scope",
            "strings_21_methods",
            "errors_22_tracebacks",
            "errors_23_logic_debugging",
            "data_24_shared_references",
            "oop_25_classes_objects",
            "oop_26_init_self",
            "oop_27_methods",
            "oop_28_composition",
        ]
        actual_ids = [lesson.id for lesson in self.catalog.lessons]
        self.assertEqual(actual_ids, expected_ids)
        self.assertEqual(len(self.catalog.lessons), 28)
        exercises = [ex for l in self.catalog.lessons for ex in l.exercises]
        self.assertEqual(len(exercises), 214)
        projects = [ex for ex in exercises if ex.type == "mini_project"]
        self.assertEqual(len(projects), 23)

    def test_every_runnable_has_three_hints(self) -> None:
        for lesson in self.catalog.lessons:
            for exercise in lesson.exercises:
                if exercise.is_code_exercise or exercise.type in {"predict_output", "architecture"}:
                    self.assertEqual(len(exercise.hints), 3, exercise.id)

    def test_reference_solutions_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            progress = ProgressStore(Path(tmp) / "progress.json")
            progress.load()
            checker = ExerciseChecker(CodeRunner(timeout=2.0))
            controller = CourseController(self.catalog, progress, checker)
            for lesson in self.catalog.lessons:
                for exercise in lesson.exercises:
                    if exercise.is_code_exercise:
                        code = exercise.reference_solution
                        self.assertTrue(code.strip(), f"missing reference_solution for {exercise.id}")
                        result = controller.submit_exercise(lesson, exercise, code=code)
                    else:
                        answer = exercise.expected_answer or (exercise.choices[0] if exercise.choices else "")
                        self.assertTrue(str(answer).strip(), f"missing expected_answer for {exercise.id}")
                        result = controller.submit_exercise(lesson, exercise, answer=str(answer))
                    self.assertTrue(result.passed, f"{exercise.id}: {result.message}")
