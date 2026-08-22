"""Regression tests for Phase 2 UI prerequisites (offscreen Qt)."""

from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.course_app import CourseApp
from app.theme import DARK, build_stylesheet
from app.widgets.ide_panel import IdePanel
from app.widgets.lesson_content import ExerciseCard
from course.exercise import Exercise
from engine.progress import ProgressStore
from main import build_controller


def _qt() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setStyleSheet(build_stylesheet(DARK))
    return app


def _wait_until(qt: QApplication, course: CourseApp, timeout: float = 8.0) -> None:
    deadline = time.monotonic() + timeout
    while course._busy:
        if time.monotonic() >= deadline:
            raise TimeoutError("Timed out waiting for background work")
        qt.processEvents()
        time.sleep(0.05)
    qt.processEvents()


class IdePanelChoiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def test_choice_radios_set_answer(self) -> None:
        panel = IdePanel(DARK)
        panel.set_choices(["Only print", "Return the new health"])
        panel.set_answer("2")
        self.assertEqual(panel.get_answer(), "2")
        panel.set_answer("Return the new health")
        self.assertEqual(panel.get_answer(), "2")

    def test_clear_choices_restores_text_answer(self) -> None:
        panel = IdePanel(DARK)
        panel.set_choices(["A", "B"])
        panel.clear_choices()
        panel.set_answer_visible(True)
        panel.set_answer("HP: 100")
        self.assertEqual(panel.get_answer(), "HP: 100")


class ExerciseCardPredictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def test_predict_panel_auto_sizes_for_multiline_code(self) -> None:
        card = ExerciseCard()
        lines = "\n".join(f"print({index})" for index in range(8))
        exercise = Exercise(
            id="t_predict",
            type="predict_output",
            title="Predict",
            prompt="What prints?",
            code_to_predict=lines,
            expected_answer="0",
        )
        card.set_exercise(exercise, index=0, total=1)
        self.assertGreater(card._predict.maximumHeight(), 88)

    def test_architecture_choices_render_in_card(self) -> None:
        card = ExerciseCard()
        exercise = Exercise(
            id="t_arch",
            type="architecture",
            title="Design",
            prompt="Should heal print or return?",
            choices=["Only print", "Return the new health"],
            expected_answer="2",
        )
        card.set_exercise(exercise, index=0, total=1)
        html = card._choices_label.text()
        self.assertIn("Only print", html)
        self.assertIn("Return the new health", html)


class RunCheckSeparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def test_check_does_not_clear_run_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            progress_path = Path(tmp) / "progress.json"
            controller, runner, prefs = build_controller(ROOT)
            controller.progress = ProgressStore(progress_path)
            controller.progress.load()
            course = CourseApp(controller, runner, prefs_store=prefs)
            course.show()
            self.app.processEvents()

            lesson = controller.catalog.get("fundamentals_01_print")
            assert lesson is not None
            write_ex = next(ex for ex in lesson.exercises if ex.id == "fundamentals_01_ex3")
            idx = lesson.exercises.index(write_ex)
            course._show_lesson(lesson, idx)
            self.app.processEvents()

            course.editor.set_code(
                '# Search dispatch\n'
                'print("SEARCH DISPATCH")\n'
                'print("Expedition:", 17)\n'
                'print("Status: OVERDUE")\n'
            )
            course._run_code()
            _wait_until(self.app, course)
            run_output = course.lessons_page.ide.output_text()
            self.assertIn("SEARCH DISPATCH", run_output)

            course._check_answer()
            _wait_until(self.app, course)
            self.assertIn("SEARCH DISPATCH", course.lessons_page.ide.output_text())
            feedback = course.lessons_page.ide.feedback._view.toPlainText()
            self.assertTrue(
                "Correct" in feedback or "Nice work" in feedback or "passed" in feedback.lower()
                or "Dispatch" in feedback
            )

            course.close()

    def test_hint_goes_to_feedback_not_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            progress_path = Path(tmp) / "progress.json"
            controller, runner, prefs = build_controller(ROOT)
            controller.progress = ProgressStore(progress_path)
            controller.progress.load()
            course = CourseApp(controller, runner, prefs_store=prefs)
            course.show()
            self.app.processEvents()

            lesson = controller.catalog.first()
            assert lesson is not None
            course._show_lesson(lesson, 0)
            self.app.processEvents()

            course._show_hint()
            self.app.processEvents()
            self.assertIn("Hint", course.lessons_page.ide.feedback._view.toPlainText())
            self.assertEqual(course.lessons_page.ide.output_text().strip(), "")

            course.close()

    def test_traceback_stays_in_output_after_failed_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            progress_path = Path(tmp) / "progress.json"
            controller, runner, prefs = build_controller(ROOT)
            controller.progress = ProgressStore(progress_path)
            controller.progress.load()
            course = CourseApp(controller, runner, prefs_store=prefs)
            course.show()
            self.app.processEvents()

            lesson = controller.catalog.first()
            assert lesson is not None
            write_ex = next(ex for ex in lesson.exercises if ex.is_code_exercise)
            course._show_lesson(lesson, lesson.exercises.index(write_ex))
            self.app.processEvents()

            course.editor.set_code("print(missing_name)")
            course._run_code()
            _wait_until(self.app, course)
            run_output = course.lessons_page.ide.output_text()
            self.assertIn("NameError", run_output)

            course._check_answer()
            _wait_until(self.app, course)
            self.assertIn("NameError", course.lessons_page.ide.output_text())
            self.assertTrue(course.lessons_page.ide.feedback._view.toPlainText())

            course.editor.set_code('print("after-check")')
            course._run_code()
            _wait_until(self.app, course)
            self.assertIn("after-check", course.lessons_page.ide.output_text())

            course.close()


class ArchitectureExerciseIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def test_functions_architecture_choice_visible_and_checkable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            progress_path = Path(tmp) / "progress.json"
            controller, runner, prefs = build_controller(ROOT)
            controller.progress = ProgressStore(progress_path)
            controller.progress.load()
            course = CourseApp(controller, runner, prefs_store=prefs)
            course.show()
            self.app.processEvents()

            lesson = controller.catalog.get("functions_01_basics")
            assert lesson is not None
            arch = next(ex for ex in lesson.exercises if ex.id == "functions_01_ex2")
            idx = lesson.exercises.index(arch)
            course._show_lesson(lesson, idx)
            self.app.processEvents()

            ide = course.lessons_page.ide
            course.lessons_page.set_mode("practice")
            self.app.processEvents()
            self.assertTrue(ide._choice_host.isVisible())
            self.assertEqual(len(ide._choice_buttons), 2)
            ide.set_answer("2")
            course._check_answer()
            _wait_until(self.app, course)
            feedback = ide.feedback._view.toPlainText()
            self.assertTrue("Right" in feedback or "Good reasoning" in feedback)
            self.assertTrue(controller.progress.is_exercise_complete(arch.id))

            course.close()


class OutputPanelLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def test_output_panel_has_adequate_minimum_height(self) -> None:
        panel = IdePanel(DARK)
        self.assertGreaterEqual(panel.output._view.minimumHeight(), 140)

    def test_resize_keeps_ide_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            progress_path = Path(tmp) / "progress.json"
            controller, runner, prefs = build_controller(ROOT)
            controller.progress = ProgressStore(progress_path)
            controller.progress.load()
            course = CourseApp(controller, runner, prefs_store=prefs)
            course.show()
            course.lessons_page.set_mode("practice")
            for w, h in ((1920, 1080), (1440, 900), (1200, 700)):
                course.resize(QSize(w, h))
                self.app.processEvents()
            self.assertTrue(course.lessons_page.ide.isVisible())
            course.close()


class LongOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def test_multiline_stdout_visible_in_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            progress_path = Path(tmp) / "progress.json"
            controller, runner, prefs = build_controller(ROOT)
            controller.progress = ProgressStore(progress_path)
            controller.progress.load()
            course = CourseApp(controller, runner, prefs_store=prefs)
            course.show()
            self.app.processEvents()

            lesson = controller.catalog.first()
            assert lesson is not None
            write_ex = next(ex for ex in lesson.exercises if ex.is_code_exercise)
            course._show_lesson(lesson, lesson.exercises.index(write_ex))
            self.app.processEvents()

            code = "\n".join(f'print("line-{index}")' for index in range(6))
            course.editor.set_code(code)
            course._run_code()
            _wait_until(self.app, course)
            output = course.lessons_page.ide.output_text()
            for index in range(6):
                self.assertIn(f"line-{index}", output)

            course.close()


if __name__ == "__main__":
    unittest.main()
