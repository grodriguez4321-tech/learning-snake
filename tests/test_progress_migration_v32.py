from __future__ import annotations

import json
import tempfile
from pathlib import Path

import unittest

from engine.progress import ProgressStore


def _progress_payload_v2() -> dict:
    # Minimal plausible v2 progress with some V3.2 lesson/exercise ids completed.
    return {
        "curriculum_version": 2,
        "completed_lessons": [
            "fundamentals_01_print",
            "oop_28_composition",
        ],
        "current_lesson_id": "fundamentals_02_variables",
        "exercises": {
            "fundamentals_01_ex3": {
                "completed": True,
                "attempts": 3,
                "hints_used": 1,
                "draft_code": "print('old draft')",
                "last_answer": "",
            },
            "oop_28_ex1": {
                "completed": False,
                "attempts": 1,
                "hints_used": 0,
                "draft_code": "# old oop draft",
                "last_answer": "",
            },
            # A non-core id should be preserved.
            "sandbox_ex1": {
                "completed": True,
                "attempts": 1,
                "hints_used": 0,
                "draft_code": "print('ok')",
                "last_answer": "",
            },
        },
        "mastery": {"print": 0.3, "functions": 0.2},
        "mistake_topics": {"print": 1},
    }


class ProgressMigrationV32Tests(unittest.TestCase):
    def test_migrates_v2_progress_to_v3_2_and_clears_core(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            payload = _progress_payload_v2()
            # Add representative exercise ids across all five batches.
            payload["exercises"].update(
                {
                    "decisions_10_ex3": {"completed": True, "attempts": 1, "hints_used": 0, "draft_code": "", "last_answer": ""},
                    "collections_11_ex1": {"completed": True, "attempts": 1, "hints_used": 0, "draft_code": "", "last_answer": ""},
                    "errors_22_ex1": {"completed": False, "attempts": 2, "hints_used": 1, "draft_code": "", "last_answer": ""},
                    "data_24_ex2": {"completed": False, "attempts": 1, "hints_used": 0, "draft_code": "", "last_answer": ""},
                }
            )
            path.write_text(json.dumps(payload), encoding="utf-8")
            store = ProgressStore(path)
            store.load()

            # Version stamped to current, migration recorded and backup created.
            self.assertEqual(store.data.curriculum_version, 3)
            self.assertTrue(store.migrated_from_legacy)
            archives = list(Path(tmp).glob("progress.json.pre-basilisk-v3.2-*"))
            self.assertEqual(len(archives), 1)

            # Core lesson completions and exercises are cleared; non-core preserved.
            self.assertNotIn("fundamentals_01_print", store.data.completed_lessons)
            self.assertNotIn("oop_28_composition", store.data.completed_lessons)
            for eid in ("fundamentals_01_ex3", "decisions_10_ex3", "collections_11_ex1", "errors_22_ex1", "data_24_ex2", "oop_28_ex1"):
                self.assertNotIn(eid, store.data.exercises)
            self.assertIn("sandbox_ex1", store.data.exercises)
            # Mastery reset for core topics; mistake topics preserved.
            self.assertEqual(store.data.mastery.get("print"), 0.0)
            self.assertEqual(store.data.mistake_topics.get("print"), 1)
