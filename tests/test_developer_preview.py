from __future__ import annotations

import os
import tempfile
import subprocess
import shutil
import time
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from engine.course_controller import CourseController  # noqa: E402
from course.catalog import CourseCatalog  # noqa: E402
from main import build_controller  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


class DeveloperPreviewTests(unittest.TestCase):
    def test_normal_mode_unlocks_first_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            controller, _, _ = build_controller(ROOT, data_dir=Path(tmp), developer_mode=False)
            lessons = controller.catalog.lessons
            self.assertTrue(controller.is_unlocked(lessons[0]))
            if len(lessons) >= 2:
                self.assertFalse(controller.is_unlocked(lessons[1]))

    def test_developer_mode_reports_all_unlocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            controller, _, _ = build_controller(ROOT, data_dir=Path(tmp), developer_mode=True)
            for lesson in controller.catalog.lessons:
                self.assertTrue(controller.is_unlocked(lesson), lesson.id)

    def test_initial_lesson_selection_and_invalid_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first_id = CourseCatalog(ROOT / "course" / "lessons")
            first_id.load()
            first = first_id.first()
            assert first is not None
            ctrl, _, _ = build_controller(
                ROOT, data_dir=Path(tmp), developer_mode=True, initial_lesson_id=first.id
            )
            self.assertEqual(ctrl.current_lesson().id, first.id)  # type: ignore[union-attr]
            # Unknown id in developer mode must name the id
            with self.assertRaisesRegex(ValueError, "does_not_exist"):
                build_controller(
                    ROOT, data_dir=Path(tmp), developer_mode=True, initial_lesson_id="does_not_exist"
                )

    def test_lesson_flag_without_developer_fails_and_does_not_touch_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            normal_path = data_dir / "progress.json"
            # Seed representative legacy file (would migrate if loaded)
            legacy = {
                "curriculum_version": 1,
                "completed_lessons": ["fundamentals_01_print"],
                "exercises": {
                    "fundamentals_01_ex1": {
                        "completed": True,
                        "attempts": 2,
                        "hints_used": 1,
                        "draft_code": "print('old')",
                        "last_answer": "",
                    }
                },
            }
            normal_path.parent.mkdir(parents=True, exist_ok=True)
            normal_path.write_text(__import__("json").dumps(legacy), encoding="utf-8")
            before = normal_path.read_bytes()
            with self.assertRaises(ValueError):
                build_controller(
                    ROOT,
                    data_dir=data_dir,
                    developer_mode=False,
                    initial_lesson_id="collections_19_nested_data",
                )
            after = normal_path.read_bytes()
            self.assertEqual(before, after)

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
                ROOT,
                data_dir=data_dir,
                developer_mode=True,
                initial_lesson_id="collections_19_nested_data",
            )
            # Simulate a developer action: mark a hint used and save
            lesson = ctrl_d.catalog.get("collections_19_nested_data")
            assert lesson is not None
            ex = lesson.exercises[0]
            ctrl_d.request_hint(ex)
            ctrl_d.progress.save()
            self.assertTrue(dev_path.exists())
            after = normal_path.read_bytes() if normal_path.exists() else b""
            self.assertEqual(before, after)

    def test_preview_starts_with_no_completions_or_mastery_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctrl, _, _ = build_controller(
                ROOT, data_dir=Path(tmp), developer_mode=True, initial_lesson_id="collections_19_nested_data"
            )
            snap = ctrl.progress.snapshot()
            self.assertEqual(snap["completed_lessons"], [])
            lesson = ctrl.catalog.get("collections_19_nested_data")
            assert lesson is not None
            ex_id = lesson.exercises[0].id
            record = ctrl.progress.exercise(ex_id)
            self.assertFalse(record.completed)
            self.assertEqual(record.attempts, 0)
            self.assertEqual(record.hints_used, 0)

    def test_window_title_and_notice_in_developer_mode(self) -> None:
        try:
            from PySide6.QtWidgets import QApplication  # type: ignore
            from app.course_app import CourseApp  # type: ignore
        except Exception:
            self.skipTest("Qt platform not available in this environment")
            return
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            ctrl, runner, prefs = build_controller(ROOT, data_dir=Path(tmp), developer_mode=True)
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
        # Normal mode negative case
        with tempfile.TemporaryDirectory() as tmp2:
            ctrl2, runner2, prefs2 = build_controller(ROOT, data_dir=Path(tmp2), developer_mode=False)
            win2 = CourseApp(ctrl2, runner2, prefs_store=prefs2)
            try:
                self.assertNotIn("Developer Preview", win2.windowTitle())
                win2._on_nav("settings")
                any_preview = False
                for child in win2.settings_page.findChildren(type(win2.dashboard_page._summary)):
                    try:
                        if "Developer Preview is active" in child.text():
                            any_preview = True
                            break
                    except Exception:
                        continue
                self.assertFalse(any_preview)
            finally:
                win2.close()

    def test_sidebar_enabled_states_normal_vs_preview(self) -> None:
        try:
            from PySide6.QtWidgets import QApplication  # type: ignore
            from app.course_app import CourseApp  # type: ignore
        except Exception:
            self.skipTest("Qt platform not available in this environment")
            return
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            # Normal mode: only first lesson enabled
            ctrl_n, runner_n, prefs_n = build_controller(ROOT, data_dir=Path(tmp), developer_mode=False)
            win_n = CourseApp(ctrl_n, runner_n, prefs_store=prefs_n)
            try:
                enabled_count = sum(1 for row in win_n.sidebar._lesson_rows.values() if row.isEnabled())
                self.assertEqual(enabled_count, 1)
            finally:
                win_n.close()
        with tempfile.TemporaryDirectory() as tmp2:
            ctrl_d, runner_d, prefs_d = build_controller(ROOT, data_dir=Path(tmp2), developer_mode=True)
            win_d = CourseApp(ctrl_d, runner_d, prefs_store=prefs_d)
            try:
                enabled_count = sum(1 for row in win_d.sidebar._lesson_rows.values() if row.isEnabled())
                self.assertEqual(enabled_count, len(ctrl_d.catalog.lessons))
            finally:
                win_d.close()

    def test_cli_subprocess_failures(self) -> None:
        # --lesson without --developer should fail quickly with exit code 2
        proc = subprocess.Popen(
            [sys.executable, str(ROOT / "main.py"), "--lesson", "collections_19_nested_data"],
            cwd=str(ROOT),
            env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        out, err = proc.communicate(timeout=10)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--lesson requires --developer mode", err)
        # Unknown id in developer mode must fail and include the id
        proc2 = subprocess.Popen(
            [sys.executable, str(ROOT / "main.py"), "--developer", "--lesson", "does_not_exist"],
            cwd=str(ROOT),
            env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        out2, err2 = proc2.communicate(timeout=10)
        self.assertEqual(proc2.returncode, 2)
        self.assertIn("Unknown lesson id: does_not_exist", err2)

    def test_cli_subprocess_valid_preview_starts(self) -> None:
        # Isolated runtime copy; confirm process remains alive and only developer progress is written.
        try:
            from PySide6 import QtWidgets as _  # type: ignore
        except Exception:
            self.skipTest("Qt platform not available in this environment")
            return
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "copy"
            shutil.copytree(
                ROOT, run_root, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "data")
            )
            env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
            proc = subprocess.Popen(
                [sys.executable, str(run_root / "main.py"), "--developer", "--lesson", "collections_19_nested_data"],
                cwd=str(run_root),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                deadline = time.time() + 1.5
                while time.time() < deadline:
                    if proc.poll() is not None:
                        out, err = proc.communicate(timeout=1)
                        self.fail(f"preview exited early: rc={proc.returncode}\nSTDERR:\n{err}\nSTDOUT:\n{out}")
                    time.sleep(0.05)
                self.assertIsNone(proc.poll())
                dev = run_root / "data" / "developer_progress.json"
                norm = run_root / "data" / "progress.json"
                waited = 0.0
                while not dev.exists() and waited < 1.0:
                    time.sleep(0.05)
                    waited += 0.05
                self.assertTrue(dev.exists())
                self.assertFalse(norm.exists())
                text = dev.read_text(encoding="utf-8")
                self.assertIn('"current_lesson_id": "collections_19_nested_data"', text)
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except Exception:
                    proc.kill()
                    proc.wait(timeout=5)

    def test_action_and_restart_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            normal = data_dir / "progress.json"
            ctrl_n, _, _ = build_controller(ROOT, data_dir=data_dir, developer_mode=False)
            ctrl_n.progress.save()
            base_bytes = normal.read_bytes()

            ctrl_d, runner_d, _ = build_controller(
                ROOT, data_dir=data_dir, developer_mode=True, initial_lesson_id="collections_19_nested_data"
            )
            lesson = ctrl_d.catalog.get("collections_19_nested_data")
            assert lesson is not None
            ex = lesson.exercises[0]

            # Navigate
            ctrl_d.set_current_lesson(lesson.id)
            _ = ctrl_d.go_next()
            _ = ctrl_d.go_previous()
            self.assertEqual(base_bytes, normal.read_bytes())

            # Draft + save
            ctrl_d.progress.save_draft(ex.id, "# draft code")
            ctrl_d.progress.save()
            self.assertEqual(base_bytes, normal.read_bytes())

            # Hint
            ctrl_d.request_hint(ex)
            ctrl_d.progress.save()
            self.assertEqual(base_bytes, normal.read_bytes())

            # Failing submission
            res = ctrl_d.submit_exercise(lesson, ex, code="", answer="")
            self.assertFalse(res.passed)
            ctrl_d.progress.save()
            self.assertEqual(base_bytes, normal.read_bytes())

            # Reset then post-reset actions
            ctrl_d.progress.reset()
            ctrl_d.progress.save_draft(ex.id, "# after reset")
            ctrl_d.request_hint(ex)
            ctrl_d.progress.save()
            self.assertEqual(base_bytes, normal.read_bytes())

            # Restart preview and confirm persistence
            ctrl_d2, _, _ = build_controller(
                ROOT, data_dir=data_dir, developer_mode=True, initial_lesson_id="collections_19_nested_data"
            )
            self.assertEqual(ctrl_d2.current_lesson().id, "collections_19_nested_data")  # type: ignore[union-attr]
            dev_path = data_dir / "developer_progress.json"
            text = dev_path.read_text(encoding="utf-8")
            self.assertIn('"current_lesson_id": "collections_19_nested_data"', text)

    def test_whole_catalog_fresh_preview_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctrl, _, _ = build_controller(
                ROOT, data_dir=Path(tmp), developer_mode=True, initial_lesson_id="collections_19_nested_data"
            )
            for lesson in ctrl.catalog.lessons:
                for ex in lesson.exercises:
                    rec = ctrl.progress.exercise(ex.id)
                    self.assertFalse(rec.completed, ex.id)
                    self.assertEqual(rec.attempts, 0, ex.id)
                    self.assertEqual(rec.hints_used, 0, ex.id)
            snap = ctrl.progress.snapshot()
            self.assertEqual(snap["mistake_topics"], {})
            self.assertTrue(all(v == 0.0 for v in snap["mastery"].values()))


if __name__ == "__main__":
    unittest.main()

