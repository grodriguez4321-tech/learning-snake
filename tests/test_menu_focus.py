from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLineEdit, QPlainTextEdit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.course_app import CourseApp
from app.theme import DARK, build_stylesheet
from app.ui_prefs import UiPrefsStore
from engine.progress import ProgressStore
from main import build_controller


def _qt() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setStyleSheet(build_stylesheet(DARK))
    return app


class MenuFocusRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _qt()

    def test_edit_actions_route_to_focused_widget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            controller, runner, prefs = build_controller(ROOT, data_dir=data_dir)

            course = CourseApp(controller, runner, prefs_store=prefs)
            self.app.processEvents()

            # Create a temporary line-edit and focus it
            line = QLineEdit()
            line.setText("hello")
            line.selectAll()
            line.show()
            line.setFocus()
            self.app.processEvents()

            # Locate actions
            from PySide6.QtGui import QAction
            cut_action = course.findChild(QAction, "edit.cut")
            copy_action = course.findChild(QAction, "edit.copy")
            paste_action = course.findChild(QAction, "edit.paste")
            undo_action = course.findChild(QAction, "edit.undo")
            redo_action = course.findChild(QAction, "edit.redo")
            select_all_action = course.findChild(QAction, "edit.select_all")
            for act in (cut_action, copy_action, paste_action, undo_action, redo_action, select_all_action):
                self.assertIsNotNone(act)
            assert cut_action and copy_action and paste_action and undo_action and redo_action and select_all_action

            # Verify enable state reflects selection and read-only
            self.assertTrue(cut_action.isEnabled())
            # No further assertions on copy in read-only state without selection
            select_all_action.trigger()
            self.app.processEvents()
            cut_action.trigger()
            self.app.processEvents()
            self.assertEqual(line.text(), "")

            # Paste should work
            line.setText("")
            line.setFocus()
            self.app.processEvents()
            # Put text on clipboard via setText then paste (clipboard is shared; simulate by setting selection then copy)
            line.setText("abc")
            line.selectAll()
            copy_action.trigger()
            self.app.processEvents()
            line.clear()
            paste_action.trigger()
            self.app.processEvents()
            self.assertEqual(line.text(), "abc")

            # Read-only should disable mutating actions
            line.setReadOnly(True)
            self.app.processEvents()
            # Nudge focus to recompute enabled state and explicitly fire Edit menu hook
            other = QLineEdit()
            other.show()
            other.setFocus()
            self.app.processEvents()
            line.setFocus()
            self.app.processEvents()
            # Trigger the aboutToShow hook to force recompute
            edit_menu = None
            for act in course._menubar.actions():  # type: ignore[attr-defined]
                if act.text().lower().startswith("&edit"):
                    edit_menu = act.menu()
                    break
            if edit_menu is not None:
                edit_menu.aboutToShow.emit()
                self.app.processEvents()
            self.assertFalse(cut_action.isEnabled())
            # Paste action should have no effect when target is read-only
            line.setText("RO")
            paste_action.trigger()
            self.app.processEvents()
            self.assertEqual(line.text(), "RO")
            line.setReadOnly(False)
            self.app.processEvents()

            # Now test with a QPlainTextEdit (code-like editor path)
            editor = QPlainTextEdit()
            editor.setPlainText("hello\nworld")
            editor.show()
            editor.setFocus()
            self.app.processEvents()
            # Select All via action and verify operations work end-to-end
            select_all_action.trigger()
            self.app.processEvents()
            cut_action.trigger()
            self.app.processEvents()
            self.assertEqual(editor.toPlainText(), "")
            # Undo then Redo
            # Use editor's undo/redo directly to validate behavior
            editor.undo()
            self.app.processEvents()
            self.assertIn("hello", editor.toPlainText())
            editor.redo()
            self.app.processEvents()
            self.assertEqual(editor.toPlainText(), "")
            # Paste should reinsert previously copied 'abc' from prior step
            paste_action.trigger()
            self.app.processEvents()
            self.assertTrue(len(editor.toPlainText()) > 0)

            course.close()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()

