"""Known-good solutions for catalog exercises used by loop tests."""

from __future__ import annotations

from course.exercise import Exercise
from course.lesson import Lesson
from engine.course_controller import CourseController
from engine.exercise_checker import CheckResult


SOLUTIONS: dict[str, dict[str, str]] = {
    # --- fundamentals_01_print ---
    "fundamentals_01_ex1": {"answer": "WAYSTATION 7\nExpedition: 17"},
    "fundamentals_01_ex2": {"code": 'print("EXPEDITION 17")\n'},
    "fundamentals_01_ex3": {
        "code": (
            "# Three-line search dispatch for the overdue party\n"
            'print("SEARCH DISPATCH")\n'
            'print("Expedition:", 17)\n'
            'print("Status: OVERDUE")\n'
        )
    },
    # --- fundamentals_02_variables ---
    "fundamentals_02_ex1": {"answer": "2\n3"},
    "fundamentals_02_ex2": {
        "code": (
            "tracks_found = 2\n"
            "damaged_items = 3\n"
            "evidence_count = tracks_found + damaged_items\n"
            "print(evidence_count)\n"
        )
    },
    "fundamentals_02_ex3": {"code": 'status = "OVERDUE"\nprint(status)\n'},
    "fundamentals_02_ex4": {
        "code": (
            "expedition = 17\n"
            "registered = 4\n"
            "days_overdue = 3\n"
            'status = "OVERDUE"\n'
            "print(expedition)\n"
            "print(registered)\n"
            "print(days_overdue)\n"
            "print(status)\n"
        )
    },
    # --- fundamentals_03_fstrings ---
    "fundamentals_03_ex1": {"answer": "Party registered: 4"},
    "fundamentals_03_ex2": {
        "code": 'status = "OVERDUE"\nprint(f"Status: {status}")\n'
    },
    "fundamentals_03_ex3": {
        "code": (
            "expedition = 17\n"
            "registered = 4\n"
            "days_overdue = 3\n"
            'print(f"Expedition {expedition} | Party {registered} | {days_overdue} days overdue")\n'
        )
    },
    # --- decisions_01_conditionals ---
    "decisions_01_ex1": {"answer": "No contact"},
    "decisions_01_ex2": {
        "code": (
            "bedrolls = 3\n"
            "registered = 4\n"
            "if bedrolls < registered:\n"
            '    print("Investigate")\n'
            "else:\n"
            '    print("Camp accounted for")\n'
        )
    },
    "decisions_01_ex3": {
        "code": (
            'status = "OVERDUE"\n'
            'if status == "OVERDUE":\n'
            '    print("Active search")\n'
            "else:\n"
            '    print("Cleared")\n'
        )
    },
    "decisions_01_ex4": {
        "code": (
            "expedition = 17\n"
            "registered = 4\n"
            "bedrolls = 3\n"
            "if bedrolls < registered:\n"
            '    print(f"Expedition {expedition}: INVESTIGATE")\n'
            "else:\n"
            '    print(f"Expedition {expedition}: CLEAR")\n'
        )
    },
    # --- collections_01_lists ---
    "collections_01_ex1": {"answer": "Selene"},
    "collections_01_ex2": {
        "code": 'party = ["Aria", "Rook", "Mira", "Selene"]\nprint(party[1])\n'
    },
    "collections_01_ex3": {
        "code": (
            'party = ["Aria", "Rook", "Mira", "Selene"]\n'
            'print(f"Leader: {party[0]}")\n'
            'print(f"Scout: {party[2]}")\n'
        )
    },
    # --- collections_02_append ---
    "collections_02_ex1": {"answer": "['broken lantern', 'drag marks', 'torn cloak']"},
    "collections_02_ex2": {
        "code": (
            'evidence = ["broken lantern", "drag marks"]\n'
            'evidence.append("gray dust")\n'
            "print(evidence)\n"
        )
    },
    "collections_02_ex3": {
        "code": (
            'evidence = ["broken lantern", "drag marks"]\n'
            'evidence.append("gray dust")\n'
            'print(f"Newest evidence: {evidence[2]}")\n'
        )
    },
    # --- collections_03_loops ---
    "collections_03_ex1": {"answer": "broken lantern\ndrag marks\ngray dust"},
    "collections_03_ex2": {
        "code": (
            'evidence = ["broken lantern", "drag marks", "gray dust"]\n'
            "for clue in evidence:\n"
            "    print(clue)\n"
        )
    },
    "collections_03_ex3": {
        "code": (
            'evidence = ["broken lantern", "drag marks", "gray dust"]\n'
            "for clue in evidence:\n"
            '    print(f"Evidence: {clue}")\n'
        )
    },
    "collections_03_ex4": {
        "code": (
            'evidence = ["broken lantern", "drag marks", "gray dust", "torn cloak"]\n'
            "for clue in evidence:\n"
            '    if clue == "gray dust":\n'
            '        print(f"FLAG: {clue}")\n'
            "    else:\n"
            '        print(f"logged: {clue}")\n'
        )
    },
    # --- functions_01_basics ---
    "functions_01_ex1": {"answer": "Evidence: broken lantern"},
    "functions_01_ex2": {"answer": "2"},
    "functions_01_ex3": {
        "code": (
            "def inspect_clue(clue):\n"
            '    if clue == "gray dust":\n'
            '        return f"FLAG: {clue}"\n'
            "    else:\n"
            '        return f"logged: {clue}"\n'
        )
    },
    "functions_01_ex4": {
        "code": (
            "evidence = [\n"
            '    "broken lantern",\n'
            '    "gray dust",\n'
            '    "torn cloak",\n'
            "]\n"
            "\n"
            "def inspect_clue(clue):\n"
            '    if clue == "gray dust":\n'
            '        return f"FLAG: {clue}"\n'
            "    else:\n"
            '        return f"logged: {clue}"\n'
            "\n"
            "for clue in evidence:\n"
            "    print(inspect_clue(clue))\n"
        )
    },
    # --- decisions_09_elif ---
    "decisions_09_ex1": {"answer": "Long route"},
    "decisions_09_ex2": {
        "code": (
            "rations = 14\n"
            "\n"
            "if rations >= 12:\n"
            '    status = "Cleared"\n'
            "elif rations >= 5:\n"
            '    status = "Review"\n'
            "else:\n"
            '    status = "Denied"\n'
            "\n"
            "print(status)\n"
        )
    },
    "decisions_09_ex3": {
        "code": (
            "def readiness_status(supplies):\n"
            "    if supplies >= 10:\n"
            '        return "Cleared"\n'
            "    elif supplies >= 5:\n"
            '        return "Review"\n'
            "    else:\n"
            '        return "Denied"\n'
        )
    },
    "decisions_09_ex4": {
        "code": (
            "def threat_label(level):\n"
            "    if level >= 8:\n"
            '        return "Severe"\n'
            "    elif level >= 4:\n"
            '        return "Elevated"\n'
            "    else:\n"
            '        return "Low"\n'
        )
    },
    # --- decisions_10_boolean_logic ---
    "decisions_10_ex1": {"answer": "Wait"},
    "decisions_10_ex2": {"answer": "or"},
    "decisions_10_ex3": {
        "code": (
            "def can_depart(has_guide, supplies):\n"
            "    return has_guide and supplies >= 10\n"
        )
    },
    "decisions_10_ex4": {
        "code": (
            "def can_depart(has_guide, supplies, warning_active):\n"
            "    return has_guide and supplies >= 10 and not warning_active\n"
        )
    },
    "decisions_10_ex5": {
        "code": (
            "def has_escape_route(north_open, south_open):\n"
            "    return north_open or south_open\n"
        )
    },
    # --- collections_11_len_range ---
    "collections_11_ex1": {"answer": "1\n2\n3"},
    "collections_11_ex2": {"answer": "3\nSable"},
    "collections_11_ex3": {
        "code": (
            'party = ["Mara", "Tovin", "Sable"]\n'
            "\n"
            "for index in range(len(party)):\n"
            "    print(party[index])\n"
        )
    },
    "collections_11_ex4": {
        "code": (
            "def numbered_roster(party):\n"
            "    lines = []\n"
            "    for index in range(len(party)):\n"
            '        lines.append(f"{index + 1}: {party[index]}")\n'
            "    return lines\n"
        )
    },
    "collections_11_ex5": {
        "code": (
            "def is_long_name(name):\n"
            "    return len(name) >= 8\n"
        )
    },
    # --- collections_12_list_methods ---
    "collections_12_ex1": {"answer": "chalk\n['rope', 'torch']"},
    "collections_12_ex2": {"answer": "1"},
    "collections_12_ex3": {
        "code": (
            'supplies = ["rope", "torch"]\n'
            'supplies.append("antidote")\n'
            "print(supplies)\n"
        )
    },
    "collections_12_ex4": {
        "code": (
            "def prepare_supplies(supplies, new_item, damaged_item):\n"
            "    supplies.append(new_item)\n"
            "    supplies.remove(damaged_item)\n"
            "    return supplies\n"
        )
    },
    "collections_12_ex5": {
        "code": (
            "def use_last_supply(supplies):\n"
            "    used_item = supplies.pop()\n"
            "    return [used_item, supplies]\n"
        )
    },
    "collections_12_ex6": {
        "code": (
            'party = ["Mara", "Tovin", "Sable"]\n'
            'supplies = ["rope", "torch", "cracked vial"]\n'
            "\n"
            'supplies.remove("cracked vial")\n'
            'supplies.append("antidote")\n'
            "print(len(party))\n"
            "print(len(supplies))\n"
            "if len(supplies) >= 10:\n"
            '    print("Cleared")\n'
            "elif len(supplies) >= 5:\n"
            '    print("Review")\n'
            "else:\n"
            '    print("Denied")\n'
        )
    },
    # --- collections_13_dictionaries ---
    "collections_13_ex1": {"answer": "Gloamfen\n3"},
    "collections_13_ex2": {
        "code": (
            'record = {"destination": "Gloamfen"}\n'
            'print(record["destination"])\n'
        )
    },
    "collections_13_ex3": {"answer": "2"},
    "collections_13_ex4": {
        "code": (
            "def make_record(destination, party, supplies):\n"
            "    return {\n"
            '        "destination": destination,\n'
            '        "party": party,\n'
            '        "supplies": supplies,\n'
            '        "member_count": len(party),\n'
            "    }\n"
        )
    },
    "collections_13_ex5": {
        "code": (
            "def set_clearance(record, status):\n"
            '    record["status"] = status\n'
            "    return record\n"
        )
    },
    "collections_13_ex6": {
        "code": (
            "def build_expedition_record(destination, party, supplies, has_guide, warning_active):\n"
            "    record = {\n"
            '        "destination": destination,\n'
            '        "party": party,\n'
            '        "supplies": supplies,\n'
            '        "has_guide": has_guide,\n'
            '        "warning_active": warning_active,\n'
            "    }\n"
            '    record["member_count"] = len(party)\n'
            '    record["supply_count"] = len(supplies)\n'
            "    if (not has_guide) or warning_active:\n"
            '        record["status"] = "Denied"\n'
            "    elif len(supplies) >= 5:\n"
            '        record["status"] = "Cleared"\n'
            "    else:\n"
            '        record["status"] = "Review"\n'
            "    return record\n"
        )
    },
}


def submit_solution(
    controller: CourseController,
    lesson: Lesson,
    exercise: Exercise,
) -> CheckResult:
    spec = SOLUTIONS.get(exercise.id)
    if spec is None:
        if exercise.is_code_exercise:
            raise AssertionError(f"No code solution recorded for {exercise.id}")
        return controller.submit_exercise(
            lesson, exercise, answer=exercise.expected_answer
        )
    return controller.submit_exercise(lesson, exercise, **spec)
