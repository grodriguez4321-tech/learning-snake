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
