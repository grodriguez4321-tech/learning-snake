"""Behavior-based exercise checking.

Prefer executing student code and inspecting results over comparing source
strings. Code exercises are graded inside an isolated subprocess so infinite
loops cannot freeze the UI, while still supporting stdout/globals/function/
expression/class checks declared in lesson JSON.
"""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from course.exercise import Exercise, TestCase
from engine.code_runner import TIMEOUT_MESSAGE, CodeRunner, RunResult


@dataclass
class CheckResult:
    passed: bool
    message: str
    details: list[str] = field(default_factory=list)
    run: Optional[RunResult] = None


def test_case_to_dict(test: TestCase) -> dict[str, Any]:
    payload = asdict(test)
    cleaned: dict[str, Any] = {"kind": payload["kind"]}
    for key, value in payload.items():
        if key == "kind":
            continue
        if value is None:
            continue
        # expected=[] / {} is a real assertion; do not treat it as "unset".
        if value in ([], {}) and key != "expected":
            continue
        if key == "message" and value == "":
            continue
        cleaned[key] = value
    return cleaned


class ExerciseChecker:
    def __init__(self, runner: Optional[CodeRunner] = None) -> None:
        self.runner = runner or CodeRunner()

    def check(
        self,
        exercise: Exercise,
        *,
        code: str = "",
        answer: str = "",
    ) -> CheckResult:
        if exercise.type == "predict_output":
            return self._check_predict(exercise, answer)
        if exercise.type == "architecture":
            return self._check_architecture(exercise, answer)
        return self._check_code_exercise(exercise, code)

    def _check_predict(self, exercise: Exercise, answer: str) -> CheckResult:
        cleaned = answer.strip()
        if not cleaned:
            return CheckResult(False, "Enter your predicted output in the answer box.")

        expected = self._resolve_choice(exercise, exercise.expected_answer)
        actual = self._resolve_choice(exercise, cleaned)

        if actual == expected:
            return CheckResult(True, "Correct! Your prediction matches the output.")

        # Do not reveal the exact expected text immediately.
        hint = exercise.failure_message.strip() if exercise.failure_message else ""
        if not hint:
            hint = "Check spacing, punctuation, and capitalization carefully."
            if _print_positional_arg_count(exercise.code_to_predict) >= 2:
                hint = (
                    "Remember that print() separates multiple arguments with a single "
                    "space and adds a newline at the end (you usually omit the newline "
                    "when typing your answer)."
                )
        return CheckResult(False, f"Not quite. {hint}")

    def _check_architecture(self, exercise: Exercise, answer: str) -> CheckResult:
        cleaned = answer.strip()
        if not cleaned:
            return CheckResult(False, "Choose an option in the answer box (number or full text).")

        expected = self._resolve_choice(exercise, exercise.expected_answer)
        actual = self._resolve_choice(exercise, cleaned)

        if actual == expected:
            message = exercise.success_message.strip() or (
                "Good reasoning — that choice fits this situation."
            )
            return CheckResult(True, message)
        message = exercise.failure_message.strip() or (
            "That choice does not fit this situation. Re-read the question "
            "and think about what the rest of the program needs."
        )
        return CheckResult(False, message)

    def _resolve_choice(self, exercise: Exercise, value: str) -> str:
        cleaned = value.strip()
        if cleaned.isdigit() and exercise.choices:
            index = int(cleaned) - 1
            if 0 <= index < len(exercise.choices):
                return exercise.choices[index].strip()
        return cleaned

    def _check_code_exercise(self, exercise: Exercise, code: str) -> CheckResult:
        if not code.strip():
            return CheckResult(False, "Your editor is empty. Write some code, then try again.")

        tests = [test_case_to_dict(test) for test in exercise.tests]
        run = self.runner.check(
            code,
            tests,
            allowed_modules=exercise.allowed_modules,
        )

        if run.timed_out:
            return CheckResult(False, TIMEOUT_MESSAGE, run=run)

        if not run.success and not any(t.kind == "raises" for t in exercise.tests):
            error = run.error or run.stderr or "Unknown error"
            return CheckResult(
                False,
                "Your code raised an error before tests could run.",
                details=[error],
                run=run,
            )

        if not exercise.tests:
            if run.success:
                return CheckResult(True, "Code ran successfully.", run=run)
            return CheckResult(
                False,
                "Code did not run successfully.",
                details=[run.error or ""],
                run=run,
            )

        details: list[str] = []
        for item in run.test_results:
            message = str(item.get("message", ""))
            details.append(message)
            if not item.get("ok"):
                return CheckResult(False, message, details=details, run=run)

        if len(run.test_results) < len(exercise.tests):
            # Worker stopped early or returned nothing useful.
            return CheckResult(
                False,
                "Could not finish checking this exercise. Try running the code first.",
                run=run,
            )

        message = exercise.success_message.strip() or "All checks passed. Nice work!"
        return CheckResult(True, message, details=details, run=run)


def _print_positional_arg_count(code: str) -> int:
    if not (code or "").strip():
        return 0
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 0
    max_args = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
            max_args = max(max_args, len(node.args))
    return max_args
