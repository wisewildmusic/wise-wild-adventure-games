"""
The Lost Treasure of Pythonia
-----------------------------
A text-based adventure game for practicing Python fundamentals:
variables, lists, loops, conditionals, and functions.

You are an explorer searching for a legendary treasure. Choose a
difficulty, pick your path (a forest or a cave), make smart decisions,
and answer the Python challenges set by the guardians of the land.

Scores for each difficulty level are saved to scores.json so you can
come back and try to beat your high score.
"""

import json
import os
import random
import textwrap
from datetime import datetime


# ------------------------------------------------------------------
# Game settings
# ------------------------------------------------------------------

SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scores.json")
SCREEN_WIDTH = 70
MAX_HISTORY = 5  # how many recent games the score log remembers

# Base point values. Each one is multiplied by the difficulty multiplier.
CORRECT_ANSWER_POINTS = 10
WISE_CHOICE_POINTS = 5
RELIC_POINTS = 15
TREASURE_POINTS = 50
LIFE_POINTS = 10

DIFFICULTY_SETTINGS = {
    "easy": {
        "lives": 3,
        "multiplier": 1,
        "topics": "variables, data types, lists, if/else, simple loops",
    },
    "medium": {
        "lives": 2,
        "multiplier": 2,
        "topics": "loops, slicing, dictionaries, default args, scope",
    },
    "hard": {
        "lives": 1,
        "multiplier": 3,
        "topics": "comprehensions, closures, recursion, mutability",
    },
}


# ------------------------------------------------------------------
# Python challenges for each difficulty level
# ------------------------------------------------------------------
# Every question has a prompt, a list of options, the correct answer
# (which must match one of the options exactly) and a short explanation.
# Questions about a snippet of code also include the "code" to show.

QUESTIONS = {
    "easy": [
        {
            "prompt": "What does this code print?",
            "code": "x = 5\nx = x + 2\nprint(x)",
            "options": ["5", "7", "52", "x + 2"],
            "answer": "7",
            "explain": "x starts at 5, then x + 2 (which is 7) is stored back into x.",
        },
        {
            "prompt": "Which of these is a valid Python variable name?",
            "options": ["2nd_place", "my-score", "player_name", "class"],
            "answer": "player_name",
            "explain": "Names can't start with a digit, can't contain '-', "
                       "and can't be a keyword such as 'class'.",
        },
        {
            "prompt": "What does this code print?",
            "code": 'fruits = ["apple", "banana", "cherry"]\nprint(fruits[1])',
            "options": ["apple", "banana", "cherry", "Error"],
            "answer": "banana",
            "explain": "List indexes start at 0, so index 1 is the second item.",
        },
        {
            "prompt": "What data type is the value 3.14?",
            "options": ["int", "float", "str", "bool"],
            "answer": "float",
            "explain": "Numbers with a decimal point are floats.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "age = 12\n"
                "if age >= 13:\n"
                '    print("Teen")\n'
                "else:\n"
                '    print("Kid")'
            ),
            "options": ["Teen", "Kid", "Teen and Kid", "Nothing"],
            "answer": "Kid",
            "explain": "12 >= 13 is False, so the else block runs.",
        },
        {
            "prompt": "Which numbers does this loop print?",
            "code": "for i in range(3):\n    print(i)",
            "options": ["0 1 2", "1 2 3", "0 1 2 3", "1 2"],
            "answer": "0 1 2",
            "explain": "range(3) starts at 0 and stops before 3.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "def greet(name):\n"
                '    return "Hi " + name\n'
                "\n"
                'print(greet("Ada"))'
            ),
            "options": ["Hi Ada", "Hi name", "greet Ada", "Nothing is printed"],
            "answer": "Hi Ada",
            "explain": 'The argument "Ada" is passed into the name parameter '
                       'and joined onto "Hi ".',
        },
        {
            "prompt": "Which keyword is used to define a function in Python?",
            "options": ["def", "func", "function", "define"],
            "answer": "def",
            "explain": "Functions are defined with def, e.g. def greet(name):",
        },
        {
            "prompt": "What does this code print?",
            "code": "items = [1, 2, 3]\nitems.append(4)\nprint(len(items))",
            "options": ["3", "4", "5", "Error"],
            "answer": "4",
            "explain": "append() adds one item to the end, so the list now has 4 items.",
        },
        {
            "prompt": "What does this code print?",
            "code": 'print("Py" * 3)',
            "options": ["PyPyPy", "Py3", "Py Py Py", "Error"],
            "answer": "PyPyPy",
            "explain": "Multiplying a string by a whole number repeats it.",
        },
        {
            "prompt": "What does this code print?",
            "code": "print(7 > 3 and 2 > 5)",
            "options": ["True", "False", "7", "Error"],
            "answer": "False",
            "explain": "'and' is only True when both sides are True, and 2 > 5 is False.",
        },
        {
            "prompt": "Which symbol starts a comment in Python?",
            "options": ["#", "//", "/*", "--"],
            "answer": "#",
            "explain": "Everything after # on a line is ignored by Python.",
        },
    ],
    "medium": [
        {
            "prompt": "What does this code print?",
            "code": (
                "total = 0\n"
                "for n in range(1, 5):\n"
                "    total += n\n"
                "print(total)"
            ),
            "options": ["10", "15", "4", "9"],
            "answer": "10",
            "explain": "range(1, 5) gives 1, 2, 3, 4 and their sum is 10.",
        },
        {
            "prompt": "What does this code print?",
            "code": 'word = "python"\nprint(word[1:4])',
            "options": ["pyt", "yth", "ytho", "ython"],
            "answer": "yth",
            "explain": "The slice [1:4] takes indexes 1, 2 and 3. "
                       "The end index is not included.",
        },
        {
            "prompt": "What does this code print?",
            "code": 'scores = {"ana": 90, "ben": 75}\nprint(scores.get("cal", 0))',
            "options": ["None", "0", "KeyError", "cal"],
            "answer": "0",
            "explain": ".get() returns the default value (0) when the key is "
                       "missing, instead of raising a KeyError.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "n = 15\n"
                "if n % 3 == 0 and n % 5 == 0:\n"
                '    print("FizzBuzz")\n'
                "elif n % 3 == 0:\n"
                '    print("Fizz")\n'
                "else:\n"
                "    print(n)"
            ),
            "options": ["FizzBuzz", "Fizz", "15", "Fizz FizzBuzz"],
            "answer": "FizzBuzz",
            "explain": "15 divides evenly by both 3 and 5, so the first condition "
                       "is True and the elif/else branches are skipped.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "count = 0\n"
                "while count < 10:\n"
                "    count += 3\n"
                "print(count)"
            ),
            "options": ["9", "10", "12", "3"],
            "answer": "12",
            "explain": "count goes 3, 6, 9, 12. The condition is only checked "
                       "before each pass, so the loop stops once count is 12.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "def power(base, exp=2):\n"
                "    return base ** exp\n"
                "\n"
                "print(power(3))"
            ),
            "options": ["6", "9", "27", "Error"],
            "answer": "9",
            "explain": "exp uses its default value of 2, so the result is 3 ** 2.",
        },
        {
            "prompt": "What does this code print?",
            "code": "nums = [4, 1, 3]\nresult = nums.sort()\nprint(result)",
            "options": ["[1, 3, 4]", "None", "[4, 1, 3]", "Error"],
            "answer": "None",
            "explain": "list.sort() sorts the list in place and returns None. "
                       "Use sorted(nums) to get a new sorted list.",
        },
        {
            "prompt": "What does this code print?",
            "code": 'name = "Ada"\nlevel = 3\nprint(f"{name} is level {level + 1}")',
            "options": [
                "Ada is level 4",
                "Ada is level 3 + 1",
                "{name} is level {level + 1}",
                "Ada is level 31",
            ],
            "answer": "Ada is level 4",
            "explain": "f-strings evaluate the expressions inside {} and insert the results.",
        },
        {
            "prompt": "What does this code print?",
            "code": 'letters = ["a", "b", "c", "d"]\nprint(letters[-2:])',
            "options": ["['c', 'd']", "['d']", "['b', 'c']", "c"],
            "answer": "['c', 'd']",
            "explain": "Negative indexes count from the end, so [-2:] takes the last two items.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "for i in range(5):\n"
                "    if i == 3:\n"
                "        break\n"
                '    print(i, end=" ")'
            ),
            "options": ["0 1 2", "0 1 2 3", "0 1 2 4", "3"],
            "answer": "0 1 2",
            "explain": "break exits the loop as soon as i is 3, before 3 is printed.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "x = 10\n"
                "\n"
                "def change():\n"
                "    x = 5\n"
                "\n"
                "change()\n"
                "print(x)"
            ),
            "options": ["5", "10", "None", "Error"],
            "answer": "10",
            "explain": "Assigning x inside the function creates a new local "
                       "variable. The global x is unchanged.",
        },
        {
            "prompt": "What does this code print?",
            "code": 'print(len("hello world".split()))',
            "options": ["2", "11", "10", "1"],
            "answer": "2",
            "explain": "split() breaks the string on whitespace into ['hello', 'world'].",
        },
    ],
    "hard": [
        {
            "prompt": "What does this code print?",
            "code": "print([x * x for x in range(6) if x % 2 == 0])",
            "options": ["[0, 4, 16]", "[4, 16]", "[1, 9, 25]", "[0, 2, 4]"],
            "answer": "[0, 4, 16]",
            "explain": "The comprehension keeps the even numbers 0, 2 and 4, then squares them.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "def add_item(item, bag=[]):\n"
                "    bag.append(item)\n"
                "    return bag\n"
                "\n"
                'add_item("gem")\n'
                'print(add_item("coin"))'
            ),
            "options": ["['coin']", "['gem', 'coin']", "['gem']", "Error"],
            "answer": "['gem', 'coin']",
            "explain": "A default value is created once, when the function is "
                       "defined, so every call shares the same list. "
                       "Use bag=None and create the list inside instead.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "a = [1, 2, 3]\n"
                "b = a\n"
                "c = a[:]\n"
                "b.append(4)\n"
                "c.append(5)\n"
                "print(a)"
            ),
            "options": ["[1, 2, 3]", "[1, 2, 3, 4]", "[1, 2, 3, 5]", "[1, 2, 3, 4, 5]"],
            "answer": "[1, 2, 3, 4]",
            "explain": "b is just another name for the same list as a, but a[:] "
                       "makes a copy. Only the change made through b shows up in a.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "def make_multiplier(n):\n"
                "    def multiply(x):\n"
                "        return x * n\n"
                "    return multiply\n"
                "\n"
                "triple = make_multiplier(3)\n"
                "print(triple(7))"
            ),
            "options": ["21", "10", "7", "Error"],
            "answer": "21",
            "explain": "multiply() remembers n = 3 from the function that created "
                       "it (a closure), so triple(7) is 7 * 3.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "def average(*args):\n"
                "    return sum(args) / len(args)\n"
                "\n"
                "print(average(2, 4, 9))"
            ),
            "options": ["5.0", "5", "15", "Error"],
            "answer": "5.0",
            "explain": "*args collects the arguments into a tuple. The / operator "
                       "always returns a float, so 15 / 3 is 5.0.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                'words = ["pear", "fig", "kiwi", "apple"]\n'
                "print(sorted(words, key=lambda w: (len(w), w)))"
            ),
            "options": [
                "['fig', 'kiwi', 'pear', 'apple']",
                "['fig', 'pear', 'kiwi', 'apple']",
                "['apple', 'fig', 'kiwi', 'pear']",
                "['apple', 'kiwi', 'pear', 'fig']",
            ],
            "answer": "['fig', 'kiwi', 'pear', 'apple']",
            "explain": "The key sorts by length first, then alphabetically to "
                       "break ties, so 'kiwi' comes before 'pear'.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "def mystery(n):\n"
                "    if n <= 1:\n"
                "        return 1\n"
                "    return n * mystery(n - 1)\n"
                "\n"
                "print(mystery(5))"
            ),
            "options": ["120", "15", "24", "RecursionError"],
            "answer": "120",
            "explain": "mystery() is a recursive factorial: 5 * 4 * 3 * 2 * 1 = 120.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                'names = ["Ana", "Ben", "Cy"]\n'
                "ages = [30, 25]\n"
                "print(dict(zip(names, ages)))"
            ),
            "options": [
                "{'Ana': 30, 'Ben': 25}",
                "{'Ana': 30, 'Ben': 25, 'Cy': None}",
                "[('Ana', 30), ('Ben', 25)]",
                "Error",
            ],
            "answer": "{'Ana': 30, 'Ben': 25}",
            "explain": "zip() stops at the end of the shortest input, so 'Cy' is left out.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                'word = "banana"\n'
                "counts = {ch: word.count(ch) for ch in word}\n"
                "print(counts)"
            ),
            "options": [
                "{'b': 1, 'a': 3, 'n': 2}",
                "{'b': 1, 'a': 1, 'n': 1}",
                "{'banana': 6}",
                "Error",
            ],
            "answer": "{'b': 1, 'a': 3, 'n': 2}",
            "explain": "Repeated keys just overwrite each other, leaving one "
                       "entry per unique letter with its full count.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "def counter():\n"
                "    count = 0\n"
                "    def increment():\n"
                "        nonlocal count\n"
                "        count += 1\n"
                "        return count\n"
                "    return increment\n"
                "\n"
                "tick = counter()\n"
                "tick()\n"
                "tick()\n"
                "print(tick())"
            ),
            "options": ["1", "3", "0", "UnboundLocalError"],
            "answer": "3",
            "explain": "nonlocal lets increment() update count in the enclosing "
                       "function, and that value is kept between calls.",
        },
        {
            "prompt": "What does this code print?",
            "code": 'print("adventure"[::-2])',
            "options": ["eunva", "avnue", "erutnevda", "Error"],
            "answer": "eunva",
            "explain": "A step of -2 walks backwards from the last character, "
                       "taking every second one.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "def check(n):\n"
                "    try:\n"
                "        return 10 / n\n"
                "    except ZeroDivisionError:\n"
                '        return "oops"\n'
                "    finally:\n"
                '        print("done", end=" ")\n'
                "\n"
                "print(check(0))"
            ),
            "options": ["done oops", "oops done", "oops", "ZeroDivisionError"],
            "answer": "done oops",
            "explain": 'The finally block runs before the function hands back its '
                       'return value, so "done" prints before "oops".',
        },
    ],
}


# ------------------------------------------------------------------
# Display and input helpers
# ------------------------------------------------------------------

def print_banner(title):
    """Print a title framed by lines of '=' characters."""
    print()
    print("=" * SCREEN_WIDTH)
    print(title.center(SCREEN_WIDTH))
    print("=" * SCREEN_WIDTH)


def narrate(text):
    """Print a paragraph of story text, wrapped to fit the screen."""
    print()
    print(textwrap.fill(text, width=SCREEN_WIDTH))


def get_choice(prompt, valid_choices):
    """Keep asking until the player types one of the valid choices."""
    while True:
        choice = input(prompt).strip().lower()
        if choice in valid_choices:
            return choice
        print(f"  Please enter one of: {', '.join(valid_choices)}")


def choose(options):
    """Show a numbered menu and return the number the player picks, as a string."""
    print()
    for number, option in enumerate(options, start=1):
        print(f"  {number}) {option}")
    valid_choices = [str(number) for number in range(1, len(options) + 1)]
    return get_choice(f"What will you do? ({'/'.join(valid_choices)}): ", valid_choices)


# ------------------------------------------------------------------
# Player helpers
# ------------------------------------------------------------------

def create_player(name, difficulty):
    """Build the dictionary that tracks the player's progress."""
    return {
        "name": name,
        "difficulty": difficulty,
        "lives": DIFFICULTY_SETTINGS[difficulty]["lives"],
        "score": 0,
        "inventory": [],
        "questions": [],  # shuffled deck, filled by draw_question()
    }


def show_status(player):
    """Print the player's current lives, score and relics."""
    relics = ", ".join(player["inventory"]) if player["inventory"] else "none"
    print(f"[ {player['name']} | {player['difficulty'].title()} | "
          f"Lives: {player['lives']} | Score: {player['score']} | Relics: {relics} ]")


def add_points(player, base_points, reason):
    """Add points scaled by the difficulty multiplier and announce them."""
    points = base_points * DIFFICULTY_SETTINGS[player["difficulty"]]["multiplier"]
    player["score"] += points
    print(f"  +{points} points ({reason})  Score: {player['score']}")


def lose_life(player):
    """Take away one life. Returns True if the player still has lives left."""
    player["lives"] -= 1
    if player["lives"] > 0:
        print(f"  You lose a life! Lives remaining: {player['lives']}")
    else:
        print("  You have no lives left!")
    return player["lives"] > 0


def collect_relic(player, relic):
    """Add a relic to the player's inventory. Relics are worth points if you win."""
    player["inventory"].append(relic)
    print(f"  * You found a relic: {relic}! *")


# ------------------------------------------------------------------
# Python challenges
# ------------------------------------------------------------------

def draw_question(player):
    """Take the next question from the player's deck, reshuffling when it runs out."""
    if not player["questions"]:
        player["questions"] = QUESTIONS[player["difficulty"]][:]
        random.shuffle(player["questions"])
    return player["questions"].pop()


def ask_question(player, challenger):
    """Ask one Python question. Returns True if the player answers correctly."""
    question = draw_question(player)
    options = question["options"][:]
    random.shuffle(options)
    letters = ["a", "b", "c", "d"][:len(options)]

    print()
    print(f"{challenger} challenges you:")
    print(f"  {question['prompt']}")
    if "code" in question:
        print()
        for line in question["code"].splitlines():
            print("      " + line)
    print()
    for letter, option in zip(letters, options):
        print(f"    {letter}) {option}")

    answer = get_choice(f"Your answer ({'/'.join(letters)}): ", letters)
    correct_letter = letters[options.index(question["answer"])]
    if answer == correct_letter:
        print("  Correct!")
        add_points(player, CORRECT_ANSWER_POINTS, "correct answer")
        is_correct = True
    else:
        print(f"  Wrong! The answer was {correct_letter}) {question['answer']}")
        is_correct = False
    print(textwrap.fill(question["explain"], width=SCREEN_WIDTH,
                        initial_indent="  Why: ", subsequent_indent="       "))
    return is_correct


def face_challenge(player, challenger):
    """Ask questions until one is answered correctly. Each wrong answer costs a life.

    Returns True if the challenge is passed, or False if the player runs out of lives.
    """
    while True:
        if ask_question(player, challenger):
            return True
        if not lose_life(player):
            return False
        print(f"  {challenger} gives you another chance...")


# ------------------------------------------------------------------
# Game start and difficulty
# ------------------------------------------------------------------

def select_difficulty(score_log):
    """Let the player pick easy, medium or hard. Returns the level name."""
    levels = list(DIFFICULTY_SETTINGS)  # ["easy", "medium", "hard"]
    print("\nChoose your difficulty:")
    for number, level in enumerate(levels, start=1):
        settings = DIFFICULTY_SETTINGS[level]
        life_word = "life" if settings["lives"] == 1 else "lives"
        high_score = score_log["levels"][level]["high_score"]
        print(f"  {number}) {level.title():<6} - {settings['lives']} {life_word + ',':<6} "
              f"x{settings['multiplier']} points   (High score: {high_score})")
        print(f"     Topics: {settings['topics']}")

    valid_choices = [str(number) for number in range(1, len(levels) + 1)] + levels
    choice = get_choice("Select a difficulty (1/2/3): ", valid_choices)
    if choice.isdigit():
        choice = levels[int(choice) - 1]
    print(f"\n{choice.title()} difficulty selected. Good luck!")
    return choice


def start_game(score_log, player_name=None):
    """Introduce the quest, set up the player, and send them down their first path.

    Returns the player dictionary and the result of the quest: "win" or "lose".
    """
    print_banner("THE LOST TREASURE OF PYTHONIA")
    narrate("Centuries ago, the ancient coders of Pythonia hid their greatest "
            "treasure, the Golden Interpreter, deep within this wild land. Its "
            "guardians still test every traveler with riddles written in the "
            "language of the serpent: Python.")
    narrate("Answer wisely and choose your path carefully. Every wrong answer "
            "costs you a life, and some choices lead to certain doom...")
    print()

    # On a replay, pressing Enter keeps the name from the last game.
    prompt = "What is your name, explorer? "
    if player_name:
        prompt = f"What is your name, explorer? (press Enter to keep {player_name}) "
    player_name = input(prompt).strip() or player_name or "Explorer"

    difficulty = select_difficulty(score_log)
    player = create_player(player_name, difficulty)

    narrate(f"Welcome, {player_name}! You arrive at the edge of Pythonia with "
            "nothing but a backpack and your wits. Two paths lie before you: a "
            "dense, whispering forest, and a dark cave whose mouth seems to hiss "
            "softly in the wind.")
    choice = choose(["Explore the Whispering Forest", "Enter the Serpent's Cave"])
    if choice == "1":
        result = forest_path(player)
    else:
        result = cave_path(player)
    return player, result


# ------------------------------------------------------------------
# The forest
# ------------------------------------------------------------------

def forest_path(player):
    """The forest: follow the river or climb the giant tree."""
    print_banner("THE WHISPERING FOREST")
    show_status(player)
    narrate("Towering trees close in around you and strange birds call from the "
            "canopy. To your left, a river murmurs through the ferns. To your "
            "right stands an ancient tree so tall its top disappears into the "
            "mist. From up there, you could see for miles.")
    choice = choose(["Follow the river", "Climb the giant tree"])
    if choice == "1":
        return river_route(player)
    else:
        return tree_route(player)


def river_route(player):
    """The river leads to a waterfall and its guardian."""
    print_banner("THE ROARING WATERFALL")
    show_status(player)
    narrate("You follow the river until it plunges over a cliff in a roaring "
            "waterfall. The water swirls, rises, and takes the shape of a "
            "towering figure: the River Guardian. \"None may pass without "
            "answering my riddle,\" it booms.")
    if not face_challenge(player, "The River Guardian"):
        return game_over("The Guardian's patience runs dry. A great wave sweeps "
                         "you downstream, far away from the treasure.")

    narrate("The Guardian bows and places a shimmering pearl in your hand.")
    collect_relic(player, "River Pearl")
    narrate("It points a watery finger at a dark gap hidden behind the "
            "waterfall. Nearby, a fallen log covered in slick green moss "
            "stretches across the gorge. It looks like a quicker way across.")
    choice = choose(["Slip behind the waterfall, as the Guardian showed you",
                     "Cross the gorge on the mossy log"])
    if choice == "1":
        add_points(player, WISE_CHOICE_POINTS, "wise choice")
        narrate("Behind the curtain of water, a hidden tunnel leads you straight "
                "to the steps of an ancient temple.")
        return temple_vault(player)
    else:
        return game_over("Halfway across, your boot slips on the moss. You "
                         "tumble into the rapids and are carried far from the "
                         "treasure. Somewhere behind you, the Guardian sighs.")


def tree_route(player):
    """The giant tree, where a wise owl guards the safe way to the temple."""
    print_banner("THE TOP OF THE GIANT TREE")
    show_status(player)
    narrate("You climb branch by branch until you break through the mist. Far to "
            "the east, a golden temple roof glints above the jungle. A great grey "
            "owl lands beside you and blinks. \"Hoo! Only those who think like a "
            "programmer may learn the safe way down.\"")
    if not face_challenge(player, "The Wise Owl"):
        return game_over("The owl ruffles its feathers and flies away. As you "
                         "reach after it, the branch beneath you snaps...")

    narrate("\"Well reasoned!\" hoots the owl, and it plucks a feather for you.")
    collect_relic(player, "Owl Feather")
    narrate("\"Now listen closely. The swamp below is the shortest way to the "
            "temple, but it swallows the careless. The vines are slow, but strong.\"")
    choice = choose(["Swing along the vines toward the temple",
                     "Climb down and take the swamp shortcut"])
    if choice == "1":
        add_points(player, WISE_CHOICE_POINTS, "wise choice")
        narrate("Vine by vine, you swing through the canopy like a jungle "
                "acrobat and land softly on the temple steps.")
        return temple_vault(player)
    else:
        return game_over("Three steps into the swamp, the mud grabs your boots. "
                         "The harder you struggle, the deeper you sink. You "
                         "should have listened to the owl!")


# ------------------------------------------------------------------
# The cave
# ------------------------------------------------------------------

def cave_path(player):
    """The cave: light a torch or proceed in the dark."""
    print_banner("THE SERPENT'S CAVE")
    show_status(player)
    narrate("Cold air flows from the cave mouth, carrying a faint hissing sound. "
            "Snake carvings coil around the entrance. Just inside, you find an "
            "old torch and a flint. Lighting it would help you see, but the light "
            "might also wake whatever is hissing in the dark...")
    choice = choose(["Light the torch", "Proceed in the dark"])
    if choice == "1":
        add_points(player, WISE_CHOICE_POINTS, "wise choice")
        narrate("The torch flares to life. Good thing, too: the floor ahead is "
                "riddled with deep pits! The hissing, you realize, is only wind "
                "whistling through cracks in the rock.")
        return glyph_door(player)
    else:
        return dark_tunnel(player)


def dark_tunnel(player):
    """Going on without light is a setback that costs a life, or ends the quest."""
    narrate("You creep forward in total darkness, one hand on the cold, damp "
            "wall. Suddenly the ground vanishes beneath your feet and you "
            "tumble into a pit!")
    if not lose_life(player):
        return game_over("The pit is far too deep to climb out of without "
                         "light. Your quest ends here, in the dark.")

    narrate("Bruised but alive, you claw your way out and crawl back to the "
            "entrance. This time you light the torch. Lesson learned! In its glow "
            "you can see the floor is riddled with pits.")
    return glyph_door(player)


def glyph_door(player):
    """Deep in the cave, a door sealed with a Python puzzle."""
    print_banner("THE GLYPH DOOR")
    show_status(player)
    narrate("You weave between the pits until the tunnel ends at a massive "
            "stone door. Glowing glyphs crawl across its surface and rearrange "
            "themselves into lines of Python code.")
    if not face_challenge(player, "The Glyph Door"):
        return game_over("The glyphs flash red. With a deep rumble the tunnel "
                         "behind you seals shut, and your torch flickers out...")

    narrate("The glyphs flash gold and the door grinds open. A small carved "
            "tablet falls from the wall at your feet.")
    collect_relic(player, "Glyph Tablet")
    narrate("Beyond the door the tunnel splits in two. From the left drifts warm "
            "air and a faint golden glow. The right tunnel is cold, its walls "
            "marked with fresh, deep claw scratches, and something in there is "
            "growling.")
    choice = choose(["Take the left tunnel toward the golden glow",
                     "Take the right tunnel past the claw marks"])
    if choice == "1":
        add_points(player, WISE_CHOICE_POINTS, "wise choice")
        narrate("The golden glow grows brighter with every step until you emerge "
                "at the heart of an ancient temple.")
        return temple_vault(player)
    else:
        return game_over("The claw marks belong to a very large, very grumpy "
                         "cave bear who does not appreciate visitors. You flee "
                         "all the way back to the entrance, your quest in ruins.")


# ------------------------------------------------------------------
# The temple and the end of the quest
# ------------------------------------------------------------------

def temple_vault(player):
    """The final challenge: an optional jeweled chest, then two serpent locks."""
    print_banner("THE TEMPLE OF THE GOLDEN INTERPRETER")
    show_status(player)
    narrate("Torches burst into flame as you enter the temple's great hall. At "
            "the far end stands the vault, its door sealed by two stone serpent "
            "locks. Beside the path sits a small jeweled chest with a riddle "
            "carved into its lid. Solving it would earn you a rare relic, but a "
            "wrong answer will cost you a life.")
    choice = choose(["Try to open the jeweled chest",
                     "Ignore the chest and head for the vault"])
    if choice == "1":
        if ask_question(player, "The Jeweled Chest"):
            narrate("Click! The lid springs open, revealing a ring set with a "
                    "blazing ruby.")
            collect_relic(player, "Ruby Ring")
        else:
            if not lose_life(player):
                return game_over("A dart coated in sleeping venom shoots from "
                                 "the lock. You doze off just steps away from "
                                 "the treasure...")
            narrate("A tiny dart shoots from the lock and stings your hand. "
                    "The chest stays shut.")
    else:
        narrate("You leave the chest alone. Sometimes the wisest move is not "
                "to gamble.")

    narrate("You approach the vault door. The eyes of the stone serpents begin "
            "to glow.")
    for lock_number in range(1, 3):
        if not face_challenge(player, f"Serpent Lock #{lock_number}"):
            return game_over("The serpent's eyes flash red and the vault seals "
                             "itself forever. The treasure remains lost.")
        print(f"  Serpent Lock #{lock_number} slides open!")
    return victory(player)


def victory(player):
    """The vault opens! Award the end-of-quest bonuses."""
    print_banner("THE TREASURE IS YOURS!")
    narrate("The vault door swings open with a groan. Inside, resting on a "
            "pedestal of black stone, sits the legendary Golden Interpreter, "
            f"humming with ancient power. Congratulations, {player['name']}! "
            "Your name will be carved among the great coders of Pythonia.")
    print()
    add_points(player, TREASURE_POINTS, "found the treasure")
    for relic in player["inventory"]:
        add_points(player, RELIC_POINTS, f"relic: {relic}")
    add_points(player, LIFE_POINTS * player["lives"],
               f"lives remaining: {player['lives']}")
    return "win"


def game_over(message):
    """End the quest with a failure message."""
    narrate(message)
    print_banner("GAME OVER")
    return "lose"


# ------------------------------------------------------------------
# Score log (saved to scores.json)
# ------------------------------------------------------------------

def new_score_log():
    """Create an empty score log with a row for every difficulty level."""
    levels = {}
    for level in DIFFICULTY_SETTINGS:
        levels[level] = {
            "games_played": 0,
            "wins": 0,
            "last_score": 0,
            "high_score": 0,
            "best_explorer": "",
        }
    return {"levels": levels, "history": []}


def load_scores():
    """Load the score log from disk, or start a fresh one if there isn't one yet."""
    score_log = new_score_log()
    try:
        with open(SCORE_FILE, "r", encoding="utf-8") as file:
            saved = json.load(file)
        for level, stats in saved.get("levels", {}).items():
            if level in score_log["levels"]:
                score_log["levels"][level].update(stats)
        score_log["history"] = saved.get("history", [])
    except (OSError, ValueError):
        pass  # no saved scores yet, or the file is unreadable
    return score_log


def save_scores(score_log):
    """Write the score log to disk."""
    try:
        with open(SCORE_FILE, "w", encoding="utf-8") as file:
            json.dump(score_log, file, indent=2)
    except OSError:
        print("  (Could not save the score log.)")


def record_score(score_log, player, result):
    """Add this game to the score log. Returns True if it set a new high score."""
    stats = score_log["levels"][player["difficulty"]]
    stats["games_played"] += 1
    stats["last_score"] = player["score"]
    if result == "win":
        stats["wins"] += 1

    is_new_high_score = player["score"] > stats["high_score"]
    if is_new_high_score:
        stats["high_score"] = player["score"]
        stats["best_explorer"] = player["name"]

    score_log["history"].append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "explorer": player["name"],
        "difficulty": player["difficulty"],
        "score": player["score"],
        "result": "Found the treasure" if result == "win" else "Quest failed",
    })
    score_log["history"] = score_log["history"][-MAX_HISTORY:]
    save_scores(score_log)
    return is_new_high_score


def show_final_score(player, score_log, is_new_high_score):
    """Print the player's final score next to the high score for their level."""
    level = player["difficulty"]
    stats = score_log["levels"][level]
    print(f"\n{player['name']}'s final score: {player['score']}")
    if is_new_high_score:
        print(f"*** NEW {level.upper()} HIGH SCORE! ***")
    else:
        holder = stats["best_explorer"] or "nobody yet"
        print(f"{level.title()} high score to beat: {stats['high_score']} ({holder})")


def show_scoreboard(score_log):
    """Print the latest and highest score for each difficulty, plus recent games."""
    print_banner("SCORE LOG")
    print(f"  {'Level':<8}{'Played':>8}{'Wins':>6}{'Latest':>8}{'High':>7}   Best explorer")
    print("  " + "-" * (SCREEN_WIDTH - 4))
    for level, stats in score_log["levels"].items():
        if stats["games_played"] == 0:
            print(f"  {level.title():<8}  (not played yet)")
        else:
            print(f"  {level.title():<8}{stats['games_played']:>8}{stats['wins']:>6}"
                  f"{stats['last_score']:>8}{stats['high_score']:>7}   "
                  f"{stats['best_explorer'] or '-'}")

    if score_log["history"]:
        print("\n  Recent games:")
        for game in reversed(score_log["history"]):
            print(f"    {game['date']}  {game['explorer']:<12} "
                  f"{game['difficulty'].title():<7}{game['score']:>5} pts  {game['result']}")


# ------------------------------------------------------------------
# Main game loop
# ------------------------------------------------------------------

def play_again(result):
    """Ask whether to start a new quest. Returns True for yes."""
    if result == "win":
        prompt = "\nWould you like to play again? (y/n): "
    else:
        prompt = "\nYour quest has failed. Would you like to try again? (y/n): "
    return get_choice(prompt, ["y", "n", "yes", "no"]) in ["y", "yes"]


def main():
    """Keep running quests until the player decides to stop."""
    score_log = load_scores()
    player_name = None
    playing = True
    while playing:
        player, result = start_game(score_log, player_name)
        player_name = player["name"]

        is_new_high_score = record_score(score_log, player, result)
        show_final_score(player, score_log, is_new_high_score)
        show_scoreboard(score_log)
        playing = play_again(result)

    print("\nThanks for playing The Lost Treasure of Pythonia. Happy coding!")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\nYou leave Pythonia for now. Farewell, explorer!")
