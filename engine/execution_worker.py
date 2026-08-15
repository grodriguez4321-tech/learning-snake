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
import tokenize
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
            # Prefer learner-facing message if supplied
            return False, test.get("message") or f"Could not evaluate the required expression: {exc}"
        if actual != test.get("expected"):
            # Do not expose raw hidden expressions or advanced syntax; use provided message when present.
            return False, test.get("message") or "A required check did not match the expected value."
        # On success, keep the confirmation generic as well.
        return True, test.get("success_message") or "Check matched the expected value."

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


def _function_nodes(tree: ast.AST, name: str) -> list[ast.AST]:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return list(ast.walk(node))
    return []


def _scoped_nodes(tree: ast.AST, in_function: str = "") -> list[ast.AST]:
    if in_function:
        return _function_nodes(tree, in_function)
    return list(ast.walk(tree))


def _iter_is_items_on(node: ast.For, dict_name: str | None = None) -> tuple[bool, str | None]:
    """Whether the for-loop iterates over some_dict.items(). Returns (True, dict_name)."""
    iter_node = node.iter
    if not isinstance(iter_node, ast.Call):
        return False, None
    func = iter_node.func
    if not (isinstance(func, ast.Attribute) and func.attr == "items"):
        return False, None
    base = func.value
    if isinstance(base, ast.Name):
        if dict_name is None or base.id == dict_name:
            return True, base.id
    return False, None


def _target_pair_names(target: ast.AST) -> tuple[str | None, str | None]:
    """Extract (first, second) variable names from a for-loop target like `for a, b in ...`."""
    if isinstance(target, ast.Tuple) and len(target.elts) == 2:
        left, right = target.elts
        if isinstance(left, ast.Name) and isinstance(right, ast.Name):
            return left.id, right.id
    return None, None


def _call_uses_names(node: ast.AST, required: set[str]) -> bool:
    """True if any argument/f-string of this call references all required names."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
        return False
    used: set[str] = set()
    for arg in node.args:
        if isinstance(arg, ast.Name):
            used.add(arg.id)
        else:
            used.update(child.id for child in ast.walk(arg) if isinstance(child, ast.Name))
    return required <= used


def _append_uses_names(node: ast.AST, list_name: str, required: set[str]) -> bool:
    """True if this is list_name.append(...) and argument references all required names."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
        return False
    if node.func.attr != "append":
        return False
    if not (isinstance(node.func.value, ast.Name) and node.func.value.id == list_name):
        return False
    used: set[str] = set()
    for arg in node.args:
        if isinstance(arg, ast.Name):
            used.add(arg.id)
        else:
            used.update(child.id for child in ast.walk(arg) if isinstance(child, ast.Name))
    return required <= used


def _assignments_of_name(nodes: list[ast.AST], name: str) -> int:
    count = 0
    for node in nodes:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if _assigned_name(t) == name:
                    count += 1
        elif isinstance(node, ast.AugAssign) and _assigned_name(node.target) == name:
            count += 1
        # Named expressions (walrus) do not bind the target name on the left for our purposes here.
    return count


def _method_called_on_name(nodes: list[ast.AST], name: str, methods: set[str]) -> bool:
    for node in nodes:
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == name:
                if node.func.attr in methods:
                    return True
    return False


def _any_subscript_on_name(nodes: list[ast.AST], name: str) -> bool:
    for node in nodes:
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == name:
            return True
    return False


def _any_membership_on_name(nodes: list[ast.AST], name: str) -> bool:
    for node in nodes:
        if isinstance(node, ast.Compare):
            # x in name  OR  x not in name
            if any(isinstance(op, (ast.In, ast.NotIn)) for op in node.ops):
                for comp in node.comparators:
                    if isinstance(comp, ast.Name) and comp.id == name:
                        return True
    return False


def _while_body_updates_name(loop: ast.While, name: str) -> bool:
    for stmt in loop.body:
        for node in ast.walk(stmt):
            if isinstance(node, ast.AugAssign) and _assigned_name(node.target) == name:
                return True
            if isinstance(node, ast.Assign):
                targets = [_assigned_name(t) for t in node.targets]
                if name in targets:
                    used = {child.id for child in ast.walk(node.value) if isinstance(child, ast.Name)}
                    if name in used:
                        return True
    return False


def _while_body_prints_name(loop: ast.While, name: str) -> bool:
    for stmt in loop.body:
        for node in ast.walk(stmt):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "print"
            ):
                if any(isinstance(arg, ast.Name) and arg.id == name for arg in node.args):
                    return True
                # Also accept f-strings that reference the variable.
                for arg in node.args:
                    if isinstance(arg, ast.JoinedStr):
                        used = {child.id for child in ast.walk(arg) if isinstance(child, ast.Name)}
                        if name in used:
                            return True
    return False


def _function_aliases(tree: ast.AST, func_name: str) -> set[str]:
    """Names that were assigned the function object (e.g. alias = trail_total)."""
    aliases: set[str] = set()
    # Walk the whole tree for aliasing (both at module scope and inside functions).
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Name) and node.value.id == func_name:
                for t in node.targets:
                    name = _assigned_name(t)
                    if name:
                        aliases.add(name)
    return aliases


def _calls_to_names(nodes: list[ast.AST], names: set[str]) -> bool:
    for node in nodes:
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in names:
                return True
    return False


def _has_method_call(nodes: list[ast.AST], method: str, list_name: str = "") -> bool:
    for node in nodes:
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != method:
            continue
        if not list_name:
            return True
        if isinstance(func.value, ast.Name) and func.value.id == list_name:
            return True
    return False


def _source_has_elif_token(source: str) -> bool:
    """True when source contains a real ``elif`` keyword (not ``else: if``)."""
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        return any(tok.type == tokenize.NAME and tok.string == "elif" for tok in tokens)
    except tokenize.TokenError:
        return False


def apply_source_uses(test: dict[str, Any], source: str) -> tuple[bool, str]:
    """Check that learner code uses a construct that is itself the learning objective."""
    feature = str(test.get("feature") or "")
    required = list(test.get("names") or [])
    target = str(test.get("name") or "")
    custom = str(test.get("message") or "")
    in_function = str(test.get("in_function") or "")
    inside = str(test.get("inside") or "")
    ops_wanted = list(test.get("ops") or [])

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

    nodes = _scoped_nodes(tree, in_function)
    if in_function and not nodes:
        return False, custom or f"Define a function named {in_function}."

    if feature == "fstring":
        for node in nodes:
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
        for node in nodes:
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
        for node in nodes:
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
        for node in nodes:
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

    if feature == "append_call":
        name = target
        if _has_method_call(nodes, "append", name):
            return True, "Used append()."
        return False, custom or (
            f"Call {(name + '.') if name else ''}append(...) to add one item."
        )

    if feature == "remove_call":
        name = target
        if _has_method_call(nodes, "remove", name):
            return True, "Used remove()."
        return False, custom or (
            f"Call {(name + '.') if name else ''}remove(...) to delete a matching value."
        )

    if feature == "pop_call":
        name = target
        if _has_method_call(nodes, "pop", name):
            return True, "Used pop()."
        return False, custom or (
            f"Call {(name + '.') if name else ''}pop() to remove and return an item."
        )

    if feature == "len_call":
        for node in nodes:
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "len"
            ):
                if not required:
                    return True, "Used len()."
                used = {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}
                if set(required) <= used:
                    return True, "Used len()."
        return False, custom or "Use len() to measure the collection or string."

    if feature == "boolean_and":
        for node in nodes:
            if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
                return True, "Used Boolean and."
        return False, custom or "Combine the requirements with and."

    if feature == "boolean_or":
        for node in nodes:
            if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
                return True, "Used Boolean or."
        return False, custom or "Combine the alternatives with or."

    if feature == "unary_not":
        for node in nodes:
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
                return True, "Used Boolean not."
        return False, custom or "Use not to reverse a Boolean value."

    if feature == "subscript":
        for node in nodes:
            if not isinstance(node, ast.Subscript):
                continue
            if not target:
                return True, "Used an index."
            if isinstance(node.value, ast.Name) and node.value.id == target:
                return True, "Used an index."
        return False, custom or "Use square-bracket indexing, such as party[0]."

    if feature == "if_statement":
        for node in nodes:
            if isinstance(node, ast.If):
                return True, "Used an if statement."
        return False, custom or "Use if and else to choose what to print."

    if feature == "for_loop":
        for node in nodes:
            if isinstance(node, ast.For):
                return True, "Used a for loop."
        return False, custom or "Use a for loop to visit each item in the list."

    if feature == "elif_branch":
        # Prefer a real elif token so an indented else: if does not count.
        if in_function:
            for node in ast.walk(tree):
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == in_function
                ):
                    try:
                        segment = ast.get_source_segment(source, node) or ""
                    except Exception:  # noqa: BLE001
                        segment = source
                    if _source_has_elif_token(segment):
                        # Also require the nested-If shape inside this function.
                        for child in ast.walk(node):
                            if (
                                isinstance(child, ast.If)
                                and child.orelse
                                and len(child.orelse) == 1
                                and isinstance(child.orelse[0], ast.If)
                                and child.col_offset == child.orelse[0].col_offset
                            ):
                                return True, "Used elif in a decision chain."
                    break
        elif _source_has_elif_token(source):
            for node in nodes:
                if (
                    isinstance(node, ast.If)
                    and node.orelse
                    and len(node.orelse) == 1
                    and isinstance(node.orelse[0], ast.If)
                    and node.col_offset == node.orelse[0].col_offset
                ):
                    return True, "Used elif in a decision chain."
        return False, custom or (
            "Use elif so the chain can test another condition after if fails."
        )

    if feature == "calls_name":
        want = target or (required[0] if required else "")
        if not want:
            return False, custom or "Call the required function."

        def _is_wanted_call(node: ast.AST) -> bool:
            return (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == want
            )

        if inside == "for_loop":
            for node in nodes:
                if not isinstance(node, ast.For):
                    continue
                # Only the loop body counts — for ... else runs once after
                # iteration and must not satisfy a per-item call requirement.
                for stmt in node.body:
                    for child in ast.walk(stmt):
                        if _is_wanted_call(child):
                            return True, f"Called {want}() inside the loop."
            return False, custom or (
                f"Call {want}() from inside the for loop body "
                "(a call elsewhere is not enough)."
            )

        for node in nodes:
            if _is_wanted_call(node):
                return True, f"Called {want}()."
        return False, custom or f"Call {want}() so you reuse the function you defined."

    if feature == "print_names":
        want = set(required)
        printed: set[str] = set()
        for node in nodes:
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
        for node in nodes:
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
        # Objective is range as the for-loop iterable (dummy range elsewhere must fail).
        for node in nodes:
            if not isinstance(node, ast.For):
                continue
            iter_node = node.iter
            if (
                isinstance(iter_node, ast.Call)
                and isinstance(iter_node.func, ast.Name)
                and iter_node.func.id == "range"
            ):
                return True, "Used range() to drive a for loop."
        return False, custom or (
            "Use range(...) as the sequence in your for loop header."
        )

    if feature == "compares_names":
        want = set(required)
        op_names = set(ops_wanted)
        for node in nodes:
            if not isinstance(node, ast.Compare):
                continue
            used = {child.id for child in ast.walk(node) if isinstance(child, ast.Name)}
            if want and not want <= used:
                continue
            if op_names:
                found = {type(op).__name__ for op in node.ops}
                if not op_names <= found:
                    continue
            return True, "Compared the required names."
        return False, custom or (
            "Write a real comparison that uses the required variable names."
        )

    # New semantic source checks used by later lessons.
    if feature == "print_pair_from_items_loop":
        dict_name = target or (required[0] if required else None)
        try:
            module = ast.parse(source)
        except SyntaxError:
            return False, custom or "Your code could not be parsed."
        for node in ast.walk(module):
            if isinstance(node, ast.For):
                ok, found_dict = _iter_is_items_on(node, dict_name)
                if not ok:
                    continue
                a, b = _target_pair_names(node.target)
                if not (a and b):
                    continue
                need = {a, b}
                # Require a print(...) in the loop body that uses both pair variables.
                for stmt in node.body:
                    for child in ast.walk(stmt):
                        if _call_uses_names(child, need) and isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == "print":
                            return True, "Printed the pair inside the .items() loop."
        return False, custom or (
            "Loop over stock.items() and print both the item name and its count from inside the loop body."
        )

    if feature == "append_pair_from_items_loop":
        # required[0] may be the list variable name (e.g. "lines"); target may hold dict name.
        list_name = (required or [""])[0]
        dict_name = target or None
        try:
            module = ast.parse(source)
        except SyntaxError:
            return False, custom or "Your code could not be parsed."
        for node in ast.walk(module):
            if isinstance(node, ast.For):
                ok, _ = _iter_is_items_on(node, dict_name)
                if not ok:
                    continue
                a, b = _target_pair_names(node.target)
                if not (a and b):
                    continue
                need = {a, b}
                for stmt in node.body:
                    for child in ast.walk(stmt):
                        if _append_uses_names(child, list_name, need):
                            return True, f"Appended both {a} and {b} inside the loop."
        return False, custom or (
            f"Inside the .items() loop, call {list_name}.append(...) using both pair variables."
        )

    if feature == "return_name":
        name = target or (required[0] if required else "")
        for node in nodes:
            if isinstance(node, ast.Return) and isinstance(node.value, ast.Name) and node.value.id == name:
                return True, f"Returned {name}."
        return False, custom or f"Return {name} at the end."

    if feature == "ban_reassign":
        # Fail if variable is assigned more than once (helps ensure lines is not replaced).
        name = target or (required[0] if required else "")
        assigns = _assignments_of_name(nodes, name)
        if assigns <= 1:
            return True, f"Did not reassign {name}."
        return False, custom or f"Do not reassign {name} after you start building it."

    if feature == "ban_list_methods":
        name = target or (required[0] if required else "")
        methods = set(required[1:]) if required and len(required) > 1 else set(ops_wanted or [])
        if not methods:
            methods = {"pop"}
        if _method_called_on_name(nodes, name, methods):
            return False, custom or f"Do not call {name}.{', '.join(sorted(methods))}()."
        return True, f"Did not call disallowed methods on {name}."

    if feature == "ban_subscript_on":
        name = target or (required[0] if required else "")
        if _any_subscript_on_name(nodes, name):
            return False, custom or f"Do not use indexing on {name} for this task."
        return True, f"No indexing on {name}."

    if feature == "ban_membership_on":
        name = target or (required[0] if required else "")
        if _any_membership_on_name(nodes, name):
            return False, custom or f"Do not use 'in {name}' for this task."
        return True, f"No membership tests on {name}."

    if feature == "dict_get_on":
        name = target or (required[0] if required else "")
        for node in nodes:
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "get" and isinstance(node.func.value, ast.Name) and node.func.value.id == name:
                    return True, f"Used {name}.get(...)."
        return False, custom or f"Use {name}.get(key, default) as taught."

    if feature == "while_updates":
        name = target or (required[0] if required else "")
        # Accept update in any while loop within scope (including nested).
        for node in nodes:
            if isinstance(node, ast.While) and _while_body_updates_name(node, name):
                return True, f"Updated {name} inside the while loop."
        return False, custom or f"Update {name} inside the while loop (for each step)."

    if feature == "print_inside_while":
        name = target or (required[0] if required else "")
        for node in nodes:
            if isinstance(node, ast.While) and _while_body_prints_name(node, name):
                return True, f"Printed {name} from within the while loop."
        return False, custom or f"Print {name} inside the while loop body."

    if feature == "index_accumulator_while":
        # Require the canonical beginner algorithm: index/total init; while index < len(seq); total += seq[index]; index += 1; return total
        seq = (required or ["distances"])[0]
        index_var = (ops_wanted or ["index"])[0] if ops_wanted else "index"
        total_var = target or "total"
        have_index_init = False
        have_total_init = False
        have_while = False
        have_total_update = False
        have_index_increment = False
        have_return_total = False
        for node in nodes:
            if isinstance(node, ast.Assign):
                ids = [_assigned_name(t) for t in node.targets]
                if index_var in ids and isinstance(node.value, ast.Constant) and node.value.value == 0:
                    have_index_init = True
                if total_var in ids and isinstance(node.value, ast.Constant) and node.value.value == 0:
                    have_total_init = True
            if isinstance(node, ast.While):
                # Condition should reference index and len(seq)
                cond_used = {child.id for child in ast.walk(node.test) if isinstance(child, ast.Name)}
                if index_var in cond_used and any(
                    isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == "len"
                    for child in ast.walk(node.test)
                ):
                    have_while = True
                # Look for updates in body
                for stmt in node.body:
                    for child in ast.walk(stmt):
                        if isinstance(child, ast.AugAssign) and _assigned_name(child.target) == total_var:
                            # Check right-hand uses seq[index]
                            used_names = {n.id for n in ast.walk(child.value) if isinstance(n, ast.Name)}
                            if total_var in used_names and index_var in used_names and seq in used_names:
                                have_total_update = True
                            else:
                                # Also accept total += seq[index]
                                if index_var in used_names and seq in used_names:
                                    have_total_update = True
                        if isinstance(child, ast.Assign):
                            ids = [_assigned_name(t) for t in child.targets]
                            if index_var in ids:
                                used = {n.id for n in ast.walk(child.value) if isinstance(n, ast.Name)}
                                # index = index + 1
                                if index_var in used:
                                    have_index_increment = True
                        if isinstance(child, ast.AugAssign) and _assigned_name(child.target) == index_var:
                            have_index_increment = True
            if isinstance(node, ast.Return) and isinstance(node.value, ast.Name) and node.value.id == total_var:
                have_return_total = True
        if all([have_index_init, have_total_init, have_while, have_total_update, have_index_increment, have_return_total]):
            return True, "Used the index/accumulator while-loop algorithm."
        return False, custom or (
            "Inside the function, initialize index and total to 0; loop while index < len(values); "
            "add values[index] to total and increment index; finally return total."
        )

    if feature == "ban_calls":
        banned = set(required)
        for node in nodes:
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in banned:
                    return False, custom or f"Do not call {', '.join(sorted(banned))} for this task."
        return True, "Did not call any banned functions."

    if feature == "ban_listcomp":
        for node in nodes:
            if isinstance(node, (ast.ListComp, ast.GeneratorExp, ast.SetComp, ast.DictComp)):
                return False, custom or "Do not use a comprehension here."
        return True, "No comprehensions used."

    if feature == "ban_recursion":
        func_name = in_function or target or (required[0] if required else "")
        if not func_name:
            return False, custom or "Specify the function name to check for recursion."
        tree = ast.parse(source)
        aliases = _function_aliases(tree, func_name)
        alias_or_self = aliases | {func_name}
        if _calls_to_names(_scoped_nodes(tree, in_function), alias_or_self):
            return False, custom or "Do not call the function recursively for this task."
        return True, "No recursion detected."

    if feature == "ban_builtins_get_sum":
        # Disallow __builtins__.get('sum')(...).
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Call):
                inner = node.func
                if isinstance(inner.func, ast.Attribute) and inner.func.attr == "get":
                    if isinstance(inner.func.value, ast.Name) and inner.func.value.id == "__builtins__":
                        if inner.args and isinstance(inner.args[0], ast.Constant) and inner.args[0].value == "sum":
                            return False, custom or "Do not retrieve sum via __builtins__.get('sum')."
        return True, "Did not access sum via __builtins__.get."

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
