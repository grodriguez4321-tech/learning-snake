"""Tests for reliability fixes: termination, imports, progress recovery."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from course.exercise import Exercise, TestCase
from engine import code_runner as code_runner_module
from engine.code_runner import CodeRunner, terminate_process_tree
from engine.exercise_checker import ExerciseChecker
from engine.import_policy import CURRICULUM_MODULES, ImportPolicy, normalize_allowed_modules
from engine.progress import ProgressStore


class TerminationTests(unittest.TestCase):
    def test_platform_popen_kwargs_posix(self) -> None:
        with mock.patch.object(code_runner_module, "IS_WINDOWS", False):
            kwargs = code_runner_module._platform_popen_kwargs()
        self.assertEqual(kwargs, {"start_new_session": True})

    def test_platform_popen_kwargs_windows(self) -> None:
        with mock.patch.object(code_runner_module, "IS_WINDOWS", True):
            kwargs = code_runner_module._platform_popen_kwargs()
        self.assertIn("creationflags", kwargs)
        expected = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        self.assertEqual(kwargs["creationflags"], expected)

    def test_terminate_process_tree_idempotent_on_finished_process(self) -> None:
        process = subprocess.Popen(
            [sys.executable, "-c", "print('done')"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        process.communicate(timeout=5)
        # Should not raise even though the process already exited.
        terminate_process_tree(process)

    def test_timeout_still_works_after_termination_helper(self) -> None:
        runner = CodeRunner(timeout=0.4)
        started = time.monotonic()
        result = runner.run("while True:\n    pass\n")
        elapsed = time.monotonic() - started
        self.assertTrue(result.timed_out)
        self.assertLess(elapsed, 3.0)


class ImportPolicyTests(unittest.TestCase):
    def test_default_denies_imports(self) -> None:
        runner = CodeRunner(timeout=2.0)
        result = runner.run("import math\nprint(math.pi)\n")
        self.assertFalse(result.success)
        self.assertIn("ImportError", result.error or "")
        self.assertIn("not enabled", result.error or "")

    def test_allowlisted_curriculum_module_works(self) -> None:
        runner = CodeRunner(timeout=2.0)
        result = runner.run(
            "import math\nprint(int(math.floor(3.7)))\n",
            allowed_modules=["math"],
        )
        self.assertTrue(result.success, result.error)
        self.assertEqual(result.stdout.strip(), "3")

    def test_non_curriculum_module_cannot_be_enabled(self) -> None:
        # os is intentionally outside CURRICULUM_MODULES.
        self.assertNotIn("os", CURRICULUM_MODULES)
        modules = normalize_allowed_modules(["os", "math"])
        self.assertEqual(modules, ["math"])
        policy = ImportPolicy(["os"])
        self.assertFalse(policy.is_allowed("os"))

    def test_exercise_allowed_modules_flow_through_checker(self) -> None:
        exercise = Exercise(
            id="import_math",
            type="write_code",
            title="math",
            prompt="use math",
            allowed_modules=["math"],
            tests=[TestCase(kind="stdout_equals", expected="4\n")],
        )
        checker = ExerciseChecker(CodeRunner(timeout=2.0))
        denied = checker.check(exercise, code="import os\nprint(4)\n")
        self.assertFalse(denied.passed)
        allowed = checker.check(
            exercise,
            code="import math\nprint(int(math.sqrt(16)))\n",
        )
        self.assertTrue(allowed.passed, allowed.message)


class ProgressRecoveryTests(unittest.TestCase):
    def test_corrupt_json_is_quarantined_and_reset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            path.write_text("{not valid json", encoding="utf-8")
            store = ProgressStore(path)
            store.load()
            self.assertTrue(store.recovered_from_corrupt)
            self.assertIsNotNone(store.load_warning)
            self.assertEqual(store.data.completed_lessons, [])
            backups = list(Path(tmp).glob("progress.json.corrupt-*"))
            self.assertEqual(len(backups), 1)

    def test_empty_file_recovers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            path.write_text("   \n", encoding="utf-8")
            store = ProgressStore(path)
            store.load()
            self.assertTrue(store.recovered_from_corrupt)
            self.assertIn("empty", (store.load_warning or "").lower())

    def test_malformed_but_valid_json_salvages_what_it_can(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            payload = {
                "completed_lessons": ["a", 2],
                "current_lesson_id": "lesson_1",
                "exercises": {
                    "ex1": {"completed": True, "attempts": "3", "hints_used": 1},
                    "ex_bad": "nope",
                },
                "mastery": {"variables": "0.5", "bad": "x"},
                "mistake_topics": {"variables": "2"},
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            store = ProgressStore(path)
            store.load()
            self.assertFalse(store.recovered_from_corrupt)
            self.assertEqual(store.data.current_lesson_id, "lesson_1")
            self.assertTrue(store.exercise("ex1").completed)
            self.assertEqual(store.exercise("ex1").attempts, 3)
            self.assertNotIn("ex_bad", store.data.exercises)
            self.assertAlmostEqual(store.data.mastery["variables"], 0.5)
            self.assertNotIn("bad", store.data.mastery)

    def test_non_object_root_recovers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            path.write_text("[1, 2, 3]", encoding="utf-8")
            store = ProgressStore(path)
            store.load()
            self.assertTrue(store.recovered_from_corrupt)


class AsyncExecutionSmokeTests(unittest.TestCase):
    def test_runner_can_execute_from_background_thread(self) -> None:
        runner = CodeRunner(timeout=2.0)
        box: dict[str, object] = {}

        def worker() -> None:
            box["result"] = runner.run("print('threaded')")

        thread = threading.Thread(target=worker)
        thread.start()
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive())
        result = box["result"]
        assert isinstance(result, code_runner_module.RunResult)
        self.assertTrue(result.success)
        self.assertEqual(result.stdout.strip(), "threaded")


if __name__ == "__main__":
    unittest.main()
