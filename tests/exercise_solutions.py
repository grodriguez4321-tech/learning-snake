"""Known-good solutions for catalog exercises used by loop tests."""

from __future__ import annotations

from course.exercise import Exercise
from course.lesson import Lesson
from engine.course_controller import CourseController
from engine.exercise_checker import CheckResult

SOLUTIONS: dict[str, dict[str, str]] = {
    "fundamentals_01_ex2": {"answer": "HP: 100"},
    "fundamentals_01_ex1": {"code": "print('Hello, Adventurer!')"},
    "fundamentals_01_ex3": {"code": "# Show the gold amount\nprint('Gold:', 50)\n"},
    "fundamentals_02_ex2": {
        "code": (
            "strength = 12\n"
            "weapon_bonus = 3\n"
            "attack = strength + weapon_bonus\n"
            "print(attack)\n"
        )
    },
    "fundamentals_02_ex3": {"code": "gold = 50\ngold = gold + 10\nprint(gold)\n"},
    "fundamentals_02_ex1": {
        "code": (
            'name = "Rook"\n'
            "health = 80\n"
            "level = 3\n"
            "print(name)\n"
            "print(health)\n"
            "print(level)\n"
        )
    },
    "fundamentals_03_ex2": {"answer": "Inventory: 3x Potion"},
    "fundamentals_03_ex3": {"code": 'name = "Mira"\nprint(f"Ready, {name}!")\n'},
    "fundamentals_03_ex1": {
        "code": (
            'name = "Selene"\n'
            "health = 90\n"
            "level = 5\n"
            'print(f"{name} - Level {level} - HP {health}")\n'
        )
    },
    "decisions_01_ex1": {"answer": "KO"},
    "decisions_01_ex2": {
        "code": (
            "health = 80\n"
            "if health > 0:\n"
            '    print("Standing")\n'
            "else:\n"
            '    print("KO")\n'
        )
    },
    "decisions_01_ex3": {
        "code": (
            "gold = 8\n"
            "if gold >= 10:\n"
            '    print("enough")\n'
            "else:\n"
            '    print("too little")\n'
        )
    },
    "decisions_02_ex1": {"answer": "wounded"},
    "decisions_02_ex2": {
        "code": (
            "gold = 15\n"
            "if gold >= 20:\n"
            '    print("buy armor")\n'
            "elif gold >= 10:\n"
            '    print("buy potion")\n'
            "else:\n"
            '    print("save up")\n'
        )
    },
    "decisions_02_ex3": {
        "code": (
            "def wound_label(health):\n"
            "    if health > 50:\n"
            '        return "healthy"\n'
            "    elif health > 0:\n"
            '        return "wounded"\n'
            "    else:\n"
            '        return "critical"\n'
        )
    },
    "decisions_02_ex4": {"answer": "2"},
    "decisions_03_ex1": {"answer": "blocked"},
    "decisions_03_ex2": {"answer": "blocked"},
    "decisions_03_ex3": {
        "code": (
            "health = 30\n"
            "enemies = 3\n"
            "if health < 20 or enemies >= 3:\n"
            '    print("flee")\n'
            "else:\n"
            '    print("fight")\n'
        )
    },
    "decisions_03_ex4": {
        "code": (
            'passphrase = "open"\n'
            'entered = "open"\n'
            "if entered == passphrase:\n"
            '    print("enter")\n'
            "else:\n"
            '    print("blocked")\n'
        )
    },
    "decisions_03_ex5": {
        "code": (
            "def can_enter(has_key, gold):\n"
            "    return has_key and gold >= 10\n"
        )
    },
    "decisions_03_ex6": {
        "code": (
            "health = 100\n"
            "if health >= 0 and health <= 100:\n"
            '    print("valid")\n'
            "else:\n"
            '    print("invalid")\n'
        )
    },
    "decisions_03_ex7": {"answer": "1"},
    "collections_04_ex1": {"answer": "2"},
    "collections_04_ex2": {
        "code": (
            "for turn in range(3):\n"
            '    print(f"Turn {turn + 1}")\n'
        )
    },
    "collections_04_ex3": {
        "code": 'items = ["sword", "shield", "potion"]\nprint(items[-1])\n'
    },
    "collections_04_ex4": {
        "code": (
            "def last_item(items):\n"
            "    if len(items) == 0:\n"
            "        return None\n"
            "    return items[-1]\n"
        )
    },
    "collections_04_ex5": {
        "code": (
            "def numbered_lines(items):\n"
            "    lines = []\n"
            "    for i in range(len(items)):\n"
            '        lines.append(f"{i + 1}. {items[i]}")\n'
            "    return lines\n"
        )
    },
    "collections_05_ex1": {"answer": "sword"},
    "collections_05_ex2": {
        "code": (
            'inventory = ["sword", "shield", "torch"]\n'
            'if "torch" in inventory:\n'
            '    print("ready")\n'
            "else:\n"
            '    print("missing")\n'
        )
    },
    "collections_05_ex3": {
        "code": (
            'inventory = ["sword", "potion", "key"]\n'
            'inventory.remove("potion")\n'
            "print(inventory)\n"
        )
    },
    "collections_05_ex4": {
        "code": (
            "def drop_item(inventory, item):\n"
            "    if item in inventory:\n"
            "        inventory.remove(item)\n"
            "    return inventory\n"
        )
    },
    "collections_07_ex1": {"answer": "7"},
    "collections_07_ex2": {
        "code": (
            'name = "Mira"\n'
            "hp = 42\n"
            "gold = 10\n"
            'hero = {"name": name, "health": hp, "gold": gold}\n'
            'print(hero["name"])\n'
        )
    },
    "collections_07_ex3": {
        "code": (
            'hero = {"name": "Mira", "health": 42, "gold": 10}\n'
            'print(hero["health"])\n'
        )
    },
    "collections_07_ex4": {
        "code": (
            "def make_stats(name, hp, gold):\n"
            '    return {"name": name, "health": hp, "gold": gold}\n'
        )
    },
    "collections_07_ex5": {
        "code": (
            "def can_afford(stats, price):\n"
            '    return stats["gold"] >= price\n'
        )
    },
    "collections_01_ex3": {"answer": "Aria"},
    "collections_01_ex2": {
        "code": 'party = ["Aria", "Rook", "Mira"]\nprint(party[0])\n'
    },
    "collections_01_ex4": {
        "code": (
            'party = ["Aria", "Rook", "Mira"]\n'
            'print(f"Leader: {party[0]}")\n'
        )
    },
    "collections_02_ex1": {"answer": "['Aria', 'Rook', 'Mira']"},
    "collections_02_ex2": {
        "code": (
            'inventory = ["sword", "shield", "potion"]\n'
            'inventory.append("torch")\n'
            "print(inventory)\n"
        )
    },
    "collections_02_ex3": {
        "code": (
            'inventory = ["sword", "shield", "potion"]\n'
            'print(f"Wielding {inventory[0]}")\n'
        )
    },
    "collections_03_ex1": {"answer": "sword\nshield"},
    "collections_03_ex2": {
        "code": (
            'party = ["Aria", "Rook", "Mira"]\n'
            "for member in party:\n"
            "    print(member)\n"
        )
    },
    "collections_03_ex3": {
        "code": (
            'inventory = ["sword", "shield", "potion"]\n'
            "for item in inventory:\n"
            '    print(f"- {item}")\n'
        )
    },
    "functions_01_ex1": {"code": "def double(number):\n    return number + number\n"},
    "functions_01_ex2": {"answer": "2"},
    "functions_01_ex3": {
        "code": "def heal(health, amount):\n    return health + amount\n"
    },
    "functions_01_ex4": {
        "code": (
            "def format_status(name, health):\n"
            '    return f"{name} has {health} HP"\n'
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
