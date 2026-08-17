"""Three-stage lesson UI and menu bar tests (offscreen Qt)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget
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
        # Use a temporary runtime directory for both progress and UI prefs
        tmp = tempfile.TemporaryDirectory()
        controller, runner, prefs = build_controller(ROOT, data_dir=Path(tmp.name))
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

    def test_back_and_forth_through_all_stages(self) -> None:
        course = self._new_course()
        content = course.lessons_page.content
        for stage in ("learn", "examples", "practice", "examples", "learn"):
            content.set_stage(stage)
            self.app.processEvents()
        # back on learn, ide still hidden but pref unchanged
        self.assertFalse(course.lessons_page.ide.isVisible())
        self.assertEqual(course.prefs_store.prefs.editor_visible, course._editor_visible)
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

    def test_active_exercise_persists_in_session(self) -> None:
        course = self._new_course()
        lesson = course.controller.current_lesson()
        assert lesson is not None
        # move to last exercise
        last_index = len(lesson.exercises) - 1
        course._show_lesson(lesson, last_index)
        self.app.processEvents()
        # navigate away and back; still on last exercise
        course._on_nav("dashboard")
        self.app.processEvents()
        course._on_nav("lessons")
        self.app.processEvents()
        # Check exercise meta shows last index (1-based)
        label = course.lessons_page.content._exercise._ex_meta.text()
        self.assertIn(f"{last_index + 1}", label)
        course.close()

    def test_view_menu_editor_state_reflects_prefs_on_reading_stage(self) -> None:
        course = self._new_course()
        content = course.lessons_page.content
        # Ensure pref is True
        course.prefs_store.update(editor_visible=True)
        course._editor_visible = True
        content.set_stage("learn")
        self.app.processEvents()
        # Action disabled and visually unchecked while saved pref remains True
        act = course.findChild(QAction, "actionViewEditor")
        self.assertIsNotNone(act)
        assert act is not None
        self.assertFalse(act.isEnabled())
        self.assertFalse(act.isChecked())
        # IDE hidden:
        self.assertFalse(course.lessons_page.ide.isVisible())
        course.close()

    def test_stage_buttons_navigate(self) -> None:
        course = self._new_course()
        content = course.lessons_page.content
        # Start on learn
        self.assertTrue(content._explanation.isVisible())
        # Click to examples
        content._to_examples.click()
        self.app.processEvents()
        self.assertTrue(content._examples.isVisible())
        # Start practice
        content._start_practice.click()
        self.app.processEvents()
        self.assertTrue(content._exercise.isVisible())
        # Back to learn
        content._back_to_learn.click()
        self.app.processEvents()
        self.assertTrue(content._explanation.isVisible())
        # Toolbar reflects pref while IDE is hidden
        course.close()

    def test_readable_width_container(self) -> None:
        course = self._new_course()
        course.resize(1400, 900)
        self.app.processEvents()
        content = course.lessons_page.content
        content.set_stage("learn")
        self.app.processEvents()
        # Column should be centered and capped
        col = course.findChild(QWidget, "ContentColumn")
        self.assertIsNotNone(col)
        assert col is not None
        self.assertLessEqual(col.width(), 960)
        course.close()


class MenuBarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def test_menubar_structure_and_actions(self) -> None:
        # Isolate runtime state
        tmp = tempfile.TemporaryDirectory()
        controller, runner, prefs = build_controller(ROOT, data_dir=Path(tmp.name))
        course = CourseApp(controller, runner, prefs_store=prefs)
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

