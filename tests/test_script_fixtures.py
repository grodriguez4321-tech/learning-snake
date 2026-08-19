from __future__ import annotations

import unittest

from course.exercise import exercise_from_dict
from engine.exercise_checker import ExerciseChecker
from engine.code_runner import CodeRunner


class ScriptFixturesTests(unittest.TestCase):
    def test_script_fixtures_pass_for_variable_based_solution_end_to_end(self) -> None:
        runner = CodeRunner(timeout=2.0)
        checker = ExerciseChecker(runner)
        ex = exercise_from_dict(
            {
                "id": "tmp_ex",
                "type": "write_code",
                "title": "Hidden fixtures pass",
                "prompt": "Script prints based on variables",
                "tests": [
                    {
                        "kind": "script_fixtures",
                        "fixtures": [
                            {
                                "expedition": 17,
                                "registered": 4,
                                "bedrolls": 3,
                                "expected_stdout": "Expedition 17: INVESTIGATE\n",
                            },
                            {
                                "expedition": 17,
                                "registered": 4,
                                "bedrolls": 4,
                                "expected_stdout": "Expedition 17: CLEAR\n",
                            },
                        ],
                    }
                ],
            }
        )
        code = (
            "if bedrolls < registered:\n"
            "    print(f\"Expedition {expedition}: INVESTIGATE\")\n"
            "else:\n"
            "    print(f\"Expedition {expedition}: CLEAR\")\n"
        )
        result = checker.check(ex, code=code)
        self.assertTrue(result.passed, result.message)


    def test_script_fixtures_fail_for_hardcoded_output_end_to_end(self) -> None:
        runner = CodeRunner(timeout=2.0)
        checker = ExerciseChecker(runner)
        ex = exercise_from_dict(
            {
                "id": "tmp_ex",
                "type": "write_code",
                "title": "Hidden fixtures fail",
                "prompt": "Script prints based on variables",
                "tests": [
                    {
                        "kind": "script_fixtures",
                        "fixtures": [
                            {
                                "expedition": 17,
                                "registered": 4,
                                "bedrolls": 3,
                                "expected_stdout": "Expedition 17: INVESTIGATE\n",
                            },
                            {
                                "expedition": 17,
                                "registered": 4,
                                "bedrolls": 4,
                                "expected_stdout": "Expedition 17: CLEAR\n",
                            },
                        ],
                    }
                ],
            }
        )
        code = 'print("Expedition 17: INVESTIGATE")\n'
        result = checker.check(ex, code=code)
        self.assertFalse(result.passed)

    def test_script_fixtures_override_baseline_assignments(self) -> None:
        # Student script with baseline assignments should still be driven by hidden fixtures.
        runner = CodeRunner(timeout=2.0)
        checker = ExerciseChecker(runner)
        ex = exercise_from_dict(
            {
                "id": "tmp_ex2",
                "type": "write_code",
                "title": "Hidden fixtures override",
                "prompt": "Script prints based on variables",
                "tests": [
                    {
                        "kind": "script_fixtures",
                        "fixtures": [
                            {
                                "expedition": 18,
                                "registered": 3,
                                "bedrolls": 2,
                                "expected_stdout": "Expedition 18: INVESTIGATE\n",
                            },
                            {
                                "expedition": 18,
                                "registered": 3,
                                "bedrolls": 3,
                                "expected_stdout": "Expedition 18: CLEAR\n",
                            },
                        ],
                    }
                ],
            }
        )
        code = (
            "expedition = 999\n"
            "registered = 0\n"
            "bedrolls = 0\n"
            "if bedrolls < registered:\n"
            "    print(f\"Expedition {expedition}: INVESTIGATE\")\n"
            "else:\n"
            "    print(f\"Expedition {expedition}: CLEAR\")\n"
        )
        result = checker.check(ex, code=code)
        self.assertTrue(result.passed, result.message)
