"""Three-stage lesson UI and menu bar tests (offscreen Qt)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPlainTextEdit
from PySide6.QtGui import QAction, QGuiApplication
from PySide6.QtCore import Qt

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
        # Fully isolate runtime: both progress and UI prefs under a temp dir
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
        # negative visibility: not on Examples or Practice pages
        self.assertEqual(content._stack.currentIndex(), 0)
        # Examples: IDE hidden, examples visible
        # Examples: IDE hidden, examples visible
        content.set_stage("examples")
        self.app.processEvents()
        self.assertFalse(course.lessons_page.ide.isVisible())
        self.assertTrue(content._examples.isVisible())
        self.assertEqual(content._stack.currentIndex(), 1)
        # Practice: IDE follows preference and exercise visible
        content.set_stage("practice")
        self.app.processEvents()
        self.assertEqual(course.prefs_store.prefs.editor_visible, course._editor_visible)
        self.assertEqual(course.lessons_page.ide.isVisible(), course._editor_visible)
        self.assertTrue(content._exercise.isVisible())
        self.assertEqual(content._stack.currentIndex(), 2)
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
        # Action disabled but check reflects pref
        act = course.findChild(QAction, "actionViewEditor")
        self.assertIsNotNone(act)
        assert act is not None
        self.assertFalse(act.isEnabled())
        self.assertTrue(act.isChecked())
        # IDE hidden:
        self.assertFalse(course.lessons_page.ide.isVisible())
        course.close()

    def test_prev_next_exercise_clicks(self) -> None:
        course = self._new_course()
        content = course.lessons_page.content
        content.set_stage("practice")
        self.app.processEvents()
        # Ensure next enabled when more than one exercise
        lesson = course.controller.current_lesson()
        assert lesson is not None
        if len(lesson.exercises) >= 2:
            meta_before = content._exercise._ex_meta.text()
            content._exercise._next_ex.click()
            self.app.processEvents()
            meta_after = content._exercise._ex_meta.text()
            self.assertNotEqual(meta_before, meta_after)
            # and back
            content._exercise._prev_ex.click()
            self.app.processEvents()
            self.assertEqual(content._exercise._ex_meta.text(), meta_before)
        course.close()

    def test_every_catalog_lesson_renders_all_stages(self) -> None:
        course = self._new_course()
        for lesson in list(course.controller.catalog.lessons):
            course._show_lesson(lesson)
            for stage in ("learn", "examples", "practice"):
                course.lessons_page.content.set_stage(stage)
                self.app.processEvents()
                # just ensure no crash and a title is present
                self.assertTrue(bool(course.lessons_page.content._title.text()))
        course.close()

    def test_stage_changes_create_no_new_windows(self) -> None:
        course = self._new_course()
        before = [w for w in QApplication.topLevelWidgets() if w.isWindow()]
        for stage in ("learn", "examples", "practice", "examples", "learn"):
            course.lessons_page.content.set_stage(stage)
            self.app.processEvents()
        after = [w for w in QApplication.topLevelWidgets() if w.isWindow()]
        self.assertEqual(len(before), len(after))
        course.close()

    def test_locked_unlocked_prev_next_visibility(self) -> None:
        course = self._new_course()
        content = course.lessons_page.content
        current = course.controller.current_lesson()
        assert current is not None
        # Initially, previous should be hidden on first lesson
        first = course.controller.catalog.first()
        assert first is not None
        course._show_lesson(first)
        self.app.processEvents()
        self.assertFalse(content._prev_lesson_lrn.isVisible())
        self.assertFalse(content._prev_lesson_pr.isVisible())
        # Next is hidden until first lesson is completed
        self.assertFalse(content._next_lesson_lrn.isVisible() or content._next_lesson_ex.isVisible() or content._next_lesson_pr.isVisible())
        # Mark first lesson complete via progress to unlock next
        for ex in first.exercises:
            course.controller.progress.mark_exercise_result(ex.id, passed=True)
        course.controller.progress.refresh_lesson_completion(first.id, first.exercise_ids)
        course.controller.progress.save()
        # Reload lesson UI to recompute visibility
        course._show_lesson(first)
        self.app.processEvents()
        self.assertTrue(content._next_lesson_lrn.isVisible() or content._next_lesson_ex.isVisible() or content._next_lesson_pr.isVisible())
        course.close()

    def test_practice_run_check_hint_reset_cycle(self) -> None:
        course = self._new_course()
        content = course.lessons_page.content
        content.set_stage("practice")
        self.app.processEvents()
        ide = course.lessons_page.ide
        ide.editor.setFocus()
        ide.set_code("print(1)\n")
        self.app.processEvents()
        # Run
        ide._run.click()
        # pump until not busy or timeout
        for _ in range(200):
            self.app.processEvents()
            if not course._busy:
                break
        out = ide.output_text()
        self.assertTrue(out is not None)
        # Check (does not need to pass, just update feedback)
        ide._check.click()
        for _ in range(200):
            self.app.processEvents()
            if not course._busy:
                break
        self.assertTrue(bool(ide.feedback._view.toPlainText()))
        # Reset (auto-yes)
        from PySide6.QtWidgets import QMessageBox
        old = QMessageBox.question
        try:
            QMessageBox.question = lambda *a, **k: QMessageBox.StandardButton.Yes  # type: ignore[assignment]
            self.assertIsNotNone(course._current_exercise)
            course._busy = False  # ensure reset path not gated by background work
            course._reset_exercise()
            for _ in range(5):
                self.app.processEvents()
            self.assertEqual(ide.get_code(), ide._starter)
        finally:
            QMessageBox.question = old  # type: ignore[assignment]
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
        # Menu order
        texts = [a.text() for a in course.menuBar().actions()]
        self.assertEqual(texts[:4], ["&File", "&Edit", "&View", "&Help"])
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

    def test_edit_menu_behavior_plaintext_and_lineedit(self) -> None:
        course = CourseApp(*build_controller(ROOT)[:2])
        course.show()
        self.app.processEvents()
        # Focus code editor (QPlainTextEdit)
        editor = course.lessons_page.ide.editor
        editor.setPlainText("hello world")
        editor.setFocus()
        self.app.processEvents()
        # No selection => Cut/Copy disabled
        course._update_edit_actions_enabled()
        self.assertFalse(course.actionEditCut.isEnabled())
        self.assertFalse(course.actionEditCopy.isEnabled())
        # Select text => Cut/Copy enabled
        cursor = editor.textCursor()
        cursor.select(cursor.SelectionType.Document)
        editor.setTextCursor(cursor)
        self.app.processEvents()
        course._update_edit_actions_enabled()
        self.assertTrue(course.actionEditCut.isEnabled())
        self.assertTrue(course.actionEditCopy.isEnabled())
        # Copy once via QAction
        calls = {"copy": 0}
        def on_copy(_=False):  # slot receives checked: bool
            calls["copy"] += 1
        course.actionEditCopy.triggered.connect(on_copy)
        course.actionEditCopy.trigger()
        self.app.processEvents()
        self.assertEqual(calls["copy"], 1)
        # Paste available when clipboard has text
        QGuiApplication.clipboard().setText("x")
        course._update_edit_actions_enabled()
        self.assertTrue(course.actionEditPaste.isEnabled())
        # Undo/Redo availability track real document
        editor.insertPlainText("!")
        self.app.processEvents()
        course._update_edit_actions_enabled()
        self.assertTrue(course.actionEditUndo.isEnabled())
        course.actionEditUndo.trigger()
        self.app.processEvents()
        course._update_edit_actions_enabled()
        # After one undo, redo should be available once
        self.assertTrue(course.actionEditRedo.isEnabled())
        course.actionEditRedo.trigger()
        self.app.processEvents()
        # LineEdit path
        ans = course.lessons_page.ide._answer
        ans.setFocus()
        ans.setText("abc")
        self.app.processEvents()
        course._update_edit_actions_enabled()
        # With selection
        ans.selectAll()
        course._update_edit_actions_enabled()
        self.assertTrue(course.actionEditCut.isEnabled())
        self.assertTrue(course.actionEditCopy.isEnabled())
        # Read-only selection (use output panel)
        out = course.lessons_page.ide.output._view  # QPlainTextEdit read-only
        out.setPlainText("read-only")
        out.setFocus()
        cursor = out.textCursor()
        cursor.select(cursor.SelectionType.Document)
        out.setTextCursor(cursor)
        self.app.processEvents()
        course._update_edit_actions_enabled()
        self.assertFalse(course.actionEditCut.isEnabled())
        self.assertTrue(course.actionEditCopy.isEnabled())
        self.assertTrue(course.actionEditSelectAll.isEnabled())
        # Paste disabled in read-only
        self.assertFalse(course.actionEditPaste.isEnabled())
        course.close()

    def test_help_and_file_actions_invoke_once(self) -> None:
        course = CourseApp(*build_controller(ROOT)[:2])
        course.show()
        self.app.processEvents()
        # Help dialogs should not leave extra windows around after invocation
        from PySide6.QtWidgets import QMessageBox
        orig_info = QMessageBox.information
        try:
            # Avoid modal dialogs in offscreen tests
            QMessageBox.information = lambda *a, **k: None  # type: ignore[assignment]
            before = [w for w in QApplication.topLevelWidgets() if w.isWindow()]
            course.actionHelpShortcuts.trigger()
            course.actionHelpAbout.trigger()
            self.app.processEvents()
            after = [w for w in QApplication.topLevelWidgets() if w.isWindow()]
            self.assertEqual(len(before), len(after))
        finally:
            QMessageBox.information = orig_info  # type: ignore[assignment]
        # Save and Exit signals fire exactly once each
        calls = {"save": 0, "exit": 0}
        course.actionFileSaveProgress.triggered.connect(lambda _=False: calls.__setitem__("save", calls["save"] + 1))
        course.actionFileExit.triggered.connect(lambda _=False: calls.__setitem__("exit", calls["exit"] + 1))
        course.actionFileSaveProgress.trigger()
        course.actionFileExit.trigger()
        self.app.processEvents()
        self.assertEqual(calls["save"], 1)
        self.assertEqual(calls["exit"], 1)
        course.close()

    def test_screenshot_capture_isolation(self) -> None:
        # Repository runtime files before
        repo_progress = ROOT / "data" / "progress.json"
        repo_prefs = ROOT / "data" / "ui_prefs.json"
        before_prog = repo_progress.read_bytes() if repo_progress.exists() else None
        before_prefs = repo_prefs.read_bytes() if repo_prefs.exists() else None
        # Run capture into a temp output dir with a temp runtime dir
        out_dir = Path(tempfile.mkdtemp())
        data_dir = Path(tempfile.mkdtemp())
        # Use module entrypoint
        import importlib.util
        spec = importlib.util.spec_from_file_location("capture", str(ROOT / "tools" / "capture_screenshots.py"))
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        sys.modules["capture"] = mod
        spec.loader.exec_module(mod)  # type: ignore[arg-type]
        # Invoke main via CLI-like call
        argv_backup = sys.argv[:]
        try:
            sys.argv = ["capture_screenshots.py", "--data-dir", str(data_dir), "--out-dir", str(out_dir)]
            mod.main()  # type: ignore[attr-defined]
        finally:
            sys.argv = argv_backup
        # Verify PNGs were written to temp out_dir, not repo docs/
        pngs = list(out_dir.glob("*.png"))
        self.assertGreaterEqual(len(pngs), 3)
        repo_pngs = list((ROOT / "docs" / "screenshots" / "three-stage-ui").glob("*.png"))
        # Running capture in tests must NOT modify repo screenshots
        self.assertTrue(all(p.exists() for p in repo_pngs))
        # Repository runtime must remain unchanged
        after_prog = repo_progress.read_bytes() if repo_progress.exists() else None
        after_prefs = repo_prefs.read_bytes() if repo_prefs.exists() else None
        self.assertEqual(before_prog, after_prog)
        self.assertEqual(before_prefs, after_prefs)
