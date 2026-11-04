"""
The Lost Package of Oraclia
---------------------------
The PL/SQL adventure: a copy of the Python game (pythonia.py), the same story in the same
places, played the same way, but with its own words and every riddle about PL/SQL, Oracle's
language of blocks (Oracle 19c, with DBMS_OUTPUT switched on).

Like pythonia.py:
- Wherever a console game would wait for input(), these functions *yield* a prompt (a
  Choice or a Question) and the page's buttons send the explorer's answer back in.
- A quest is saved as its random seed plus the moves made so far, and replay() plays it
  again from the start with those moves for every page.
- A winner can carry their score on: to the next level (next_level()), or down a path not
  taken yet (paths_left()), without the questions the level's earlier paths asked.
- After a win, the explorer may wake that path and level's dragon (DRAGONS,
  dragon_battle()) for one bonus riddle.
- An explorer who completes every path on every level may face the Mutating Table, the
  final boss (boss_battle()): one of the nine hardest questions (BOSS_QUESTIONS), for the
  title of PL/SQL Master, or the loss of their whole score.

tools/check-sql-questions.py runs every snippet on an Oracle database to check its answer.
"""

import random
import re

# Change GAME_VERSION when the questions change. A quest keeps the version it started on and
# is always replayed with that version's questions: the first QUESTION_COUNTS[version] of each
# level's list (new questions only ever go on the end).
GAME_VERSION = 1
QUESTION_COUNTS = {1: 20}


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
# Game settings (as in pythonia.py)
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
        "topics": "blocks, variables, NULL and '', ||, IF/ELSIF, loops, SELECT INTO",
    },
    "medium": {
        "lives": 2,
        "multiplier": 2,
        "topics": "loop rules, labels, cursors, CASE, subprograms, exceptions, collections",
    },
    "hard": {
        "lives": 1,
        "multiplier": 3,
        "topics": "NULL logic, exception corners, cursor states, bulk binds, Oracle quirks",
    },
}


def next_level(difficulty):
    """The level a winner can go on to (easy -> medium -> hard), or None after the hardest."""
    levels = list(DIFFICULTY_SETTINGS)
    position = levels.index(difficulty) + 1
    return levels[position] if position < len(levels) else None


# The three ways in, in the order the first choice offers them, and what's said about each one
# when a winner goes back for a path they didn't take. (The keys are the Python game's, since
# the pictures are shared.)
PATHS = {
    "forest": "Explore the Forest of Nested Blocks",
    "cave": "Enter the Caverns of DUAL",
    "castle": "Climb to the Ruins of Castle Ada",
}
PATH_NAMES = {
    "forest": "the Forest of Nested Blocks",
    "cave": "the Caverns of DUAL",
    "castle": "the Ruins of Castle Ada",
}
PATH_SIGHTS = {
    "forest": "the Forest of Nested Blocks, where every tree grows inside another",
    "cave": "the Caverns of DUAL, where every echo comes back exactly once",
    "castle": "the torch-lit trail that climbs to the Ruins of Castle Ada",
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
# PL/SQL challenges for each difficulty level
# ------------------------------------------------------------------
# Every question has a prompt, a list of options, the correct answer
# (which must match one of the options exactly) and a short explanation.
# Questions about a snippet of code also include the "code" to show.
# "setup", never shown, makes the tables a snippet's comment shows, for
# tools/check-sql-questions.py, which runs every snippet to check its answer.
# An answer for several rows lists them in order: a row's values joined by
# spaces, the rows by commas.

QUESTIONS = {
    "easy": [
        {
            "prompt": "What does this print?",
            "code": (
                "BEGIN\n"
                "  DBMS_OUTPUT.PUT_LINE('Dragon' || NULL || 'fly');\n"
                "END;"
            ),
            "options": ["Dragonfly", "(an empty line)", "Dragon fly", "DragonNULLfly"],
            "answer": "Dragonfly",
            "explain": "In Oracle, || simply skips a NULL, so 'Dragon' || NULL is just 'Dragon'. (In "
                       "standard SQL the whole thing would be NULL.)",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  clue VARCHAR2(10) := '';\n"
                "BEGIN\n"
                "  IF clue IS NULL THEN\n"
                "    DBMS_OUTPUT.PUT_LINE('It is NULL');\n"
                "  ELSE\n"
                "    DBMS_OUTPUT.PUT_LINE('It is empty');\n"
                "  END IF;\n"
                "END;"
            ),
            "options": ["It is NULL", "It is empty", "(an empty line)", "Error"],
            "answer": "It is NULL",
            "explain": "Oracle treats the empty string '' as NULL, so clue IS NULL is true.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  n NUMBER := 0;\n"
                "BEGIN\n"
                "  FOR i IN REVERSE 1..3 LOOP\n"
                "    n := n * 10 + i;\n"
                "  END LOOP;\n"
                "  DBMS_OUTPUT.PUT_LINE(n);\n"
                "END;"
            ),
            "options": ["321", "123", "0", "6"],
            "answer": "321",
            "explain": "REVERSE runs the loop from the top down, 3, 2, 1, even though the range is still "
                       "written low..high.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  gold NUMBER;\n"
                "BEGIN\n"
                "  gold := gold + 10;\n"
                "  IF gold IS NULL THEN\n"
                "    DBMS_OUTPUT.PUT_LINE('No gold');\n"
                "  ELSE\n"
                "    DBMS_OUTPUT.PUT_LINE(gold);\n"
                "  END IF;\n"
                "END;"
            ),
            "options": ["No gold", "10", "0", "Error"],
            "answer": "No gold",
            "explain": "A variable declared without a value starts as NULL, not 0, and NULL + 10 is still "
                       "NULL.",
        },
        {
            "prompt": "Inside a PL/SQL block, how do you store 5 in the variable gold?",
            "options": ["gold := 5;", "gold = 5;", "SET gold = 5;", "LET gold = 5;"],
            "answer": "gold := 5;",
            "explain": "PL/SQL assigns with := (it comes from Ada). A plain = only compares two values.",
        },
        {
            "prompt": "Which keyword adds another condition to a PL/SQL IF statement?",
            "options": ["ELSIF", "ELSEIF", "ELIF", "ELSWHEN"],
            "answer": "ELSIF",
            "explain": "It's spelled ELSIF, with no second E: IF ... THEN ... ELSIF ... THEN ... ELSE ... "
                       "END IF;",
        },
        {
            "prompt": "Which of these is the smallest valid PL/SQL block?",
            "options": ["BEGIN NULL; END;", "BEGIN END;", "BEGIN; END;", "DECLARE BEGIN END;"],
            "answer": "BEGIN NULL; END;",
            "explain": "A block needs at least one statement between BEGIN and END. NULL; is the statement "
                       "that does nothing, made for exactly this.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "-- knights\n"
                "--  id | name\n"
                "--  1  | Arthur\n"
                "--  2  | Lancelot\n"
                "DECLARE\n"
                "  who VARCHAR2(20);\n"
                "BEGIN\n"
                "  SELECT name INTO who FROM knights WHERE id = 3;\n"
                "  DBMS_OUTPUT.PUT_LINE(who);\n"
                "EXCEPTION\n"
                "  WHEN NO_DATA_FOUND THEN\n"
                "    DBMS_OUTPUT.PUT_LINE('No such knight');\n"
                "END;"
            ),
            "setup": (
                "CREATE TABLE knights (id NUMBER, name VARCHAR2(20));\n"
                "INSERT INTO knights VALUES (1, 'Arthur');\n"
                "INSERT INTO knights VALUES (2, 'Lancelot');\n"
                "COMMIT;"
            ),
            "options": ["No such knight", "(an empty line)", "NULL", "Nothing is printed"],
            "answer": "No such knight",
            "explain": "SELECT INTO must find exactly one row. Finding none raises NO_DATA_FOUND, so the "
                       "handler runs instead.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "BEGIN\n"
                "  IF 'Ruby' = 'RUBY' THEN\n"
                "    DBMS_OUTPUT.PUT_LINE('Same');\n"
                "  ELSE\n"
                "    DBMS_OUTPUT.PUT_LINE('Different');\n"
                "  END IF;\n"
                "END;"
            ),
            "options": ["Different", "Same", "Error", "(an empty line)"],
            "answer": "Different",
            "explain": "Oracle compares text case-sensitively by default (binary comparison), so 'Ruby' "
                       "and 'RUBY' are not equal.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  Gold NUMBER := 7;\n"
                "BEGIN\n"
                "  DBMS_OUTPUT.PUT_LINE(GOLD + gold);\n"
                "END;"
            ),
            "options": ["14", "7", "77", "Error: GOLD is not declared"],
            "answer": "14",
            "explain": "PL/SQL names aren't case-sensitive: Gold, GOLD and gold are the same variable. "
                       "Only text inside quotes cares about case.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "BEGIN\n"
                "  DBMS_OUTPUT.PUT_LINE(2 ** 3);\n"
                "END;"
            ),
            "options": ["8", "6", "9", "Error"],
            "answer": "8",
            "explain": "** is PL/SQL's power operator, so 2 ** 3 is 2 cubed. (Oracle SQL has no **; there "
                       "you'd write POWER(2, 3).)",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "BEGIN\n"
                "  DBMS_OUTPUT.PUT_LINE(7 / 2);\n"
                "END;"
            ),
            "options": ["3.5", "3", "4", "3.50"],
            "answer": "3.5",
            "explain": "In PL/SQL, / is true division and keeps the fraction, even between whole numbers: "
                       "7 / 2 is 3.5.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "BEGIN\n"
                "  DBMS_OUTPUT.PUT_LINE(q'[The knight's sword]');\n"
                "END;"
            ),
            "options": ["The knight's sword", "q'[The knight's sword]'", "[The knight's sword]", "Error"],
            "answer": "The knight's sword",
            "explain": "q'[...]' is Oracle's alternative quoting: whatever is between the brackets is the "
                       "string, so the apostrophe needs no doubling.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  steps NUMBER := 0;\n"
                "BEGIN\n"
                "  LOOP\n"
                "    steps := steps + 3;\n"
                "    EXIT WHEN steps > 10;\n"
                "  END LOOP;\n"
                "  DBMS_OUTPUT.PUT_LINE(steps);\n"
                "END;"
            ),
            "options": ["12", "9", "10", "15"],
            "answer": "12",
            "explain": "A basic LOOP runs until EXIT WHEN is true. steps goes 3, 6, 9, 12, and 12 is the "
                       "first value over 10.",
        },
        {
            "prompt": "In a DECLARE section, what does  v_name knights.name%TYPE;  declare?",
            "options": [
                "A variable of the same type as knights.name",
                "A variable holding the first knights.name",
                "A record for a whole knights row",
                "A cursor over knights.name",
            ],
            "answer": "A variable of the same type as knights.name",
            "explain": "%TYPE borrows the data type of a column (or of another variable), so the code "
                       "follows the column if it changes. A whole row is %ROWTYPE.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  gem VARCHAR2(3);\n"
                "BEGIN\n"
                "  gem := 'Dragon';\n"
                "  DBMS_OUTPUT.PUT_LINE(gem);\n"
                "END;"
            ),
            "options": ["Error: character string buffer too small", "Dra", "Dragon", "(an empty line)"],
            "answer": "Error: character string buffer too small",
            "explain": "PL/SQL never quietly cuts a string down to fit. Putting 6 characters into a "
                       "VARCHAR2(3) raises VALUE_ERROR (ORA-06502).",
            "expect_error": True,
        },
        {
            "prompt": "What does this print?",
            "code": (
                "BEGIN\n"
                "  DBMS_OUTPUT.PUT('Sw');\n"
                "  DBMS_OUTPUT.PUT('or');\n"
                "  DBMS_OUTPUT.PUT_LINE('d');\n"
                "END;"
            ),
            "options": ["Sword", "Sw or d", "d", "Sw"],
            "answer": "Sword",
            "explain": "PUT adds text to the current line without ending it. PUT_LINE adds its text and "
                       "then ends the line.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "-- gems\n"
                "--  name | power\n"
                "--  Ruby | 5\n"
                "--  Opal | 2\n"
                "--  Jade | 8\n"
                "BEGIN\n"
                "  UPDATE gems SET power = power + 1 WHERE power > 3;\n"
                "  DBMS_OUTPUT.PUT_LINE(SQL%ROWCOUNT);\n"
                "END;"
            ),
            "setup": (
                "CREATE TABLE gems (name VARCHAR2(10), power NUMBER);\n"
                "INSERT INTO gems VALUES ('Ruby', 5);\n"
                "INSERT INTO gems VALUES ('Opal', 2);\n"
                "INSERT INTO gems VALUES ('Jade', 8);\n"
                "COMMIT;"
            ),
            "options": ["2", "3", "1", "TRUE"],
            "answer": "2",
            "explain": "SQL%ROWCOUNT tells you how many rows the latest SQL statement touched: Ruby and "
                       "Jade.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  relic CHAR(5) := 'Orb';\n"
                "BEGIN\n"
                "  DBMS_OUTPUT.PUT_LINE(LENGTH(relic));\n"
                "END;"
            ),
            "options": ["5", "3", "4", "Error"],
            "answer": "5",
            "explain": "CHAR is fixed-length: 'Orb' is padded with blanks to 5 characters, and LENGTH "
                       "counts the blanks too.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  lives CONSTANT NUMBER := 3;\n"
                "BEGIN\n"
                "  lives := lives + 1;\n"
                "  DBMS_OUTPUT.PUT_LINE(lives);\n"
                "END;"
            ),
            "options": ["Error: lives can't be assigned to", "4", "3", "(an empty line)"],
            "answer": "Error: lives can't be assigned to",
            "explain": "A CONSTANT gets its value once, when it's declared. Assigning to it doesn't even "
                       "compile (PLS-00363).",
            "expect_error": True,
        },
    ],
    "medium": [
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  i NUMBER := 10;\n"
                "BEGIN\n"
                "  FOR i IN 1..3 LOOP\n"
                "    NULL;\n"
                "  END LOOP;\n"
                "  DBMS_OUTPUT.PUT_LINE(i);\n"
                "END;"
            ),
            "options": ["10", "3", "4", "Error"],
            "answer": "10",
            "explain": "A FOR loop declares its own index, which exists only inside the loop and hides the "
                       "outer i. The outer i is never touched.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  n NUMBER := 3;\n"
                "  turns NUMBER := 0;\n"
                "BEGIN\n"
                "  FOR i IN 1..n LOOP\n"
                "    n := 10;\n"
                "    turns := turns + 1;\n"
                "  END LOOP;\n"
                "  DBMS_OUTPUT.PUT_LINE(turns);\n"
                "END;"
            ),
            "options": ["3", "10", "1", "Error"],
            "answer": "3",
            "explain": "A FOR loop works out its bounds once, before the first pass. Changing n inside the "
                       "loop doesn't change how many times it runs.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  gem VARCHAR2(10) := 'Pearl';\n"
                "BEGIN\n"
                "  CASE gem\n"
                "    WHEN 'Ruby' THEN DBMS_OUTPUT.PUT_LINE('red');\n"
                "    WHEN 'Jade' THEN DBMS_OUTPUT.PUT_LINE('green');\n"
                "  END CASE;\n"
                "END;"
            ),
            "options": [
                "Error: ORA-06592: CASE not found",
                "Nothing is printed",
                "(an empty line)",
                "green",
            ],
            "answer": "Error: ORA-06592: CASE not found",
            "explain": "A CASE statement with no ELSE must match something. When nothing matches it raises "
                       "CASE_NOT_FOUND instead of doing nothing.",
            "expect_error": True,
        },
        {
            "prompt": "A package body has a package-level variable counter NUMBER := 0, and a procedure "
                      "that adds 1 to it. You call that procedure in three separate blocks, one after "
                      "another, in the same session. What is counter now?",
            "options": ["3", "1", "0", "NULL"],
            "answer": "3",
            "explain": "Package-level variables keep their values for the whole session, from call to "
                       "call. Each block sees what the last one left.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  n NUMBER := 0;\n"
                "BEGIN\n"
                "  <<hunt>>\n"
                "  FOR i IN 1..3 LOOP\n"
                "    FOR j IN 1..3 LOOP\n"
                "      EXIT hunt WHEN i * j = 4;\n"
                "      n := n + 1;\n"
                "    END LOOP;\n"
                "  END LOOP;\n"
                "  DBMS_OUTPUT.PUT_LINE(n);\n"
                "END;"
            ),
            "options": ["4", "7", "5", "9"],
            "answer": "4",
            "explain": "EXIT hunt leaves the labelled outer loop, not just the inner one. It counts i = 1 "
                       "(3 times) and i = 2, j = 1, then stops at 2 * 2.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "-- relics\n"
                "--  name\n"
                "--  Orb\n"
                "--  Ring\n"
                "--  Crown\n"
                "DECLARE\n"
                "  CURSOR c IS SELECT name FROM relics;\n"
                "  r relics.name%TYPE;\n"
                "BEGIN\n"
                "  OPEN c;\n"
                "  FETCH c INTO r;\n"
                "  FETCH c INTO r;\n"
                "  DBMS_OUTPUT.PUT_LINE(c%ROWCOUNT);\n"
                "END;"
            ),
            "setup": (
                "CREATE TABLE relics (name VARCHAR2(10));\n"
                "INSERT INTO relics VALUES ('Orb');\n"
                "INSERT INTO relics VALUES ('Ring');\n"
                "INSERT INTO relics VALUES ('Crown');\n"
                "COMMIT;"
            ),
            "options": ["2", "3", "1", "0"],
            "answer": "2",
            "explain": "%ROWCOUNT on an explicit cursor counts the rows fetched so far, not the rows in "
                       "the result: two fetches, so 2.",
        },
        {
            "prompt": "How can PL/SQL code run a CREATE TABLE statement?",
            "options": [
                "With EXECUTE IMMEDIATE",
                "Write it directly, like an INSERT",
                "Only from inside a trigger",
                "Put CALL in front of it",
            ],
            "answer": "With EXECUTE IMMEDIATE",
            "explain": "Static PL/SQL allows only DML, queries and transaction control. DDL has to go "
                       "through dynamic SQL, such as EXECUTE IMMEDIATE.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "-- relics (name): Orb, Ring\n"
                "DECLARE\n"
                "  CURSOR c IS SELECT name FROM relics;\n"
                "BEGIN\n"
                "  FOR r IN c LOOP\n"
                "    NULL;\n"
                "  END LOOP;\n"
                "  IF c%ISOPEN THEN\n"
                "    DBMS_OUTPUT.PUT_LINE('open');\n"
                "  ELSE\n"
                "    DBMS_OUTPUT.PUT_LINE('closed');\n"
                "  END IF;\n"
                "END;"
            ),
            "setup": (
                "CREATE TABLE relics (name VARCHAR2(10));\n"
                "INSERT INTO relics VALUES ('Orb');\n"
                "INSERT INTO relics VALUES ('Ring');\n"
                "COMMIT;"
            ),
            "options": ["closed", "open", "Error: invalid cursor", "(an empty line)"],
            "answer": "closed",
            "explain": "A cursor FOR loop opens the cursor, fetches every row and closes it again by "
                       "itself. %ISOPEN is the one attribute safe to ask afterwards.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "-- gems\n"
                "--  name | power\n"
                "--  Ruby | 5\n"
                "--  Opal | 2\n"
                "BEGIN\n"
                "  UPDATE gems SET power = 0 WHERE name = 'Diamond';\n"
                "  IF SQL%NOTFOUND THEN\n"
                "    DBMS_OUTPUT.PUT_LINE('No such gem');\n"
                "  ELSE\n"
                "    DBMS_OUTPUT.PUT_LINE('Updated');\n"
                "  END IF;\n"
                "EXCEPTION\n"
                "  WHEN NO_DATA_FOUND THEN\n"
                "    DBMS_OUTPUT.PUT_LINE('No data found');\n"
                "END;"
            ),
            "setup": (
                "CREATE TABLE gems (name VARCHAR2(10), power NUMBER);\n"
                "INSERT INTO gems VALUES ('Ruby', 5);\n"
                "INSERT INTO gems VALUES ('Opal', 2);\n"
                "COMMIT;"
            ),
            "options": ["No such gem", "No data found", "Updated", "Error"],
            "answer": "No such gem",
            "explain": "Only SELECT INTO raises NO_DATA_FOUND. An UPDATE that matches no rows is fine; it "
                       "just leaves SQL%NOTFOUND true.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  gold NUMBER := 5;\n"
                "  PROCEDURE add_one(g OUT NUMBER) IS\n"
                "  BEGIN\n"
                "    g := NVL(g, 0) + 1;\n"
                "  END;\n"
                "BEGIN\n"
                "  add_one(gold);\n"
                "  DBMS_OUTPUT.PUT_LINE(gold);\n"
                "END;"
            ),
            "options": ["1", "6", "5", "(an empty line)"],
            "answer": "1",
            "explain": "An OUT parameter starts as NULL inside the procedure, whatever the caller's "
                       "variable held. Use IN OUT to pass the 5 in.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  PROCEDURE show(a NUMBER := 1, b NUMBER := 2) IS\n"
                "  BEGIN\n"
                "    DBMS_OUTPUT.PUT_LINE(a * 10 + b);\n"
                "  END;\n"
                "BEGIN\n"
                "  show(b => 5);\n"
                "END;"
            ),
            "options": ["15", "52", "12", "Error"],
            "answer": "15",
            "explain": "Named notation (b => 5) sets b by name, so a keeps its default of 1: 1 * 10 + 5 = "
                       "15.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  FUNCTION sign_of(n NUMBER) RETURN VARCHAR2 IS\n"
                "  BEGIN\n"
                "    IF n > 0 THEN\n"
                "      RETURN 'positive';\n"
                "    ELSIF n < 0 THEN\n"
                "      RETURN 'negative';\n"
                "    END IF;\n"
                "  END;\n"
                "BEGIN\n"
                "  DBMS_OUTPUT.PUT_LINE(sign_of(0));\n"
                "END;"
            ),
            "options": [
                "Error: function returned without value",
                "(an empty line)",
                "positive",
                "negative",
            ],
            "answer": "Error: function returned without value",
            "explain": "A function that reaches its END without a RETURN doesn't hand back NULL: it raises "
                       "ORA-06503: Function returned without value.",
            "expect_error": True,
        },
        {
            "prompt": "Inside a procedure, you assign a new value to a parameter declared IN. What happens?",
            "options": [
                "It doesn't compile",
                "The caller's variable changes too",
                "Only a local copy changes",
                "It raises VALUE_ERROR when run",
            ],
            "answer": "It doesn't compile",
            "explain": "An IN parameter is read-only inside the subprogram. Assigning to it is a compile "
                       "error (PLS-00363); use IN OUT if you need to change it.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "BEGIN\n"
                "  RAISE_APPLICATION_ERROR(-20042, 'The dragon wakes');\n"
                "EXCEPTION\n"
                "  WHEN OTHERS THEN\n"
                "    DBMS_OUTPUT.PUT_LINE(SQLERRM);\n"
                "END;"
            ),
            "options": [
                "ORA-20042: The dragon wakes",
                "The dragon wakes",
                "-20042",
                "User-Defined Exception",
            ],
            "answer": "ORA-20042: The dragon wakes",
            "explain": "RAISE_APPLICATION_ERROR raises a real Oracle error with your number and text, and "
                       "SQLERRM shows it in the usual ORA-nnnnn: form.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  n NUMBER := 0;\n"
                "  s VARCHAR2(20) := 'A';\n"
                "BEGIN\n"
                "  BEGIN\n"
                "    s := s || 'B';\n"
                "    n := 1 / n;\n"
                "    s := s || 'C';\n"
                "  EXCEPTION\n"
                "    WHEN NO_DATA_FOUND THEN s := s || 'D';\n"
                "  END;\n"
                "  DBMS_OUTPUT.PUT_LINE(s || 'E');\n"
                "EXCEPTION\n"
                "  WHEN ZERO_DIVIDE THEN DBMS_OUTPUT.PUT_LINE(s || 'F');\n"
                "END;"
            ),
            "options": ["ABF", "ABE", "ABDE", "ABCE"],
            "answer": "ABF",
            "explain": "The inner block has no handler for ZERO_DIVIDE, so the error leaves it and skips "
                       "everything up to the outer block's handler.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "<<castle>>\n"
                "DECLARE\n"
                "  gold NUMBER := 1;\n"
                "BEGIN\n"
                "  DECLARE\n"
                "    gold NUMBER := 2;\n"
                "  BEGIN\n"
                "    DBMS_OUTPUT.PUT_LINE(castle.gold || gold);\n"
                "  END;\n"
                "END;"
            ),
            "options": ["12", "22", "11", "21"],
            "answer": "12",
            "explain": "The inner gold hides the outer one, but the block label lets you reach it: "
                       "castle.gold is 1, plain gold is the inner 2.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  TYPE hoard_t IS TABLE OF NUMBER\n"
                "    INDEX BY VARCHAR2(10);\n"
                "  h hoard_t;\n"
                "BEGIN\n"
                "  h('ruby')  := 5;\n"
                "  h('amber') := 2;\n"
                "  h('opal')  := 9;\n"
                "  DBMS_OUTPUT.PUT_LINE(h.FIRST);\n"
                "END;"
            ),
            "options": ["amber", "ruby", "opal", "2"],
            "answer": "amber",
            "explain": "An associative array keeps its keys sorted, not in the order you added them, and "
                       "FIRST returns the lowest key, not a value.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  TYPE num_list IS TABLE OF NUMBER;\n"
                "  t num_list := num_list(10, 20, 30, 40);\n"
                "BEGIN\n"
                "  t.DELETE(2);\n"
                "  DBMS_OUTPUT.PUT_LINE(t.COUNT || ' ' || t.LAST);\n"
                "END;"
            ),
            "options": ["3 4", "3 3", "4 4", "4 3"],
            "answer": "3 4",
            "explain": "DELETE(2) leaves a gap instead of moving the others down: three elements are left, "
                       "but the last one is still number 4.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "-- gems\n"
                "--  name | power\n"
                "--  Ruby | 5\n"
                "--  Opal | 2\n"
                "DECLARE\n"
                "  TYPE name_list IS TABLE OF gems.name%TYPE;\n"
                "  t name_list;\n"
                "BEGIN\n"
                "  SELECT name BULK COLLECT INTO t\n"
                "    FROM gems WHERE power > 100;\n"
                "  DBMS_OUTPUT.PUT_LINE(t.COUNT);\n"
                "EXCEPTION\n"
                "  WHEN NO_DATA_FOUND THEN DBMS_OUTPUT.PUT_LINE('none');\n"
                "END;"
            ),
            "setup": (
                "CREATE TABLE gems (name VARCHAR2(10), power NUMBER);\n"
                "INSERT INTO gems VALUES ('Ruby', 5);\n"
                "INSERT INTO gems VALUES ('Opal', 2);\n"
                "COMMIT;"
            ),
            "options": ["0", "none", "(an empty line)", "Error: collection is null"],
            "answer": "0",
            "explain": "BULK COLLECT never raises NO_DATA_FOUND. With no rows it just leaves the "
                       "collection empty, so COUNT is 0.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  gold INTEGER;\n"
                "BEGIN\n"
                "  gold := 7 / 2;\n"
                "  DBMS_OUTPUT.PUT_LINE(gold);\n"
                "END;"
            ),
            "options": ["4", "3", "3.5", "Error"],
            "answer": "4",
            "explain": "7 / 2 is worked out as 3.5 first. INTEGER is really NUMBER(38,0), so storing 3.5 "
                       "rounds it to 4 rather than cutting it to 3.",
        },
    ],
    "hard": [
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  gold NUMBER;\n"
                "BEGIN\n"
                "  IF gold > 5 THEN\n"
                "    DBMS_OUTPUT.PUT_LINE('rich');\n"
                "  ELSIF NOT (gold > 5) THEN\n"
                "    DBMS_OUTPUT.PUT_LINE('poor');\n"
                "  ELSE\n"
                "    DBMS_OUTPUT.PUT_LINE('unknown');\n"
                "  END IF;\n"
                "END;"
            ),
            "options": ["unknown", "poor", "rich", "Error"],
            "answer": "unknown",
            "explain": "gold is NULL, so gold > 5 is NULL, and NOT NULL is still NULL. IF only takes a "
                       "branch whose condition is TRUE, so it falls through to ELSE.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  gold NUMBER := 0;\n"
                "BEGIN\n"
                "  IF gold = 0 OR 100 / gold > 1 THEN\n"
                "    DBMS_OUTPUT.PUT_LINE('safe');\n"
                "  ELSE\n"
                "    DBMS_OUTPUT.PUT_LINE('risky');\n"
                "  END IF;\n"
                "END;"
            ),
            "options": ["safe", "risky", "Error: divisor is equal to zero", "Nothing is printed"],
            "answer": "safe",
            "explain": "PL/SQL uses short-circuit evaluation: once gold = 0 is TRUE the OR is already "
                       "TRUE, so 100 / gold is never worked out.",
        },
        {
            "prompt": "A procedure with PRAGMA AUTONOMOUS_TRANSACTION inserts a row, then ends without a "
                      "COMMIT or ROLLBACK. What happens?",
            "options": [
                "It fails: ORA-06519, and the insert is undone",
                "The insert joins the caller's transaction",
                "The insert is committed automatically",
                "The insert waits until the session ends",
            ],
            "answer": "It fails: ORA-06519, and the insert is undone",
            "explain": "An autonomous transaction must be finished before control returns. If not, Oracle "
                       "rolls it back and raises ORA-06519 (active autonomous transaction detected and "
                       "rolled back).",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  dragon_awake EXCEPTION;\n"
                "BEGIN\n"
                "  RAISE dragon_awake;\n"
                "END;"
            ),
            "options": [
                "Error: ORA-06510: unhandled user-defined",
                "Error: ORA-20000: dragon_awake",
                "Error: ORA-01403: no data found",
                "Nothing: the exception is ignored",
            ],
            "answer": "Error: ORA-06510: unhandled user-defined",
            "explain": "An exception you declare yourself has no Oracle error number. Left unhandled, it "
                       "reaches the caller as ORA-06510: PL/SQL: unhandled user-defined exception.",
            "expect_error": True,
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  no_divisor EXCEPTION;\n"
                "  PRAGMA EXCEPTION_INIT(no_divisor, -1476);\n"
                "  zero NUMBER := 0;\n"
                "  n NUMBER;\n"
                "BEGIN\n"
                "  n := 10 / zero;\n"
                "EXCEPTION\n"
                "  WHEN no_divisor THEN\n"
                "    DBMS_OUTPUT.PUT_LINE('caught ' || SQLCODE);\n"
                "END;"
            ),
            "options": ["caught -1476", "caught 1", "caught 1476", "Error: divisor is equal to zero"],
            "answer": "caught -1476",
            "explain": "PRAGMA EXCEPTION_INIT ties your name to an Oracle error number, so ORA-01476 "
                       "(divide by zero) is caught as no_divisor. SQLCODE is -1476.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  gold NUMBER := 100;\n"
                "  loot gold%TYPE;\n"
                "BEGIN\n"
                "  DBMS_OUTPUT.PUT_LINE(NVL(TO_CHAR(loot), 'empty'));\n"
                "END;"
            ),
            "options": ["empty", "100", "0", "Error"],
            "answer": "empty",
            "explain": "%TYPE copies the data type (and size and constraints) of gold, but never its "
                       "starting value, so loot starts as NULL.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "-- relics\n"
                "--  name\n"
                "--  Orb\n"
                "--  Ring\n"
                "--  Crown\n"
                "DECLARE\n"
                "  CURSOR c IS SELECT name FROM relics;\n"
                "BEGIN\n"
                "  FOR r IN c LOOP\n"
                "    NULL;\n"
                "  END LOOP;\n"
                "  DBMS_OUTPUT.PUT_LINE(c%ROWCOUNT);\n"
                "END;"
            ),
            "setup": (
                "CREATE TABLE relics (name VARCHAR2(10));\n"
                "INSERT INTO relics VALUES ('Orb');\n"
                "INSERT INTO relics VALUES ('Ring');\n"
                "INSERT INTO relics VALUES ('Crown');\n"
                "COMMIT;"
            ),
            "options": ["Error: ORA-01001: invalid cursor", "3", "0", "(an empty line)"],
            "answer": "Error: ORA-01001: invalid cursor",
            "explain": "The FOR loop closes the cursor when it ends. Asking a closed cursor for any "
                       "attribute but %ISOPEN raises INVALID_CURSOR.",
            "expect_error": True,
        },
        {
            "prompt": "What does this print?",
            "code": (
                "-- gems (name): Ruby, Opal\n"
                "DECLARE\n"
                "  CURSOR c IS SELECT name FROM gems;\n"
                "  g gems.name%TYPE;\n"
                "  n NUMBER := 0;\n"
                "BEGIN\n"
                "  OPEN c;\n"
                "  INSERT INTO gems VALUES ('Jade');\n"
                "  LOOP\n"
                "    FETCH c INTO g;\n"
                "    EXIT WHEN c%NOTFOUND;\n"
                "    n := n + 1;\n"
                "  END LOOP;\n"
                "  DBMS_OUTPUT.PUT_LINE(n);\n"
                "END;"
            ),
            "setup": (
                "CREATE TABLE gems (name VARCHAR2(10));\n"
                "INSERT INTO gems VALUES ('Ruby');\n"
                "INSERT INTO gems VALUES ('Opal');\n"
                "COMMIT;"
            ),
            "options": ["2", "3", "0", "Error"],
            "answer": "2",
            "explain": "A cursor's rows are fixed at the moment it is OPENed (read consistency). Jade was "
                       "inserted afterwards, so the cursor never sees it.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  TYPE party_t IS VARRAY(3) OF VARCHAR2(10);\n"
                "  party party_t := party_t('Knight', 'Mage', 'Thief');\n"
                "BEGIN\n"
                "  party.EXTEND;\n"
                "  party(4) := 'Bard';\n"
                "  DBMS_OUTPUT.PUT_LINE(party.COUNT);\n"
                "END;"
            ),
            "options": [
                "Error: ORA-06532: Subscript outside of limit",
                "Error: ORA-06533: Subscript beyond count",
                "4",
                "3",
            ],
            "answer": "Error: ORA-06532: Subscript outside of limit",
            "explain": "A VARRAY(3) can never hold more than 3 elements. EXTEND past that limit raises "
                       "SUBSCRIPT_OUTSIDE_LIMIT before Bard is even stored.",
            "expect_error": True,
        },
        {
            "prompt": "What does this print?",
            "code": (
                "-- gems (name, color): Ruby red, Garnet red, Jade green,\n"
                "--   Emerald green, Peridot green, Opal white\n"
                "DECLARE\n"
                "  TYPE color_list IS TABLE OF VARCHAR2(10);\n"
                "  colors color_list := color_list('red', 'blue', 'green');\n"
                "BEGIN\n"
                "  FORALL i IN 1..colors.COUNT\n"
                "    DELETE FROM gems WHERE color = colors(i);\n"
                "  DBMS_OUTPUT.PUT_LINE(SQL%BULK_ROWCOUNT(3)\n"
                "                       || ' ' || SQL%ROWCOUNT);\n"
                "END;"
            ),
            "setup": (
                "CREATE TABLE gems (name VARCHAR2(10), color VARCHAR2(10));\n"
                "INSERT INTO gems VALUES ('Ruby', 'red');\n"
                "INSERT INTO gems VALUES ('Garnet', 'red');\n"
                "INSERT INTO gems VALUES ('Jade', 'green');\n"
                "INSERT INTO gems VALUES ('Emerald', 'green');\n"
                "INSERT INTO gems VALUES ('Peridot', 'green');\n"
                "INSERT INTO gems VALUES ('Opal', 'white');\n"
                "COMMIT;"
            ),
            "options": ["3 5", "5 5", "3 3", "0 5"],
            "answer": "3 5",
            "explain": "SQL%BULK_ROWCOUNT(i) counts only the i-th DELETE (green: 3), while SQL%ROWCOUNT "
                       "adds up the whole FORALL: 2 + 0 + 3 = 5.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "-- gem_seq is a new sequence: START WITH 1 INCREMENT BY 1\n"
                "DECLARE\n"
                "  a NUMBER;\n"
                "  b NUMBER;\n"
                "BEGIN\n"
                "  SELECT gem_seq.NEXTVAL, gem_seq.NEXTVAL INTO a, b\n"
                "    FROM dual;\n"
                "  DBMS_OUTPUT.PUT_LINE(a || ' ' || b);\n"
                "END;"
            ),
            "setup": "CREATE SEQUENCE gem_seq START WITH 1 INCREMENT BY 1;",
            "options": ["1 1", "1 2", "2 2", "0 1"],
            "answer": "1 1",
            "explain": "NEXTVAL moves on only once per row of a SQL statement, however many times it's "
                       "named there, so both columns get the same value.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "-- relics\n"
                "--  name\n"
                "--  Orb\n"
                "--  Ring\n"
                "--  Crown\n"
                "DECLARE\n"
                "  n NUMBER;\n"
                "BEGIN\n"
                "  SELECT COUNT(*) INTO n FROM relics WHERE ROWNUM > 1;\n"
                "  DBMS_OUTPUT.PUT_LINE(n);\n"
                "END;"
            ),
            "setup": (
                "CREATE TABLE relics (name VARCHAR2(10));\n"
                "INSERT INTO relics VALUES ('Orb');\n"
                "INSERT INTO relics VALUES ('Ring');\n"
                "INSERT INTO relics VALUES ('Crown');\n"
                "COMMIT;"
            ),
            "options": ["0", "2", "3", "1"],
            "answer": "0",
            "explain": "ROWNUM is given out as rows pass the WHERE. The first row gets 1, fails ROWNUM > 1 "
                       "and is dropped, so the next row gets 1 too, and so on.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  word VARCHAR2(10);\n"
                "BEGIN\n"
                "  word := DECODE(1, 1, 'one', 'other');\n"
                "  DBMS_OUTPUT.PUT_LINE(word);\n"
                "END;"
            ),
            "options": ["Error: DECODE only works inside SQL", "one", "other", "(an empty line)"],
            "answer": "Error: DECODE only works inside SQL",
            "explain": "DECODE is a SQL-only function: in a plain PL/SQL assignment it doesn't compile "
                       "(PLS-00204). Use CASE, or SELECT DECODE(...) INTO ... FROM dual.",
            "expect_error": True,
        },
        {
            "prompt": "What does this print?",
            "code": (
                "BEGIN\n"
                "  DBMS_OUTPUT.PUT_LINE(TO_CHAR(\n"
                "    ADD_MONTHS(DATE '2024-02-29', 1), 'YYYY-MM-DD'));\n"
                "END;"
            ),
            "options": ["2024-03-31", "2024-03-29", "2024-03-30", "Error: invalid date"],
            "answer": "2024-03-31",
            "explain": "ADD_MONTHS has a last-day rule: from the last day of a month you land on the last "
                       "day of the new month. 29 Feb 2024 is February's last day.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "BEGIN\n"
                "  DBMS_OUTPUT.PUT_LINE('[' || TO_CHAR(5, '000') || ']');\n"
                "END;"
            ),
            "options": ["[ 005]", "[005]", "[5]", "[  5]"],
            "answer": "[ 005]",
            "explain": "A number format keeps one place in front for the sign, which is a blank for a "
                       "positive number. 'FM000' would drop it.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "BEGIN\n"
                "  DBMS_OUTPUT.PUT_LINE(1 / 2);\n"
                "END;"
            ),
            "options": [".5", "0.5", "0", "0.50"],
            "answer": ".5",
            "explain": "When Oracle turns a number into text by default, it leaves out the zero before the "
                       "decimal point, so 0.5 prints as .5.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  TYPE gem_t IS RECORD (name VARCHAR2(10), power NUMBER);\n"
                "  a gem_t;\n"
                "  b gem_t;\n"
                "BEGIN\n"
                "  a.name := 'Ruby';\n"
                "  a.power := 5;\n"
                "  b := a;\n"
                "  IF a = b THEN\n"
                "    DBMS_OUTPUT.PUT_LINE('same');\n"
                "  ELSE\n"
                "    DBMS_OUTPUT.PUT_LINE('different');\n"
                "  END IF;\n"
                "END;"
            ),
            "options": ["Error: records can't be compared with =", "same", "different", "(an empty line)"],
            "answer": "Error: records can't be compared with =",
            "explain": "You can copy a whole record with :=, but PL/SQL can't compare records with = "
                       "(PLS-00306). You have to compare them field by field.",
            "expect_error": True,
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  TYPE num_list IS TABLE OF NUMBER;\n"
                "  a num_list := num_list(1, 2, 3);\n"
                "  b num_list := num_list(2, 3, 4);\n"
                "  c num_list;\n"
                "BEGIN\n"
                "  c := a MULTISET UNION b;\n"
                "  DBMS_OUTPUT.PUT_LINE(c.COUNT);\n"
                "END;"
            ),
            "options": ["6", "4", "2", "Error"],
            "answer": "6",
            "explain": "Unlike SQL's UNION, MULTISET UNION keeps duplicates by default (it means MULTISET "
                       "UNION ALL). MULTISET UNION DISTINCT would give 4.",
        },
        {
            "prompt": "A SELECT works when you run it yourself, but the same SELECT in your stored "
                      "procedure won't compile: ORA-00942, table or view does not exist. You were given "
                      "access to the table through a role. Why?",
            "options": [
                "Definer's rights code ignores roles",
                "Procedures can't read other schemas",
                "Static SQL needs EXECUTE IMMEDIATE",
                "The GRANT needs a COMMIT first",
            ],
            "answer": "Definer's rights code ignores roles",
            "explain": "A stored procedure runs with its owner's rights by default, and those count only "
                       "privileges granted directly, never through a role.",
        },
        {
            "prompt": "A row-level trigger on knights runs SELECT COUNT(*) FROM knights. What happens when "
                      "an UPDATE changes several knights?",
            "options": [
                "It fails: ORA-04091, the table is mutating",
                "It counts the rows before the update",
                "It counts the rows after the update",
                "The trigger is skipped for that table",
            ],
            "answer": "It fails: ORA-04091, the table is mutating",
            "explain": "A row-level trigger can't read the table its statement is in the middle of "
                       "changing. A statement-level or compound trigger is the usual way round it.",
        },
    ],
}


# ------------------------------------------------------------------
# Bonus dragons (as in pythonia.py)
# ------------------------------------------------------------------
# After a win, the dragon of that path and level sleeps on a chest of treasure nearby. The
# explorer may wake it (the move DRAGON_MOVE) for one bonus riddle, a step harder than the
# level's own questions on the same topics. Answered right, it's worth DRAGON_POINTS (times
# the level's multiplier) from the dragon's hoard; answered wrong, the explorer flees with
# nothing lost. Either way the quest stays won, and the explorer carries on as after any win.
# The dragons and their pictures are the Python game's.

DRAGON_MOVE = "dragon"
DRAGON_POINTS = 30

DRAGON_LAIRS = {
    "forest": "On your way back through the Forest of Nested Blocks, a glint of gold catches your eye in a "
              "mossy hollow.",
    "cave": "On your way back out of the Caverns of DUAL, a glint of gold catches your eye in a side "
            "cavern.",
    "castle": "On your way back through Castle Ada, a glint of gold catches your eye through a doorway: a "
              "forgotten treasury.",
}

DRAGONS = {
    ("easy", "cave"): {
        "scene": "dragon-emerald", "scales": "green as moss",
        "question": {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  total NUMBER := 0;\n"
                "BEGIN\n"
                "  FOR i IN REVERSE 3..1 LOOP\n"
                "    total := total + i;\n"
                "  END LOOP;\n"
                "  DBMS_OUTPUT.PUT_LINE(total);\n"
                "END;"
            ),
            "options": ["0", "6", "3", "Error"],
            "answer": "0",
            "explain": "With REVERSE you still write the range low..high. 3..1 is an empty range, so the "
                       "loop body never runs.",
        },
    },
    ("medium", "cave"): {
        "scene": "dragon-ember", "scales": "glowing like hot coals",
        "question": {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  gem VARCHAR2(10) := 'Pearl';\n"
                "  color VARCHAR2(10);\n"
                "BEGIN\n"
                "  color := CASE gem\n"
                "             WHEN 'Ruby' THEN 'red'\n"
                "             WHEN 'Jade' THEN 'green'\n"
                "           END;\n"
                "  DBMS_OUTPUT.PUT_LINE(NVL(color, 'no color'));\n"
                "END;"
            ),
            "options": ["no color", "Error: ORA-06592: CASE not found", "green", "(an empty line)"],
            "answer": "no color",
            "explain": "This is a CASE expression, not a CASE statement. With no match and no ELSE, an "
                       "expression just gives NULL; only the statement raises CASE_NOT_FOUND.",
        },
    },
    ("hard", "cave"): {
        "scene": "dragon-frost", "scales": "glittering with ice",
        "question": {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  zero NUMBER := 0;\n"
                "  n NUMBER;\n"
                "BEGIN\n"
                "  BEGIN\n"
                "    RAISE NO_DATA_FOUND;\n"
                "  EXCEPTION\n"
                "    WHEN NO_DATA_FOUND THEN n := 1 / zero;\n"
                "    WHEN ZERO_DIVIDE THEN DBMS_OUTPUT.PUT_LINE('inner');\n"
                "  END;\n"
                "EXCEPTION\n"
                "  WHEN ZERO_DIVIDE THEN DBMS_OUTPUT.PUT_LINE('outer');\n"
                "END;"
            ),
            "options": ["outer", "inner", "inner outer", "Error: divisor is equal to zero"],
            "answer": "outer",
            "explain": "An exception raised inside a handler leaves that block at once; its other handlers "
                       "don't get a look. It goes up to the outer block.",
        },
    },
    ("easy", "forest"): {
        "scene": "dragon-pearl", "scales": "white as moonlight",
        "question": {
            "prompt": "What does this print?",
            "code": (
                "-- relics\n"
                "--  name | power\n"
                "--  Orb  | 5\n"
                "--  Ring | 2\n"
                "DECLARE\n"
                "  best NUMBER;\n"
                "BEGIN\n"
                "  SELECT MAX(power) INTO best FROM relics WHERE power > 10;\n"
                "  DBMS_OUTPUT.PUT_LINE(NVL(TO_CHAR(best), 'none'));\n"
                "EXCEPTION\n"
                "  WHEN NO_DATA_FOUND THEN\n"
                "    DBMS_OUTPUT.PUT_LINE('no data');\n"
                "END;"
            ),
            "setup": (
                "CREATE TABLE relics (name VARCHAR2(10), power NUMBER);\n"
                "INSERT INTO relics VALUES ('Orb', 5);\n"
                "INSERT INTO relics VALUES ('Ring', 2);\n"
                "COMMIT;"
            ),
            "options": ["none", "no data", "0", "5"],
            "answer": "none",
            "explain": "An aggregate with no matching rows still returns one row, holding NULL. SELECT "
                       "INTO gets its one row, so NO_DATA_FOUND is never raised.",
        },
    },
    ("medium", "forest"): {
        "scene": "dragon-amethyst", "scales": "a deep, shimmering purple",
        "question": {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  TYPE num_list IS TABLE OF NUMBER;\n"
                "  t num_list := num_list(5, 15, 25);\n"
                "  total NUMBER := 0;\n"
                "BEGIN\n"
                "  t.DELETE(2);\n"
                "  FOR i IN 1..t.COUNT LOOP\n"
                "    total := total + t(i);\n"
                "  END LOOP;\n"
                "  DBMS_OUTPUT.PUT_LINE(total);\n"
                "END;"
            ),
            "options": ["Error: ORA-01403: no data found", "30", "20", "45"],
            "answer": "Error: ORA-01403: no data found",
            "explain": "After DELETE(2), COUNT is 2, so the loop asks for t(1) and then t(2), which is "
                       "gone. Reading a deleted element raises NO_DATA_FOUND.",
            "expect_error": True,
        },
    },
    ("hard", "forest"): {
        "scene": "dragon-autumn", "scales": "the color of falling leaves",
        "question": {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  TYPE gem_list IS TABLE OF VARCHAR2(10);\n"
                "  a gem_list := gem_list('ruby', 'opal', 'jade');\n"
                "  b gem_list := gem_list('jade', 'ruby', 'opal');\n"
                "BEGIN\n"
                "  IF a = b THEN\n"
                "    DBMS_OUTPUT.PUT_LINE('equal');\n"
                "  ELSE\n"
                "    DBMS_OUTPUT.PUT_LINE('not equal');\n"
                "  END IF;\n"
                "END;"
            ),
            "options": ["equal", "not equal", "Error: collections can't be compared", "(an empty line)"],
            "answer": "equal",
            "explain": "Nested tables can be compared with =, and they are equal when they hold the same "
                       "elements, in any order.",
        },
    },
    ("easy", "castle"): {
        "scene": "dragon-gold", "scales": "as bright as the coins beneath it",
        "question": {
            "prompt": "What does this print?",
            "code": (
                "DECLARE\n"
                "  a CHAR(5) := 'Orb';\n"
                "  b VARCHAR2(5) := 'Orb';\n"
                "BEGIN\n"
                "  IF a = b THEN\n"
                "    DBMS_OUTPUT.PUT_LINE('Equal');\n"
                "  ELSE\n"
                "    DBMS_OUTPUT.PUT_LINE('Not equal');\n"
                "  END IF;\n"
                "END;"
            ),
            "options": ["Not equal", "Equal", "Error", "(an empty line)"],
            "answer": "Not equal",
            "explain": "a really holds 'Orb' plus two blanks. When one side is a VARCHAR2, Oracle compares "
                       "without padding, so the blanks make them differ.",
        },
    },
    ("medium", "castle"): {
        "scene": "dragon-silver", "scales": "gleaming like polished armor",
        "question": {
            "prompt": "What does this print?",
            "code": (
                "-- relics\n"
                "--  name\n"
                "--  Orb\n"
                "--  Ring\n"
                "DECLARE\n"
                "  CURSOR c IS SELECT name FROM relics;\n"
                "  r relics.name%TYPE;\n"
                "BEGIN\n"
                "  OPEN c;\n"
                "  LOOP\n"
                "    FETCH c INTO r;\n"
                "    EXIT WHEN c%NOTFOUND;\n"
                "  END LOOP;\n"
                "  DBMS_OUTPUT.PUT_LINE(c%ROWCOUNT);\n"
                "END;"
            ),
            "setup": (
                "CREATE TABLE relics (name VARCHAR2(10));\n"
                "INSERT INTO relics VALUES ('Orb');\n"
                "INSERT INTO relics VALUES ('Ring');\n"
                "COMMIT;"
            ),
            "options": ["2", "3", "0", "1"],
            "answer": "2",
            "explain": "The loop fetches three times, but the third fetch finds nothing. %ROWCOUNT only "
                       "counts rows actually fetched, so it stays at 2.",
        },
    },
    ("hard", "castle"): {
        "scene": "dragon-shadow", "scales": "as black as a moonless night",
        "question": {
            "prompt": "What does this print?",
            "code": (
                "-- gold (amt NUMBER) starts empty\n"
                "DECLARE\n"
                "  n NUMBER;\n"
                "BEGIN\n"
                "  INSERT INTO gold VALUES (50);\n"
                "  EXECUTE IMMEDIATE 'CREATE TABLE vault (amt NUMBER)';\n"
                "  ROLLBACK;\n"
                "  SELECT COUNT(*) INTO n FROM gold;\n"
                "  DBMS_OUTPUT.PUT_LINE(n);\n"
                "END;"
            ),
            "setup": "CREATE TABLE gold (amt NUMBER);",
            "options": ["1", "0", "Error", "2"],
            "answer": "1",
            "explain": "In Oracle every DDL statement commits, before and after it runs. The CREATE TABLE "
                       "committed the insert, so the ROLLBACK had nothing to undo.",
        },
    },
}


# ------------------------------------------------------------------
# The final boss: the Mutating Table
# ------------------------------------------------------------------
# Only an explorer who completes every path on every level meets the Mutating Table. It asks one of
# these nine, picked at random: the hardest questions in the game. Answer right and they
# become a PL/SQL Master, with BOSS_POINTS (times the Hard multiplier) besides; answer
# wrong and all is lost: their score falls to zero, and they must start over.

BOSS_MOVE = "boss"
BOSS_POINTS = 100

# The page's own words for this game. The other games have their own, by the same keys.
TEXTS = {
    "title": "The Lost Package of Oraclia",
    "language": "PL/SQL",
    "intro": [
        "Long ago, the priests of Oraclia wrote all their wisdom in blocks, DECLARE, BEGIN, EXCEPTION and "
        "END, and bound the greatest of it into one package: the Golden Package. They hid it deep within "
        "this wild land, and its guardians still test every traveler with riddles written in the priests' "
        "own language: PL/SQL.",
        "One law holds in Oraclia: an empty string is NULL. (And DBMS_OUTPUT is always switched on, so "
        "every PUT_LINE is seen.) Answer wisely and choose your path carefully. Every wrong answer costs "
        "you a life, and some choices lead to certain doom...",
    ],
    "found": "Found the treasure",
    "master": "PL/SQL Master",
    "lost_to_boss": "Lost to the Mutating Table",
    "hall_note": "Walk every path on every level to face the Mutating Table.",
    "boss_offer_title": "The final challenge: the Mutating Table",
    "boss_offer": "You have walked every path on every level, and the Mutating Table, whose rows never "
                  "keep still, is waiting. Answer its question, the hardest in all of Oraclia, to earn the "
                  "title of PL/SQL Master and {points} points.",
    "boss_warning": "Beware: if you fail, all is lost. Your score falls to zero and you must start over.",
    "boss_button": "Face the Mutating Table",
    "boss_confirm": "Face the Mutating Table? If you fail, all is lost: your score falls to zero and you "
                    "must start over.",
    "boss_won": "You have stilled the Mutating Table. You are a PL/SQL Master!",
    "boss_lost": "The Mutating Table has defeated you. All is lost: your score is gone, and you must start "
                 "over.",
    "conquered_every_path": "Every path on every level: you've explored all of Oraclia!",
    "conquered_every_level": "Easy, Medium and Hard: you've conquered every level of Oraclia!",
}

BOSS_QUESTIONS = [
    {
        "prompt": "What does this print?",
        "code": (
            "BEGIN\n"
            "  DECLARE\n"
            "    gold NUMBER(3) := 5000;\n"
            "  BEGIN\n"
            "    DBMS_OUTPUT.PUT_LINE(gold);\n"
            "  EXCEPTION\n"
            "    WHEN VALUE_ERROR THEN DBMS_OUTPUT.PUT_LINE('inner');\n"
            "  END;\n"
            "EXCEPTION\n"
            "  WHEN VALUE_ERROR THEN DBMS_OUTPUT.PUT_LINE('outer');\n"
            "END;"
        ),
        "options": ["outer", "inner", "5000", "Error: number precision too large"],
        "answer": "outer",
        "explain": "An exception raised while a block declares its variables happens before that block's "
                   "handlers are in force, so it goes straight to the enclosing block.",
    },
    {
        "prompt": "What does this print?",
        "code": (
            "DECLARE\n"
            "  n NUMBER;\n"
            "BEGIN\n"
            "  EXECUTE IMMEDIATE 'SELECT :x * 10 + :x FROM dual'\n"
            "    INTO n USING 1, 2;\n"
            "  DBMS_OUTPUT.PUT_LINE(n);\n"
            "END;"
        ),
        "options": ["12", "11", "22", "Error: bind variable does not exist"],
        "answer": "12",
        "explain": "In dynamic SQL (not a PL/SQL block), placeholders are bound by position, not by name: "
                   "the first :x gets 1, the second :x gets 2.",
    },
    {
        "prompt": "What does this print?",
        "code": (
            "DECLARE\n"
            "  p1 PLS_INTEGER := 2147483647;\n"
            "  p2 PLS_INTEGER := 1;\n"
            "  n NUMBER;\n"
            "BEGIN\n"
            "  n := p1 + p2;\n"
            "  DBMS_OUTPUT.PUT_LINE(n);\n"
            "END;"
        ),
        "options": [
            "Error: ORA-01426: numeric overflow",
            "2147483648",
            "-2147483648",
            "Error: ORA-06502: value error",
        ],
        "answer": "Error: ORA-01426: numeric overflow",
        "explain": "Adding two PLS_INTEGERs is done in PLS_INTEGER arithmetic, which tops out at "
                   "2147483647. It overflows even though the result goes into a NUMBER.",
        "expect_error": True,
    },
    {
        "prompt": "What does this print?",
        "code": (
            "DECLARE\n"
            "  gold NUMBER := 10;\n"
            "  PROCEDURE spend(g IN OUT NUMBER) IS\n"
            "  BEGIN\n"
            "    g := 99;\n"
            "    RAISE_APPLICATION_ERROR(-20001, 'Robbed!');\n"
            "  END;\n"
            "BEGIN\n"
            "  BEGIN\n"
            "    spend(gold);\n"
            "  EXCEPTION\n"
            "    WHEN OTHERS THEN NULL;\n"
            "  END;\n"
            "  DBMS_OUTPUT.PUT_LINE(gold);\n"
            "END;"
        ),
        "options": ["10", "99", "(an empty line)", "Error: ORA-20001: Robbed!"],
        "answer": "10",
        "explain": "IN OUT parameters are passed by value (without NOCOPY): the new value is copied back "
                   "only if the procedure ends normally. It failed, so gold keeps 10.",
    },
    {
        "prompt": "What does this print?",
        "code": (
            "DECLARE\n"
            "  s VARCHAR2(10) := 'gold';\n"
            "  n NUMBER;\n"
            "BEGIN\n"
            "  n := TO_NUMBER(s);\n"
            "EXCEPTION\n"
            "  WHEN INVALID_NUMBER THEN\n"
            "    DBMS_OUTPUT.PUT_LINE('invalid number');\n"
            "  WHEN VALUE_ERROR THEN\n"
            "    DBMS_OUTPUT.PUT_LINE('value error');\n"
            "END;"
        ),
        "options": ["value error", "invalid number", "(an empty line)", "Error: ORA-01722: invalid number"],
        "answer": "value error",
        "explain": "A failed text-to-number conversion raises INVALID_NUMBER (ORA-01722) only inside a SQL "
                   "statement. In a PL/SQL statement it's VALUE_ERROR (ORA-06502).",
    },
    {
        "prompt": "What does this print?",
        "code": (
            "-- gold (amt NUMBER) starts empty\n"
            "DECLARE\n"
            "  total NUMBER;\n"
            "  PROCEDURE tithe IS\n"
            "    PRAGMA AUTONOMOUS_TRANSACTION;\n"
            "  BEGIN\n"
            "    INSERT INTO gold VALUES (5); COMMIT;\n"
            "  END;\n"
            "BEGIN\n"
            "  INSERT INTO gold VALUES (100);\n"
            "  tithe;\n"
            "  ROLLBACK;\n"
            "  SELECT SUM(amt) INTO total FROM gold;\n"
            "  DBMS_OUTPUT.PUT_LINE(total);\n"
            "END;"
        ),
        "setup": "CREATE TABLE gold (amt NUMBER);",
        "options": ["5", "105", "100", "(an empty line)"],
        "answer": "5",
        "explain": "tithe runs in its own autonomous transaction, so its COMMIT saves only its own 5. The "
                   "ROLLBACK then undoes the main block's 100.",
    },
    {
        "prompt": "What does this print?",
        "code": (
            "-- gems (name VARCHAR2(5)) starts empty\n"
            "DECLARE\n"
            "  TYPE name_list IS TABLE OF VARCHAR2(10);\n"
            "  t name_list := name_list('ruby', 'emerald', 'opal');\n"
            "  n NUMBER;\n"
            "BEGIN\n"
            "  BEGIN\n"
            "    FORALL i IN 1..3\n"
            "      INSERT INTO gems VALUES (t(i));\n"
            "  EXCEPTION\n"
            "    WHEN OTHERS THEN NULL;\n"
            "  END;\n"
            "  SELECT COUNT(*) INTO n FROM gems;\n"
            "  DBMS_OUTPUT.PUT_LINE(n);\n"
            "END;"
        ),
        "setup": "CREATE TABLE gems (name VARCHAR2(5));",
        "options": ["1", "0", "2", "3"],
        "answer": "1",
        "explain": "Without SAVE EXCEPTIONS, FORALL stops at the first failing row ('emerald' is too "
                   "long). Only that row's work is undone; 'ruby', already in, stays.",
    },
    {
        "prompt": "What does this print?",
        "code": (
            "-- relics\n"
            "--  name  | power\n"
            "--  Orb   | 5\n"
            "--  Ring  | 2\n"
            "--  Crown | 3\n"
            "DECLARE\n"
            "  name VARCHAR2(10) := 'Orb';\n"
            "BEGIN\n"
            "  DELETE FROM relics WHERE name = name;\n"
            "  DBMS_OUTPUT.PUT_LINE(SQL%ROWCOUNT);\n"
            "END;"
        ),
        "setup": (
            "CREATE TABLE relics (name VARCHAR2(10), power NUMBER);\n"
            "INSERT INTO relics VALUES ('Orb', 5);\n"
            "INSERT INTO relics VALUES ('Ring', 2);\n"
            "INSERT INTO relics VALUES ('Crown', 3);\n"
            "COMMIT;"
        ),
        "options": ["3", "1", "0", "Error"],
        "answer": "3",
        "explain": "Inside a SQL statement, a column name wins over a PL/SQL variable of the same name. So "
                   "name = name compares the column with itself: every row goes.",
    },
    {
        "prompt": "What does this print?",
        "code": (
            "-- gems (name): Ruby, Opal, Jade, Onyx, Pearl\n"
            "DECLARE\n"
            "  CURSOR c IS SELECT name FROM gems;\n"
            "  TYPE name_list IS TABLE OF gems.name%TYPE;\n"
            "  batch name_list;\n"
            "  n NUMBER := 0;\n"
            "BEGIN\n"
            "  OPEN c;\n"
            "  LOOP\n"
            "    FETCH c BULK COLLECT INTO batch LIMIT 2;\n"
            "    EXIT WHEN c%NOTFOUND;\n"
            "    n := n + batch.COUNT;\n"
            "  END LOOP;\n"
            "  DBMS_OUTPUT.PUT_LINE(n);\n"
            "END;"
        ),
        "setup": (
            "CREATE TABLE gems (name VARCHAR2(10));\n"
            "INSERT INTO gems VALUES ('Ruby');\n"
            "INSERT INTO gems VALUES ('Opal');\n"
            "INSERT INTO gems VALUES ('Jade');\n"
            "INSERT INTO gems VALUES ('Onyx');\n"
            "INSERT INTO gems VALUES ('Pearl');\n"
            "COMMIT;"
        ),
        "options": ["4", "5", "6", "2"],
        "answer": "4",
        "explain": "After a BULK COLLECT ... LIMIT fetch, %NOTFOUND is TRUE whenever it got fewer rows "
                   "than the limit, so the last batch (1 row) is never counted.",
    },
]


# ------------------------------------------------------------------
# Scenes: each has a banner, a picture (static/img/adventure/, shared with the Python game
# but for the door and the boss) and a description of it
# ------------------------------------------------------------------

SCENES = {
    "start": ("The Lost Package of Oraclia", "title.webp",
              "A moonlit jungle valley wrapped in mist, a golden temple glowing on a far hilltop"),
    "forest": ("The Forest of Nested Blocks", "forest.webp",
               "Sunbeams falling through towering trees onto a stream, ferns and one giant mossy tree"),
    "waterfall": ("The Falls of LOOP", "waterfall.webp",
                  "A roaring waterfall crashing into a green pool between mossy cliffs, a fallen log high "
                  "across the gorge"),
    "tree": ("The Top of the Giant Tree", "tree.webp",
             "A great owl on a mossy branch above a sea of mist at sunrise, a golden temple glinting in "
             "the distance"),
    "cave": ("The Caverns of DUAL", "cave.webp",
             "A dark cave mouth framed by carved stone serpents, a torch burning beside it"),
    "dark": ("The Pit of NO_DATA_FOUND", "pit.webp",
             "A deep pit in the floor of a rocky tunnel, the cave entrance glowing far behind"),
    "glyph": ("The Door of Exceptions", "glyph-door-pl-sql.webp",
              "A massive stone door glowing with a block of PL/SQL, BEGIN, EXCEPTION and END, fire bowls "
              "burning on either side"),
    "castle": ("The Ruins of Castle Ada", "castle.webp",
               "A ruined castle on a misty hilltop under a full moon, torches lighting the stone path that "
               "winds up to it"),
    "gate": ("The Castle Gate", "castle-gate.webp",
             "A great arched gate with a raised iron portcullis, griffin banners and blazing torches on "
             "ivy-covered walls"),
    "hall": ("The Hall of Packages", "great-hall.webp",
             "A ruined great hall of broken gothic arches, torches flickering beside an empty throne at "
             "the top of worn steps"),
    "ramparts": ("The Castle Ramparts", "ramparts.webp",
                 "Torch-lit battlements under a full moon, stone towers rising above a misty valley"),
    "gallery": ("The Moonlit Gallery", "gallery.webp",
                "A stone gallery high in a tower, ivy twisting around its pillars, the full moon over a "
                "misty valley beyond the balustrade"),
    "temple": ("The Temple of the Golden Package", "temple.webp",
               "A torch-lit temple hall leading to a golden vault door guarded by two stone serpents, a "
               "jeweled chest by the path"),
    "victory": ("The Treasure Is Yours!", "treasure.webp",
                "The Golden Package: a glowing golden orb wrapped by a serpent, on a stone pedestal among "
                "gold and gems"),
    # The bonus dragons (see DRAGONS): the Python game's, and its pictures.
    "dragon-emerald": ("The Emerald Dragon", "dragon-emerald.webp",
                       "A green dragon asleep in a cave, curled around an open treasure chest full of gold "
                       "and emeralds"),
    "dragon-ember": ("The Ember Dragon", "dragon-ember.webp",
                     "A red dragon asleep in a fiery cave around a treasure chest of gold and rubies, a "
                     "sword and a crown beside it"),
    "dragon-frost": ("The Frost Dragon", "dragon-frost.webp",
                     "A blue dragon asleep in an ice cave, its treasure chest full of gold and glowing "
                     "sapphires"),
    "dragon-pearl": ("The Pearl Dragon", "dragon-pearl.webp",
                     "A white dragon asleep in a sunlit forest beside a treasure chest of gold, diamonds "
                     "and a silver crown"),
    "dragon-amethyst": ("The Amethyst Dragon", "dragon-amethyst.webp",
                        "A purple dragon coiled around a treasure chest of gold and glowing amethysts in a "
                        "violet forest"),
    "dragon-autumn": ("The Autumn Dragon", "dragon-autumn.webp",
                      "A copper dragon asleep among autumn leaves beside a treasure chest of gold and a "
                      "golden goblet"),
    "dragon-gold": ("The Golden Dragon", "dragon-gold.webp",
                    "A golden dragon asleep on a heap of gold coins beside a treasure chest in a torch-lit "
                    "castle hall"),
    "dragon-silver": ("The Silver Dragon", "dragon-silver.webp",
                      "A silver dragon asleep in a castle hall beside a chest of silver and diamonds, a "
                      "knight's helmet and a sword"),
    "dragon-shadow": ("The Shadow Dragon", "dragon-shadow.webp",
                      "A black dragon asleep in a castle hall around a chest of gold and rubies, a jeweled "
                      "crown at its feet"),
    # The final boss (see BOSS_QUESTIONS), from its own picture (see tools/make-adventure-images.py).
    "boss": ("The Mutating Table", "mutating-table.webp",
             "The Mutating Table: a crowned monster with writhing tentacles whose body is a glowing "
             "database table, fangs bared, waving scrolls reading ORA-04091 and CREATE TRIGGER beside a "
             "stack of PL/SQL books"),
    "game_over": ("ORA-01403: No Data Found", "game-over.webp",
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
    """A PL/SQL challenge: the explorer picks an answer (moves "a" to "d")."""
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
        self.final = final          # it completes every path on every level: after its win, the boss awaits
        self.boss = None            # the final boss's question: "won" or "lost" once answered
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
        (or the boss has been faced, which ends everything)."""
        if self.result == "win" and self.prompt is None and self.dragon is None and self.boss is None:
            return DRAGONS.get((self.player["difficulty"], self.path))
        return None

    def boss_awaits(self):
        """After the win that completes every path on every level: the boss, until faced."""
        return self.final and self.result == "win" and self.prompt is None and self.boss is None

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
    quest (the one that completes every path on every level) can then face the final boss:
    the move BOSS_MOVE, then the answer."""
    quest = Quest(name, difficulty, seed, carried, only_path, skip_questions, version, final)
    game = start_game(quest)
    quest.prompt = next(game)
    for move in moves:
        battle = (dragon_battle if move == DRAGON_MOVE and quest.dragon_awaits()
                  else boss_battle if move == BOSS_MOVE and quest.boss_awaits() else None)
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
# PL/SQL challenges
# ------------------------------------------------------------------

def draw_question(quest):
    """Take the next question from the player's deck, reshuffling when it runs out. The deck
    holds question numbers (places in QUESTIONS; the quest's game version says how many),
    and every question drawn is noted in quest.asked."""
    player = quest.player
    if not player["questions"]:
        every = range(QUESTION_COUNTS[quest.version])
        # A path not taken yet starts with a deck of the questions the level's earlier paths
        # didn't ask. A quest asks at most 6, so a level's 20 questions are enough for all
        # three paths.
        unasked = [number for number in every if number not in quest.skip_questions] if not quest.asked else []
        player["questions"] = unasked or list(every)
        quest.rng.shuffle(player["questions"])
    number = player["questions"].pop()
    quest.asked.append(number)
    return QUESTIONS[player["difficulty"]][number]


def ask_question(quest, challenger, question=None, points=CORRECT_ANSWER_POINTS, reason="correct answer"):
    """Ask one PL/SQL question: the next from the deck, or `question` (a dragon's or the
    boss's). Returns True if the player answers correctly, and earns them `points`."""
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
        # A winner going back for a path they didn't take, score and all.
        quest.narrate(f"Welcome back, {quest.player['name']}! You return to the edge of "
                      f"Oraclia with {quest.carried} points from your last quest, wondering "
                      "what waits down the way you didn't take. This time you turn toward "
                      f"{PATH_SIGHTS[quest.only_path]}"
                      f"{', where new riddles await' if quest.skip_questions else ''}.")
        yield Choice([PATHS[quest.only_path]])
        choice = str(list(PATHS).index(quest.only_path) + 1)
    else:
        if quest.carried:
            # A winner carrying their score up to the next level.
            quest.narrate(f"Welcome back, {quest.player['name']}! You return to the edge of "
                          f"Oraclia with {quest.carried} points from your last quest. Word of "
                          "your success has reached the guardians, and their riddles will be "
                          "harder this time. " + "Three paths lie before you once more: the Forest of "
                                                 "Nested Blocks, the Caverns of DUAL and the trail to the "
                                                 "Ruins of Castle Ada.")
        else:
            quest.narrate(f"Welcome, {quest.player['name']}! You arrive at the edge of Oraclia "
                          "with nothing but a backpack and your wits. " + "Three paths lie before you: the "
                                                                          "Forest of Nested Blocks, where "
                                                                          "every tree grows inside "
                                                                          "another; the Caverns of DUAL, "
                                                                          "where every echo comes back "
                                                                          "exactly once; and a torch-lit "
                                                                          "trail that climbs to the Ruins "
                                                                          "of Castle Ada, whose builders "
                                                                          "taught Oraclia its blocks.")
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
    quest.narrate("Towering trees close in around you, each one growing inside a bigger one, BEGIN inside "
                  "BEGIN, END after END. To your left, a river murmurs through the ferns. To your right "
                  "stands an ancient tree so tall its top disappears into the mist. From up there, you "
                  "could see for miles.")
    choice = yield Choice(["Follow the river", "Climb the giant tree"])
    if choice == "1":
        return (yield from river_route(quest))
    return (yield from tree_route(quest))


def river_route(quest):
    """The river leads to a waterfall and its guardian."""
    quest.banner("waterfall")
    quest.narrate("You follow the river until it plunges over a cliff at the Falls of LOOP, which nobody "
                  "has ever told to EXIT. The water swirls, rises, and takes the shape of a towering "
                  'figure: the River Guardian. "None may pass without answering my riddle," it booms.')
    if not (yield from face_challenge(quest, "The River Guardian")):
        return game_over(quest, "The Guardian's patience runs dry. A great wave sweeps you downstream, far "
                                "away from the treasure.")

    quest.narrate("The Guardian bows and places a shimmering pearl in your hand, shaped exactly like the "
                  "river that made it.")
    collect_relic(quest, "Pearl of %TYPE")
    quest.narrate("It points a watery finger at a dark gap hidden behind the waterfall. Nearby, a fallen "
                  "log covered in slick green moss stretches across the gorge. It looks like a quicker way "
                  "across.")
    choice = yield Choice(["Slip behind the waterfall, as the Guardian showed you",
                           "Cross the gorge on the mossy log"])
    if choice == "1":
        add_points(quest, WISE_CHOICE_POINTS, "wise choice")
        quest.narrate("Behind the curtain of water, a hidden tunnel leads you straight to the steps of an "
                      "ancient temple.")
        return (yield from temple_vault(quest))
    return game_over(quest, "Halfway across, your boot slips on the moss. You tumble into the rapids and "
                            "are carried far from the treasure. Somewhere behind you, the Guardian sighs.")


def tree_route(quest):
    """The giant tree, where a wise owl guards the safe way to the temple."""
    quest.banner("tree")
    quest.narrate("You climb branch by branch until you break through the mist. Far to the east, a golden "
                  'temple roof glints above the trees. A great grey owl lands beside you and blinks. "Hoo! '
                  "Every branch of this tree is a block inside a block, and a name declared further in "
                  "hides the same name further out. Only those who know which is which may learn the safe "
                  'way down."')
    if not (yield from face_challenge(quest, "The Wise Owl")):
        return game_over(quest, "The owl ruffles its feathers and flies away. As you reach after it, the "
                                "branch beneath you snaps...")

    quest.narrate('"Well reasoned!" hoots the owl, and it plucks a feather for you.')
    collect_relic(quest, "Owl Feather")
    quest.narrate('"Now listen closely. The swamp below is the shortest way to the temple, but it swallows '
                  'the careless. The vines are slow, but strong."')
    choice = yield Choice(["Swing along the vines toward the temple",
                           "Climb down and take the swamp shortcut"])
    if choice == "1":
        add_points(quest, WISE_CHOICE_POINTS, "wise choice")
        quest.narrate("Vine by vine, you swing through the canopy like a jungle acrobat and land softly on "
                      "the temple steps.")
        return (yield from temple_vault(quest))
    return game_over(quest, "Three steps into the swamp, the mud grabs your boots. The harder you "
                            "struggle, the deeper you sink. You should have listened to the owl!")


# ------------------------------------------------------------------
# The cave
# ------------------------------------------------------------------

def cave_path(quest):
    """The cave: light a torch or proceed in the dark."""
    quest.banner("cave")
    quest.narrate("Cold air flows from the cave mouth, carrying a faint hissing sound. Stone serpents coil "
                  "around the entrance, and above them one word is carved: DUAL. Call into the cave and "
                  "your echo comes back exactly once, never twice and never not at all. Just inside, you "
                  "find an old torch and a flint. Lighting it would help you see, but the light might also "
                  "wake whatever is hissing in the dark...")
    choice = yield Choice(["Light the torch", "Proceed in the dark"])
    if choice == "1":
        add_points(quest, WISE_CHOICE_POINTS, "wise choice")
        quest.narrate("The torch flares to life. Good thing, too: the floor ahead is riddled with deep "
                      "pits! The hissing, you realize, is only wind whistling through cracks in the rock.")
        return (yield from glyph_door(quest))
    return (yield from dark_tunnel(quest))


def dark_tunnel(quest):
    """Going on without light is a setback that costs a life, or ends the quest."""
    quest.banner("dark")
    quest.narrate("You creep forward in total darkness, one hand on the cold, damp wall. Suddenly the "
                  "ground vanishes beneath your feet and you tumble into the Pit of NO_DATA_FOUND, where "
                  "you SELECT INTO the dark and nothing comes back!")
    if not lose_life(quest):
        return game_over(quest, "The pit is far too deep to climb out of without light, and no handler is "
                                "there to catch you. Your quest ends here, in the dark.")

    # A pause here, so the pit gets its moment on screen.
    yield Choice(["Climb out of the pit"])
    quest.narrate("Bruised but alive, you claw your way out and crawl back to the entrance. This time you "
                  "light the torch. Lesson learned: always keep a WHEN NO_DATA_FOUND ready! In its glow "
                  "you can see the floor is riddled with pits.")
    return (yield from glyph_door(quest))


def glyph_door(quest):
    """Deep in the cave, a door sealed with a PL/SQL puzzle."""
    quest.banner("glyph")
    quest.narrate("You weave between the pits until the tunnel ends at a massive stone door: the Door of "
                  "Exceptions. Glowing glyphs crawl across its surface and arrange themselves into a block "
                  "of PL/SQL: BEGIN, a test, and an EXCEPTION section waiting for whatever goes wrong.")
    if not (yield from face_challenge(quest, "The Door of Exceptions")):
        return game_over(quest, "The glyphs flash red: an unhandled exception. With a deep rumble the "
                                "tunnel behind you seals shut, and your torch flickers out...")

    quest.narrate("The glyphs flash gold and the door grinds open. A small carved tablet falls from the "
                  "wall at your feet, with -20000 on its face, the first of the numbers Oraclia keeps for "
                  "errors of your own.")
    collect_relic(quest, "Tablet of -20000")
    quest.narrate("Beyond the door the tunnel splits in two. From the left drifts warm air and a faint "
                  "golden glow. The right tunnel is cold, its walls marked with fresh, deep claw "
                  "scratches, and something in there is growling.")
    choice = yield Choice(["Take the left tunnel toward the golden glow",
                           "Take the right tunnel past the claw marks"])
    if choice == "1":
        add_points(quest, WISE_CHOICE_POINTS, "wise choice")
        quest.narrate("The golden glow grows brighter with every step until you emerge at the heart of an "
                      "ancient temple.")
        return (yield from temple_vault(quest))
    return game_over(quest, "The claw marks belong to a very large, very grumpy cave bear who does not "
                            "appreciate visitors. You flee all the way back to the entrance, your quest in "
                            "ruins.")


# ------------------------------------------------------------------
# The castle
# ------------------------------------------------------------------

def castle_path(quest):
    """The castle ruins: the great gate or the ramparts."""
    quest.banner("castle")
    quest.narrate("A winding stone trail climbs out of the mist to the Ruins of Castle Ada. Its builders "
                  "spoke a stern language of BEGIN and END, and when the priests of Oraclia made their "
                  "own, they borrowed its bones. Torches still burn along the way. The trail ends at the "
                  "great gate. Beside it, a crumbling stair climbs the outer wall toward the ramparts.")
    choice = yield Choice(["Follow the torches to the great gate",
                           "Climb the crumbling stair to the ramparts"])
    if choice == "1":
        return (yield from castle_gate(quest))
    return (yield from castle_ramparts(quest))


def castle_gate(quest):
    """The gate's ghostly knight, then the great hall and its two ways on."""
    quest.banner("gate")
    quest.narrate("Golden griffins glare down from tattered banners as you reach the gate. The iron "
                  "portcullis is raised, but as you step beneath it a ghostly knight in rusted armor "
                  'drifts out of the stone. "Halt! None may enter the Hall of Packages without EXECUTE. '
                  'Prove you are a true coder of Oraclia."')
    if not (yield from face_challenge(quest, "The Ghost Knight")):
        return game_over(quest, "The ghost knight raises its sword and the portcullis crashes down. You "
                                "are left outside in the dark, far from the treasure.")

    quest.narrate("The knight lowers its sword and presses a cold silver ring into your palm.")
    collect_relic(quest, "Knight's Signet")
    quest.banner("hall")
    quest.narrate("Beyond the gate lies the Hall of Packages, its arches broken and open to the sky. Every "
                  "alcove holds two stone books: a spec that anyone may read, and a body that only its "
                  "owner knows. Torches flicker beside an empty throne. Behind it, a narrow passage glows "
                  "with a faint golden light. To one side, a grand staircase climbs into the dark, its "
                  "steps cracked and crumbling.")
    choice = yield Choice(["Take the glowing passage behind the throne",
                           "Climb the crumbling grand staircase"])
    if choice == "1":
        add_points(quest, WISE_CHOICE_POINTS, "wise choice")
        quest.narrate("The passage winds down beneath the castle and comes out on the steps of an ancient "
                      "temple.")
        return (yield from temple_vault(quest))
    return game_over(quest, "Halfway up, the staircase gives way beneath your feet. You tumble down in a "
                            "cloud of dust, and the castle keeps its secrets.")


def castle_ramparts(quest):
    """The ramparts' stone gargoyle, then the moonlit gallery high in a tower."""
    quest.banner("ramparts")
    quest.narrate("You climb onto the battlements. The moon hangs over a sea of mist and the wind howls "
                  "between the towers. On the wall ahead crouches a stone gargoyle. As you come near, its "
                  'eyes crack open and glow. "Answer me, climber, or take the short way down."')
    if not (yield from face_challenge(quest, "The Stone Gargoyle")):
        return game_over(quest, "The gargoyle spreads its stone wings, and one great gust sweeps you off "
                                "the wall and into the mist.")

    quest.narrate("The gargoyle grinds out a laugh and drops a glittering stone from its claw.")
    collect_relic(quest, "Gargoyle's Eye")
    quest.banner("gallery")
    quest.narrate("The ramparts lead into a tall tower and up to a moonlit gallery, its pillars numbered "
                  "1, 2, 3 in the order you pass them, like ROWNUM. Far below the balustrade, a golden "
                  "temple roof glints through the mist. Ivy as thick as rope hangs over the edge, and a "
                  "spiral stair winds down inside the tower.")
    choice = yield Choice(["Take the spiral stair down inside the tower",
                           "Climb down the ivy from the gallery"])
    if choice == "1":
        add_points(quest, WISE_CHOICE_POINTS, "wise choice")
        quest.narrate("Round and round you go, down and down, until a small door at the foot of the tower "
                      "opens beside the temple steps.")
        return (yield from temple_vault(quest))
    return game_over(quest, "The ivy is older than it looks. It tears loose with a snap, and you drop into "
                            "the mist far below.")


# ------------------------------------------------------------------
# The temple and the end of the quest
# ------------------------------------------------------------------

def temple_vault(quest):
    """The final challenge: an optional jeweled chest, then the vault's two locks."""
    quest.banner("temple")
    quest.narrate("Torches burst into flame as you enter the temple's great hall. At the far end stands "
                  "the vault, its door sealed by two locks, each watched by a stone serpent: the Spec Lock "
                  "and the Body Lock. Beside the path sits a small jeweled chest with a riddle carved into "
                  "its lid. Solving it would earn you a rare relic, but a wrong answer will cost you a "
                  "life.")
    choice = yield Choice(["Try to open the jeweled chest",
                           "Ignore the chest and head for the vault"])
    if choice == "1":
        if (yield from ask_question(quest, "The Jeweled Chest")):
            quest.narrate("Click! The lid springs open, revealing a ring set with a blazing ruby, PRAGMA "
                          "AUTONOMOUS_TRANSACTION engraved inside the band: it keeps its own promises, "
                          "whatever becomes of yours.")
            collect_relic(quest, "Autonomous Ring")
        else:
            if not lose_life(quest):
                return game_over(quest, "A dart coated in sleeping venom shoots from the lock. You doze "
                                        "off just steps away from the treasure...")
            quest.narrate("A tiny dart shoots from the lock and stings your hand. "
                          "The chest stays shut.")
    else:
        quest.narrate("You leave the chest alone. Sometimes the wisest move is not "
                      "to gamble.")

    quest.narrate("You approach the vault door. The eyes of the stone serpents begin to glow. The Spec "
                  "Lock shows anyone what it expects; the Body Lock keeps its secrets, and opens only for "
                  "those who passed the first.")
    for lock in LOCKS:
        if not (yield from face_challenge(quest, lock)):
            return game_over(quest, "The serpent's eyes flash red and the vault seals itself forever. The "
                                    "treasure remains lost.")
        quest.note("info", f"{lock} slides open!")
    return victory(quest)


# The vault's two locks, in the order they're faced.
LOCKS = ["The Spec Lock", "The Body Lock"]


def victory(quest):
    """The vault opens! Award the end-of-quest bonuses."""
    player = quest.player
    quest.banner("victory")
    quest.narrate("The vault door swings open with a groan. Inside, resting on a pedestal of black stone, "
                  "sits the legendary Golden Package, a golden orb in a serpent's coils, its spec on the "
                  "outside and its body sealed within, humming with ancient power. Congratulations, "
                  "{name}! Your name will be carved among the great coders of Oraclia.".format(name=player["name"]))
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


def boss_battle(quest):
    """The final boss, for a winner who has completed every path on every level: one of the
    nine ultimate questions, picked at random. Right: the title of PL/SQL Master and
    BOSS_POINTS besides. Wrong: all is lost, the score falls to zero. Returns "win", since
    the quest that led here was won."""
    quest.banner("boss")
    quest.narrate("You have walked every path in Oraclia. As you leave the temple for the last time, its "
                  "floor slides open onto a stair that winds down into a crypt, where a vast table "
                  "crouches on clawed feet. Its rows are moving, writhing and rewriting themselves even as "
                  "you watch; tentacles thrash from beneath it, and a fanged mouth gapes where its data "
                  "should be. This is the Mutating Table, crowned king of every trigger that ever tried to "
                  'read it. "Every path, every level," it grinds. "One question remains. Answer it, and '
                  'you are a PL/SQL Master. Fail, and ORA-04091 takes everything."')
    question = quest.rng.choice(BOSS_QUESTIONS)
    if (yield from ask_question(quest, "The Mutating Table", question, BOSS_POINTS, "PL/SQL Master")):
        quest.boss = "won"
        quest.narrate("The table's rows fall still at last, its tentacles curl away, and it bows its "
                      'crowned head. "Well answered, Master." From this day on, the coders of Oraclia will '
                      "know you by your new title.")
        quest.note("relic", "You are a PL/SQL Master!")
    else:
        quest.boss = "lost"
        quest.player["score"] = 0
        quest.narrate('The table heaves. "ORA-04091: table ORACLIA.TREASURE is mutating, trigger/function '
                      'may not see it." Every coin, relic and point you carried mutates into nothing, and '
                      "you wake at the edge of Oraclia with nothing but a backpack and your wits.")
        quest.note("life", "All is lost! Your score falls to 0.")
    return "win"


def game_over(quest, message):
    """End the quest with a failure message."""
    quest.narrate(message)
    quest.banner("game_over")
    return "lose"
