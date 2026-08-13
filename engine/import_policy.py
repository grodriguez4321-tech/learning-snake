"""Controlled import policy for learner code.

Curriculum does not introduce modules until later sections. Until then, imports
are denied with a clear message. When a lesson needs a module, it declares
``allowed_modules`` and the worker installs a guarded ``__import__``.
"""

from __future__ import annotations

import builtins
from typing import Any, Iterable, Optional


# Modules the course may eventually enable. Keep this list intentional — do not
# add os/sys/subprocess/socket here; those are not beginner curriculum targets.
CURRICULUM_MODULES: frozenset[str] = frozenset(
    {
        "math",
        "random",
        "json",
        "datetime",
        "collections",
        "typing",
        "dataclasses",
        "pathlib",
        "re",
        "copy",
        "itertools",
        "functools",
        "operator",
        "string",
        "time",
        "decimal",
        "fractions",
        "statistics",
        "enum",
        "abc",
    }
)

# Default for Phase 1 lessons: no imports until the Modules unit unlocks them.
DEFAULT_ALLOWED_MODULES: frozenset[str] = frozenset()


class ImportPolicy:
    """Allow only an explicit set of top-level module names."""

    def __init__(self, allowed: Optional[Iterable[str]] = None) -> None:
        if allowed is None:
            names = DEFAULT_ALLOWED_MODULES
        else:
            names = frozenset(str(item).split(".", 1)[0] for item in allowed)
        # Silently ignore unknown names so lesson JSON typos cannot unlock
        # dangerous modules outside the curriculum catalog.
        self.allowed: frozenset[str] = frozenset(
            name for name in names if name in CURRICULUM_MODULES
        )

    def is_allowed(self, module_name: str) -> bool:
        root = module_name.split(".", 1)[0]
        return root in self.allowed

    def guarded_import(
        self,
        name: str,
        globals: Optional[dict[str, Any]] = None,
        locals: Optional[dict[str, Any]] = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> Any:
        if level != 0:
            raise ImportError(
                "Relative imports are not available in course exercises."
            )
        root = name.split(".", 1)[0]
        if not self.is_allowed(name):
            if self.allowed:
                allowed_text = ", ".join(sorted(self.allowed))
            else:
                allowed_text = (
                    "(none yet — imports unlock in the Intermediate Python section)"
                )
            raise ImportError(
                f"Import of {name!r} is not enabled for this exercise. "
                f"Allowed modules: {allowed_text}."
            )
        return builtins.__import__(name, globals, locals, fromlist, level)

    def to_list(self) -> list[str]:
        return sorted(self.allowed)


def normalize_allowed_modules(values: Optional[Iterable[str]]) -> list[str]:
    return ImportPolicy(values).to_list()
