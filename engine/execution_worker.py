"""Isolated worker process for executing learner code.

Invoked as ``python -m engine.execution_worker``. The parent process owns the
timeout and can kill this worker if student code loops forever — something a
thread inside the GUI process cannot reliably do.
"""

from __future__ import annotations

import ast
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
    "ImportError",
    "ModuleNotFoundError",
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


def safe_builtins(allowed_modules: list[str] | None = None) -> dict[str, Any]:
    raw = __builtins__ if isinstance(__builtins__, dict) else __builtins__.__dict__
    mapping = {name: raw[name] for name in ALLOWED_BUILTINS if name in raw}
    # ImportPolicy is imported lazily so the worker module stays lightweight if
    # the parent only needs traceback helpers in tests.
    from engine.import_policy import ImportPolicy

    policy = ImportPolicy(allowed_modules)
    mapping["__import__"] = policy.guarded_import
    return mapping


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


def decode_namespace(
    blob: str | None,
    *,
    allowed_modules: list[str] | None = None,
) -> dict[str, Any]:
    namespace: dict[str, Any] = {
        "__name__": "__student__",
        "__builtins__": safe_builtins(allowed_modules),
    }
    if not blob:
        return namespace
    try:
        restored = pickle.loads(base64.b64decode(blob.encode("ascii")))
    except Exception:  # noqa: BLE001
        return namespace
    if isinstance(restored, dict):
        namespace.update(restored)
    namespace["__builtins__"] = safe_builtins(allowed_modules)
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


def apply_test(
    test: dict[str, Any],
    namespace: dict[str, Any],
    stdout: str,
    success: bool,
    *,
    source: str = "",
) -> tuple[bool, str]:
    kind = test.get("kind", "stdout_equals")

    if kind == "stdout_equals":
        expected = test.get("expected", "")
        expected_text = expected if isinstance(expected, str) else str(expected)
        if stdout.rstrip("\n") == expected_text.rstrip("\n"):
            return True, "Printed output matched."
        shown = stdout if stdout.strip() else "(no output)"
        return False, test.get("message") or (
            f"Your program printed {shown!r}, which is not the required output. "
            "Check spelling, spaces, and punctuation."
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
        import copy

        args = copy.deepcopy(list(test.get("args", [])))
        kwargs = copy.deepcopy(dict(test.get("kwargs", {})))
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
        arg_after = test.get("arg_after")
        if isinstance(arg_after, dict):
            for key, expected_arg in arg_after.items():
                index = int(key)
                if index >= len(args) or args[index] != expected_arg:
                    return False, test.get("message") or (
                        f"After {call}, argument {index} should be {expected_arg!r}, "
                        f"but it was {args[index] if index < len(args) else 'missing'!r}. "
                        "Mutate the list in place rather than replacing it with a copy."
                    )
        same_list = test.get("return_shares_arg")
        if same_list is not None:
            index = int(same_list)
            if not (
                isinstance(actual, (list, tuple))
                and len(actual) >= 2
                and index < len(args)
                and actual[1] is args[index]
            ):
                return False, test.get("message") or (
                    "Return the used item and the same list object you mutated "
                    "(not a copied list)."
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

    if kind == "source_uses":
        return apply_source_uses(test, source)

    return False, f"Unknown test kind: {kind}"


def _assigned_name(target: ast.AST) -> str | None:
    if isinstance(target, ast.Name):
        return target.id
    return None


def apply_source_uses(test: dict[str, Any], source: str) -> tuple[bool, str]:
    """Check that learner code uses a construct that is itself the learning objective."""
    feature = str(test.get("feature") or "")
    required = list(test.get("names") or [])
    target = str(test.get("name") or "")
    custom = str(test.get("message") or "")

    if feature == "comment":
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") and any(char.isalpha() for char in stripped):
                return True, "Found a comment."
        return False, custom or (
            "Add a comment that starts with # and explains the next line."
        )

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False, custom or "Your code could not be parsed."

    if feature == "fstring":
        for node in ast.walk(tree):
            if isinstance(node, ast.JoinedStr):
                used = {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}
                if not required or set(required) <= used:
                    return True, "Used an f-string."
        return False, custom or (
            "Use an f-string (a string that starts with f) and put the variable "
            "names inside braces."
        )

    if feature == "binop_names":
        want = set(required)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            names = [_assigned_name(item) for item in node.targets]
            if target and target not in names:
                continue
            used = {child.id for child in ast.walk(node.value) if isinstance(child, ast.Name)}
            if want <= used and isinstance(node.value, ast.BinOp):
                return True, "Used the variables in an expression."
        return False, custom or (
            "Build the new value from the existing variable names, not a hardcoded number."
        )

    if feature == "rebind_self":
        name = target or (required[0] if required else "")
        for node in ast.walk(tree):
            if isinstance(node, ast.AugAssign) and _assigned_name(node.target) == name:
                return True, "Updated the variable using its current value."
            if isinstance(node, ast.Assign):
                assigned = [_assigned_name(item) for item in node.targets]
                if name not in assigned:
                    continue
                used = {child.id for child in ast.walk(node.value) if isinstance(child, ast.Name)}
                if name in used:
                    return True, "Updated the variable using its current value."
        return False, custom or (
            f"Give {name} a new value that uses {name} on the right-hand side."
        )

    if feature == "append_or_extend":
        name = target
        for node in ast.walk(tree):
            if isinstance(node, ast.AugAssign) and _assigned_name(node.target) == name:
                return True, "Grew the list."
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"append", "extend"}
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == name
            ):
                return True, "Grew the list."
            if isinstance(node, ast.Assign):
                assigned = [_assigned_name(item) for item in node.targets]
                if name in assigned and isinstance(node.value, ast.BinOp) and isinstance(
                    node.value.op, ast.Add
                ):
                    return True, "Grew the list."
        return False, custom or (
            f"Add an item to {name} with append, extend, or +=."
        )

    if feature == "subscript":
        for node in ast.walk(tree):
            if not isinstance(node, ast.Subscript):
                continue
            if not target:
                return True, "Used an index."
            if isinstance(node.value, ast.Name) and node.value.id == target:
                return True, "Used an index."
        return False, custom or "Use square-bracket indexing, such as party[0]."

    if feature == "if_statement":
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                return True, "Used an if statement."
        return False, custom or "Use if and else to choose what to print."

    if feature == "for_loop":
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                return True, "Used a for loop."
        return False, custom or "Use a for loop to visit each item in the list."

    if feature == "elif_branch":
        for node in ast.walk(tree):
            if isinstance(node, ast.If) and node.orelse:
                # elif is compiled as a nested If inside orelse.
                if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                    return True, "Used elif in a decision chain."
        return False, custom or (
            "Use elif so the chain can test another condition after if fails."
        )

    if feature == "calls_name":
        want = target or (required[0] if required else "")
        if not want:
            return False, custom or "Call the required function."
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == want:
                    return True, f"Called {want}()."
        return False, custom or f"Call {want}() so you reuse the function you defined."

    if feature == "print_names":
        want = set(required)
        printed: set[str] = set()
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "print"
            ):
                continue
            for arg in node.args:
                if isinstance(arg, ast.Name):
                    printed.add(arg.id)
        if want and want <= printed:
            return True, "Printed the required variable names."
        return False, custom or (
            "Print the variable names themselves (for example print(expedition)), "
            "not hardcoded literal values."
        )

    if feature == "print_min_calls":
        minimum = int(test.get("expected") or test.get("count") or 3)
        count = 0
        multi_arg = 0
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "print"
            ):
                count += 1
                if len(node.args) >= 2:
                    multi_arg += 1
        if count < minimum:
            return False, custom or (
                f"Use at least {minimum} separate print() calls — one per line of output."
            )
        if required and "multi_arg" in required and multi_arg < 1:
            return False, custom or (
                "At least one print() call must take two arguments "
                "(the label and the number)."
            )
        return True, "Used enough print() calls."

    if feature == "range_call":
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "range"
            ):
                return True, "Used range()."
        return False, custom or "Use range() to generate the positions or numbers."

    if feature == "compares_names":
        want = set(required)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            used = {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}
            if want and want <= used:
                return True, "Compared the required names."
            if not want:
                return True, "Used a comparison."
        return False, custom or (
            "Write a real comparison that uses the required variable names."
        )

    return False, f"Unknown source_uses feature: {feature}"


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
    allowed_modules = list(payload.get("allowed_modules") or [])
    namespace = decode_namespace(
        payload.get("namespace_blob"),
        allowed_modules=allowed_modules,
    )
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
            ok, message = apply_test(test, namespace, stdout, success, source=source)
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
