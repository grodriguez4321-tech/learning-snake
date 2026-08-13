"""Execute learner code in an isolated subprocess with a timeout.

Student programs must never freeze the Tkinter UI:
1. Code runs in a child process that can be killed on timeout.
2. GUI callers should invoke the runner from a worker thread (see CourseApp).

Termination is implemented for both POSIX (process group signals) and Windows
(CREATE_NEW_PROCESS_GROUP + terminate/kill).
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from engine.import_policy import normalize_allowed_modules


DEFAULT_TIMEOUT = 2.0
TIMEOUT_MESSAGE = (
    "Your program ran for too long and was stopped. Check for an infinite loop."
)
IS_WINDOWS = sys.platform == "win32"


@dataclass
class RunResult:
    success: bool
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    timed_out: bool = False
    namespace: dict[str, Any] = field(default_factory=dict)
    namespace_blob: str = ""
    test_results: list[dict[str, Any]] = field(default_factory=list)
    exception: Optional[BaseException] = None

    @property
    def output(self) -> str:
        parts: list[str] = []
        if self.stdout:
            parts.append(self.stdout.rstrip("\n"))
        if self.stderr:
            parts.append(self.stderr.rstrip("\n"))
        if self.error:
            parts.append(self.error.rstrip("\n"))
        return "\n".join(part for part in parts if part).rstrip()

    @property
    def learner_message(self) -> str:
        if self.timed_out:
            return TIMEOUT_MESSAGE
        return self.output or "(no output)"


class CodeRunner:
    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        *,
        allowed_modules: Optional[list[str]] = None,
    ) -> None:
        self.timeout = timeout
        self.allowed_modules = normalize_allowed_modules(allowed_modules)
        self._playground_blob = ""
        self._lock = threading.RLock()

    def reset_playground(self) -> None:
        with self._lock:
            self._playground_blob = ""

    @property
    def playground_namespace(self) -> dict[str, Any]:
        # Compatibility attribute for older callers/tests; the real state lives
        # in the pickled blob exchanged with the worker process.
        return {"__blob__": self._playground_blob}

    def run(
        self,
        source: str,
        *,
        namespace_blob: str = "",
        mode: str = "run",
        tests: Optional[list[dict[str, Any]]] = None,
        timeout: Optional[float] = None,
        allowed_modules: Optional[list[str]] = None,
    ) -> RunResult:
        modules = (
            normalize_allowed_modules(allowed_modules)
            if allowed_modules is not None
            else list(self.allowed_modules)
        )
        payload = {
            "source": source,
            "mode": mode,
            "namespace_blob": namespace_blob,
            "tests": tests or [],
            "allowed_modules": modules,
        }
        return self._invoke(payload, timeout=timeout)

    def run_playground(
        self,
        source: str,
        *,
        timeout: Optional[float] = None,
        allowed_modules: Optional[list[str]] = None,
    ) -> RunResult:
        with self._lock:
            result = self.run(
                source,
                namespace_blob=self._playground_blob,
                mode="playground",
                timeout=timeout,
                allowed_modules=allowed_modules,
            )
            if not result.timed_out:
                self._playground_blob = result.namespace_blob
            return result

    def check(
        self,
        source: str,
        tests: list[dict[str, Any]],
        *,
        timeout: Optional[float] = None,
        allowed_modules: Optional[list[str]] = None,
    ) -> RunResult:
        return self.run(
            source,
            mode="check",
            tests=tests,
            timeout=timeout,
            allowed_modules=allowed_modules,
        )

    def _invoke(self, payload: dict[str, Any], *, timeout: Optional[float]) -> RunResult:
        limit = self.timeout if timeout is None else timeout
        popen_kwargs: dict[str, Any] = {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "cwd": str(_repo_root()),
        }
        popen_kwargs.update(_platform_popen_kwargs())

        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "engine.execution_worker"],
                **popen_kwargs,
            )
        except OSError as exc:
            return RunResult(
                success=False,
                error=f"Could not start the code runner: {exc}",
            )

        try:
            stdout, stderr = process.communicate(
                input=json.dumps(payload),
                timeout=limit,
            )
        except subprocess.TimeoutExpired:
            terminate_process_tree(process)
            stdout, stderr = _drain_after_kill(process)
            return RunResult(
                success=False,
                stdout=stdout or "",
                stderr=stderr or "",
                error=TIMEOUT_MESSAGE,
                timed_out=True,
            )

        body = (stdout or "").strip()
        if not body:
            err = (stderr or "").strip() or "Code runner returned no result."
            return RunResult(success=False, stderr=stderr or "", error=err)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return RunResult(
                success=False,
                stdout=stdout or "",
                stderr=stderr or "",
                error="Code runner returned unreadable output.",
            )

        return RunResult(
            success=bool(data.get("success")),
            stdout=str(data.get("stdout") or ""),
            stderr=str(data.get("stderr") or ""),
            error=data.get("error"),
            timed_out=bool(data.get("timed_out")),
            namespace_blob=str(data.get("namespace_blob") or ""),
            test_results=list(data.get("test_results") or []),
        )


def _platform_popen_kwargs() -> dict[str, Any]:
    """Return OS-specific flags so the child can be killed reliably."""
    if IS_WINDOWS:
        # New process group lets us signal/kill without affecting the GUI.
        # Constant is Windows-only; keep a numeric fallback for analyzers/tests.
        flag = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        return {"creationflags": flag}
    # New session => own process group; killpg can reap the whole tree.
    return {"start_new_session": True}


def terminate_process_tree(process: subprocess.Popen[Any]) -> None:
    """Best-effort cross-platform termination of a worker process.

    POSIX: SIGTERM to the process group, then SIGKILL.
    Windows: terminate() then kill() (TerminateProcess).
    """
    if process.poll() is not None:
        return

    if IS_WINDOWS:
        _windows_terminate(process)
    else:
        _posix_terminate(process)

    try:
        process.wait(timeout=1)
    except Exception:  # noqa: BLE001
        pass


def _windows_terminate(process: subprocess.Popen[Any]) -> None:
    # Prefer a graceful terminate, then hard-kill. CTRL_BREAK is unreliable for
    # Python -m workers; TerminateProcess via kill() is the dependable path.
    for action in (process.terminate, process.kill):
        if process.poll() is not None:
            return
        try:
            action()
        except OSError:
            pass
        try:
            process.wait(timeout=0.5)
        except Exception:  # noqa: BLE001
            pass


def _posix_terminate(process: subprocess.Popen[Any]) -> None:
    pid = process.pid
    if not pid:
        return
    for sig in (signal.SIGTERM, signal.SIGKILL):
        if process.poll() is not None:
            return
        try:
            os.killpg(pid, sig)
        except ProcessLookupError:
            return
        except OSError:
            try:
                process.send_signal(sig)
            except OSError:
                pass
        try:
            process.wait(timeout=0.5)
        except Exception:  # noqa: BLE001
            pass


def _drain_after_kill(process: subprocess.Popen[Any]) -> tuple[str, str]:
    try:
        stdout, stderr = process.communicate(timeout=1)
        return stdout or "", stderr or ""
    except Exception:  # noqa: BLE001
        return "", ""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]
