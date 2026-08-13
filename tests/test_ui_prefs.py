"""UI preference and theme helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.theme import DARK, LIGHT, get_theme
from app.ui_prefs import UiPrefsStore


class ThemeTests(unittest.TestCase):
    def test_get_theme(self) -> None:
        self.assertEqual(get_theme("dark").name, "dark")
        self.assertEqual(get_theme("light").name, "light")
        self.assertIs(get_theme("dark"), DARK)
        self.assertIs(get_theme("light"), LIGHT)


class UiPrefsTests(unittest.TestCase):
    def test_save_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ui_prefs.json"
            store = UiPrefsStore(path)
            store.update(theme="light", sidebar_visible=False, editor_visible=True)
            reloaded = UiPrefsStore(path)
            reloaded.load()
            self.assertEqual(reloaded.prefs.theme, "light")
            self.assertFalse(reloaded.prefs.sidebar_visible)
            self.assertTrue(reloaded.prefs.editor_visible)

    def test_corrupt_prefs_fall_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ui_prefs.json"
            path.write_text("{bad", encoding="utf-8")
            store = UiPrefsStore(path)
            prefs = store.load()
            self.assertEqual(prefs.theme, "dark")
            self.assertTrue(prefs.sidebar_visible)


if __name__ == "__main__":
    unittest.main()
