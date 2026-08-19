from __future__ import annotations

import json
import tempfile
from pathlib import Path

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


def test_migrates_v2_progress_to_v3_2_and_clears_core() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "progress.json"
        payload = _progress_payload_v2()
        path.write_text(json.dumps(payload), encoding="utf-8")
        store = ProgressStore(path)
        store.load()

        # Version stamped to current, migration recorded and backup created.
        assert store.data.curriculum_version == 3
        assert store.migrated_from_legacy
        archives = list(Path(tmp).glob("progress.json.pre-basilisk-v3.2-*"))
        assert len(archives) == 1

        # Core lesson completions and exercises are cleared; mastery preserved.
        assert "fundamentals_01_print" not in store.data.completed_lessons
        assert "oop_28_composition" not in store.data.completed_lessons
        assert "fundamentals_01_ex3" not in store.data.exercises
        assert "oop_28_ex1" not in store.data.exercises
        # Non-core keys untouched.
        assert "sandbox_ex1" in store.data.exercises
        assert store.data.mastery.get("print") == 0.3
        assert store.data.mistake_topics.get("print") == 1
