"""Windows-oriented process-timeout regression tests.

These also run on POSIX so Linux developers catch kill regressions, but they
assert the real Windows CREATE_NEW_PROCESS_GROUP + terminate/kill path when
sys.platform is win32. They never wait for human input.
"""

from __future__ import annotations

import subprocess
import sys
import time
import unittest

from engine import code_runner as code_runner_module
from engine.code_runner import (
    TIMEOUT_MESSAGE,
    CodeRunner,
    terminate_process_tree,
)


def _spawn_sleeper(seconds: float = 30.0) -> subprocess.Popen:
    """Start a child with the same platform flags the learner runner uses."""
    return subprocess.Popen(
        [sys.executable, "-c", f"import time; time.sleep({seconds})"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        **code_runner_module._platform_popen_kwargs(),
    )


class WindowsTimeoutTests(unittest.TestCase):
    def test_real_platform_popen_kwargs(self) -> None:
        kwargs = code_runner_module._platform_popen_kwargs()
        if sys.platform == "win32":
            self.assertTrue(code_runner_module.IS_WINDOWS)
            self.assertIn("creationflags", kwargs)
            expected = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
            self.assertEqual(kwargs["creationflags"], expected)
            self.assertNotIn("start_new_session", kwargs)
        else:
            self.assertFalse(code_runner_module.IS_WINDOWS)
            self.assertEqual(kwargs, {"start_new_session": True})

    def test_terminate_process_tree_kills_live_child(self) -> None:
        process = _spawn_sleeper(30)
        try:
            self.assertIsNone(process.poll(), "child should still be running")
            started = time.monotonic()
            terminate_process_tree(process)
            elapsed = time.monotonic() - started
            self.assertIsNotNone(process.poll(), "child should be dead after terminate")
            self.assertLess(elapsed, 3.0)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            if process.stdout:
                process.stdout.close()
            if process.stderr:
                process.stderr.close()

    def test_infinite_loop_times_out_and_next_run_works(self) -> None:
        """Hung learner code must not leak a worker that blocks later runs.

        This is the Windows regression the CREATE_NEW_PROCESS_GROUP +
        terminate/kill path exists to prevent.
        """
        runner = CodeRunner(timeout=0.4)
        started = time.monotonic()
        hung = runner.run("while True:\n    pass\n")
        elapsed = time.monotonic() - started

        self.assertTrue(hung.timed_out)
        self.assertFalse(hung.success)
        self.assertEqual(hung.error, TIMEOUT_MESSAGE)
        self.assertLess(elapsed, 3.0)

        follow_up = runner.run("print(123)")
        self.assertTrue(follow_up.success, follow_up.error)
        self.assertFalse(follow_up.timed_out)
        self.assertEqual(follow_up.stdout.strip(), "123")

    def test_timeout_during_check_then_valid_run(self) -> None:
        runner = CodeRunner(timeout=0.4)
        hung = runner.check(
            "while True:\n    pass\n",
            tests=[{"kind": "stdout_equals", "expected": "ok\n"}],
        )
        self.assertTrue(hung.timed_out)
        self.assertEqual(hung.error, TIMEOUT_MESSAGE)

        ok = runner.run("print('recovered')")
        self.assertTrue(ok.success, ok.error)
        self.assertEqual(ok.stdout.strip(), "recovered")


if __name__ == "__main__":
    unittest.main()
