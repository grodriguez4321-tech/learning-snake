"""Execute learner code in an isolated subprocess with a timeout.

Student programs must never freeze the Tkinter UI. Infinite loops are killed by
the parent after ``timeout`` seconds (process-group kill). Playground variables
persist via a pickled namespace blob passed between subprocess runs.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


DEFAULT_TIMEOUT = 2.0
TIMEOUT_MESSAGE = (
    "Your program ran for too long and was stopped. Check for an infinite loop."
)


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
    def __init__(self, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout
        self._playground_blob = ""

    def reset_playground(self) -> None:
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
    ) -> RunResult:
        payload = {
            "source": source,
            "mode": mode,
            "namespace_blob": namespace_blob,
            "tests": tests or [],
        }
        return self._invoke(payload, timeout=timeout)

    def run_playground(self, source: str, *, timeout: Optional[float] = None) -> RunResult:
        result = self.run(
            source,
            namespace_blob=self._playground_blob,
            mode="playground",
            timeout=timeout,
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
    ) -> RunResult:
        return self.run(source, mode="check", tests=tests, timeout=timeout)

    def _invoke(self, payload: dict[str, Any], *, timeout: Optional[float]) -> RunResult:
        limit = self.timeout if timeout is None else timeout
        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "engine.execution_worker"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(_repo_root()),
                start_new_session=True,
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
            _kill_process_group(process)
            try:
                stdout, stderr = process.communicate(timeout=1)
            except Exception:  # noqa: BLE001
                stdout, stderr = "", ""
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


def _kill_process_group(process: subprocess.Popen[str]) -> None:
    try:
        if process.pid:
            os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        process.kill()
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=1)
    except Exception:  # noqa: BLE001
        pass


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]
