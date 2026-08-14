"""Persist lightweight UI preferences (theme + panel visibility)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from app.theme import ThemeName


@dataclass
class UiPrefs:
    theme: ThemeName = "dark"
    sidebar_visible: bool = True
    editor_visible: bool = True


class UiPrefsStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.prefs = UiPrefs()

    def load(self) -> UiPrefs:
        if not self.path.exists():
            return self.prefs
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return self.prefs
        if not isinstance(raw, dict):
            return self.prefs
        theme = raw.get("theme", "dark")
        if theme not in {"dark", "light"}:
            theme = "dark"
        self.prefs = UiPrefs(
            theme=theme,  # type: ignore[arg-type]
            sidebar_visible=bool(raw.get("sidebar_visible", True)),
            editor_visible=bool(raw.get("editor_visible", True)),
        )
        return self.prefs

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(self.prefs), indent=2) + "\n", encoding="utf-8")

    def update(
        self,
        *,
        theme: Optional[ThemeName] = None,
        sidebar_visible: Optional[bool] = None,
        editor_visible: Optional[bool] = None,
    ) -> None:
        if theme is not None:
            self.prefs.theme = theme
        if sidebar_visible is not None:
            self.prefs.sidebar_visible = sidebar_visible
        if editor_visible is not None:
            self.prefs.editor_visible = editor_visible
        self.save()
