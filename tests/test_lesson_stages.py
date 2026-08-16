"""Three-stage lesson UI and menu bar tests (offscreen Qt)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QAction

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.course_app import CourseApp  # noqa: E402
from app.theme import DARK, build_stylesheet  # noqa: E402
from engine.progress import ProgressStore  # noqa: E402
from main import build_controller  # noqa: E402


def _qt() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setStyleSheet(build_stylesheet(DARK))
    return app


class LessonStagesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def _new_course(self) -> CourseApp:
        controller, runner, prefs = build_controller(ROOT)
        # use a temp progress file
        tmp = tempfile.TemporaryDirectory()
        progress_path = Path(tmp.name) / "progress.json"
        controller.progress = ProgressStore(progress_path)
        controller.progress.load()
        course = CourseApp(controller, runner, prefs_store=prefs)
        course.show()
        self.app.processEvents()
        # attach tempdir to instance to keep it alive
        course._tmpdir = tmp  # type: ignore[attr-defined]
        return course

    def test_stage_navigation_and_content_groups(self) -> None:
        course = self._new_course()
        content = course.lessons_page.content
        # default: Learn stage, IDE hidden
        content.set_stage("learn")
        self.app.processEvents()
        self.assertFalse(course.lessons_page.ide.isVisible())
        self.assertTrue(content._explanation.isVisible())
        # Examples: IDE hidden, examples visible
        content.set_stage("examples")
        self.app.processEvents()
        self.assertFalse(course.lessons_page.ide.isVisible())
        self.assertTrue(content._examples.isVisible())
        # Practice: IDE follows preference and exercise visible
        content.set_stage("practice")
        self.app.processEvents()
        self.assertEqual(course.prefs_store.prefs.editor_visible, course._editor_visible)
        self.assertEqual(course.lessons_page.ide.isVisible(), course._editor_visible)
        self.assertTrue(content._exercise.isVisible())
        course.close()

    def test_learn_examples_do_not_change_editor_preference(self) -> None:
        course = self._new_course()
        before = course.prefs_store.prefs.editor_visible
        course.lessons_page.content.set_stage("learn")
        self.app.processEvents()
        self.assertEqual(course.prefs_store.prefs.editor_visible, before)
        course.lessons_page.content.set_stage("examples")
        self.app.processEvents()
        self.assertEqual(course.prefs_store.prefs.editor_visible, before)
        course.close()

    def test_stage_restored_after_dashboard_nav(self) -> None:
        course = self._new_course()
        course.lessons_page.content.set_stage("examples")
        self.app.processEvents()
        course._on_nav("dashboard")
        self.app.processEvents()
        course._on_nav("lessons")
        self.app.processEvents()
        # Should still be in Examples
        self.assertFalse(course.lessons_page.ide.isVisible())
        self.assertTrue(course.lessons_page.content._examples.isVisible())
        course.close()


class MenuBarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def test_menubar_structure_and_actions(self) -> None:
        course = CourseApp(*build_controller(ROOT)[:2])
        course.show()
        self.app.processEvents()
        # File menu actions
        save: QAction | None = course.findChild(QAction, "actionFileSaveProgress")
        self.assertIsNotNone(save)
        exit_act: QAction | None = course.findChild(QAction, "actionFileExit")
        self.assertIsNotNone(exit_act)
        # Edit menu actions
        for name in (
            "actionEditUndo",
            "actionEditRedo",
            "actionEditCut",
            "actionEditCopy",
            "actionEditPaste",
            "actionEditSelectAll",
        ):
            self.assertIsNotNone(course.findChild(QAction, name), name)
        # View menu actions
        view_sidebar: QAction | None = course.findChild(QAction, "actionViewSidebar")
        view_editor: QAction | None = course.findChild(QAction, "actionViewEditor")
        toggle_theme: QAction | None = course.findChild(QAction, "actionViewToggleTheme")
        self.assertIsNotNone(view_sidebar)
        self.assertIsNotNone(view_editor)
        self.assertIsNotNone(toggle_theme)
        # Help menu actions
        kb: QAction | None = course.findChild(QAction, "actionHelpShortcuts")
        about: QAction | None = course.findChild(QAction, "actionHelpAbout")
        self.assertIsNotNone(kb)
        self.assertIsNotNone(about)
        course.close()

