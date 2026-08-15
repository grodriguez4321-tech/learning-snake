from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from engine.course_controller import CourseController  # noqa: E402
from course.catalog import CourseCatalog  # noqa: E402
from main import build_controller  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


class DeveloperPreviewTests(unittest.TestCase):
    def test_normal_mode_unlocks_first_only(self) -> None:
        controller, _, _ = build_controller(ROOT, data_dir=None, developer_mode=False)
        lessons = controller.catalog.lessons
        self.assertTrue(controller.is_unlocked(lessons[0]))
        if len(lessons) >= 2:
            self.assertFalse(controller.is_unlocked(lessons[1]))

    def test_developer_mode_reports_all_unlocked(self) -> None:
        controller, _, _ = build_controller(ROOT, developer_mode=True)
        for lesson in controller.catalog.lessons:
            self.assertTrue(controller.is_unlocked(lesson), lesson.id)

    def test_initial_lesson_selection_and_invalid_id(self) -> None:
        first_id = CourseCatalog(ROOT / "course" / "lessons")
        first_id.load()
        first = first_id.first()
        assert first is not None
        ctrl, _, _ = build_controller(ROOT, developer_mode=True, initial_lesson_id=first.id)
        self.assertEqual(ctrl.current_lesson().id, first.id)  # type: ignore[union-attr]
        with self.assertRaises(ValueError):
            build_controller(ROOT, developer_mode=False, initial_lesson_id="does_not_exist")

    def test_lesson_flag_without_developer_fails(self) -> None:
        with self.assertRaises(ValueError):
            build_controller(ROOT, developer_mode=False, initial_lesson_id="collections_19_nested_data")

    def test_progress_isolated_between_modes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            # Start normal mode and record file state
            normal_path = data_dir / "progress.json"
            dev_path = data_dir / "developer_progress.json"
            ctrl_n, _, _ = build_controller(ROOT, data_dir=data_dir, developer_mode=False)
            # Touch normal progress by saving
            ctrl_n.progress.save()
            before = normal_path.read_bytes() if normal_path.exists() else b""
            # Developer session should not change normal bytes
            ctrl_d, _, _ = build_controller(
                ROOT, data_dir=data_dir, developer_mode=True, initial_lesson_id=ctrl_n.catalog.lessons[-1].id
            )
            # Simulate a developer action: mark a hint used and save
            lesson = ctrl_d.catalog.lessons[-1]
            ex = lesson.exercises[0]
            ctrl_d.request_hint(ex)
            ctrl_d.progress.save()
            self.assertTrue(dev_path.exists())
            after = normal_path.read_bytes() if normal_path.exists() else b""
            self.assertEqual(before, after)

    def test_window_title_and_notice_in_developer_mode(self) -> None:
        try:
            from PySide6.QtWidgets import QApplication  # type: ignore
            from app.course_app import CourseApp  # type: ignore
        except Exception:
            self.skipTest("Qt platform not available in this environment")
            return
        app = QApplication.instance() or QApplication([])
        ctrl, runner, prefs = build_controller(ROOT, developer_mode=True)
        win = CourseApp(ctrl, runner, prefs_store=prefs)
        try:
            self.assertIn("Developer Preview", win.windowTitle())
            win._on_nav("settings")
            found = False
            for child in win.settings_page.findChildren(type(win.dashboard_page._summary)):
                try:
                    if "Developer Preview is active" in child.text():
                        found = True
                        break
                except Exception:
                    continue
            self.assertTrue(found)
        finally:
            win.close()


if __name__ == "__main__":
    unittest.main()

