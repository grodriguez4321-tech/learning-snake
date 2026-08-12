"""Isolated worker process for executing learner code.

Invoked as ``python -m engine.execution_worker``. The parent process owns the
timeout and can kill this worker if student code loops forever — something a
thread inside the GUI process cannot reliably do.
"""

from __future__ import annotations

import base64
import io
import json
import pickle
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout
from typing import Any


ALLOWED_BUILTINS = [
    "__build_class__",
    "abs",
    "all",
    "any",
    "bool",
    "dict",
    "enumerate",
    "float",
    "format",
    "frozenset",
    "hasattr",
    "int",
    "isinstance",
    "issubclass",
    "len",
    "list",
    "map",
    "max",
    "min",
    "object",
    "print",
    "property",
    "range",
    "repr",
    "reversed",
    "round",
    "set",
    "sorted",
    "str",
    "sum",
    "super",
    "tuple",
    "type",
    "zip",
    "Exception",
    "ValueError",
    "TypeError",
    "NameError",
    "IndexError",
    "KeyError",
    "ZeroDivisionError",
    "AttributeError",
    "RuntimeError",
    "AssertionError",
]


def safe_builtins() -> dict[str, Any]:
    raw = __builtins__ if isinstance(__builtins__, dict) else __builtins__.__dict__
    return {name: raw[name] for name in ALLOWED_BUILTINS if name in raw}


def student_traceback(exc: BaseException) -> str:
    """Format a traceback that points at learner code, not the app internals."""
    chunks = traceback.format_exception(type(exc), exc, exc.__traceback__)
    filtered: list[str] = []
    keep = False
    for chunk in chunks:
        if '<student>' in chunk or '<playground>' in chunk:
            keep = True
        if keep or chunk.startswith("Traceback") or chunk.startswith(type(exc).__name__) or (
            filtered and not chunk.startswith("  File ")
        ):
            # Always keep the final exception line.
            if chunk.startswith("  File ") and '<student>' not in chunk and '<playground>' not in chunk:
                continue
            filtered.append(chunk)
    if not filtered:
        return f"{type(exc).__name__}: {exc}"
    # Ensure header exists
    if not filtered[0].startswith("Traceback"):
        filtered.insert(0, "Traceback (most recent call last):\n")
    text = "".join(filtered).rstrip()
    return text


def decode_namespace(blob: str | None) -> dict[str, Any]:
    namespace: dict[str, Any] = {
        "__name__": "__student__",
        "__builtins__": safe_builtins(),
    }
    if not blob:
        return namespace
    try:
        restored = pickle.loads(base64.b64decode(blob.encode("ascii")))
    except Exception:  # noqa: BLE001
        return namespace
    if isinstance(restored, dict):
        namespace.update(restored)
    namespace["__builtins__"] = safe_builtins()
    return namespace


def encode_namespace(namespace: dict[str, Any]) -> str:
    skip = {"__builtins__", "__name__", "__package__", "__loader__", "__spec__", "__doc__"}
    export: dict[str, Any] = {}
    for key, value in namespace.items():
        if key in skip:
            continue
        try:
            pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception:  # noqa: BLE001 - skip unpickleable values (e.g. some classes)
            continue
        export[key] = value
    raw = pickle.dumps(export, protocol=pickle.HIGHEST_PROTOCOL)
    return base64.b64encode(raw).decode("ascii")


def format_call(name: str, args: list[Any], kwargs: dict[str, Any]) -> str:
    bits = [repr(arg) for arg in args]
    bits.extend(f"{key}={value!r}" for key, value in kwargs.items())
    return f"{name}({', '.join(bits)})"


def apply_test(test: dict[str, Any], namespace: dict[str, Any], stdout: str, success: bool) -> tuple[bool, str]:
    kind = test.get("kind", "stdout_equals")

    if kind == "stdout_equals":
        expected = test.get("expected", "")
        expected_text = expected if isinstance(expected, str) else str(expected)
        if stdout.rstrip("\n") == expected_text.rstrip("\n"):
            return True, "Printed output matched."
        return False, test.get("message") or (
            f"Your program printed {stdout!r}, but it should print {expected_text!r}."
        )

    if kind == "stdout_contains":
        needle = test.get("contains")
        if needle is None:
            needle = str(test.get("expected", ""))
        if needle in stdout:
            return True, f"Output contained {needle!r}."
        return False, test.get("message") or (
            f"Expected the output to contain {needle!r}, but got {stdout!r}."
        )

    if kind == "globals":
        name = test.get("name") or ""
        if name not in namespace:
            return False, test.get("message") or f"Expected a variable named {name!r}."
        value = namespace[name]
        type_name = test.get("type_name")
        if type_name:
            type_map = {
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "tuple": tuple,
                "dict": dict,
                "set": set,
            }
            expected_type = type_map.get(type_name)
            if expected_type and not isinstance(value, expected_type):
                return False, (
                    f"{name} should be a {type_name}, but got {type(value).__name__}."
                )
        if "expected" in test and test["expected"] is not None and value != test["expected"]:
            return False, test.get("message") or (
                f"{name} should be {test['expected']!r}, but it was {value!r}."
            )
        return True, f"Variable {name} looks correct."

    if kind == "function":
        func_name = test.get("function") or ""
        func = namespace.get(func_name)
        if not callable(func):
            return False, f"Expected a function named {func_name}()."
        args = list(test.get("args", []))
        kwargs = dict(test.get("kwargs", {}))
        call = format_call(func_name, args, kwargs)
        try:
            actual = func(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            return False, f"{call} raised {type(exc).__name__}: {exc}"
        expected = test.get("expected")
        if actual != expected:
            return False, test.get("message") or (
                f"{call} returned {actual!r} instead of {expected!r}."
            )
        return True, f"{call} returned {expected!r}."

    if kind == "expression":
        expression = test.get("expression") or ""
        try:
            actual = eval(expression, namespace, namespace)  # noqa: S307
        except Exception as exc:  # noqa: BLE001
            return False, f"Could not evaluate {expression!r}: {exc}"
        if actual != test.get("expected"):
            return False, (
                f"Expression {expression} evaluated to {actual!r}, "
                f"expected {test.get('expected')!r}."
            )
        return True, f"Expression {expression} matched."

    if kind == "attribute":
        expression = test.get("expression") or ""
        try:
            actual = eval(expression, namespace, namespace)  # noqa: S307
        except Exception as exc:  # noqa: BLE001
            return False, f"Could not read {expression!r}: {exc}"
        if actual != test.get("expected"):
            return False, (
                f"{expression} was {actual!r}, expected {test.get('expected')!r}."
            )
        return True, f"{expression} matched."

    if kind == "class_defined":
        name = test.get("name") or ""
        value = namespace.get(name)
        if not isinstance(value, type):
            return False, f"Expected a class named {name}."
        return True, f"Class {name} is defined."

    if kind == "raises":
        expression = test.get("expression") or ""
        expected_name = test.get("expected") or test.get("exception") or "Exception"
        try:
            eval(expression, namespace, namespace)  # noqa: S307
        except Exception as exc:  # noqa: BLE001
            if type(exc).__name__ == expected_name or expected_name == "Exception":
                return True, f"{expression} raised {type(exc).__name__} as expected."
            return False, (
                f"{expression} raised {type(exc).__name__}, expected {expected_name}."
            )
        return False, f"{expression} did not raise {expected_name}."

    if kind == "runs_successfully":
        if success:
            return True, "Code ran without errors."
        return False, "Code raised an error."

    return False, f"Unknown test kind: {kind}"


def improve_function_feedback(results: list[dict[str, Any]]) -> None:
    """Rewrite the first failing function message using earlier passes."""
    passed_by_func: dict[str, list[str]] = {}
    for item in results:
        test = item.get("test", {})
        if test.get("kind") != "function":
            continue
        name = test.get("function") or ""
        call = format_call(name, list(test.get("args", [])), dict(test.get("kwargs", {})))
        if item.get("ok"):
            passed_by_func.setdefault(name, []).append(call)
            continue
        prior = passed_by_func.get(name, [])
        if prior:
            item["message"] = (
                f"Your {name}() function worked for {', '.join(prior)}, but "
                f"{item['message'].rstrip('.')}."
                f" Check how your return value is calculated."
            )
        break


def run_payload(payload: dict[str, Any]) -> dict[str, Any]:
    source = payload.get("source", "")
    filename = "<playground>" if payload.get("mode") == "playground" else "<student>"
    namespace = decode_namespace(payload.get("namespace_blob"))
    if payload.get("mode") == "playground":
        namespace["__name__"] = "__playground__"

    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    success = True
    error = None
    try:
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            compiled = compile(source, filename, "exec")
            exec(compiled, namespace, namespace)
    except Exception as exc:  # noqa: BLE001
        success = False
        error = student_traceback(exc)

    stdout = stdout_buffer.getvalue()
    stderr = stderr_buffer.getvalue()
    result: dict[str, Any] = {
        "success": success,
        "stdout": stdout,
        "stderr": stderr,
        "error": error,
        "timed_out": False,
        "namespace_blob": encode_namespace(namespace),
        "test_results": [],
    }

    if payload.get("mode") == "check":
        test_results: list[dict[str, Any]] = []
        for test in payload.get("tests", []):
            ok, message = apply_test(test, namespace, stdout, success)
            test_results.append({"ok": ok, "message": message, "test": test})
            if not ok:
                break
        improve_function_feedback(test_results)
        # Strip raw test payloads from response to keep messages lean.
        result["test_results"] = [
            {"ok": item["ok"], "message": item["message"]} for item in test_results
        ]

    return result


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        json.dump(
            {
                "success": False,
                "stdout": "",
                "stderr": "",
                "error": f"Worker received invalid payload: {exc}",
                "timed_out": False,
                "namespace_blob": "",
                "test_results": [],
            },
            sys.stdout,
        )
        return 1
    result = run_payload(payload)
    json.dump(result, sys.stdout)
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
