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
        custom = str(test.get("message") or "")
        try:
            actual = eval(expression, namespace, namespace)  # noqa: S307
        except Exception as exc:  # noqa: BLE001
            return False, custom or f"Could not evaluate {expression!r}: {exc}"
        if actual != test.get("expected"):
            return False, custom or (
                f"Expression {expression} evaluated to {actual!r}, "
                f"expected {test.get('expected')!r}."
            )
        return True, custom or f"Expression {expression} matched."

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


def _is_constant_ast(node: ast.AST) -> bool:
    """True for literal while/if tests such as False, True, 0, or None."""
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return _is_constant_ast(node.operand)
    return False


_UNKNOWN = object()


def _scope_statements(tree: ast.AST, in_function: str = "") -> list[ast.stmt]:
    if in_function:
        for node in ast.walk(tree):
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == in_function
            ):
                return list(node.body)
        return []
    if isinstance(tree, ast.Module):
        return list(tree.body)
    return []


def _scope_root(tree: ast.AST, in_function: str = "") -> ast.AST:
    if in_function:
        for node in ast.walk(tree):
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == in_function
            ):
                return node
        return tree
    return tree


def _reachable_statements(body: list[ast.stmt]) -> list[ast.stmt]:
    """Statements that can run before an unconditional terminator."""
    reachable: list[ast.stmt] = []
    for stmt in body:
        reachable.append(stmt)
        if isinstance(stmt, (ast.Break, ast.Continue, ast.Return, ast.Raise)):
            break
    return reachable


def _update_constant_bindings(bindings: dict[str, Any], stmt: ast.stmt) -> None:
    if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
        return
    target = stmt.targets[0]
    if not isinstance(target, ast.Name):
        return
    value = _eval_simple(stmt.value, bindings)
    if value is not _UNKNOWN:
        bindings[target.id] = value
    elif isinstance(stmt.value, ast.Constant):
        bindings[target.id] = stmt.value.value
    else:
        bindings.pop(target.id, None)


def _eval_simple(node: ast.AST, bindings: dict[str, Any]) -> Any:
    """Return a concrete value, or ``_UNKNOWN`` when not statically known."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id in bindings:
        return bindings[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = _eval_simple(node.operand, bindings)
        if value is not _UNKNOWN and isinstance(value, (int, float)):
            return -value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        value = _eval_simple(node.operand, bindings)
        if value is not _UNKNOWN:
            return not bool(value)
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):
        left = _eval_simple(node.left, bindings)
        right = _eval_simple(node.right, bindings)
        if left is _UNKNOWN or right is _UNKNOWN:
            return _UNKNOWN
        try:
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            return left * right
        except TypeError:
            return _UNKNOWN
    if isinstance(node, ast.BoolOp):
        values = [_eval_simple(v, bindings) for v in node.values]
        if any(v is _UNKNOWN for v in values):
            # Partial folding for and False / or True.
            if isinstance(node.op, ast.And) and any(v is not _UNKNOWN and not bool(v) for v in values):
                return False
            if isinstance(node.op, ast.Or) and any(v is not _UNKNOWN and bool(v) for v in values):
                return True
            return _UNKNOWN
        if isinstance(node.op, ast.And):
            result = True
            for value in values:
                result = result and bool(value)
                if not result:
                    return False
            return True
        result = False
        for value in values:
            result = result or bool(value)
            if result:
                return True
        return False
    return _UNKNOWN


def _compare_values(left: Any, op: ast.cmpop, right: Any) -> bool | None:
    try:
        if isinstance(op, ast.Lt):
            return left < right
        if isinstance(op, ast.LtE):
            return left <= right
        if isinstance(op, ast.Gt):
            return left > right
        if isinstance(op, ast.GtE):
            return left >= right
        if isinstance(op, ast.Eq):
            return left == right
        if isinstance(op, ast.NotEq):
            return left != right
    except TypeError:
        return None
    return None


def _condition_truth(test: ast.AST, bindings: dict[str, Any]) -> bool | None:
    """Return True/False when statically known, otherwise None."""
    simple = _eval_simple(test, bindings)
    if simple is not _UNKNOWN:
        return bool(simple)
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And):
        parts = [_condition_truth(v, bindings) for v in test.values]
        if any(p is False for p in parts):
            return False
        if all(p is True for p in parts):
            return True
        return None
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.Or):
        parts = [_condition_truth(v, bindings) for v in test.values]
        if any(p is True for p in parts):
            return True
        if all(p is False for p in parts):
            return False
        return None
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        inner = _condition_truth(test.operand, bindings)
        return None if inner is None else (not inner)
    if isinstance(test, ast.Compare) and len(test.ops) == 1 and len(test.comparators) == 1:
        left = _eval_simple(test.left, bindings)
        right = _eval_simple(test.comparators[0], bindings)
        if left is _UNKNOWN or right is _UNKNOWN:
            # Truthiness of a bare name (if distances:) stays unknown.
            return None
        return _compare_values(left, test.ops[0], right)
    if isinstance(test, ast.Name):
        if test.id in bindings:
            return bool(bindings[test.id])
        return None
    return None


def _condition_provably_false(test: ast.AST, bindings: dict[str, Any]) -> bool:
    return _condition_truth(test, bindings) is False


def _condition_provably_true(test: ast.AST, bindings: dict[str, Any]) -> bool:
    return _condition_truth(test, bindings) is True


def _walk_reachable(body: list[ast.stmt], bindings: dict[str, Any] | None = None) -> list[ast.AST]:
    """AST nodes in statements that can actually run (skips dead if branches)."""
    bindings = dict(bindings or {})
    nodes: list[ast.AST] = []
    for stmt in _reachable_statements(body):
        if isinstance(stmt, ast.If):
            truth = _condition_truth(stmt.test, bindings)
            if truth is False:
                nodes.extend(_walk_reachable(stmt.orelse, bindings))
            elif truth is True:
                nodes.extend(_walk_reachable(stmt.body, bindings))
            else:
                nodes.extend(_walk_reachable(stmt.body, bindings))
                nodes.extend(_walk_reachable(stmt.orelse, bindings))
            continue
        nodes.extend(ast.walk(stmt))
        _update_constant_bindings(bindings, stmt)
    return nodes


def _iter_whiles_with_bindings(
    stmts: list[ast.stmt],
    bindings: dict[str, Any] | None = None,
):
    """Yield (while_node, bindings_before) including whiles nested under if/while."""
    bindings = dict(bindings or {})
    for stmt in stmts:
        if isinstance(stmt, ast.While):
            yield stmt, dict(bindings)
            yield from _iter_whiles_with_bindings(stmt.body, bindings)
            continue
        if isinstance(stmt, ast.If):
            truth = _condition_truth(stmt.test, bindings)
            if truth is False:
                yield from _iter_whiles_with_bindings(stmt.orelse, bindings)
            elif truth is True:
                yield from _iter_whiles_with_bindings(stmt.body, bindings)
            else:
                yield from _iter_whiles_with_bindings(stmt.body, bindings)
                yield from _iter_whiles_with_bindings(stmt.orelse, bindings)
            continue
        _update_constant_bindings(bindings, stmt)


def _while_is_enterable(while_node: ast.While, bindings: dict[str, Any]) -> bool:
    if _condition_provably_false(while_node.test, bindings):
        return False
    if _is_constant_ast(while_node.test) and not _condition_provably_true(
        while_node.test, bindings
    ):
        return False
    return True


def _live_whiles(
    tree: ast.AST,
    in_function: str = "",
    *,
    require_enterable: bool = True,
) -> list[ast.While]:
    """While loops that can run (optionally rejecting never-entered conditions)."""
    stmts = _scope_statements(tree, in_function)
    live: list[ast.While] = []
    for while_node, bindings in _iter_whiles_with_bindings(stmts):
        if require_enterable and not _while_is_enterable(while_node, bindings):
            continue
        if not require_enterable and not isinstance(while_node, ast.While):
            continue
        live.append(while_node)
    return live


def _block_has_live_while(stmts: list[ast.stmt], bindings: dict[str, Any]) -> bool:
    for while_node, while_bindings in _iter_whiles_with_bindings(stmts, bindings):
        if _while_is_enterable(while_node, while_bindings):
            return True
    return False


def _is_hardcoded_numeric(node: ast.AST) -> bool:
    """True for literals and literal arithmetic such as ``3`` or ``1 + 2``."""
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (int, float)) and not isinstance(
            node.value, bool
        )
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return _is_hardcoded_numeric(node.operand)
    if isinstance(node, ast.BinOp) and isinstance(
        node.op, (ast.Add, ast.Sub, ast.Mult)
    ):
        return _is_hardcoded_numeric(node.left) and _is_hardcoded_numeric(node.right)
    return False


def _hardcoded_assign_after_live_while(
    stmts: list[ast.stmt],
    name: str,
    bindings: dict[str, Any] | None = None,
    *,
    seen_live_while: bool = False,
) -> bool:
    """True when ``name`` is hardcoded after an enterable while in this block."""
    bindings = dict(bindings or {})
    for stmt in stmts:
        if isinstance(stmt, ast.While):
            enterable = _while_is_enterable(stmt, bindings)
            # Assignments inside the loop body are the loop's work, not post-loop hardcoding.
            if _hardcoded_assign_after_live_while(
                stmt.body, name, bindings, seen_live_while=False
            ):
                return True
            if enterable:
                seen_live_while = True
            continue
        if isinstance(stmt, ast.If):
            truth = _condition_truth(stmt.test, bindings)
            before = seen_live_while
            if truth is False:
                if _hardcoded_assign_after_live_while(
                    stmt.orelse, name, bindings, seen_live_while=before
                ):
                    return True
                if _block_has_live_while(stmt.orelse, bindings):
                    seen_live_while = True
            elif truth is True:
                if _hardcoded_assign_after_live_while(
                    stmt.body, name, bindings, seen_live_while=before
                ):
                    return True
                if _block_has_live_while(stmt.body, bindings):
                    seen_live_while = True
            else:
                if _hardcoded_assign_after_live_while(
                    stmt.body, name, bindings, seen_live_while=before
                ):
                    return True
                if _hardcoded_assign_after_live_while(
                    stmt.orelse, name, bindings, seen_live_while=before
                ):
                    return True
                if _block_has_live_while(stmt.body, bindings) or _block_has_live_while(
                    stmt.orelse, bindings
                ):
                    seen_live_while = True
            continue
        if seen_live_while and isinstance(stmt, ast.Assign):
            assigned = [_assigned_name(item) for item in stmt.targets]
            if name in assigned and _is_hardcoded_numeric(stmt.value):
                return True
        _update_constant_bindings(bindings, stmt)
    return False


def _expr_resolves_to_banned(expr: ast.AST, banned: str, aliases: set[str]) -> bool:
    if isinstance(expr, ast.Name) and expr.id in aliases:
        return True
    if isinstance(expr, ast.Attribute) and expr.attr == banned:
        return True
    if isinstance(expr, ast.Subscript) and isinstance(expr.slice, ast.Constant):
        if expr.slice.value == banned:
            return True
    if (
        isinstance(expr, ast.Call)
        and isinstance(expr.func, ast.Name)
        and expr.func.id == "getattr"
        and len(expr.args) >= 2
        and isinstance(expr.args[1], ast.Constant)
        and expr.args[1].value == banned
    ):
        return True
    return False


def _collect_banned_aliases(tree: ast.AST, banned: str) -> set[str]:
    aliases = {banned}
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target = node.targets[0]
            if not isinstance(target, ast.Name):
                continue
            if _expr_resolves_to_banned(node.value, banned, aliases):
                if target.id not in aliases:
                    aliases.add(target.id)
                    changed = True
    return aliases


def _is_forbidden_named_call(
    node: ast.AST,
    banned: str,
    aliases: set[str] | None = None,
) -> bool:
    """Detect direct, aliased, and indirect calls to a banned builtin."""
    if not isinstance(node, ast.Call):
        return False
    aliases = aliases or {banned}
    return _expr_resolves_to_banned(node.func, banned, aliases)


def _segment_has_method(nodes: list[ast.AST], method: str) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == method
        for node in nodes
    )


def _append_receiver_name(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr == "append":
        if isinstance(func.value, ast.Name):
            return func.value.id
    return None


def _returned_names(stmts: list[ast.stmt]) -> set[str]:
    names: set[str] = set()
    for stmt in stmts:
        if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Name):
            names.add(stmt.value.id)
        elif isinstance(stmt, ast.If):
            names |= _returned_names(stmt.body)
            names |= _returned_names(stmt.orelse)
        elif isinstance(stmt, ast.While):
            names |= _returned_names(stmt.body)
    return names


def _const_str(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _method_call_contributes(
    nodes: list[ast.AST],
    match: Any,
    *,
    mode: str = "result",
    stmts: list[ast.stmt] | None = None,
) -> bool:
    """Require a matching method call to feed live return/decision work."""
    stmts = stmts or []

    # Linear dataflow for names assigned from the method call.
    origin: dict[str, str] = {}
    for stmt in stmts:
        if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
            continue
        target = stmt.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if match(stmt.value):
            origin[target.id] = "method"
        else:
            origin[target.id] = "other"

    def _test_uses_call_or_bound(test: ast.AST) -> bool:
        if any(match(child) for child in ast.walk(test)):
            return True
        names = {child.id for child in ast.walk(test) if isinstance(child, ast.Name)}
        return any(origin.get(name) == "method" for name in names)

    if mode == "return":
        for stmt in stmts:
            if not isinstance(stmt, ast.Return) or stmt.value is None:
                continue
            value = stmt.value
            if match(value):
                return True
            if isinstance(value, ast.Name) and origin.get(value.id) == "method":
                return True
        return False

    if mode in {"branching_append", "antidote_status"}:
        returned = _returned_names(stmts)
        if not returned:
            returned = {"lines"}
        for index, stmt in enumerate(stmts):
            if not isinstance(stmt, ast.If):
                continue
            if _condition_provably_false(stmt.test, {}):
                continue
            if not _test_uses_call_or_bound(stmt.test):
                continue
            body_nodes = _walk_reachable(stmt.body)
            else_nodes = _walk_reachable(stmt.orelse)
            # Pattern A: both branches append to the returned list.
            body_recv = {
                _append_receiver_name(n)
                for n in body_nodes
                if _append_receiver_name(n) in returned
            }
            else_recv = {
                _append_receiver_name(n)
                for n in else_nodes
                if _append_receiver_name(n) in returned
            }
            if body_recv and else_recv and (body_recv & else_recv or body_recv or else_recv):
                if body_recv & returned and else_recv & returned:
                    return True
            # Pattern B: both branches assign a status name, then append it once.
            body_assigns: dict[str, str] = {}
            else_assigns: dict[str, str] = {}
            for node in stmt.body:
                if isinstance(node, ast.Assign) and len(node.targets) == 1:
                    target = node.targets[0]
                    text = _const_str(node.value)
                    if isinstance(target, ast.Name) and text is not None:
                        body_assigns[target.id] = text
            for node in stmt.orelse:
                if isinstance(node, ast.Assign) and len(node.targets) == 1:
                    target = node.targets[0]
                    text = _const_str(node.value)
                    if isinstance(target, ast.Name) and text is not None:
                        else_assigns[target.id] = text
            shared = set(body_assigns) & set(else_assigns)
            for status_name in shared:
                if {body_assigns[status_name], else_assigns[status_name]} != {
                    "Antidote ready",
                    "Antidote missing",
                }:
                    continue
                for later in stmts[index + 1 :]:
                    for child in ast.walk(later):
                        if _append_receiver_name(child) not in returned:
                            continue
                        if not isinstance(child, ast.Call) or not child.args:
                            continue
                        arg0 = child.args[0]
                        if isinstance(arg0, ast.Name) and arg0.id == status_name:
                            return True
                        text = _const_str(arg0)
                        if text in {"Antidote ready", "Antidote missing"}:
                            return True
        return False

    if mode in {"True", "true", "result", "1"}:
        for stmt in stmts:
            if isinstance(stmt, ast.Return) and stmt.value is not None:
                value = stmt.value
                if match(value):
                    return True
                if isinstance(value, ast.Name) and origin.get(value.id) == "method":
                    return True
            if isinstance(stmt, ast.If) and not _condition_provably_false(stmt.test, {}):
                if _test_uses_call_or_bound(stmt.test):
                    return True
        return False

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

        def _is_rebind(node: ast.AST) -> bool:
            if isinstance(node, ast.AugAssign) and _assigned_name(node.target) == name:
                return True
            if isinstance(node, ast.Assign):
                assigned = [_assigned_name(item) for item in node.targets]
                if name not in assigned:
                    return False
                used = {child.id for child in ast.walk(node.value) if isinstance(child, ast.Name)}
                return name in used
            return False

        if inside == "while_loop":
            for while_node in _live_whiles(
                tree, in_function, require_enterable=True
            ):
                for child in _walk_reachable(while_node.body):
                    if _is_rebind(child):
                        return True, "Updated the variable inside the while loop."
            return False, custom or (
                f"Update {name} inside the while loop body so the condition can become false."
            )

        for node in nodes:
            if _is_rebind(node):
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

    if feature == "while_loop":
        require_nonconstant = bool(test.get("nonconstant"))
        live = _live_whiles(
            tree, in_function, require_enterable=require_nonconstant
        )
        if live:
            return True, "Used a while loop."
        if require_nonconstant:
            return False, custom or (
                "Use a while loop whose condition can actually become true and then "
                "change — not while False, and False, or a comparison that never runs."
            )
        return False, custom or (
            "Use a while loop that repeats until its condition becomes false."
        )

    if feature == "forbidden_call":
        banned = target or (required[0] if required else "")
        if not banned:
            return False, custom or "Forbidden call check is misconfigured."
        # Aliases may be bound at module level even when the call is inside a function.
        aliases = _collect_banned_aliases(tree, banned)
        for node in nodes:
            if _is_forbidden_named_call(node, banned, aliases):
                return False, custom or (
                    f"Do not call {banned}() for this exercise — write the loop logic yourself."
                )
        return True, f"Did not call {banned}()."

    if feature == "no_literal_assign":
        name = target or (required[0] if required else "")
        if not name:
            return False, custom or "Literal-assign check is misconfigured."
        after_while = bool(test.get("after_while"))
        stmts = _scope_statements(tree, in_function)
        if after_while:
            if _hardcoded_assign_after_live_while(stmts, name):
                return False, custom or (
                    f"Do not hardcode {name} after the while loop — "
                    f"let the loop compute {name}."
                )
            return True, f"No hardcoded assign to {name}."
        for stmt in stmts:
            if not isinstance(stmt, ast.Assign):
                continue
            assigned = [_assigned_name(item) for item in stmt.targets]
            if name in assigned and _is_hardcoded_numeric(stmt.value):
                return False, custom or (
                    f"Do not hardcode {name} — let the loop compute {name}."
                )
        return True, f"No hardcoded assign to {name}."

    if feature == "no_self_call":
        func_name = in_function or target or (required[0] if required else "")
        if not func_name:
            return False, custom or "Self-call check is misconfigured."
        for node in nodes:
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == func_name
            ):
                return False, custom or (
                    f"Do not call {func_name}() from inside itself — "
                    "use a while loop to walk the list."
                )
        return True, f"Did not recurse into {func_name}()."

    if feature == "no_for_loop":
        for node in nodes:
            if isinstance(node, ast.For):
                return False, custom or (
                    "Use a while loop for this exercise — do not total the list with for."
                )
        return True, "Did not use a for loop."

    if feature == "method_call":
        method = str(test.get("method") or "")
        if not method:
            return False, custom or "Call the required method."
        min_args = test.get("min_args")
        try:
            min_args_n = int(min_args) if min_args is not None else None
        except (TypeError, ValueError):
            min_args_n = None
        arg_equals = {
            str(key): value for key, value in dict(test.get("arg_equals") or {}).items()
        }
        contributes = test.get("contributes")
        body_calls_name = str(test.get("body_calls_name") or "")
        body_method = str(test.get("body_method") or "")
        scope_stmts = _scope_statements(tree, in_function)

        def _args_match(node: ast.Call) -> bool:
            if min_args_n is not None and len(node.args) < min_args_n:
                return False
            for idx_text, expected in arg_equals.items():
                try:
                    idx = int(idx_text)
                except (TypeError, ValueError):
                    return False
                if idx >= len(node.args):
                    return False
                try:
                    if ast.literal_eval(node.args[idx]) != expected:
                        return False
                except Exception:  # noqa: BLE001
                    return False
            return True

        def _matching_method_call(node: ast.AST) -> bool:
            if not isinstance(node, ast.Call):
                return False
            func = node.func
            if not isinstance(func, ast.Attribute) or func.attr != method:
                return False
            if target and not (
                isinstance(func.value, ast.Name) and func.value.id == target
            ):
                return False
            return _args_match(node)

        def _for_body_has_required_work(for_node: ast.For) -> bool:
            if not body_calls_name and not body_method:
                return True
            body_nodes = _walk_reachable(for_node.body)
            if body_calls_name:
                found = any(
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Name)
                    and child.func.id == body_calls_name
                    for child in body_nodes
                )
                if not found:
                    return False
            if body_method:
                found = any(
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Attribute)
                    and child.func.attr == body_method
                    for child in body_nodes
                )
                if not found:
                    return False
                # When the graded work is append, it must grow a list that is returned
                # (not a throwaway scratch list discarded before return).
                if body_method == "append" and in_function:
                    append_targets: set[str] = set()
                    for child in body_nodes:
                        if (
                            isinstance(child, ast.Call)
                            and isinstance(child.func, ast.Attribute)
                            and child.func.attr == "append"
                            and isinstance(child.func.value, ast.Name)
                        ):
                            append_targets.add(child.func.value.id)
                    returned_names: set[str] = set()
                    for stmt in scope_stmts:
                        if isinstance(stmt, ast.Return) and isinstance(
                            stmt.value, ast.Name
                        ):
                            returned_names.add(stmt.value.id)
                    if not (append_targets & returned_names):
                        return False
            return True

        discarded: set[int] = set()
        for node in nodes:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                discarded.add(id(node.value))

        if inside == "for_iter":
            for node in nodes:
                if not isinstance(node, ast.For):
                    continue
                if not _matching_method_call(node.iter):
                    continue
                if not _for_body_has_required_work(node):
                    continue
                return True, f"Used .{method}() to drive a for loop."
            receiver = f"{target}." if target else ""
            if body_calls_name or body_method:
                work = body_calls_name or f".{body_method}()"
                return False, custom or (
                    f"Use {receiver}{method}() as the for-loop sequence, and "
                    f"do the real work ({work}) inside that same loop body "
                    "(not after break, not in a dead branch, and not into a "
                    "list you never return)."
                )
            return False, custom or (
                f"Use {receiver}{method}() as the sequence in your for loop header."
            )

        matching_calls = [
            node
            for node in nodes
            if isinstance(node, ast.Call)
            and _matching_method_call(node)
            and id(node) not in discarded
        ]
        if contributes in {
            True,
            "result",
            "return",
            "branching_append",
            "antidote_status",
        }:
            if not _method_call_contributes(
                nodes,
                _matching_method_call,
                mode=str(contributes),
                stmts=scope_stmts,
            ):
                receiver = f"{target}." if target else ""
                return False, custom or (
                    f"Use the value from {receiver}{method}(...) in your live return "
                    "value or decision — a discarded or unreachable call is not enough."
                )
            return True, f"Used .{method}()."

        if matching_calls:
            return True, f"Used .{method}()."
        for node in nodes:
            if _matching_method_call(node):
                return True, f"Used .{method}()."
        receiver = f"{target}." if target else ""
        extra = ""
        if min_args_n is not None:
            extra = f" with at least {min_args_n} argument(s)"
        return False, custom or f"Call {receiver}{method}(){extra}."

    if feature == "function_signature":
        func_name = str(test.get("name") or "")
        parameters = list(test.get("parameters") or [])
        defaults_map = dict(test.get("defaults") or {})
        if not func_name:
            return False, custom or "Define the required function."

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name != func_name:
                continue
            args = node.args
            if args.vararg is not None or args.kwarg is not None:
                return False, custom or (
                    f"Define {func_name}({', '.join(parameters)}) with named parameters "
                    "(not *args)."
                )
            if args.posonlyargs or args.kwonlyargs:
                return False, custom or (
                    f"Define {func_name}({', '.join(parameters)}) with the required "
                    "positional parameters."
                )
            declared = [arg.arg for arg in args.args]
            if declared != parameters:
                return False, custom or (
                    f"Define {func_name}({', '.join(parameters)})."
                )
            # defaults apply to the last N positional parameters
            default_nodes = list(args.defaults)
            defaulted_names = declared[len(declared) - len(default_nodes) :]
            actual_defaults: dict[str, Any] = {}
            for name, default_node in zip(defaulted_names, default_nodes):
                try:
                    actual_defaults[name] = ast.literal_eval(default_node)
                except Exception:  # noqa: BLE001
                    return False, custom or (
                        f"Define {func_name} with literal default values in the signature."
                    )
            for key, expected_default in defaults_map.items():
                if key not in actual_defaults:
                    return False, custom or (
                        f"Declare default parameter {key}={expected_default!r} "
                        f"in the {func_name} signature."
                    )
                if actual_defaults[key] != expected_default:
                    return False, custom or (
                        f"Define {func_name} with {key}={expected_default!r}."
                    )
            # Reject unexpected defaults when a defaults map is provided.
            if defaults_map:
                for key in actual_defaults:
                    if key not in defaults_map:
                        return False, custom or (
                            f"Define {func_name}({', '.join(parameters)}) with only "
                            "the required defaults."
                        )
            return True, f"Defined {func_name} with the required signature."
        return False, custom or f"Define a function named {func_name}."

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
                # Only reachable loop-body statements count — work after break
                # must not satisfy a per-item call requirement.
                for child in _walk_reachable(node.body):
                    if _is_wanted_call(child):
                        return True, f"Called {want}() inside the loop."
            return False, custom or (
                f"Call {want}() from inside the for loop body "
                "(a call elsewhere is not enough)."
            )

        if inside == "while_loop":
            for while_node in _live_whiles(
                tree, in_function, require_enterable=True
            ):
                for child in _walk_reachable(while_node.body):
                    if _is_wanted_call(child):
                        return True, f"Called {want}() inside the while loop."
            return False, custom or (
                f"Call {want}() from inside the while loop body "
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
