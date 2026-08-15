"""Exercise models and JSON deserialization.

Exercise checking is behavior-based whenever practical: student code is
executed and inspected (stdout, returned values, defined names) rather than
compared as raw source text. That keeps "hardcoded" fake solutions from
passing function tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# Supported exercise kinds for Phase 1+. Additional kinds can be added
# without changing the GUI if the checker knows how to evaluate them.
EXERCISE_TYPES = (
    "predict_output",
    "fill_blank",
    "write_code",
    "debug",
    "architecture",
    "mini_project",
)


@dataclass
class TestCase:
    """A single behavior check applied after executing student code."""

    kind: str  # stdout_equals | stdout_contains | function | globals | expression | source_uses
    expected: Any = None
    function: Optional[str] = None
    args: list[Any] = field(default_factory=list)
    kwargs: dict[str, Any] = field(default_factory=dict)
    name: Optional[str] = None
    type_name: Optional[str] = None
    expression: Optional[str] = None
    contains: Optional[str] = None
    message: str = ""
    # source_uses: construct feature name (see execution_worker.apply_source_uses)
    feature: Optional[str] = None
    names: list[str] = field(default_factory=list)
    # source_uses: optional Compare op names (Lt, Gt, Eq, NotEq, …)
    ops: list[str] = field(default_factory=list)
    # source_uses: limit the AST walk to a named function body
    in_function: Optional[str] = None
    # source_uses: further scope (e.g. calls_name inside "for_loop")
    inside: Optional[str] = None
    # function: optional post-call argument expectations (mutation checks)
    arg_after: Optional[dict[str, Any]] = None
    return_shares_arg: Optional[int] = None


@dataclass
class Exercise:
    id: str
    type: str
    title: str
    prompt: str
    starter_code: str = ""
    hints: list[str] = field(default_factory=list)
    tests: list[TestCase] = field(default_factory=list)
    # For predict_output / architecture questions answered outside the editor.
    expected_answer: str = ""
    choices: list[str] = field(default_factory=list)
    code_to_predict: str = ""
    topics: list[str] = field(default_factory=list)
    # Optional solution shown only after many failed attempts (Phase 1: unused).
    reference_solution: str = ""
    # Modules this exercise may import. Empty => imports disabled.
    allowed_modules: list[str] = field(default_factory=list)
    success_message: str = ""
    failure_message: str = ""

    @property
    def is_code_exercise(self) -> bool:
        return self.type in {"fill_blank", "write_code", "debug", "mini_project"}

    @property
    def is_choice_exercise(self) -> bool:
        return self.type in {"predict_output", "architecture"} and bool(self.choices)

    @property
    def uses_free_text_answer(self) -> bool:
        return self.type == "predict_output" and not self.choices


def test_case_from_dict(data: dict[str, Any]) -> TestCase:
    # Prefer explicit "kind". Older lesson files may use "type" for the check kind;
    # do not confuse that with type_name for variable checks.
    kind = data.get("kind")
    if kind is None and data.get("type") in {
        "stdout_equals",
        "stdout_contains",
        "function",
        "globals",
        "expression",
        "attribute",
        "class_defined",
        "raises",
        "runs_successfully",
        "source_uses",
    }:
        kind = data.get("type")
    if kind is None:
        kind = "stdout_equals"
    return TestCase(
        kind=str(kind),
        expected=data.get("expected"),
        function=data.get("function"),
        args=list(data.get("args", [])),
        kwargs=dict(data.get("kwargs", {})),
        name=data.get("name"),
        type_name=data.get("type_name"),
        expression=data.get("expression"),
        contains=data.get("contains"),
        message=data.get("message", ""),
        feature=data.get("feature"),
        names=list(data.get("names", [])),
        ops=list(data.get("ops", [])),
        in_function=data.get("in_function"),
        inside=data.get("inside"),
        arg_after=(
            dict(data["arg_after"])
            if isinstance(data.get("arg_after"), dict)
            else None
        ),
        return_shares_arg=(
            int(data["return_shares_arg"])
            if data.get("return_shares_arg") is not None
            else None
        ),
    )


def exercise_from_dict(data: dict[str, Any]) -> Exercise:
    tests = [test_case_from_dict(item) for item in data.get("tests", [])]
    return Exercise(
        id=data["id"],
        type=data.get("type", "write_code"),
        title=data.get("title", "Exercise"),
        prompt=data.get("prompt", ""),
        starter_code=data.get("starter_code", ""),
        hints=list(data.get("hints", [])),
        tests=tests,
        expected_answer=str(data.get("expected_answer", "")),
        choices=list(data.get("choices", [])),
        code_to_predict=data.get("code_to_predict", data.get("code", "")),
        topics=list(data.get("topics", [])),
        reference_solution=data.get("reference_solution", ""),
        allowed_modules=list(data.get("allowed_modules", [])),
        success_message=str(data.get("success_message", "")),
        failure_message=str(data.get("failure_message", "")),
    )
