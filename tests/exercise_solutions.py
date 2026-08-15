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
            "def classify_rations(rations):\n"
            "    if rations >= 12:\n"
            '        status = "Cleared"\n'
            "    elif rations >= 5:\n"
            '        status = "Review"\n'
            "    else:\n"
            '        status = "Denied"\n'
            "    return status\n"
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
            "    return supplies.pop()\n"
        )
    },
    "collections_12_ex6": {
        "code": (
            'party = ["Mara", "Tovin", "Sable"]\n'
            'supplies = ["rope", "torch", "chalk", "map", "cracked vial"]\n'
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
    # --- collections_14_dict_iteration ---
    "collections_14_ex1": {"answer": "rope"},
    "collections_14_ex2": {
        "code": (
            'stock = {"rope": 2, "torch": 1}\n'
            "\n"
            "for item, count in stock.items():\n"
            '    print(f"{item}: {count}")\n'
        )
    },
    "collections_14_ex3": {
        "code": (
            'stock = {"rope": 2, "torch": 1}\n'
            "\n"
            "for item, count in stock.items():\n"
            '    print(f"{item}: {count}")\n'
        )
    },
    "collections_14_ex4": {
        "code": (
            "def antidote_count(stock):\n"
            '    return stock.get("antidote", 0)\n'
        )
    },
    "collections_14_ex5": {
        "code": (
            "def field_ledger(stock):\n"
            "    lines = []\n"
            "    for item, count in stock.items():\n"
            '        lines.append(f"{item}: {count}")\n'
            '    if stock.get("antidote", 0) > 0:\n'
            '        lines.append("Antidote ready")\n'
            "    else:\n"
            '        lines.append("Antidote missing")\n'
            "    return lines\n"
        )
    },
    # --- collections_15_while ---
    "collections_15_ex1": {"answer": "0"},
    "collections_15_ex2": {
        "code": (
            "steps = 0\n"
            "distance = 3\n"
            "\n"
            "while distance > 0:\n"
            "    steps += 1\n"
            "    distance -= 1\n"
            "\n"
            "print(steps)\n"
        )
    },
    "collections_15_ex3": {
        "code": (
            "signal = 3\n"
            "\n"
            "while signal > 0:\n"
            "    print(signal)\n"
            "    signal -= 1\n"
            "\n"
            'print("clear")\n'
        )
    },
    "collections_15_ex4": {"answer": "1"},
    "collections_15_ex5": {
        "code": (
            "def trail_total(distances):\n"
            "    index = 0\n"
            "    total = 0\n"
            "    while index < len(distances):\n"
            "        total += distances[index]\n"
            "        index += 1\n"
            "    return total\n"
        )
    },
    # --- functions_16_parameters ---
    "functions_16_ex1": {"answer": "Gloamfen: Review"},
    "functions_16_ex2": {
        "code": (
            "def supply_cost(price, quantity):\n"
            "    return price * quantity\n"
            "\n"
            "print(supply_cost(5, 3))\n"
        )
    },
    "functions_16_ex3": {
        "code": (
            "def badge(name, role):\n"
            '    return f"{name} — {role}"\n'
            "\n"
            'print(badge("Mira", "Scout"))\n'
        )
    },
    "functions_16_ex4": {
        "code": (
            "def carry_capacity(base_slots, bonus_slots):\n"
            "    return base_slots + bonus_slots\n"
        )
    },
    "functions_16_ex5": {
        "code": (
            "def dispatch_status(party, supplies, warning_active):\n"
            "    if warning_active or len(party) == 0:\n"
            '        return "Denied"\n'
            "    elif len(supplies) >= 2 * len(party):\n"
            '        return "Ready"\n'
            "    else:\n"
            '        return "Review"\n'
        )
    },
    # --- functions_17_defaults ---
    "functions_17_ex1": {"answer": "Gloamfen: Review"},
    "functions_17_ex2": {"answer": "1"},
    "functions_17_ex3": {
        "code": (
            "def format_supply(item, quantity=1):\n"
            '    return f"{quantity} x {item}"\n'
            "\n"
            'print(format_supply("rope"))\n'
        )
    },
    "functions_17_ex4": {
        "code": (
            'def mark_dispatch(destination, status="Review"):\n'
            '    return f"{destination}: {status}"\n'
        )
    },
    "functions_17_ex5": {
        "code": (
            'def log_entry(message, level="NOTICE", source="field"):\n'
            '    return f"[{level}][{source}] {message}"\n'
        )
    },
    # --- functions_18_returning_data ---
    "functions_18_ex1": {"answer": "None"},
    "functions_18_ex2": {"answer": "2"},
    "functions_18_ex3": {
        "code": (
            "def label_supplies(supplies):\n"
            "    lines = []\n"
            "    for item in supplies:\n"
            '        lines.append(f"Packed: {item}")\n'
            "    return lines\n"
        )
    },
    "functions_18_ex4": {
        "code": (
            "def add_item(supplies, item):\n"
            "    packed = list(supplies)\n"
            "    packed.append(item)\n"
            "    return packed\n"
        )
    },
    "functions_18_ex5": {
        "code": (
            'def build_dispatch(destination, party, supplies, status="Review"):\n'
            "    return {\n"
            '        "destination": destination,\n'
            '        "party": list(party),\n'
            '        "supplies": list(supplies),\n'
            '        "member_count": len(party),\n'
            '        "supply_count": len(supplies),\n'
            '        "status": status,\n'
            "    }\n"
        )
    },
    # --- collections_19_nested_data ---
    "collections_19_ex1": {"answer": "5"},
    "collections_19_ex2": {
        "code": (
            'dispatch = {\n'
            '    "destination": "Gloamfen",\n'
            '    "party": [{"name": "Mira", "health": 8}],\n'
            "}\n"
            'print(dispatch["party"][0]["name"])\n'
        )
    },
    "collections_19_ex3": {
        "code": (
            'dispatch = {"supplies": ["rope"]}\n'
            'dispatch["supplies"].append("torch")\n'
            'print(dispatch["supplies"])\n'
        )
    },
    "collections_19_ex4": {
        "code": (
            "def total_party_health(party):\n"
            "    total = 0\n"
            "    for member in party:\n"
            '        total += member["health"]\n'
            "    return total\n"
        )
    },
    "collections_19_ex5": {
        "code": (
            "def numbered_roster(party):\n"
            "    lines = []\n"
            "    for i, member in enumerate(party, start=1):\n"
            '        lines.append(f"{i}. {member[\'name\']} — {member[\"health\"]} HP")\n'
            "    return lines\n"
        )
    },
    # --- functions_20_scope ---
    "functions_20_ex1": {"answer": "waiting"},
    "functions_20_ex2": {"answer": "2"},
    "functions_20_ex3": {
        "code": (
            "supplies = 3\n"
            "\n"
            "def use_supply(supplies):\n"
            "    return supplies - 1\n"
            "\n"
            "print(use_supply(3))\n"
        )
    },
    "functions_20_ex4": {
        "code": (
            "def apply_damage(health, hit):\n"
            "    return health - hit\n"
        )
    },
    "functions_20_ex5": {
        "code": (
            "total_health = 999\n"
            "\n"
            "def party_report(party):\n"
            "    total = 0\n"
            "    for member in party:\n"
            '        total += member["health"]\n'
            "    return {\n"
            "        \"member_count\": len(party),\n"
            "        \"total_health\": total,\n"
            "    }\n"
        )
    },
    # --- strings_21_methods ---
    "strings_21_ex1": {"answer": "north"},
    "strings_21_ex2": {
        "code": (
            'entry = "Mira|Scout"\n'
            'parts = entry.split("|")\n'
            "print(parts[1])\n"
        )
    },
    "strings_21_ex3": {
        "code": (
            'command = "  OPEN GATE  "\n'
            "command = command.strip().lower()\n"
            "print(command)\n"
        )
    },
    "strings_21_ex4": {
        "code": (
            "def normalize_username(text):\n"
            "    return text.strip().lower()\n"
        )
    },
    "strings_21_ex5": {
        "code": (
            "def parse_log_line(line):\n"
            '    name, status = [part.strip() for part in line.split("|")]\n'
            "    return {\"name\": name, \"status\": status.lower()}\n"
        )
    },
    # --- errors_22_tracebacks ---
    "errors_22_ex1": {"answer": "1"},
    "errors_22_ex2": {
        "code": (
            "def route_status(ready):\n"
            "    if ready:\n"
            '        return "Ready"\n'
            '    return "Review"\n'
        )
    },
    "errors_22_ex3": {
        "code": (
            "def member_label(member):\n"
            '    return f"{member[\'name\']}: {member[\'role\']}"\n'
        )
    },
    "errors_22_ex4": {
        "code": (
            "def supply_label(item, count):\n"
            '    return f"{item}: {count}"\n'
        )
    },
    "errors_22_ex5": {
        "code": (
            "def second_health(party):\n"
            '    return party[1]["health"]\n'
            "\n"
            "party = [\n"
            '    {"name": "Mira", "health": 8},\n'
            '    {"name": "Rook", "health": 10},\n'
            "]\n"
            "print(second_health(party))\n"
        )
    },
    # --- errors_23_logic_debugging ---
    "errors_23_ex1": {"answer": "3"},
    "errors_23_ex2": {"answer": "wounded"},
    "errors_23_ex3": {
        "code": (
            "def signal_level(score):\n"
            "    if score >= 80:\n"
            '        return "Elite"\n'
            "    elif score >= 50:\n"
            '        return "Ready"\n'
            '    return "Hold"\n'
        )
    },
    "errors_23_ex4": {
        "code": (
            "def countdown(start):\n"
            "    values = []\n"
            "    while start > 0:\n"
            "        values.append(start)\n"
            "        start -= 1\n"
            "    return values\n"
        )
    },
    "errors_23_ex5": {
        "code": (
            "def expedition_report(party):\n"
            "    total_health = 0\n"
            "    needs_rest = False\n"
            "    for member in party:\n"
            '        total_health += member["health"]\n'
            '        if member["health"] < 5:\n'
            "            needs_rest = True\n"
            "    return {\n"
            "        \"member_count\": len(party),\n"
            "        \"total_health\": total_health,\n"
            "        \"needs_rest\": needs_rest,\n"
            "    }\n"
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
