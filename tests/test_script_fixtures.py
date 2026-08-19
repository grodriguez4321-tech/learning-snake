from __future__ import annotations

from engine.code_runner import CodeRunner


def test_script_fixtures_pass_for_variable_based_solution() -> None:
    runner = CodeRunner(timeout=2.0)
    code = (
        "if bedrolls < registered:\n"
        "    print(f\"Expedition {expedition}: INVESTIGATE\")\n"
        "else:\n"
        "    print(f\"Expedition {expedition}: CLEAR\")\n"
    )
    tests = [
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
    ]
    result = runner.check(code, tests)
    assert result.success, result.error or result.output
    assert all(item["ok"] for item in result.test_results), result.test_results


def test_script_fixtures_fail_for_hardcoded_output() -> None:
    runner = CodeRunner(timeout=2.0)
    code = (
        "print(\"Expedition 17: INVESTIGATE\")\n"
    )
    tests = [
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
    ]
    result = runner.check(code, tests)
    # Should fail on the second scenario.
    assert not all(item["ok"] for item in result.test_results), result.test_results
