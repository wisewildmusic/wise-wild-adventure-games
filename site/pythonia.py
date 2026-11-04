"""
The Lost Treasure of Pythonia, web edition
------------------------------------------
The text adventure from AdventuresInPython.py, rebuilt to run as a page of the website
(/adventure/). The story, the Python challenges and the scoring are the same as in the
console game, and so are the names of its functions. What changed for the web:

- Wherever the console game waited for input(), these functions *yield* a prompt (a
  Choice or a Question) and the page's buttons send the explorer's answer back in.
- Instead of printing, the game notes what happens (story, points, relics, answers) in
  the quest's log, and the page shows it, with a picture for each scene.
- A quest is saved as its random seed plus the moves made so far. Every time the page is
  shown, replay() plays the quest again from the start with those moves, which always
  ends in the same place. The server keeps nothing in memory, and going back in the
  browser can't rewind a quest.
- Explorer names must pass clean_name(): letters, numbers and spaces only.
- Scores are saved in the website's adventure database (see app.py) and shared by
  every explorer, instead of in scores.json.
- An explorer who wins on Easy or Medium can go on to the next level (next_level()),
  keeping their score: the new quest starts with it (replay's `carried`) and adds to it.
- An explorer who wins can instead go back for a path they haven't taken yet on that
  level (paths_left()), score and all: the new quest offers only that path (replay's
  `only_path`) and asks none of the questions the level's earlier paths asked (replay's
  `skip_questions`).
- The castle ruins (castle_path()) are a third way in, added on the web; its pictures are
  cut from one picture sheet. Quests keep the game version they started on, so the
  questions added with it don't change quests saved before (QUESTION_COUNTS).
- After a win, the explorer may wake that path and level's dragon (DRAGONS,
  dragon_battle()) for one bonus riddle and a share of its treasure.
- An explorer who completes every path on every level may face Python, the final boss
  (python_battle()): one of the nine hardest questions (PYTHON_QUESTIONS), for the title of
  Python Master, or the loss of their whole score.
"""

import random
import re

# Change GAME_VERSION when the questions change. A quest keeps the version it started on and
# is always replayed with that version's questions: the first QUESTION_COUNTS[version] of each
# level's list (new questions only ever go on the end). Version 2 (2026-11-01) added eight
# questions per level, with the castle path.
GAME_VERSION = 2
QUESTION_COUNTS = {1: 12, 2: 20}


def can_replay(version):
    """Whether a quest saved by this version of the game can still be played."""
    return version in QUESTION_COUNTS

# Explorer names: letters, numbers and spaces only, starting with a letter, up to 20
# characters. Nothing else gets in, so a name can never carry code or markup.
NAME_MAX_LENGTH = 20
NAME_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9 ]*")
DEFAULT_NAME = "Explorer"


def clean_name(raw):
    """The explorer's name with extra spaces tidied ("Explorer" if left blank), or None if
    it breaks the rules."""
    name = " ".join(str(raw).split())
    if not name:
        return DEFAULT_NAME
    if len(name) > NAME_MAX_LENGTH or not NAME_PATTERN.fullmatch(name):
        return None
    return name


# ------------------------------------------------------------------
# Game settings and questions (as in AdventuresInPython.py)
# ------------------------------------------------------------------

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


def next_level(difficulty):
    """The level a winner can go on to (easy -> medium -> hard), or None after the hardest."""
    levels = list(DIFFICULTY_SETTINGS)
    position = levels.index(difficulty) + 1
    return levels[position] if position < len(levels) else None


# The three ways into Pythonia, in the order the first choice offers them (the castle came
# third, on 2026-11-01), and what's said about each one when a winner goes back for a path
# they didn't take.
PATHS = {
    "forest": "Explore the Whispering Forest",
    "cave": "Enter the Serpent's Cave",
    "castle": "Climb to the Ancient Castle Ruins",
}
PATH_NAMES = {"forest": "the Whispering Forest", "cave": "the Serpent's Cave", "castle": "the Ancient Castle Ruins"}
PATH_SIGHTS = {
    "forest": "the dense, whispering forest",
    "cave": "the dark cave whose mouth seems to hiss softly in the wind",
    "castle": "the torch-lit trail that climbs to the ruins of an ancient castle",
}


def path_taken(moves, only_path=None):
    """The path a quest went down: the one it was sent on, or else the one its first move
    picked. None before the first move."""
    if only_path:
        return only_path
    if moves and moves[0] in [str(number) for number in range(1, len(PATHS) + 1)]:
        return list(PATHS)[int(moves[0]) - 1]
    return None


def paths_left(done):
    """The paths not taken yet (of those in `done`), in the order the first choice offers them."""
    return [path for path in PATHS if path not in done]


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
        # Added in version 2, with the castle path.
        {
            "prompt": "What does this code print?",
            "code": "print(10 // 3)",
            "options": ["3", "3.33", "3.0", "1"],
            "answer": "3",
            "explain": "// is floor division: it divides, then drops the remainder, "
                       "leaving a whole number.",
        },
        {
            "prompt": "What does this code print?",
            "code": 'print("10" + "5")',
            "options": ["15", "105", "10 5", "Error"],
            "answer": "105",
            "explain": 'With quotes, "10" and "5" are strings, and + joins strings '
                       "end to end instead of adding numbers.",
        },
        {
            "prompt": "What does this code print?",
            "code": 'name = "Castle"\nprint(len(name))',
            "options": ["5", "6", "7", "Castle"],
            "answer": "6",
            "explain": "len() counts the characters in a string: C-a-s-t-l-e is 6.",
        },
        {
            "prompt": "What does this code print?",
            "code": 'colors = ["red", "green", "blue"]\nprint(colors[-1])',
            "options": ["red", "green", "blue", "Error"],
            "answer": "blue",
            "explain": "Index -1 means the last item in the list.",
        },
        {
            "prompt": "What does this code print?",
            "code": "print(17 % 5)",
            "options": ["3", "2", "3.4", "12"],
            "answer": "2",
            "explain": "% gives the remainder of a division: 17 is 3 fives (15) with 2 left over.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "x = 3\n"
                "if x > 5:\n"
                '    print("big")\n'
                "elif x > 2:\n"
                '    print("medium")\n'
                "else:\n"
                '    print("small")'
            ),
            "options": ["big", "medium", "small", "medium small"],
            "answer": "medium",
            "explain": "x > 5 is False, so Python checks the elif: 3 > 2 is True, and "
                       "the else is skipped.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "total = 0\n"
                "for n in [2, 4, 6]:\n"
                "    total = total + n\n"
                "print(total)"
            ),
            "options": ["6", "12", "246", "0"],
            "answer": "12",
            "explain": "The loop adds each number to total in turn: 2 + 4 + 6 = 12.",
        },
        {
            "prompt": "What does this code print?",
            "code": 'print("knight".upper())',
            "options": ["KNIGHT", "Knight", "knight", "Error"],
            "answer": "KNIGHT",
            "explain": "upper() gives back a copy of the string in capital letters.",
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
        # Added in version 2, with the castle path.
        {
            "prompt": "What does this code print?",
            "code": (
                'castle = {"towers": 4, "gates": 1}\n'
                "for key in castle:\n"
                '    print(key, end=" ")'
            ),
            "options": ["towers gates", "4 1", "towers 4 gates 1", "Error"],
            "answer": "towers gates",
            "explain": "Looping over a dictionary gives its keys, in the order they were added.",
        },
        {
            "prompt": "What does this code print?",
            "code": "nums = [0, 1, 2, 3, 4, 5]\nprint(nums[::2])",
            "options": ["[0, 2, 4]", "[1, 3, 5]", "[0, 1]", "[2, 3, 4, 5]"],
            "answer": "[0, 2, 4]",
            "explain": "The third number in a slice is the step: [::2] takes every second "
                       "item, starting from the first.",
        },
        {
            "prompt": "What does this code print?",
            "code": 'print("-".join(["moat", "wall", "keep"]))',
            "options": ["moat-wall-keep", "-moat-wall-keep-", "moatwallkeep", "['moat', 'wall', 'keep']"],
            "answer": "moat-wall-keep",
            "explain": 'join() puts the string it is called on ("-") between the items '
                       "of the list.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                'def greet(name, greeting="Hello"):\n'
                '    return f"{greeting}, {name}!"\n'
                "\n"
                'print(greet("Ada", greeting="Hail"))'
            ),
            "options": ["Hail, Ada!", "Hello, Ada!", "Hello, Hail!", "Error"],
            "answer": "Hail, Ada!",
            "explain": "A keyword argument (greeting=...) replaces the default value for "
                       "that call.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "count = 0\n"
                "\n"
                "def add():\n"
                "    global count\n"
                "    count += 1\n"
                "\n"
                "add()\n"
                "add()\n"
                "print(count)"
            ),
            "options": ["0", "1", "2", "UnboundLocalError"],
            "answer": "2",
            "explain": "global lets the function change the count outside it, so both "
                       "calls add to the same variable.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "for i in range(5):\n"
                "    if i % 2 == 0:\n"
                "        continue\n"
                '    print(i, end=" ")'
            ),
            "options": ["1 3", "0 2 4", "0 1 2 3 4", "1 3 5"],
            "answer": "1 3",
            "explain": "continue skips the rest of the loop body for that pass, so the "
                       "even numbers are never printed.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                'knights = {"Ana": 3}\n'
                'knights["Ben"] = 5\n'
                'knights["Ana"] = 4\n'
                'print(len(knights), knights["Ana"])'
            ),
            "options": ["2 4", "3 4", "2 3", "3 3"],
            "answer": "2 4",
            "explain": "Assigning to an existing key replaces its value, so there are "
                       "still only 2 keys, and Ana's value is now 4.",
        },
        {
            "prompt": "What does this code print?",
            "code": "print(list(range(10, 0, -3)))",
            "options": ["[10, 7, 4, 1]", "[10, 7, 4]", "[1, 4, 7, 10]", "[]"],
            "answer": "[10, 7, 4, 1]",
            "explain": "range(10, 0, -3) counts down from 10 in steps of 3 and stops "
                       "before reaching 0.",
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
        # Added in version 2, with the castle path.
        {
            "prompt": "What does this code print?",
            "code": "print([(x, y) for x in range(2) for y in range(2) if x != y])",
            "options": ["[(0, 1), (1, 0)]", "[(0, 0), (1, 1)]", "[(0, 1)]", "[]"],
            "answer": "[(0, 1), (1, 0)]",
            "explain": "The two for clauses work like nested loops, and the if keeps only "
                       "the pairs where x and y differ.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "funcs = [lambda: i for i in range(3)]\n"
                "print([f() for f in funcs])"
            ),
            "options": ["[0, 1, 2]", "[2, 2, 2]", "[0, 0, 0]", "Error"],
            "answer": "[2, 2, 2]",
            "explain": "Each lambda looks up i when it is called, not when it is made. By "
                       "then the loop has finished and i is 2.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "def count_down(n):\n"
                "    if n == 0:\n"
                '        return "Liftoff"\n'
                '    return str(n) + " " + count_down(n - 1)\n'
                "\n"
                "print(count_down(3))"
            ),
            "options": ["3 2 1 Liftoff", "Liftoff 1 2 3", "3 2 1 0 Liftoff", "RecursionError"],
            "answer": "3 2 1 Liftoff",
            "explain": "Each call adds its own number in front of the result of the next "
                       "call, until n reaches 0 and the recursion stops.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                "def steps(n):\n"
                "    if n <= 2:\n"
                "        return n\n"
                "    return steps(n - 1) + steps(n - 2)\n"
                "\n"
                "print(steps(5))"
            ),
            "options": ["5", "8", "13", "120"],
            "answer": "8",
            "explain": "steps(3) = 2 + 1 = 3, steps(4) = 3 + 2 = 5, and "
                       "steps(5) = 5 + 3 = 8.",
        },
        {
            "prompt": "What does this code print?",
            "code": "t = ([1], [2])\nt[0].append(3)\nprint(t)",
            "options": ["([1, 3], [2])", "([1], [2])", "TypeError", "([1], [2], 3)"],
            "answer": "([1, 3], [2])",
            "explain": "A tuple can't be changed, but the lists inside it can: append() "
                       "changes the first list in place.",
        },
        {
            "prompt": "What does this code print?",
            "code": "grid = [[0] * 2] * 2\ngrid[0][0] = 1\nprint(grid)",
            "options": ["[[1, 0], [1, 0]]", "[[1, 0], [0, 0]]", "[[1, 1], [0, 0]]", "Error"],
            "answer": "[[1, 0], [1, 0]]",
            "explain": "* 2 copies the reference, not the inner list, so both rows are the "
                       "same list. Changing one changes both.",
        },
        {
            "prompt": "What does this code print?",
            "code": (
                'prices = {"sword": 30, "shield": 20, "helm": 10}\n'
                "print({k: v for k, v in prices.items() if v > 15})"
            ),
            "options": [
                "{'sword': 30, 'shield': 20}",
                "{'helm': 10}",
                "['sword', 'shield']",
                "{'sword': 30, 'shield': 20, 'helm': 10}",
            ],
            "answer": "{'sword': 30, 'shield': 20}",
            "explain": "The dictionary comprehension keeps only the items whose value is "
                       "over 15.",
        },
        {
            "prompt": "What does this code print?",
            "code": "first, *rest = [1, 2, 3, 4]\nprint(rest)",
            "options": ["[2, 3, 4]", "(2, 3, 4)", "4", "[1, 2, 3, 4]"],
            "answer": "[2, 3, 4]",
            "explain": "The starred name collects every item left over after first, "
                       "as a list.",
        },
    ],
}


# ------------------------------------------------------------------
# Bonus dragons (web edition, 2026-11-01)
# ------------------------------------------------------------------
# After a win, the dragon of that path and level sleeps on a chest of treasure nearby. The
# explorer may wake it (the move DRAGON_MOVE) for one bonus riddle, a step harder than the
# level's own questions on the same topics. Answered right, it's worth DRAGON_POINTS (times
# the level's multiplier) from the dragon's hoard; answered wrong, the explorer flees with
# nothing lost. Either way the quest stays won, and the explorer carries on as after any win.
# Each dragon's picture is its scene (in SCENES), cut from the dragons' picture sheet.

DRAGON_MOVE = "dragon"
DRAGON_POINTS = 30

DRAGON_LAIRS = {
    "forest": "On your way back through the Whispering Forest, a glint of gold catches your "
              "eye in a mossy hollow.",
    "cave": "On your way back out of the Serpent's Cave, a glint of gold catches your eye in "
            "a side cavern.",
    "castle": "On your way back through the castle ruins, a glint of gold catches your eye "
              "through a doorway: a forgotten treasury.",
}

DRAGONS = {
    ("easy", "cave"): {
        "scene": "dragon-emerald", "scales": "green as moss",
        "question": {
            "prompt": "What does this code print?",
            "code": (
                "gems = 0\n"
                "for n in range(1, 6):\n"
                "    if n % 2 == 1:\n"
                "        gems = gems + n\n"
                "print(gems)"
            ),
            "options": ["9", "15", "6", "5"],
            "answer": "9",
            "explain": "range(1, 6) gives 1 to 5, and n % 2 == 1 keeps only the odd ones: "
                       "1 + 3 + 5 = 9.",
        },
    },
    ("medium", "cave"): {
        "scene": "dragon-ember", "scales": "glowing like hot coals",
        "question": {
            "prompt": "What does this code print?",
            "code": (
                'hoard = {"gold": 3, "gems": 5, "crowns": 1}\n'
                "total = 0\n"
                "for item, count in hoard.items():\n"
                "    if count > 2:\n"
                "        total += count\n"
                "print(total)"
            ),
            "options": ["8", "9", "5", "3"],
            "answer": "8",
            "explain": ".items() gives each key with its value. Only gold (3) and gems (5) "
                       "are more than 2, so total is 8.",
        },
    },
    ("hard", "cave"): {
        "scene": "dragon-frost", "scales": "glittering with ice",
        "question": {
            "prompt": "What does this code print?",
            "code": (
                "def flatten(items):\n"
                "    result = []\n"
                "    for item in items:\n"
                "        if isinstance(item, list):\n"
                "            result += flatten(item)\n"
                "        else:\n"
                "            result.append(item)\n"
                "    return result\n"
                "\n"
                "print(flatten([1, [2, [3, 4]], 5]))"
            ),
            "options": ["[1, 2, 3, 4, 5]", "[1, [2, [3, 4]], 5]", "[1, 2, [3, 4], 5]", "RecursionError"],
            "answer": "[1, 2, 3, 4, 5]",
            "explain": "Each inner list is flattened by a recursive call, however deep it "
                       "goes, and its items are added to the result in order.",
        },
    },
    ("easy", "forest"): {
        "scene": "dragon-pearl", "scales": "white as moonlight",
        "question": {
            "prompt": "What does this code print?",
            "code": (
                'trees = ["oak", "elm", "ash"]\n'
                'trees.insert(1, "fir")\n'
                "print(trees[2])"
            ),
            "options": ["elm", "fir", "ash", "oak"],
            "answer": "elm",
            "explain": 'insert(1, "fir") puts fir at index 1 and moves the rest along: '
                       "['oak', 'fir', 'elm', 'ash'], so index 2 is elm.",
        },
    },
    ("medium", "forest"): {
        "scene": "dragon-amethyst", "scales": "a deep, shimmering purple",
        "question": {
            "prompt": "What does this code print?",
            "code": 'word = "amethyst"\nprint(word[2:7:2])',
            "options": ["ehs", "eth", "ehst", "mty"],
            "answer": "ehs",
            "explain": "[2:7:2] starts at index 2, stops before 7 and takes every second "
                       "letter: indexes 2, 4 and 6, which are e, h and s.",
        },
    },
    ("hard", "forest"): {
        "scene": "dragon-autumn", "scales": "the color of falling leaves",
        "question": {
            "prompt": "What does this code print?",
            "code": (
                "funcs = [lambda x, i=i: x * i for i in range(1, 4)]\n"
                "print([f(10) for f in funcs])"
            ),
            "options": ["[10, 20, 30]", "[30, 30, 30]", "[0, 10, 20]", "Error"],
            "answer": "[10, 20, 30]",
            "explain": "i=i saves the value of i as a default when each lambda is made, so "
                       "each one keeps its own i (1, 2, 3) instead of the last one.",
        },
    },
    ("easy", "castle"): {
        "scene": "dragon-gold", "scales": "as bright as the coins beneath it",
        "question": {
            "prompt": "What does this code print?",
            "code": 'gold = "3"\ncoins = int(gold) * 2 + len(gold)\nprint(coins)',
            "options": ["7", "6", "33", "Error"],
            "answer": "7",
            "explain": 'int("3") turns the string into the number 3, so 3 * 2 is 6. '
                       'len("3") is 1, the length of the string: 6 + 1 = 7.',
        },
    },
    ("medium", "castle"): {
        "scene": "dragon-silver", "scales": "gleaming like polished armor",
        "question": {
            "prompt": "What does this code print?",
            "code": (
                "n = 0\n"
                "while n < 5:\n"
                "    n += 2\n"
                "    if n == 4:\n"
                "        break\n"
                "else:\n"
                "    n = 100\n"
                "print(n)"
            ),
            "options": ["4", "100", "6", "5"],
            "answer": "4",
            "explain": "A loop's else block runs only if the loop ends without break. Here "
                       "break stops it at 4, so the else is skipped.",
        },
    },
    ("hard", "castle"): {
        "scene": "dragon-shadow", "scales": "as black as a moonless night",
        "question": {
            "prompt": "What does this code print?",
            "code": "gen = (n * n for n in range(4))\nprint(sum(gen), sum(gen))",
            "options": ["14 0", "14 14", "0 14", "Error"],
            "answer": "14 0",
            "explain": "A generator can only be used once: the first sum() uses up "
                       "0 + 1 + 4 + 9 = 14, leaving nothing for the second.",
        },
    },
}


# ------------------------------------------------------------------
# The final boss: Python (web edition, 2026-11-01)
# ------------------------------------------------------------------
# Only an explorer who completes every path on every level meets Python. It asks one of
# these nine, picked at random: the hardest questions in the game. Answer right and they
# become a Python Master, with PYTHON_POINTS (times the Hard multiplier) besides; answer
# wrong and all is lost: their score falls to zero, and they must start over.

PYTHON_MOVE = "python"
PYTHON_POINTS = 100
BOSS_MOVE, BOSS_POINTS = PYTHON_MOVE, PYTHON_POINTS  # (what the site calls them, for either game)

# The page's own words for this game. The C# and VB.NET games have their own, by the same keys.
TEXTS = {
    "title": "The Lost Treasure of Pythonia",
    "language": "Python",
    "intro": [
        "Centuries ago, the ancient coders of Pythonia hid their greatest treasure, the Golden "
        "Interpreter, deep within this wild land. Its guardians still test every traveler with riddles "
        "written in the language of the serpent: Python.",
        "Answer wisely and choose your path carefully. Every wrong answer costs you a life, and some "
        "choices lead to certain doom...",
    ],
    "found": "Found the treasure",
    "master": "Python Master",
    "lost_to_boss": "Lost to Python",
    "hall_note": "Walk every path on every level to face Python.",
    "boss_offer_title": "The final challenge: Python",
    "boss_offer": "You have walked every path on every level, and Python, the great serpent of code, is "
                  "waiting. Answer its question, the hardest in all of Pythonia, to earn the title of "
                  "Python Master and {points} points.",
    "boss_warning": "Beware: if you fail, all is lost. Your score falls to zero and you must start over.",
    "boss_button": "Face Python",
    "boss_confirm": "Face Python? If you fail, all is lost: your score falls to zero and you must start over.",
    "boss_won": "You have defeated Python. You are a Python Master!",
    "boss_lost": "Python has defeated you. All is lost: your score is gone, and you must start over.",
    "conquered_every_path": "Every path on every level: you've explored all of Pythonia!",
    "conquered_every_level": "Easy, Medium and Hard: you've conquered every level of Pythonia!",
}

PYTHON_QUESTIONS = [
    {
        "prompt": "What does this code print?",
        "code": (
            "class A:\n"
            "    def who(self):\n"
            '        return "A"\n'
            "\n"
            "class B(A):\n"
            "    def who(self):\n"
            '        return "B" + super().who()\n'
            "\n"
            "class C(A):\n"
            "    def who(self):\n"
            '        return "C" + super().who()\n'
            "\n"
            "class D(B, C):\n"
            "    def who(self):\n"
            '        return "D" + super().who()\n'
            "\n"
            "print(D().who())"
        ),
        "options": ["DBCA", "DBA", "DCBA", "DBAC"],
        "answer": "DBCA",
        "explain": "super() follows the method resolution order, D -> B -> C -> A, not just "
                   "each class's own parent. So B's super() is C, not A.",
    },
    {
        "prompt": "What does this code print?",
        "code": (
            "def echo():\n"
            "    total = 0\n"
            "    while True:\n"
            "        value = yield total\n"
            "        total += value\n"
            "\n"
            "gen = echo()\n"
            "next(gen)\n"
            "gen.send(5)\n"
            "print(gen.send(10))"
        ),
        "options": ["15", "10", "5", "None"],
        "answer": "15",
        "explain": "next() runs to the first yield. Each send() resumes it with value set "
                   "to what was sent, adds it to total and yields the new total: 5, then 15.",
    },
    {
        "prompt": "What does this code print?",
        "code": (
            "class Vault:\n"
            "    gems = []\n"
            "    count = 0\n"
            "\n"
            "    def add(self, gem):\n"
            "        self.gems.append(gem)\n"
            "        self.count += 1\n"
            "\n"
            "a, b = Vault(), Vault()\n"
            'a.add("ruby")\n'
            'b.add("opal")\n'
            "print(len(a.gems), a.count, Vault.count)"
        ),
        "options": ["2 1 0", "1 1 0", "2 2 2", "1 1 2"],
        "answer": "2 1 0",
        "explain": "append() changes the one gems list the class shares, but self.count += 1 "
                   "makes each object its own count, leaving Vault.count at 0.",
    },
    {
        "prompt": "What does this code print?",
        "code": (
            "def double(f):\n"
            "    return lambda x: f(x) * 2\n"
            "\n"
            "def inc(f):\n"
            "    return lambda x: f(x) + 1\n"
            "\n"
            "@double\n"
            "@inc\n"
            "def same(x):\n"
            "    return x\n"
            "\n"
            "print(same(5))"
        ),
        "options": ["12", "11", "10", "7"],
        "answer": "12",
        "explain": "Decorators apply from the bottom up: same = double(inc(same)). So 5 + 1 "
                   "happens first, then * 2.",
    },
    {
        "prompt": "What does this code print?",
        "code": (
            "class Gem:\n"
            "    def __init__(self, name):\n"
            "        self.name = name\n"
            "\n"
            "    def __eq__(self, other):\n"
            "        return self.name == other.name\n"
            "\n"
            'print(len({Gem("ruby"), Gem("ruby")}))'
        ),
        "options": ["TypeError", "1", "2", "0"],
        "answer": "TypeError",
        "explain": "Defining __eq__ without __hash__ makes a class unhashable, so its "
                   "objects can't go in a set: TypeError: unhashable type: 'Gem'.",
    },
    {
        "prompt": "What does this code print?",
        "code": (
            "x = 10\n"
            "gen = (x * i for i in range(3))\n"
            "x = 100\n"
            "print(list(gen))"
        ),
        "options": ["[0, 100, 200]", "[0, 10, 20]", "[0, 100, 20]", "Error"],
        "answer": "[0, 100, 200]",
        "explain": "A generator runs only when it's used. By the time list() asks for its "
                   "values, x is 100.",
    },
    {
        "prompt": "What does this code print?",
        "code": (
            'a = {"x": 1, "y": 2}\n'
            'b = {"y": 3, "z": 4}\n'
            'merged = {**a, **b, "x": 5}\n'
            "print(list(merged.items()))"
        ),
        "options": [
            "[('x', 5), ('y', 3), ('z', 4)]",
            "[('y', 3), ('z', 4), ('x', 5)]",
            "[('x', 1), ('y', 3), ('z', 4)]",
            "[('x', 5), ('y', 2), ('z', 4)]",
        ],
        "answer": "[('x', 5), ('y', 3), ('z', 4)]",
        "explain": "Later values win, but a key keeps the place where it first appeared. "
                   "So x stays first even though its value 5 came last.",
    },
    {
        "prompt": "What does this code print?",
        "code": (
            "def ways(n, memo={}):\n"
            "    if n in memo:\n"
            "        return memo[n]\n"
            "    if n <= 1:\n"
            "        return 1\n"
            "    memo[n] = ways(n - 1) + ways(n - 2)\n"
            "    return memo[n]\n"
            "\n"
            "print(ways(10), len(ways.__defaults__[0]))"
        ),
        "options": ["89 9", "89 0", "55 9", "89 11"],
        "answer": "89 9",
        "explain": "ways(n) = ways(n - 1) + ways(n - 2) from 1, 1: 2, 3, 5, ..., 89. The "
                   "default memo is one shared dict that keeps n = 2 to 10: 9 entries.",
    },
    {
        "prompt": "What does this code print?",
        "code": "it = iter(range(6))\nprint(list(zip(it, it)))",
        "options": [
            "[(0, 1), (2, 3), (4, 5)]",
            "[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]",
            "[(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]",
            "[]",
        ],
        "answer": "[(0, 1), (2, 3), (4, 5)]",
        "explain": "Both arguments are the same iterator, so each pair takes the next two "
                   "values from it.",
    },
]


# ------------------------------------------------------------------
# Scenes: each has a banner, a picture (static/img/adventure/, made from the photoreal
# originals by tools/make-adventure-images.py) and a description of it
# ------------------------------------------------------------------

SCENES = {
    "start": ("The Lost Treasure of Pythonia", "title.webp",
              "A moonlit jungle valley wrapped in mist, a golden temple glowing on a far hilltop"),
    "forest": ("The Whispering Forest", "forest.webp",
               "Sunbeams falling through towering trees onto a stream, ferns and one giant mossy tree"),
    "waterfall": ("The Roaring Waterfall", "waterfall.webp",
                  "A roaring waterfall crashing into a green pool between mossy cliffs, a fallen log high across the gorge"),
    "tree": ("The Top of the Giant Tree", "tree.webp",
             "A great owl on a mossy branch above a sea of mist at sunrise, a golden temple glinting in the distance"),
    "cave": ("The Serpent's Cave", "cave.webp",
             "A dark cave mouth framed by carved stone serpents, a torch burning beside it"),
    "dark": ("The Dark Tunnel", "pit.webp",
             "A deep pit in the floor of a rocky tunnel, the cave entrance glowing far behind"),
    "glyph": ("The Glyph Door", "glyph-door.webp",
              "A massive stone door glowing with lines of Python code, fire bowls burning on either side"),
    # The castle path's scenes are cut from one picture sheet (see tools/make-adventure-images.py).
    "castle": ("The Ancient Castle Ruins", "castle.webp",
               "A ruined castle on a misty hilltop under a full moon, torches lighting the stone path that winds up to it"),
    "gate": ("The Castle Gate", "castle-gate.webp",
             "A great arched gate with a raised iron portcullis, griffin banners and blazing torches on ivy-covered walls"),
    "hall": ("The Great Hall", "great-hall.webp",
             "A ruined great hall of broken gothic arches, torches flickering beside an empty throne at the top of worn steps"),
    "ramparts": ("The Castle Ramparts", "ramparts.webp",
                 "Torch-lit battlements under a full moon, stone towers rising above a misty valley"),
    "gallery": ("The Moonlit Gallery", "gallery.webp",
                "A stone gallery high in a tower, ivy twisting around its pillars, the full moon over a misty valley beyond the balustrade"),
    "temple": ("The Temple of the Golden Interpreter", "temple.webp",
               "A torch-lit temple hall leading to a golden vault door guarded by two stone serpents, a jeweled chest by the path"),
    "victory": ("The Treasure Is Yours!", "treasure.webp",
                "The Golden Interpreter: a glowing golden orb wrapped by a serpent, on a stone pedestal among gold and gems"),
    # The bonus dragons (see DRAGONS), cut from one picture sheet (see tools/make-adventure-images.py).
    "dragon-emerald": ("The Emerald Dragon", "dragon-emerald.webp",
                       "A green dragon asleep in a cave, curled around an open treasure chest full of gold and emeralds"),
    "dragon-ember": ("The Ember Dragon", "dragon-ember.webp",
                     "A red dragon asleep in a fiery cave around a treasure chest of gold and rubies, a sword and a crown beside it"),
    "dragon-frost": ("The Frost Dragon", "dragon-frost.webp",
                     "A blue dragon asleep in an ice cave, its treasure chest full of gold and glowing sapphires"),
    "dragon-pearl": ("The Pearl Dragon", "dragon-pearl.webp",
                     "A white dragon asleep in a sunlit forest beside a treasure chest of gold, diamonds and a silver crown"),
    "dragon-amethyst": ("The Amethyst Dragon", "dragon-amethyst.webp",
                        "A purple dragon coiled around a treasure chest of gold and glowing amethysts in a violet forest"),
    "dragon-autumn": ("The Autumn Dragon", "dragon-autumn.webp",
                      "A copper dragon asleep among autumn leaves beside a treasure chest of gold and a golden goblet"),
    "dragon-gold": ("The Golden Dragon", "dragon-gold.webp",
                    "A golden dragon asleep on a heap of gold coins beside a treasure chest in a torch-lit castle hall"),
    "dragon-silver": ("The Silver Dragon", "dragon-silver.webp",
                      "A silver dragon asleep in a castle hall beside a chest of silver and diamonds, a knight's helmet and a sword"),
    "dragon-shadow": ("The Shadow Dragon", "dragon-shadow.webp",
                      "A black dragon asleep in a castle hall around a chest of gold and rubies, a jeweled crown at its feet"),
    # The final boss (see PYTHON_QUESTIONS), from its own picture (see tools/make-adventure-images.py).
    "python": ("Python, the Great Serpent", "python.webp",
               "A giant golden python with a glowing blue eye coiled through a candlelit library of "
               "ancient Python books, scrolls of code and an open spellbook"),
    "game_over": ("Game Over", "game-over.webp",
                  "A burnt-out torch and a lost compass on rocky ground under a blood-red sky"),
}

LETTERS = ["a", "b", "c", "d"]


# ------------------------------------------------------------------
# Prompts: what the game waits for (instead of input())
# ------------------------------------------------------------------

class Choice:
    """A menu: the explorer picks an option (moves "1", "2", ...)."""
    kind = "choice"

    def __init__(self, options):
        self.options = options
        self.moves = [str(number) for number in range(1, len(options) + 1)]

    def accepts(self, move):
        return move in self.moves


class Question:
    """A Python challenge: the explorer picks an answer (moves "a" to "d")."""
    kind = "question"

    def __init__(self, challenger, question, options):
        self.challenger = challenger
        self.prompt = question["prompt"]
        self.code = question.get("code")
        self.options = list(zip(LETTERS, options))
        self.moves = LETTERS[:len(options)]

    def accepts(self, move):
        return move in self.moves


class Quest:
    """One explorer's quest: their progress, the scene they're in, what happened since
    their last move, and what the game is waiting for now."""

    def __init__(self, name, difficulty, seed, carried=0, only_path=None, skip_questions=(), version=GAME_VERSION,
                 final=False):
        self.rng = random.Random(seed)  # with the same seed, the same shuffles every replay
        self.final = final          # it completes every path on every level: after its win, Python awaits
        self.python = None          # the final boss's question: "won" or "lost" once answered
        self.version = version      # the game version it started on: which questions it draws from
        self.player = create_player(name, difficulty, carried)
        self.carried = carried      # the score brought along from the quest won before this one
        self.only_path = only_path  # "forest", "cave" or "castle" when sent down a path not taken yet
        self.skip_questions = set(skip_questions)  # numbers of questions the level's earlier paths asked
        self.asked = []             # numbers (in QUESTIONS[difficulty]) of the questions asked, in order
        self.path = None            # the path it went down, once chosen
        self.dragon = None          # the bonus dragon's riddle after a win: "won" or "lost" once answered
        self.scene = "start"
        self.log = []        # (kind, text) pairs: story, points, relic, life, info, correct, wrong, why
        self.prompt = None   # a Choice or a Question, or None once the quest (or the dragon) is over
        self.result = None   # "win" or "lose" once the quest is over

    def dragon_awaits(self):
        """After a win, the dragon of this path and level (from DRAGONS), until it's woken
        (or Python has been faced, which ends everything)."""
        if self.result == "win" and self.prompt is None and self.dragon is None and self.python is None:
            return DRAGONS.get((self.player["difficulty"], self.path))
        return None

    def python_awaits(self):
        """After the win that completes every path on every level: Python, until faced."""
        return self.final and self.result == "win" and self.prompt is None and self.python is None

    # (What the site calls them, for either game.)
    boss_awaits = python_awaits

    @property
    def boss(self):
        return self.python

    def banner(self, scene):
        self.scene = scene

    def narrate(self, text):
        self.log.append(("story", text))

    def note(self, kind, text):
        self.log.append((kind, text))


def replay(name, difficulty, seed, moves, carried=0, only_path=None, skip_questions=(), version=GAME_VERSION,
           final=False):
    """Play a quest from the start with the moves made so far, and return it as it stands
    now. Its log holds what happened after the last move. A quest carried on from a win
    starts with that score (`carried`); one sent down a path not taken yet on its level
    (`only_path`) offers only that path at the start, and doesn't ask again the questions
    the level's earlier paths asked (`skip_questions`: their numbers, from those quests'
    `asked`). `version` is the game version the quest started on. After a win, the move
    DRAGON_MOVE wakes the bonus dragon, and the next move answers its riddle. A `final`
    quest (the one that completes every path on every level) can then face Python, the final
    boss: the move PYTHON_MOVE, then the answer."""
    quest = Quest(name, difficulty, seed, carried, only_path, skip_questions, version, final)
    game = start_game(quest)
    quest.prompt = next(game)
    for move in moves:
        battle = (dragon_battle if move == DRAGON_MOVE and quest.dragon_awaits()
                  else python_battle if move == PYTHON_MOVE and quest.python_awaits() else None)
        if battle:
            game = battle(quest)
            quest.log = []
            quest.prompt = next(game)
            continue
        if quest.prompt is None or not quest.prompt.accepts(move):
            break
        quest.log = []
        try:
            quest.prompt = game.send(move)
        except StopIteration as end:
            quest.result, quest.prompt = end.value, None
    return quest


# ------------------------------------------------------------------
# Player helpers
# ------------------------------------------------------------------

def create_player(name, difficulty, score=0):
    """Build the dictionary that tracks the player's progress. Lives and relics start
    afresh on every level; only the score is carried up."""
    return {
        "name": name,
        "difficulty": difficulty,
        "lives": DIFFICULTY_SETTINGS[difficulty]["lives"],
        "score": score,
        "inventory": [],
        "questions": [],  # shuffled deck, filled by draw_question()
    }


def add_points(quest, base_points, reason):
    """Add points scaled by the difficulty multiplier and announce them."""
    player = quest.player
    points = base_points * DIFFICULTY_SETTINGS[player["difficulty"]]["multiplier"]
    player["score"] += points
    quest.note("points", f"+{points} points ({reason})")


def lose_life(quest):
    """Take away one life. Returns True if the player still has lives left."""
    player = quest.player
    player["lives"] -= 1
    if player["lives"] > 0:
        quest.note("life", f"You lose a life! Lives remaining: {player['lives']}")
    else:
        quest.note("life", "You have no lives left!")
    return player["lives"] > 0


def collect_relic(quest, relic):
    """Add a relic to the player's inventory. Relics are worth points if you win."""
    quest.player["inventory"].append(relic)
    quest.note("relic", f"You found a relic: {relic}!")


# ------------------------------------------------------------------
# Python challenges
# ------------------------------------------------------------------

def draw_question(quest):
    """Take the next question from the player's deck, reshuffling when it runs out. The deck
    holds question numbers (places in QUESTIONS; the quest's game version says how many),
    and every question drawn is noted in quest.asked."""
    player = quest.player
    if not player["questions"]:
        every = range(QUESTION_COUNTS[quest.version])
        # (Web edition: a path not taken yet starts with a deck of the questions the level's
        # earlier paths didn't ask. A quest asks at most 6, so a level's 20 questions are
        # enough for all three paths.)
        unasked = [number for number in every if number not in quest.skip_questions] if not quest.asked else []
        player["questions"] = unasked or list(every)
        quest.rng.shuffle(player["questions"])
    number = player["questions"].pop()
    quest.asked.append(number)
    return QUESTIONS[player["difficulty"]][number]


def ask_question(quest, challenger, question=None, points=CORRECT_ANSWER_POINTS, reason="correct answer"):
    """Ask one Python question: the next from the deck, or `question` (a dragon's). Returns
    True if the player answers correctly, and earns them `points`."""
    question = question or draw_question(quest)
    options = question["options"][:]
    quest.rng.shuffle(options)

    answer = yield Question(challenger, question, options)
    correct_letter = LETTERS[options.index(question["answer"])]
    if answer == correct_letter:
        quest.note("correct", "Correct!")
        add_points(quest, points, reason)
        is_correct = True
    else:
        quest.note("wrong", f"{correct_letter}) {question['answer']}")
        is_correct = False
    quest.note("why", question["explain"])
    return is_correct


def face_challenge(quest, challenger):
    """Ask questions until one is answered correctly. Each wrong answer costs a life.

    Returns True if the challenge is passed, or False if the player runs out of lives.
    """
    while True:
        if (yield from ask_question(quest, challenger)):
            return True
        if not lose_life(quest):
            return False
        quest.note("info", f"{challenger} gives you another chance...")


# ------------------------------------------------------------------
# Game start (the name and difficulty are chosen on the page first)
# ------------------------------------------------------------------

def start_game(quest):
    """Welcome the explorer and send them down their first path. Returns "win" or "lose"."""
    quest.banner("start")
    if quest.only_path:
        # (Web edition: a winner going back for a path they didn't take, score and all.)
        quest.narrate(f"Welcome back, {quest.player['name']}! You return to the edge of "
                      f"Pythonia with {quest.carried} points from your last quest, wondering "
                      "what waits down the way you didn't take. This time you turn toward "
                      f"{PATH_SIGHTS[quest.only_path]}"
                      f"{', where new riddles await' if quest.skip_questions else ''}.")
        yield Choice([PATHS[quest.only_path]])
        choice = str(list(PATHS).index(quest.only_path) + 1)
    else:
        if quest.carried:
            # (Web edition: a winner carrying their score up to the next level.)
            quest.narrate(f"Welcome back, {quest.player['name']}! You return to the edge of "
                          f"Pythonia with {quest.carried} points from your last quest. Word of "
                          "your success has reached the guardians, and their riddles will be "
                          "harder this time. Three paths lie before you once more: a dense, "
                          "whispering forest, a dark cave whose mouth seems to hiss softly in "
                          "the wind, and a torch-lit trail that climbs to the ruins of an "
                          "ancient castle.")
        else:
            quest.narrate(f"Welcome, {quest.player['name']}! You arrive at the edge of Pythonia "
                          "with nothing but a backpack and your wits. Three paths lie before you: "
                          "a dense, whispering forest, a dark cave whose mouth seems to hiss "
                          "softly in the wind, and a torch-lit trail that climbs to the ruins of "
                          "an ancient castle.")
        choice = yield Choice(list(PATHS.values()))
    quest.path = list(PATHS)[int(choice) - 1]
    if choice == "1":
        return (yield from forest_path(quest))
    if choice == "2":
        return (yield from cave_path(quest))
    return (yield from castle_path(quest))


# ------------------------------------------------------------------
# The forest
# ------------------------------------------------------------------

def forest_path(quest):
    """The forest: follow the river or climb the giant tree."""
    quest.banner("forest")
    quest.narrate("Towering trees close in around you and strange birds call from the "
                  "canopy. To your left, a river murmurs through the ferns. To your "
                  "right stands an ancient tree so tall its top disappears into the "
                  "mist. From up there, you could see for miles.")
    choice = yield Choice(["Follow the river", "Climb the giant tree"])
    if choice == "1":
        return (yield from river_route(quest))
    return (yield from tree_route(quest))


def river_route(quest):
    """The river leads to a waterfall and its guardian."""
    quest.banner("waterfall")
    quest.narrate("You follow the river until it plunges over a cliff in a roaring "
                  "waterfall. The water swirls, rises, and takes the shape of a "
                  "towering figure: the River Guardian. \"None may pass without "
                  "answering my riddle,\" it booms.")
    if not (yield from face_challenge(quest, "The River Guardian")):
        return game_over(quest, "The Guardian's patience runs dry. A great wave sweeps "
                                "you downstream, far away from the treasure.")

    quest.narrate("The Guardian bows and places a shimmering pearl in your hand.")
    collect_relic(quest, "River Pearl")
    quest.narrate("It points a watery finger at a dark gap hidden behind the "
                  "waterfall. Nearby, a fallen log covered in slick green moss "
                  "stretches across the gorge. It looks like a quicker way across.")
    choice = yield Choice(["Slip behind the waterfall, as the Guardian showed you",
                           "Cross the gorge on the mossy log"])
    if choice == "1":
        add_points(quest, WISE_CHOICE_POINTS, "wise choice")
        quest.narrate("Behind the curtain of water, a hidden tunnel leads you straight "
                      "to the steps of an ancient temple.")
        return (yield from temple_vault(quest))
    return game_over(quest, "Halfway across, your boot slips on the moss. You "
                            "tumble into the rapids and are carried far from the "
                            "treasure. Somewhere behind you, the Guardian sighs.")


def tree_route(quest):
    """The giant tree, where a wise owl guards the safe way to the temple."""
    quest.banner("tree")
    quest.narrate("You climb branch by branch until you break through the mist. Far to "
                  "the east, a golden temple roof glints above the jungle. A great grey "
                  "owl lands beside you and blinks. \"Hoo! Only those who think like a "
                  "programmer may learn the safe way down.\"")
    if not (yield from face_challenge(quest, "The Wise Owl")):
        return game_over(quest, "The owl ruffles its feathers and flies away. As you "
                                "reach after it, the branch beneath you snaps...")

    quest.narrate("\"Well reasoned!\" hoots the owl, and it plucks a feather for you.")
    collect_relic(quest, "Owl Feather")
    quest.narrate("\"Now listen closely. The swamp below is the shortest way to the "
                  "temple, but it swallows the careless. The vines are slow, but strong.\"")
    choice = yield Choice(["Swing along the vines toward the temple",
                           "Climb down and take the swamp shortcut"])
    if choice == "1":
        add_points(quest, WISE_CHOICE_POINTS, "wise choice")
        quest.narrate("Vine by vine, you swing through the canopy like a jungle "
                      "acrobat and land softly on the temple steps.")
        return (yield from temple_vault(quest))
    return game_over(quest, "Three steps into the swamp, the mud grabs your boots. "
                            "The harder you struggle, the deeper you sink. You "
                            "should have listened to the owl!")


# ------------------------------------------------------------------
# The cave
# ------------------------------------------------------------------

def cave_path(quest):
    """The cave: light a torch or proceed in the dark."""
    quest.banner("cave")
    quest.narrate("Cold air flows from the cave mouth, carrying a faint hissing sound. "
                  "Snake carvings coil around the entrance. Just inside, you find an "
                  "old torch and a flint. Lighting it would help you see, but the light "
                  "might also wake whatever is hissing in the dark...")
    choice = yield Choice(["Light the torch", "Proceed in the dark"])
    if choice == "1":
        add_points(quest, WISE_CHOICE_POINTS, "wise choice")
        quest.narrate("The torch flares to life. Good thing, too: the floor ahead is "
                      "riddled with deep pits! The hissing, you realize, is only wind "
                      "whistling through cracks in the rock.")
        return (yield from glyph_door(quest))
    return (yield from dark_tunnel(quest))


def dark_tunnel(quest):
    """Going on without light is a setback that costs a life, or ends the quest."""
    quest.banner("dark")
    quest.narrate("You creep forward in total darkness, one hand on the cold, damp "
                  "wall. Suddenly the ground vanishes beneath your feet and you "
                  "tumble into a pit!")
    if not lose_life(quest):
        return game_over(quest, "The pit is far too deep to climb out of without "
                                "light. Your quest ends here, in the dark.")

    # (The web edition pauses here, so the pit gets its moment on screen.)
    yield Choice(["Climb out of the pit"])
    quest.narrate("Bruised but alive, you claw your way out and crawl back to the "
                  "entrance. This time you light the torch. Lesson learned! In its glow "
                  "you can see the floor is riddled with pits.")
    return (yield from glyph_door(quest))


def glyph_door(quest):
    """Deep in the cave, a door sealed with a Python puzzle."""
    quest.banner("glyph")
    quest.narrate("You weave between the pits until the tunnel ends at a massive "
                  "stone door. Glowing glyphs crawl across its surface and rearrange "
                  "themselves into lines of Python code.")
    if not (yield from face_challenge(quest, "The Glyph Door")):
        return game_over(quest, "The glyphs flash red. With a deep rumble the tunnel "
                                "behind you seals shut, and your torch flickers out...")

    quest.narrate("The glyphs flash gold and the door grinds open. A small carved "
                  "tablet falls from the wall at your feet.")
    collect_relic(quest, "Glyph Tablet")
    quest.narrate("Beyond the door the tunnel splits in two. From the left drifts warm "
                  "air and a faint golden glow. The right tunnel is cold, its walls "
                  "marked with fresh, deep claw scratches, and something in there is "
                  "growling.")
    choice = yield Choice(["Take the left tunnel toward the golden glow",
                           "Take the right tunnel past the claw marks"])
    if choice == "1":
        add_points(quest, WISE_CHOICE_POINTS, "wise choice")
        quest.narrate("The golden glow grows brighter with every step until you emerge "
                      "at the heart of an ancient temple.")
        return (yield from temple_vault(quest))
    return game_over(quest, "The claw marks belong to a very large, very grumpy "
                            "cave bear who does not appreciate visitors. You flee "
                            "all the way back to the entrance, your quest in ruins.")


# ------------------------------------------------------------------
# The castle (web edition, 2026-11-01: a third way into Pythonia)
# ------------------------------------------------------------------

def castle_path(quest):
    """The castle ruins: the great gate or the ramparts."""
    quest.banner("castle")
    quest.narrate("A winding stone trail climbs out of the mist to the ruins of an ancient "
                  "castle. Torches still burn along the way, though no one has lived here "
                  "for a thousand years. The trail ends at the great gate. Beside it, a "
                  "crumbling stair climbs the outer wall toward the ramparts.")
    choice = yield Choice(["Follow the torches to the great gate",
                           "Climb the crumbling stair to the ramparts"])
    if choice == "1":
        return (yield from castle_gate(quest))
    return (yield from castle_ramparts(quest))


def castle_gate(quest):
    """The gate's ghostly knight, then the great hall and its two ways on."""
    quest.banner("gate")
    quest.narrate("Golden griffins glare down from tattered banners as you reach the gate. "
                  "The iron portcullis is raised, but as you step beneath it a ghostly "
                  "knight in rusted armor drifts out of the stone. \"Halt! Only a true "
                  "coder may enter the hall of the Python kings.\"")
    if not (yield from face_challenge(quest, "The Ghost Knight")):
        return game_over(quest, "The ghost knight raises its sword and the portcullis "
                                "crashes down. You are left outside in the dark, far "
                                "from the treasure.")

    quest.narrate("The knight lowers its sword and presses a cold silver ring into your palm.")
    collect_relic(quest, "Knight's Signet")
    quest.banner("hall")
    quest.narrate("Beyond the gate lies the great hall, its arches broken and open to the "
                  "sky. Torches flicker beside an empty throne. Behind it, a narrow passage "
                  "glows with a faint golden light. To one side, a grand staircase climbs "
                  "into the dark, its steps cracked and crumbling.")
    choice = yield Choice(["Take the glowing passage behind the throne",
                           "Climb the crumbling grand staircase"])
    if choice == "1":
        add_points(quest, WISE_CHOICE_POINTS, "wise choice")
        quest.narrate("The passage winds down beneath the castle and comes out on the "
                      "steps of an ancient temple.")
        return (yield from temple_vault(quest))
    return game_over(quest, "Halfway up, the staircase gives way beneath your feet. You "
                            "tumble down in a cloud of dust, and the castle keeps its "
                            "secrets.")


def castle_ramparts(quest):
    """The ramparts' stone gargoyle, then the moonlit gallery high in a tower."""
    quest.banner("ramparts")
    quest.narrate("You climb onto the battlements. The moon hangs over a sea of mist and "
                  "the wind howls between the towers. On the wall ahead crouches a stone "
                  "gargoyle. As you come near, its eyes crack open and glow. \"Answer me, "
                  "climber, or take the short way down.\"")
    if not (yield from face_challenge(quest, "The Stone Gargoyle")):
        return game_over(quest, "The gargoyle spreads its stone wings, and one great gust "
                                "sweeps you off the wall and into the mist.")

    quest.narrate("The gargoyle grinds out a laugh and drops a glittering stone from its claw.")
    collect_relic(quest, "Gargoyle's Eye")
    quest.banner("gallery")
    quest.narrate("The ramparts lead into a tall tower and up to a moonlit gallery. Far "
                  "below the balustrade, a golden temple roof glints through the mist. Ivy "
                  "as thick as rope hangs over the edge, and a spiral stair winds down "
                  "inside the tower.")
    choice = yield Choice(["Take the spiral stair down inside the tower",
                           "Climb down the ivy from the gallery"])
    if choice == "1":
        add_points(quest, WISE_CHOICE_POINTS, "wise choice")
        quest.narrate("Round and round you go, down and down, until a small door at the "
                      "foot of the tower opens beside the temple steps.")
        return (yield from temple_vault(quest))
    return game_over(quest, "The ivy is older than it looks. It tears loose with a snap, "
                            "and you drop into the mist far below.")


# ------------------------------------------------------------------
# The temple and the end of the quest
# ------------------------------------------------------------------

def temple_vault(quest):
    """The final challenge: an optional jeweled chest, then two serpent locks."""
    quest.banner("temple")
    quest.narrate("Torches burst into flame as you enter the temple's great hall. At "
                  "the far end stands the vault, its door sealed by two stone serpent "
                  "locks. Beside the path sits a small jeweled chest with a riddle "
                  "carved into its lid. Solving it would earn you a rare relic, but a "
                  "wrong answer will cost you a life.")
    choice = yield Choice(["Try to open the jeweled chest",
                           "Ignore the chest and head for the vault"])
    if choice == "1":
        if (yield from ask_question(quest, "The Jeweled Chest")):
            quest.narrate("Click! The lid springs open, revealing a ring set with a "
                          "blazing ruby.")
            collect_relic(quest, "Ruby Ring")
        else:
            if not lose_life(quest):
                return game_over(quest, "A dart coated in sleeping venom shoots from "
                                        "the lock. You doze off just steps away from "
                                        "the treasure...")
            quest.narrate("A tiny dart shoots from the lock and stings your hand. "
                          "The chest stays shut.")
    else:
        quest.narrate("You leave the chest alone. Sometimes the wisest move is not "
                      "to gamble.")

    quest.narrate("You approach the vault door. The eyes of the stone serpents begin "
                  "to glow.")
    for lock_number in range(1, 3):
        if not (yield from face_challenge(quest, f"Serpent Lock #{lock_number}")):
            return game_over(quest, "The serpent's eyes flash red and the vault seals "
                                    "itself forever. The treasure remains lost.")
        quest.note("info", f"Serpent Lock #{lock_number} slides open!")
    return victory(quest)


def victory(quest):
    """The vault opens! Award the end-of-quest bonuses."""
    player = quest.player
    quest.banner("victory")
    quest.narrate("The vault door swings open with a groan. Inside, resting on a "
                  "pedestal of black stone, sits the legendary Golden Interpreter, "
                  f"humming with ancient power. Congratulations, {player['name']}! "
                  "Your name will be carved among the great coders of Pythonia.")
    add_points(quest, TREASURE_POINTS, "found the treasure")
    for relic in player["inventory"]:
        add_points(quest, RELIC_POINTS, f"relic: {relic}")
    add_points(quest, LIFE_POINTS * player["lives"], f"lives remaining: {player['lives']}")
    return "win"


def dragon_battle(quest):
    """The bonus after a win: the riddle of the dragon of this path and level. Returns "win",
    since the quest stays won whatever the answer."""
    dragon = DRAGONS[(quest.player["difficulty"], quest.path)]
    name = SCENES[dragon["scene"]][0]
    quest.banner(dragon["scene"])
    quest.narrate(f"{DRAGON_LAIRS[quest.path]} There, coiled around an overflowing treasure "
                  f"chest, sleeps {name.replace('The', 'the', 1)}, its scales {dragon['scales']}. "
                  "As you creep closer, one great eye slides open. \"A riddle, little coder,\" "
                  "it rumbles. \"Answer well, and a share of my treasure is yours. Answer "
                  "badly, and run.\"")
    if (yield from ask_question(quest, name, dragon["question"], DRAGON_POINTS, "the dragon's treasure")):
        quest.dragon = "won"
        quest.narrate("The dragon rumbles a deep laugh and nudges its chest toward you with "
                      "its snout. You fill your pockets with treasure and slip away.")
    else:
        quest.dragon = "lost"
        quest.narrate("The dragon snorts a cloud of smoke, and you flee, empty-handed but "
                      "unharmed.")
    return "win"


def python_battle(quest):
    """The final boss, for a winner who has completed every path on every level: one of the
    nine ultimate questions, picked at random. Right: the title of Python Master and
    PYTHON_POINTS besides. Wrong: all is lost, the score falls to zero. Returns "win", since
    the quest that led here was won."""
    quest.banner("python")
    quest.narrate("You have walked every path in Pythonia. As you leave the temple for the "
                  "last time, its floor slides open onto a stair that winds down into a "
                  "library older than the jungle itself. Candles flicker over towers of "
                  "ancient books and scrolls of code, and between them something vast is "
                  "moving. Python, the great serpent of code, uncoils from the shadows, one "
                  "blue eye glowing. \"Every path, every level,\" it hisses. \"One question "
                  "remains. Answer it, and you are a Python Master. Fail, and you lose "
                  "everything.\"")
    question = quest.rng.choice(PYTHON_QUESTIONS)
    if (yield from ask_question(quest, "Python", question, PYTHON_POINTS, "Python Master")):
        quest.python = "won"
        quest.narrate("Python lowers its great head until its eye is level with yours, and "
                      "bows. \"Well answered, Master.\" From this day on, the coders of "
                      "Pythonia will know you by your new title.")
        quest.note("relic", "You are a Python Master!")
    else:
        quest.python = "lost"
        quest.player["score"] = 0
        quest.narrate("Python's eye flashes. With one sweep of its tail, every coin, relic "
                      "and point you carried is gone, and you wake at the edge of Pythonia "
                      "with nothing but a backpack and your wits.")
        quest.note("life", "All is lost! Your score falls to 0.")
    return "win"


def game_over(quest, message):
    """End the quest with a failure message."""
    quest.narrate(message)
    quest.banner("game_over")
    return "lose"
