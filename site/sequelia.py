"""
The Lost Standard of Sequelia
-----------------------------
The ANSI SQL adventure: a copy of the Python game (pythonia.py), the same story in the same
places, played the same way, but with its own words and every riddle about standard SQL, the
SQL of the ISO/ANSI standard that any database keeping the standard understands.

Like pythonia.py:
- Wherever a console game would wait for input(), these functions *yield* a prompt (a
  Choice or a Question) and the page's buttons send the explorer's answer back in.
- A quest is saved as its random seed plus the moves made so far, and replay() plays it
  again from the start with those moves for every page.
- A winner can carry their score on: to the next level (next_level()), or down a path not
  taken yet (paths_left()), without the questions the level's earlier paths asked.
- After a win, the explorer may wake that path and level's dragon (DRAGONS,
  dragon_battle()) for one bonus riddle.
- An explorer who completes every path on every level may face the Cartesian Beast, the
  final boss (boss_battle()): one of the nine hardest questions (BOSS_QUESTIONS), for the
  title of ANSI SQL Master, or the loss of their whole score.

Every answer here was checked by running its query on two databases that keep the standard,
PostgreSQL and DuckDB (tools/check-sql-questions.py).
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
        "topics": "SELECT, WHERE, NULL, LIKE, BETWEEN, CASE, COALESCE, ORDER BY",
    },
    "medium": {
        "lives": 2,
        "multiplier": 2,
        "topics": "joins, GROUP BY, HAVING, subqueries, UNION, CTEs, string functions",
    },
    "hard": {
        "lives": 1,
        "multiplier": 3,
        "topics": "window functions, recursion, NULL logic, ROLLUP, LATERAL, transactions, MERGE",
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
    "forest": "Explore the Relational Forest",
    "cave": "Enter the Subquery Caverns",
    "castle": "Climb to the Ruins of Castle Codd",
}
PATH_NAMES = {
    "forest": "the Relational Forest",
    "cave": "the Subquery Caverns",
    "castle": "the Ruins of Castle Codd",
}
PATH_SIGHTS = {
    "forest": "the Relational Forest, where every tree is joined to another",
    "cave": "the Subquery Caverns, a cave inside a cave inside a cave",
    "castle": "the torch-lit trail that climbs to the Ruins of Castle Codd",
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
# ANSI SQL challenges for each difficulty level
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
            "prompt": "What does this query return?",
            "code": (
                "-- relics\n"
                "--  name  | might\n"
                "--  Orb   | 5\n"
                "--  Ring  | NULL\n"
                "--  Crown | 3\n"
                "SELECT COUNT(*), COUNT(might) FROM relics;"
            ),
            "setup": (
                "CREATE TABLE relics (name VARCHAR(20), might INTEGER);\n"
                "INSERT INTO relics VALUES ('Orb', 5), ('Ring', NULL), ('Crown', 3);"
            ),
            "options": ["3 2", "3 3", "2 2", "2 3"],
            "answer": "3 2",
            "explain": "COUNT(*) counts rows, but COUNT(might) counts only the rows where might is not "
                       "NULL.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- gems\n"
                "--  name  | carats\n"
                "--  Ruby  | 5\n"
                "--  Opal  | NULL\n"
                "--  Pearl | 2\n"
                "SELECT name FROM gems WHERE carats <> 5 ORDER BY name;"
            ),
            "setup": (
                "CREATE TABLE gems (name VARCHAR(20), carats INTEGER);\n"
                "INSERT INTO gems VALUES ('Ruby', 5), ('Opal', NULL), ('Pearl', 2);"
            ),
            "options": ["Pearl", "Opal, Pearl", "Opal, Pearl, Ruby", "No rows"],
            "answer": "Pearl",
            "explain": "Comparing NULL with anything gives UNKNOWN, not TRUE, and WHERE keeps only TRUE "
                       "rows. So Opal is dropped along with Ruby.",
        },
        {
            "prompt": "Which condition finds the relics whose might is NULL?",
            "options": ["might IS NULL", "might = NULL", "might = ''", "might = 0"],
            "answer": "might IS NULL",
            "explain": "NULL means 'unknown', so might = NULL is never true, not even for a NULL. The IS "
                       "NULL predicate is the way to test for it.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- chests\n"
                "--  id | gold\n"
                "--  1  | 10\n"
                "--  2  | 20\n"
                "--  3  | 30\n"
                "--  4  | 40\n"
                "SELECT COUNT(*) FROM chests\n"
                "WHERE gold BETWEEN 20 AND 40;"
            ),
            "setup": (
                "CREATE TABLE chests (id INTEGER, gold INTEGER);\n"
                "INSERT INTO chests VALUES (1, 10), (2, 20), (3, 30), (4, 40);"
            ),
            "options": ["3", "2", "1", "4"],
            "answer": "3",
            "explain": "BETWEEN includes both ends: it means gold >= 20 AND gold <= 40, so 20, 30 and 40 "
                       "all count.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- relics\n"
                "--  name\n"
                "--  Orb\n"
                "--  Ring\n"
                "--  Crown\n"
                "--  Rune\n"
                "SELECT name FROM relics\n"
                "WHERE name LIKE '_r%'\n"
                "ORDER BY name;"
            ),
            "setup": (
                "CREATE TABLE relics (name VARCHAR(20));\n"
                "INSERT INTO relics VALUES ('Orb'), ('Ring'), ('Crown'), ('Rune');"
            ),
            "options": ["Crown, Orb", "Ring, Rune", "Crown, Orb, Ring, Rune", "No rows"],
            "answer": "Crown, Orb",
            "explain": "In LIKE, _ matches exactly one character and % matches any number. So '_r%' means "
                       "'the second letter is r'.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- gems\n"
                "--  name     | color | worth\n"
                "--  Ruby     | red   | 5\n"
                "--  Sapphire | blue  | 8\n"
                "--  Lapis    | blue  | 20\n"
                "--  Garnet   | red   | 15\n"
                "SELECT name FROM gems\n"
                "WHERE color = 'red' OR color = 'blue' AND worth > 10\n"
                "ORDER BY name;"
            ),
            "setup": (
                "CREATE TABLE gems (name VARCHAR(20), color VARCHAR(10), worth INTEGER);\n"
                "INSERT INTO gems VALUES ('Ruby', 'red', 5), ('Sapphire', 'blue', 8),\n"
                "  ('Lapis', 'blue', 20), ('Garnet', 'red', 15);"
            ),
            "options": ["Garnet, Lapis, Ruby", "Garnet, Lapis", "Lapis", "Garnet, Lapis, Ruby, Sapphire"],
            "answer": "Garnet, Lapis, Ruby",
            "explain": "AND binds tighter than OR, so this means red OR (blue AND worth > 10). Every red "
                       "gem passes, whatever its worth.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- gems\n"
                "--  name   | color\n"
                "--  Ruby   | red\n"
                "--  Garnet | red\n"
                "--  Lapis  | blue\n"
                "--  Quartz | NULL\n"
                "SELECT COUNT(DISTINCT color) FROM gems;"
            ),
            "setup": (
                "CREATE TABLE gems (name VARCHAR(20), color VARCHAR(10));\n"
                "INSERT INTO gems VALUES ('Ruby', 'red'), ('Garnet', 'red'),\n"
                "  ('Lapis', 'blue'), ('Quartz', NULL);"
            ),
            "options": ["2", "3", "4", "1"],
            "answer": "2",
            "explain": "DISTINCT removes the repeated red, and like other aggregates COUNT skips the NULL: "
                       "red and blue make 2.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- gems\n"
                "--  color | size\n"
                "--  red   | small\n"
                "--  red   | large\n"
                "--  blue  | small\n"
                "--  red   | small\n"
                "SELECT DISTINCT color, size FROM gems\n"
                "ORDER BY color, size;"
            ),
            "setup": (
                "CREATE TABLE gems (color VARCHAR(10), size VARCHAR(10));\n"
                "INSERT INTO gems VALUES ('red', 'small'), ('red', 'large'),\n"
                "  ('blue', 'small'), ('red', 'small');"
            ),
            "options": [
                "blue small, red large, red small",
                "blue small, red small",
                "blue, red",
                "blue small, red large",
            ],
            "answer": "blue small, red large, red small",
            "explain": "DISTINCT works on the whole row, not just the first column. Only the second red "
                       "small is a true duplicate.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- knights\n"
                "--  name | level\n"
                "--  Ada  | 3\n"
                "--  Bors | 5\n"
                "--  Cai  | 3\n"
                "SELECT name FROM knights\n"
                "ORDER BY level DESC, name;"
            ),
            "setup": (
                "CREATE TABLE knights (name VARCHAR(20), level INTEGER);\n"
                "INSERT INTO knights VALUES ('Ada', 3), ('Bors', 5), ('Cai', 3);"
            ),
            "options": ["Bors, Ada, Cai", "Bors, Cai, Ada", "Ada, Cai, Bors", "Cai, Ada, Bors"],
            "answer": "Bors, Ada, Cai",
            "explain": "DESC applies only to level, so Bors (5) comes first. The tie at 3 is broken by "
                       "name, which sorts ascending by default.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- purses\n"
                "--  owner | gold\n"
                "--  Ada   | 150\n"
                "SELECT CASE WHEN gold > 50 THEN 'comfortable'\n"
                "            WHEN gold > 100 THEN 'rich'\n"
                "            ELSE 'poor'\n"
                "       END\n"
                "FROM purses;"
            ),
            "setup": (
                "CREATE TABLE purses (owner VARCHAR(20), gold INTEGER);\n"
                "INSERT INTO purses VALUES ('Ada', 150);"
            ),
            "options": ["comfortable", "rich", "poor", "NULL"],
            "answer": "comfortable",
            "explain": "CASE takes the first WHEN that is true and stops there. 150 > 50 is true, so "
                       "'rich' is never reached.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- relics\n"
                "--  name | might\n"
                "--  Ring | 2\n"
                "SELECT CASE WHEN might > 5 THEN 'mighty' END\n"
                "FROM relics;"
            ),
            "setup": (
                "CREATE TABLE relics (name VARCHAR(20), might INTEGER);\n"
                "INSERT INTO relics VALUES ('Ring', 2);"
            ),
            "options": ["NULL", "mighty", "(an empty string)", "Error"],
            "answer": "NULL",
            "explain": "A CASE with no ELSE acts as if it ended ELSE NULL, so when no WHEN matches, the "
                       "result is NULL.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- knights\n"
                "--  name | nickname | title\n"
                "--  Bors | NULL     | Sir\n"
                "SELECT COALESCE(nickname, title, name)\n"
                "FROM knights;"
            ),
            "setup": (
                "CREATE TABLE knights (name VARCHAR(20), nickname VARCHAR(20), title VARCHAR(20));\n"
                "INSERT INTO knights VALUES ('Bors', NULL, 'Sir');"
            ),
            "options": ["Sir", "Bors", "NULL", "Sir Bors"],
            "answer": "Sir",
            "explain": "COALESCE gives back its first argument that is not NULL. nickname is NULL, so it's "
                       "title: Sir.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- knights\n"
                "--  name | title\n"
                "--  Bors | NULL\n"
                "SELECT name || ' the ' || title FROM knights;"
            ),
            "setup": (
                "CREATE TABLE knights (name VARCHAR(20), title VARCHAR(20));\n"
                "INSERT INTO knights VALUES ('Bors', NULL);"
            ),
            "options": ["NULL", "Bors the", "Bors", "Error"],
            "answer": "NULL",
            "explain": "In standard SQL, joining a string to NULL with || gives NULL. Wrap the column in "
                       "COALESCE(title, '') to keep the rest.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- knights\n"
                "--  name | level\n"
                "--  Ada  | 4\n"
                "--  Bors | 9\n"
                "--  Cai  | 7\n"
                "--  Dag  | 2\n"
                "SELECT name FROM knights\n"
                "ORDER BY level DESC\n"
                "FETCH FIRST 2 ROWS ONLY;"
            ),
            "setup": (
                "CREATE TABLE knights (name VARCHAR(20), level INTEGER);\n"
                "INSERT INTO knights VALUES ('Ada', 4), ('Bors', 9), ('Cai', 7), ('Dag', 2);"
            ),
            "options": ["Bors, Cai", "Ada, Bors", "Dag, Ada", "Bors"],
            "answer": "Bors, Cai",
            "explain": "FETCH FIRST 2 ROWS ONLY is the standard way to keep the first rows after ORDER BY: "
                       "the two highest levels, 9 and 7.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- relics\n"
                "--  name\n"
                "--  Crown\n"
                "SELECT UPPER(SUBSTRING(name FROM 2 FOR 3))\n"
                "FROM relics;"
            ),
            "setup": (
                "CREATE TABLE relics (name VARCHAR(20));\n"
                "INSERT INTO relics VALUES ('Crown');"
            ),
            "options": ["ROW", "CRO", "OWN", "Row"],
            "answer": "ROW",
            "explain": "String positions start at 1, so FROM 2 FOR 3 takes the 2nd to 4th letters, 'row', "
                       "and UPPER makes them capitals.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- scrolls\n"
                "--  label\n"
                "--  **Gold**\n"
                "SELECT TRIM(BOTH '*' FROM label) FROM scrolls;"
            ),
            "setup": (
                "CREATE TABLE scrolls (label VARCHAR(20));\n"
                "INSERT INTO scrolls VALUES ('**Gold**');"
            ),
            "options": ["Gold", "*Gold*", "Gold**", "**Gold"],
            "answer": "Gold",
            "explain": "TRIM(BOTH '*' FROM ...) strips every leading and trailing *, not just one. LEADING "
                       "or TRAILING would strip only one end.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- knights\n"
                "--  name | motto\n"
                "--  Ada  | Onward\n"
                "--  Bors | ''\n"
                "--  Cai  | NULL\n"
                "SELECT name FROM knights\n"
                "WHERE motto IS NULL\n"
                "ORDER BY name;"
            ),
            "setup": (
                "CREATE TABLE knights (name VARCHAR(20), motto VARCHAR(20));\n"
                "INSERT INTO knights VALUES ('Ada', 'Onward'), ('Bors', ''), ('Cai', NULL);"
            ),
            "options": ["Cai", "Bors, Cai", "Bors", "No rows"],
            "answer": "Cai",
            "explain": "In standard SQL an empty string is a real value, just zero characters long, so "
                       "only Cai's NULL matches. (Oracle is the famous exception.)",
        },
        {
            "prompt": "Which of these starts a comment that runs to the end of the line in standard SQL?",
            "options": ["--", "#", "//", "REM"],
            "answer": "--",
            "explain": "Two hyphens start a comment that lasts to the end of the line. /* ... */ comments "
                       "can span several lines.",
        },
        {
            "prompt": "How do you write the text It's as a standard SQL string?",
            "options": ["'It''s'", "'It\\'s'", '"It\'s"', '\'It"s\''],
            "answer": "'It''s'",
            "explain": "Strings go in single quotes, and a quote inside one is written twice. Backslash "
                       "escapes are not part of standard SQL.",
        },
        {
            "prompt": 'In standard SQL, what is "Gold Coins", written in double quotes?',
            "options": [
                "A name, such as a column or table",
                "A string value",
                "A comment",
                "A syntax error",
            ],
            "answer": "A name, such as a column or table",
            "explain": "Double quotes make a delimited identifier: a name that may hold spaces and keeps "
                       "its exact case. Strings use single quotes.",
        },
    ],
    "medium": [
        {
            "prompt": "What does this query return?",
            "code": (
                "-- knights\n"
                "--  name\n"
                "--  Ada\n"
                "--  Bors\n"
                "--\n"
                "-- quests\n"
                "--  knight | quest\n"
                "--  Ada    | Grail\n"
                "--  Ada    | Dragon\n"
                "SELECT k.name, COUNT(q.quest)\n"
                "FROM knights k\n"
                "LEFT JOIN quests q ON q.knight = k.name\n"
                "GROUP BY k.name\n"
                "ORDER BY k.name;"
            ),
            "setup": (
                "CREATE TABLE knights (name VARCHAR(20));\n"
                "INSERT INTO knights VALUES ('Ada'), ('Bors');\n"
                "CREATE TABLE quests (knight VARCHAR(20), quest VARCHAR(20));\n"
                "INSERT INTO quests VALUES ('Ada', 'Grail'), ('Ada', 'Dragon');"
            ),
            "options": ["Ada 2, Bors 0", "Ada 2, Bors 1", "Ada 2", "Ada 2, Bors NULL"],
            "answer": "Ada 2, Bors 0",
            "explain": "The LEFT JOIN keeps Bors, with NULL for q.quest. COUNT(q.quest) skips that NULL, "
                       "so Bors gets 0 (COUNT(*) would have said 1).",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- knights\n"
                "--  name\n"
                "--  Ada\n"
                "--  Bors\n"
                "--  Cai\n"
                "--\n"
                "-- quests\n"
                "--  knight | done\n"
                "--  Ada    | yes\n"
                "--  Bors   | no\n"
                "SELECT k.name FROM knights k\n"
                "LEFT JOIN quests q ON q.knight = k.name\n"
                "WHERE q.done = 'yes'\n"
                "ORDER BY k.name;"
            ),
            "setup": (
                "CREATE TABLE knights (name VARCHAR(20));\n"
                "INSERT INTO knights VALUES ('Ada'), ('Bors'), ('Cai');\n"
                "CREATE TABLE quests (knight VARCHAR(20), done VARCHAR(5));\n"
                "INSERT INTO quests VALUES ('Ada', 'yes'), ('Bors', 'no');"
            ),
            "options": ["Ada", "Ada, Bors, Cai", "Ada, Cai", "Ada, Bors"],
            "answer": "Ada",
            "explain": "WHERE runs after the join. Bors's done is 'no' and Cai's is NULL, so WHERE drops "
                       "them both, and the LEFT JOIN acts like an inner join.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- vaults\n"
                "--  owner | gem\n"
                "--  Ada   | Ruby\n"
                "--  Ada   | Opal\n"
                "--\n"
                "-- purses\n"
                "--  owner | coin\n"
                "--  Ada   | Gold\n"
                "--  Ada   | Silver\n"
                "--  Ada   | Copper\n"
                "SELECT COUNT(*)\n"
                "FROM vaults v JOIN purses p ON p.owner = v.owner;"
            ),
            "setup": (
                "CREATE TABLE vaults (owner VARCHAR(20), gem VARCHAR(20));\n"
                "INSERT INTO vaults VALUES ('Ada', 'Ruby'), ('Ada', 'Opal');\n"
                "CREATE TABLE purses (owner VARCHAR(20), coin VARCHAR(20));\n"
                "INSERT INTO purses VALUES ('Ada', 'Gold'), ('Ada', 'Silver'), ('Ada', 'Copper');"
            ),
            "options": ["6", "5", "3", "2"],
            "answer": "6",
            "explain": "A join pairs every matching row with every other: each of Ada's 2 gem rows meets "
                       "each of her 3 coin rows, so 2 x 3 = 6.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- north\n"
                "--  gem\n"
                "--  Ruby\n"
                "--  Opal\n"
                "--  Jade\n"
                "--\n"
                "-- south\n"
                "--  gem\n"
                "--  Opal\n"
                "--  Jade\n"
                "--  Onyx\n"
                "SELECT COUNT(*)\n"
                "FROM north n FULL JOIN south s ON s.gem = n.gem;"
            ),
            "setup": (
                "CREATE TABLE north (gem VARCHAR(20));\n"
                "INSERT INTO north VALUES ('Ruby'), ('Opal'), ('Jade');\n"
                "CREATE TABLE south (gem VARCHAR(20));\n"
                "INSERT INTO south VALUES ('Opal'), ('Jade'), ('Onyx');"
            ),
            "options": ["4", "2", "6", "9"],
            "answer": "4",
            "explain": "Opal and Jade match (2 rows), and a FULL JOIN also keeps the unmatched rows of "
                       "both sides, Ruby and Onyx: 4 rows.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- loot\n"
                "--  kind | gold\n"
                "--  gem  | 5\n"
                "--  gem  | 8\n"
                "--  coin | 4\n"
                "--  coin | 3\n"
                "--  ring | 12\n"
                "SELECT kind, SUM(gold) FROM loot\n"
                "GROUP BY kind\n"
                "HAVING SUM(gold) > 10\n"
                "ORDER BY kind;"
            ),
            "setup": (
                "CREATE TABLE loot (kind VARCHAR(10), gold INTEGER);\n"
                "INSERT INTO loot VALUES ('gem', 5), ('gem', 8), ('coin', 4), ('coin', 3),\n"
                "  ('ring', 12);"
            ),
            "options": ["gem 13, ring 12", "ring 12", "coin 7, gem 13, ring 12", "gem 13"],
            "answer": "gem 13, ring 12",
            "explain": "HAVING filters whole groups after they are summed: gem makes 13 and ring 12, while "
                       "coin's 7 is left out.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- knights\n"
                "--  name | gold\n"
                "--  Ada  | 4\n"
                "--  Bors | NULL\n"
                "--  Cai  | 2\n"
                "SELECT AVG(gold) FROM knights;"
            ),
            "setup": (
                "CREATE TABLE knights (name VARCHAR(20), gold INTEGER);\n"
                "INSERT INTO knights VALUES ('Ada', 4), ('Bors', NULL), ('Cai', 2);"
            ),
            "options": ["3", "2", "NULL", "6"],
            "answer": "3",
            "explain": "AVG skips the NULL completely, so it's (4 + 2) / 2 = 3, not (4 + 0 + 2) / 3 = 2.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- gems\n"
                "--  name  | color\n"
                "--  Ruby  | red\n"
                "--  Opal  | NULL\n"
                "--  Lapis | blue\n"
                "--  Pearl | NULL\n"
                "SELECT color, COUNT(*) FROM gems\n"
                "GROUP BY color\n"
                "ORDER BY COUNT(*) DESC, color;"
            ),
            "setup": (
                "CREATE TABLE gems (name VARCHAR(20), color VARCHAR(10));\n"
                "INSERT INTO gems VALUES ('Ruby', 'red'), ('Opal', NULL), ('Lapis', 'blue'),\n"
                "  ('Pearl', NULL);"
            ),
            "options": [
                "NULL 2, blue 1, red 1",
                "blue 1, red 1",
                "NULL 1, NULL 1, blue 1, red 1",
                "blue 1, red 1, NULL 0",
            ],
            "answer": "NULL 2, blue 1, red 1",
            "explain": "NULL = NULL isn't true, yet GROUP BY puts all the NULLs into one group. So Opal "
                       "and Pearl are counted together.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- north\n"
                "--  gem\n"
                "--  Ruby\n"
                "--  Ruby\n"
                "--  Opal\n"
                "--\n"
                "-- south\n"
                "--  gem\n"
                "--  Opal\n"
                "--  Jade\n"
                "SELECT gem FROM north\n"
                "UNION\n"
                "SELECT gem FROM south\n"
                "ORDER BY gem;"
            ),
            "setup": (
                "CREATE TABLE north (gem VARCHAR(20));\n"
                "INSERT INTO north VALUES ('Ruby'), ('Ruby'), ('Opal');\n"
                "CREATE TABLE south (gem VARCHAR(20));\n"
                "INSERT INTO south VALUES ('Opal'), ('Jade');"
            ),
            "options": [
                "Jade, Opal, Ruby",
                "Jade, Opal, Ruby, Ruby",
                "Jade, Opal, Opal, Ruby, Ruby",
                "Opal",
            ],
            "answer": "Jade, Opal, Ruby",
            "explain": "UNION removes every duplicate in the combined result, even the two Rubys that both "
                       "came from north. UNION ALL keeps them all.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- guild_a\n"
                "--  knight\n"
                "--  Ada\n"
                "--  Bors\n"
                "--  Cai\n"
                "--\n"
                "-- guild_b\n"
                "--  knight\n"
                "--  Cai\n"
                "--  Dag\n"
                "--  Ada\n"
                "SELECT knight FROM guild_a\n"
                "INTERSECT SELECT knight FROM guild_b\n"
                "ORDER BY knight;"
            ),
            "setup": (
                "CREATE TABLE guild_a (knight VARCHAR(20));\n"
                "INSERT INTO guild_a VALUES ('Ada'), ('Bors'), ('Cai');\n"
                "CREATE TABLE guild_b (knight VARCHAR(20));\n"
                "INSERT INTO guild_b VALUES ('Cai'), ('Dag'), ('Ada');"
            ),
            "options": ["Ada, Cai", "Ada, Bors, Cai, Dag", "Bors, Dag", "Bors"],
            "answer": "Ada, Cai",
            "explain": "INTERSECT keeps only the rows that both queries return: the knights in both guilds.",
        },
        {
            "prompt": "Which is the standard SQL operator for the rows of one query that are not in "
                      "another?",
            "options": ["EXCEPT", "MINUS", "DIFFERENCE", "SUBTRACT"],
            "answer": "EXCEPT",
            "explain": "EXCEPT is the standard name, next to UNION and INTERSECT. MINUS is Oracle's older "
                       "spelling of the same thing.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- gems\n"
                "--  name   | kind | worth\n"
                "--  Ruby   | red  | 9\n"
                "--  Garnet | red  | 4\n"
                "--  Lapis  | blue | 6\n"
                "--  Iolite | blue | 7\n"
                "SELECT name FROM gems g\n"
                "WHERE worth = (SELECT MAX(worth) FROM gems x\n"
                "               WHERE x.kind = g.kind)\n"
                "ORDER BY name;"
            ),
            "setup": (
                "CREATE TABLE gems (name VARCHAR(20), kind VARCHAR(10), worth INTEGER);\n"
                "INSERT INTO gems VALUES ('Ruby', 'red', 9), ('Garnet', 'red', 4),\n"
                "  ('Lapis', 'blue', 6), ('Iolite', 'blue', 7);"
            ),
            "options": ["Iolite, Ruby", "Ruby", "Garnet, Lapis", "Iolite, Lapis, Ruby"],
            "answer": "Iolite, Ruby",
            "explain": "The subquery is correlated: it runs again for each row, finding the best worth of "
                       "that row's own kind (9 for red, 7 for blue).",
        },
        {
            "prompt": "Why does SELECT gold * 2 AS doubled FROM chests WHERE doubled > 50 fail in standard "
                      "SQL?",
            "options": [
                "WHERE is evaluated before SELECT",
                "The alias needs double quotes",
                "WHERE can't do arithmetic",
                "AS can't be used in SELECT",
            ],
            "answer": "WHERE is evaluated before SELECT",
            "explain": "Logically FROM and WHERE come before the SELECT list, so the alias doesn't exist "
                       "yet. ORDER BY comes after SELECT, so it can use it.",
        },
        {
            "prompt": "What is the standard name for a subquery written in the FROM clause, as in FROM "
                      "(SELECT ...) AS t?",
            "options": [
                "A derived table",
                "A correlated subquery",
                "A common table expression",
                "A scalar subquery",
            ],
            "answer": "A derived table",
            "explain": "A query in FROM is a derived table. A common table expression is the named kind "
                       "defined with WITH, and a scalar subquery returns one value.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- loot\n"
                "--  kind | gold\n"
                "--  gem  | 5\n"
                "--  coin | 9\n"
                "SELECT kind FROM loot\n"
                "WHERE SUM(gold) > 10\n"
                "GROUP BY kind;"
            ),
            "setup": (
                "CREATE TABLE loot (kind VARCHAR(10), gold INTEGER);\n"
                "INSERT INTO loot VALUES ('gem', 5), ('coin', 9);"
            ),
            "options": ["Error: aggregate not allowed in WHERE", "No rows", "coin", "gem"],
            "answer": "Error: aggregate not allowed in WHERE",
            "explain": "WHERE filters single rows before any groups exist, so it can't use SUM. A "
                       "condition on a group's total goes in HAVING.",
            "expect_error": True,
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- quests\n"
                "--  name  | gold | knights\n"
                "--  Grail | 10   | 0\n"
                "SELECT gold / NULLIF(knights, 0) FROM quests;"
            ),
            "setup": (
                "CREATE TABLE quests (name VARCHAR(20), gold INTEGER, knights INTEGER);\n"
                "INSERT INTO quests VALUES ('Grail', 10, 0);"
            ),
            "options": ["NULL", "0", "10", "Error: division by zero"],
            "answer": "NULL",
            "explain": "NULLIF(knights, 0) gives NULL when knights is 0, and 10 / NULL is NULL. It's the "
                       "standard way to dodge a division by zero.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- relics\n"
                "--  name  | might\n"
                "--  Orb   | 5\n"
                "--  Ring  | 1\n"
                "--  Crown | 7\n"
                "WITH strong AS (\n"
                "  SELECT name FROM relics WHERE might > 3\n"
                ")\n"
                "SELECT COUNT(*) FROM strong a CROSS JOIN strong b;"
            ),
            "setup": (
                "CREATE TABLE relics (name VARCHAR(20), might INTEGER);\n"
                "INSERT INTO relics VALUES ('Orb', 5), ('Ring', 1), ('Crown', 7);"
            ),
            "options": ["4", "2", "9", "Error"],
            "answer": "4",
            "explain": "strong holds 2 rows (Orb and Crown), and a CTE can be used more than once like a "
                       "table. Crossed with itself: 2 x 2 = 4.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- relics\n"
                "--  name\n"
                "--  Crown\n"
                "SELECT POSITION('x' IN name) FROM relics;"
            ),
            "setup": (
                "CREATE TABLE relics (name VARCHAR(20));\n"
                "INSERT INTO relics VALUES ('Crown');"
            ),
            "options": ["0", "NULL", "-1", "Error"],
            "answer": "0",
            "explain": "POSITION gives the place where the text starts, counting from 1, or 0 when it "
                       "isn't found at all.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- runes\n"
                "--  name | code\n"
                "--  Fire | XII\n"
                "SELECT CAST(code AS INTEGER) + 1 FROM runes;"
            ),
            "setup": (
                "CREATE TABLE runes (name VARCHAR(20), code VARCHAR(10));\n"
                "INSERT INTO runes VALUES ('Fire', 'XII');"
            ),
            "options": ["Error: invalid character value for cast", "NULL", "1", "XII1"],
            "answer": "Error: invalid character value for cast",
            "explain": "'XII' isn't a valid number, and the standard says a CAST that can't convert raises "
                       "an error rather than giving NULL or 0.",
            "expect_error": True,
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- chests\n"
                "--  owner | gold\n"
                "--  Ada   | 10\n"
                "--  Bors  | 20\n"
                "SELECT COUNT(*), SUM(gold) FROM chests\n"
                "WHERE gold > 50;"
            ),
            "setup": (
                "CREATE TABLE chests (owner VARCHAR(20), gold INTEGER);\n"
                "INSERT INTO chests VALUES ('Ada', 10), ('Bors', 20);"
            ),
            "options": ["0 NULL", "0 0", "No rows", "NULL NULL"],
            "answer": "0 NULL",
            "explain": "With no GROUP BY there is always one row. COUNT of no rows is 0, but SUM of no "
                       "rows is NULL, not 0.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- relics\n"
                "--  name | might\n"
                "--  Orb  | NULL\n"
                "--\n"
                "-- vault\n"
                "--  item\n"
                "--  Crown\n"
                "SELECT item FROM vault\n"
                "WHERE EXISTS (SELECT might FROM relics);"
            ),
            "setup": (
                "CREATE TABLE relics (name VARCHAR(20), might INTEGER);\n"
                "INSERT INTO relics VALUES ('Orb', NULL);\n"
                "CREATE TABLE vault (item VARCHAR(20));\n"
                "INSERT INTO vault VALUES ('Crown');"
            ),
            "options": ["Crown", "No rows", "NULL", "Error"],
            "answer": "Crown",
            "explain": "EXISTS only asks whether the subquery returns any row. It returns one (Orb's), so "
                       "EXISTS is TRUE, even though the value in it is NULL.",
        },
    ],
    "hard": [
        {
            "prompt": "What does this query return?",
            "code": (
                "-- relics\n"
                "--  name  | might\n"
                "--  Orb   | 5\n"
                "--  Crown | 3\n"
                "--\n"
                "-- cursed\n"
                "--  might\n"
                "--  5\n"
                "--  NULL\n"
                "SELECT name FROM relics\n"
                "WHERE might NOT IN (SELECT might FROM cursed)\n"
                "ORDER BY name;"
            ),
            "setup": (
                "CREATE TABLE relics (name VARCHAR(20), might INTEGER);\n"
                "INSERT INTO relics VALUES ('Orb', 5), ('Crown', 3);\n"
                "CREATE TABLE cursed (might INTEGER);\n"
                "INSERT INTO cursed VALUES (5), (NULL);"
            ),
            "options": ["No rows", "Crown", "Crown, Orb", "Orb"],
            "answer": "No rows",
            "explain": "For Crown, 3 NOT IN (5, NULL) means 3 <> 5 AND 3 <> NULL: TRUE AND UNKNOWN, which "
                       "is UNKNOWN. One NULL in the list stops NOT IN matching.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- knights\n"
                "--  name | gold\n"
                "--  Ada  | 90\n"
                "--  Bors | 90\n"
                "--  Cai  | 70\n"
                "--  Dag  | 60\n"
                "SELECT r, d FROM (\n"
                "  SELECT name,\n"
                "         RANK() OVER (ORDER BY gold DESC) AS r,\n"
                "         DENSE_RANK() OVER (ORDER BY gold DESC) AS d\n"
                "  FROM knights\n"
                ") AS t\n"
                "WHERE name = 'Dag';"
            ),
            "setup": (
                "CREATE TABLE knights (name VARCHAR(20), gold INTEGER);\n"
                "INSERT INTO knights VALUES ('Ada', 90), ('Bors', 90), ('Cai', 70), ('Dag', 60);"
            ),
            "options": ["4 3", "3 3", "4 4", "3 2"],
            "answer": "4 3",
            "explain": "Ada and Bors tie for 1st. RANK then skips to 3 for Cai and 4 for Dag; DENSE_RANK "
                       "leaves no gaps: 2 for Cai, 3 for Dag.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- loot\n"
                "--  day_no | gold\n"
                "--  1      | 10\n"
                "--  2      | 20\n"
                "--  2      | 5\n"
                "--  3      | 30\n"
                "SELECT day_no, SUM(gold) OVER (ORDER BY day_no)\n"
                "FROM loot\n"
                "ORDER BY day_no;"
            ),
            "setup": (
                "CREATE TABLE loot (day_no INTEGER, gold INTEGER);\n"
                "INSERT INTO loot VALUES (1, 10), (2, 20), (2, 5), (3, 30);"
            ),
            "options": [
                "1 10, 2 35, 2 35, 3 65",
                "1 10, 2 30, 2 35, 3 65",
                "1 10, 2 15, 2 35, 3 65",
                "1 10, 2 20, 2 5, 3 30",
            ],
            "answer": "1 10, 2 35, 2 35, 3 65",
            "explain": "With ORDER BY and no frame, the frame is RANGE BETWEEN UNBOUNDED PRECEDING AND "
                       "CURRENT ROW, and the current row brings all its ties: both day-2 rows get 35.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- loot\n"
                "--  knight | day_no | gold\n"
                "--  Ada    | 1      | 5\n"
                "--  Ada    | 2      | 8\n"
                "--  Bors   | 1      | 3\n"
                "--  Bors   | 2      | 4\n"
                "SELECT gold - LAG(gold, 1, 0) OVER (\n"
                "         PARTITION BY knight ORDER BY day_no)\n"
                "FROM loot\n"
                "ORDER BY knight, day_no;"
            ),
            "setup": (
                "CREATE TABLE loot (knight VARCHAR(20), day_no INTEGER, gold INTEGER);\n"
                "INSERT INTO loot VALUES ('Ada', 1, 5), ('Ada', 2, 8), ('Bors', 1, 3),\n"
                "  ('Bors', 2, 4);"
            ),
            "options": ["5, 3, 3, 1", "5, 3, -5, 1", "NULL, 3, NULL, 1", "0, 5, 0, 3"],
            "answer": "5, 3, 3, 1",
            "explain": "LAG looks back one row within the knight's own partition. A first row has nothing "
                       "before it, so it gets the default, 0, instead of NULL.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "WITH RECURSIVE n (i) AS (\n"
                "  VALUES (1)\n"
                "  UNION ALL\n"
                "  SELECT i * 2 FROM n WHERE i < 20\n"
                ")\n"
                "SELECT MAX(i) FROM n;"
            ),
            "options": ["32", "16", "20", "64"],
            "answer": "32",
            "explain": "The WHERE tests the row being doubled, not the new one: 1, 2, 4, 8, 16, and 16 < "
                       "20, so 32 is made too. From 32 the recursion stops.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- knights\n"
                "--  name   | mentor\n"
                "--  Arthur | NULL\n"
                "--  Bors   | Arthur\n"
                "--  Cai    | Bors\n"
                "--  Dag    | Arthur\n"
                "WITH RECURSIVE line (name, steps) AS (\n"
                "  SELECT name, 0 FROM knights WHERE mentor IS NULL\n"
                "  UNION ALL\n"
                "  SELECT k.name, l.steps + 1\n"
                "  FROM knights k JOIN line l ON k.mentor = l.name\n"
                ")\n"
                "SELECT name, steps FROM line ORDER BY steps DESC, name;"
            ),
            "setup": (
                "CREATE TABLE knights (name VARCHAR(20), mentor VARCHAR(20));\n"
                "INSERT INTO knights VALUES ('Arthur', NULL), ('Bors', 'Arthur'),\n"
                "  ('Cai', 'Bors'), ('Dag', 'Arthur');"
            ),
            "options": [
                "Cai 2, Bors 1, Dag 1, Arthur 0",
                "Bors 1, Dag 1, Arthur 0",
                "Cai 1, Bors 1, Dag 1, Arthur 0",
                "Cai 3, Bors 2, Dag 2, Arthur 1",
            ],
            "answer": "Cai 2, Bors 1, Dag 1, Arthur 0",
            "explain": "The anchor starts at Arthur (0 steps). Each round joins the knights mentored by "
                       "the last round's: Bors and Dag (1), then Cai (2).",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- pairs\n"
                "--  a    | b\n"
                "--  1    | 1\n"
                "--  1    | NULL\n"
                "--  NULL | NULL\n"
                "--  2    | 3\n"
                "SELECT COUNT(*) FROM pairs\n"
                "WHERE a IS DISTINCT FROM b;"
            ),
            "setup": (
                "CREATE TABLE pairs (a INTEGER, b INTEGER);\n"
                "INSERT INTO pairs VALUES (1, 1), (1, NULL), (NULL, NULL), (2, 3);"
            ),
            "options": ["2", "1", "3", "4"],
            "answer": "2",
            "explain": "IS DISTINCT FROM treats NULL like a value: 1 and NULL are distinct, two NULLs are "
                       "not. So (1, NULL) and (2, 3) count; a <> b would find only 1.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- loot\n"
                "--  kind | gold\n"
                "--  coin | 5\n"
                "--  coin | 20\n"
                "--  gem  | 8\n"
                "--  gem  | 3\n"
                "--  ring | 30\n"
                "SELECT kind, COUNT(*) FILTER (WHERE gold > 10)\n"
                "FROM loot\n"
                "GROUP BY kind\n"
                "ORDER BY kind;"
            ),
            "setup": (
                "CREATE TABLE loot (kind VARCHAR(10), gold INTEGER);\n"
                "INSERT INTO loot VALUES ('coin', 5), ('coin', 20), ('gem', 8), ('gem', 3),\n"
                "  ('ring', 30);"
            ),
            "options": [
                "coin 1, gem 0, ring 1",
                "coin 1, ring 1",
                "coin 2, gem 2, ring 1",
                "coin 1, gem NULL, ring 1",
            ],
            "answer": "coin 1, gem 0, ring 1",
            "explain": "FILTER picks the rows for one aggregate only, after the groups are made. So gem "
                       "keeps its group and counts 0, where a WHERE would have dropped it.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- loot\n"
                "--  kind | gold\n"
                "--  coin | 10\n"
                "--  coin | 20\n"
                "--  gem  | 15\n"
                "SELECT kind, SUM(gold) FROM loot\n"
                "GROUP BY ROLLUP (kind)\n"
                "ORDER BY GROUPING(kind), kind;"
            ),
            "setup": (
                "CREATE TABLE loot (kind VARCHAR(10), gold INTEGER);\n"
                "INSERT INTO loot VALUES ('coin', 10), ('coin', 20), ('gem', 15);"
            ),
            "options": [
                "coin 30, gem 15, NULL 45",
                "coin 30, gem 15",
                "NULL 45, coin 30, gem 15",
                "coin 30, gem 15, NULL 30",
            ],
            "answer": "coin 30, gem 15, NULL 45",
            "explain": "ROLLUP adds a grand-total row, with NULL for kind. GROUPING(kind) is 1 on that row "
                       "and 0 on the others, so the total sorts last.",
        },
        {
            "prompt": "What does this code return?",
            "code": (
                "CREATE TABLE gems (\n"
                "  name   VARCHAR(10),\n"
                "  carats INTEGER CHECK (carats > 0)\n"
                ");\n"
                "INSERT INTO gems VALUES ('Opal', NULL);\n"
                "SELECT COUNT(*) FROM gems;"
            ),
            "options": ["1", "0", "Error: check constraint violated", "NULL"],
            "answer": "1",
            "explain": "A CHECK constraint rejects a row only when its condition is FALSE. NULL > 0 is "
                       "UNKNOWN, so Opal is let in.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- relics\n"
                "--  name  | might | kind\n"
                "--  Orb   | 5     | gem\n"
                "--  Ring  | NULL  | coin\n"
                "--  Pearl | NULL  | gem\n"
                "--  Crown | 2     | gem\n"
                "SELECT name FROM relics\n"
                "WHERE NOT (might > 3 AND kind = 'gem')\n"
                "ORDER BY name;"
            ),
            "setup": (
                "CREATE TABLE relics (name VARCHAR(20), might INTEGER, kind VARCHAR(10));\n"
                "INSERT INTO relics VALUES ('Orb', 5, 'gem'), ('Ring', NULL, 'coin'),\n"
                "  ('Pearl', NULL, 'gem'), ('Crown', 2, 'gem');"
            ),
            "options": ["Crown, Ring", "Crown", "Crown, Pearl, Ring", "Pearl, Ring"],
            "answer": "Crown, Ring",
            "explain": "For Ring, UNKNOWN AND FALSE is FALSE, so NOT makes it TRUE. For Pearl, UNKNOWN AND "
                       "TRUE stays UNKNOWN, and so does its NOT.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- knights\n"
                "--  name | level\n"
                "--  Ada  | 3\n"
                "--  Bors | 5\n"
                "SELECT name FROM knights\n"
                "WHERE level = (SELECT level FROM knights\n"
                "               WHERE level > 1)\n"
                "ORDER BY name;"
            ),
            "setup": (
                "CREATE TABLE knights (name VARCHAR(20), level INTEGER);\n"
                "INSERT INTO knights VALUES ('Ada', 3), ('Bors', 5);"
            ),
            "options": ["Error: cardinality violation", "Ada, Bors", "Ada", "No rows"],
            "answer": "Error: cardinality violation",
            "explain": "A subquery used as a single value may return at most one row. This one returns "
                       "two, which the standard calls a cardinality violation.",
            "expect_error": True,
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- knights\n"
                "--  name\n"
                "--  Ada\n"
                "--  Bors\n"
                "--\n"
                "-- quests\n"
                "--  knight | gold\n"
                "--  Ada    | 5\n"
                "--  Ada    | 9\n"
                "--  Bors   | 7\n"
                "SELECT k.name, b.gold FROM knights k,\n"
                "  LATERAL (SELECT q.gold FROM quests q WHERE q.knight = k.name\n"
                "           ORDER BY q.gold DESC FETCH FIRST 1 ROW ONLY) AS b\n"
                "ORDER BY k.name;"
            ),
            "setup": (
                "CREATE TABLE knights (name VARCHAR(20));\n"
                "INSERT INTO knights VALUES ('Ada'), ('Bors');\n"
                "CREATE TABLE quests (knight VARCHAR(20), gold INTEGER);\n"
                "INSERT INTO quests VALUES ('Ada', 5), ('Ada', 9), ('Bors', 7);"
            ),
            "options": ["Ada 9, Bors 7", "Ada 9", "Ada 5, Bors 7", "Error: k.name is unknown"],
            "answer": "Ada 9, Bors 7",
            "explain": "LATERAL lets a derived table use columns from tables to its left, so the subquery "
                       "runs once per knight and keeps that knight's best quest.",
        },
        {
            "prompt": "By the SQL standard, where does ORDER BY might put NULLs when NULLS FIRST or NULLS "
                      "LAST isn't given?",
            "options": [
                "It's implementation-defined",
                "Always first",
                "Always last",
                "NULL rows are left out",
            ],
            "answer": "It's implementation-defined",
            "explain": "The standard says NULLs sort together, all before or all after the other values, "
                       "but leaves which to the product. Say NULLS FIRST or LAST.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- knights\n"
                "--  name | level\n"
                "--  Ada  | 3\n"
                "--  Bors | 7\n"
                "SELECT name FROM knights\n"
                "WHERE ROW_NUMBER() OVER (ORDER BY level DESC) = 1;"
            ),
            "setup": (
                "CREATE TABLE knights (name VARCHAR(20), level INTEGER);\n"
                "INSERT INTO knights VALUES ('Ada', 3), ('Bors', 7);"
            ),
            "options": ["Error: window function not allowed in WHERE", "Bors", "Ada", "No rows"],
            "answer": "Error: window function not allowed in WHERE",
            "explain": "Window functions are worked out after WHERE (and GROUP BY and HAVING), so WHERE "
                       "can't use them. Compute it in a derived table, then filter.",
            "expect_error": True,
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- knights\n"
                "--  name | level\n"
                "--  Ada  | 1\n"
                "--  Bors | 2\n"
                "--  Cai  | 3\n"
                "--  Dag  | 4\n"
                "--  Eve  | 5\n"
                "SELECT NTILE(2) OVER (ORDER BY level)\n"
                "FROM knights\n"
                "ORDER BY level;"
            ),
            "setup": (
                "CREATE TABLE knights (name VARCHAR(20), level INTEGER);\n"
                "INSERT INTO knights VALUES ('Ada', 1), ('Bors', 2), ('Cai', 3), ('Dag', 4),\n"
                "  ('Eve', 5);"
            ),
            "options": ["1, 1, 1, 2, 2", "1, 1, 2, 2, 2", "1, 2, 1, 2, 1", "1, 1, 2, 2, 3"],
            "answer": "1, 1, 1, 2, 2",
            "explain": "NTILE(2) deals the 5 rows into 2 groups as evenly as it can. When they can't be "
                       "equal, the earlier groups get the extra row: 3, then 2.",
        },
        {
            "prompt": "What does this code return?",
            "code": (
                "-- vault\n"
                "--  coins\n"
                "--  10\n"
                "START TRANSACTION;\n"
                "UPDATE vault SET coins = coins + 5;\n"
                "COMMIT;\n"
                "START TRANSACTION;\n"
                "UPDATE vault SET coins = coins * 2;\n"
                "ROLLBACK;\n"
                "SELECT coins FROM vault;"
            ),
            "setup": (
                "CREATE TABLE vault (coins INTEGER);\n"
                "INSERT INTO vault VALUES (10);"
            ),
            "options": ["15", "30", "10", "20"],
            "answer": "15",
            "explain": "COMMIT makes the + 5 permanent. ROLLBACK then undoes only what its own transaction "
                       "did, the doubling, leaving 15.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- loot\n"
                "--  day_no | gold\n"
                "--  1      | 10\n"
                "--  2      | 20\n"
                "--  3      | 30\n"
                "--  4      | 40\n"
                "SELECT SUM(gold) OVER (\n"
                "         ORDER BY day_no\n"
                "         ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING)\n"
                "FROM loot\n"
                "ORDER BY day_no;"
            ),
            "setup": (
                "CREATE TABLE loot (day_no INTEGER, gold INTEGER);\n"
                "INSERT INTO loot VALUES (1, 10), (2, 20), (3, 30), (4, 40);"
            ),
            "options": ["30, 60, 90, 70", "10, 30, 50, 70", "10, 30, 60, 100", "60, 60, 90, 90"],
            "answer": "30, 60, 90, 70",
            "explain": "Each row's frame is itself plus one row either side. The first and last rows have "
                       "no neighbour on one side, so they add up only two rows.",
        },
        {
            "prompt": "When a transaction doesn't choose an isolation level, which one does the SQL "
                      "standard say it gets?",
            "options": ["SERIALIZABLE", "READ COMMITTED", "REPEATABLE READ", "READ UNCOMMITTED"],
            "answer": "SERIALIZABLE",
            "explain": "The standard's default is SERIALIZABLE, the strictest level, even though many "
                       "products start at READ COMMITTED unless told otherwise.",
        },
        {
            "prompt": "What does this code return?",
            "code": (
                "-- vault\n"
                "--  gem  | qty\n"
                "--  Ruby | 1\n"
                "--  Opal | 2\n"
                "--\n"
                "-- gifts\n"
                "--  gem  | qty\n"
                "--  Ruby | 5\n"
                "--  Jade | 3\n"
                "MERGE INTO vault v USING gifts g ON v.gem = g.gem\n"
                "WHEN MATCHED THEN UPDATE SET qty = v.qty + g.qty\n"
                "WHEN NOT MATCHED THEN INSERT VALUES (g.gem, g.qty);\n"
                "SELECT gem, qty FROM vault ORDER BY gem;"
            ),
            "setup": (
                "CREATE TABLE vault (gem VARCHAR(20), qty INTEGER);\n"
                "INSERT INTO vault VALUES ('Ruby', 1), ('Opal', 2);\n"
                "CREATE TABLE gifts (gem VARCHAR(20), qty INTEGER);\n"
                "INSERT INTO gifts VALUES ('Ruby', 5), ('Jade', 3);"
            ),
            "options": [
                "Jade 3, Opal 2, Ruby 6",
                "Opal 2, Ruby 6",
                "Jade 3, Opal 2, Ruby 5",
                "Jade 3, Ruby 6",
            ],
            "answer": "Jade 3, Opal 2, Ruby 6",
            "explain": "MERGE updates the vault rows that match a gift (Ruby: 1 + 5) and inserts the gifts "
                       "that match nothing (Jade). Opal, with no gift, stays.",
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
    "forest": "On your way back through the Relational Forest, a glint of gold catches your eye in a mossy "
              "hollow.",
    "cave": "On your way back out of the Subquery Caverns, a glint of gold catches your eye in a side "
            "cavern, nested deeper than any you've seen.",
    "castle": "On your way back through Castle Codd, a glint of gold catches your eye through a doorway: a "
              "forgotten treasury.",
}

DRAGONS = {
    ("easy", "cave"): {
        "scene": "dragon-emerald", "scales": "green as moss",
        "question": {
            "prompt": "What does this query return?",
            "code": (
                "-- chests\n"
                "--  id | gold\n"
                "--  1  | 10\n"
                "--  2  | 20\n"
                "--  3  | 30\n"
                "--  4  | 40\n"
                "SELECT COUNT(*) FROM chests\n"
                "WHERE gold BETWEEN 40 AND 20;"
            ),
            "setup": (
                "CREATE TABLE chests (id INTEGER, gold INTEGER);\n"
                "INSERT INTO chests VALUES (1, 10), (2, 20), (3, 30), (4, 40);"
            ),
            "options": ["0", "3", "1", "Error"],
            "answer": "0",
            "explain": "x BETWEEN 40 AND 20 means x >= 40 AND x <= 20, which nothing can be. The smaller "
                       "bound has to come first.",
        },
    },
    ("medium", "cave"): {
        "scene": "dragon-ember", "scales": "glowing like hot coals",
        "question": {
            "prompt": "What does this query return?",
            "code": (
                "-- knights\n"
                "--  name\n"
                "--  Ada\n"
                "--  Bors\n"
                "--  Cai\n"
                "--\n"
                "-- quests\n"
                "--  knight | done\n"
                "--  Ada    | yes\n"
                "--  Bors   | no\n"
                "SELECT k.name, q.done FROM knights k\n"
                "LEFT JOIN quests q\n"
                "  ON q.knight = k.name AND q.done = 'yes'\n"
                "ORDER BY k.name;"
            ),
            "setup": (
                "CREATE TABLE knights (name VARCHAR(20));\n"
                "INSERT INTO knights VALUES ('Ada'), ('Bors'), ('Cai');\n"
                "CREATE TABLE quests (knight VARCHAR(20), done VARCHAR(5));\n"
                "INSERT INTO quests VALUES ('Ada', 'yes'), ('Bors', 'no');"
            ),
            "options": [
                "Ada yes, Bors NULL, Cai NULL",
                "Ada yes",
                "Ada yes, Bors no, Cai NULL",
                "Ada yes, Cai NULL",
            ],
            "answer": "Ada yes, Bors NULL, Cai NULL",
            "explain": "In ON, the condition only decides which quest rows match. A LEFT JOIN still keeps "
                       "every knight, so Bors's 'no' quest just doesn't match.",
        },
    },
    ("hard", "cave"): {
        "scene": "dragon-frost", "scales": "glittering with ice",
        "question": {
            "prompt": "What does this query return?",
            "code": (
                "-- loot\n"
                "--  kind | metal\n"
                "--  coin | gold\n"
                "--  coin | silver\n"
                "--  ring | gold\n"
                "SELECT COUNT(*) FROM (\n"
                "  SELECT kind, metal, COUNT(*) AS n FROM loot\n"
                "  GROUP BY GROUPING SETS ((kind), (metal), ())\n"
                ") AS g;"
            ),
            "setup": (
                "CREATE TABLE loot (kind VARCHAR(10), metal VARCHAR(10));\n"
                "INSERT INTO loot VALUES ('coin', 'gold'), ('coin', 'silver'), ('ring', 'gold');"
            ),
            "options": ["5", "4", "3", "7"],
            "answer": "5",
            "explain": "Each grouping set is grouped on its own: 2 kinds, plus 2 metals, plus one grand "
                       "total for (). That's 2 + 2 + 1 = 5 rows.",
        },
    },
    ("easy", "forest"): {
        "scene": "dragon-pearl", "scales": "white as moonlight",
        "question": {
            "prompt": "What does this query return?",
            "code": (
                "-- scrolls\n"
                "--  title\n"
                "--  50% gold\n"
                "--  Half map\n"
                "--  100%\n"
                "--  Gold_map\n"
                "SELECT COUNT(*) FROM scrolls\n"
                "WHERE title LIKE '%!%%' ESCAPE '!';"
            ),
            "setup": (
                "CREATE TABLE scrolls (title VARCHAR(20));\n"
                "INSERT INTO scrolls VALUES ('50% gold'), ('Half map'), ('100%'), ('Gold_map');"
            ),
            "options": ["2", "4", "0", "1"],
            "answer": "2",
            "explain": "ESCAPE '!' makes !% mean a real percent sign, while the outer % signs still match "
                       "anything. So it finds titles that contain a %.",
        },
    },
    ("medium", "forest"): {
        "scene": "dragon-amethyst", "scales": "a deep, shimmering purple",
        "question": {
            "prompt": "What does this query return?",
            "code": (
                "-- knights\n"
                "--  full_name\n"
                "--  Sir Bors the Bold\n"
                "SELECT SUBSTRING(full_name\n"
                "                 FROM POSITION(' ' IN full_name) + 1\n"
                "                 FOR 4)\n"
                "FROM knights;"
            ),
            "setup": (
                "CREATE TABLE knights (full_name VARCHAR(30));\n"
                "INSERT INTO knights VALUES ('Sir Bors the Bold');"
            ),
            "options": ["Bors", "Sir", "Bors the Bold", "Bold"],
            "answer": "Bors",
            "explain": "POSITION finds the first space at 4, so the SUBSTRING starts at 5 and takes 4 "
                       "characters: Bors.",
        },
    },
    ("hard", "forest"): {
        "scene": "dragon-autumn", "scales": "the color of falling leaves",
        "question": {
            "prompt": "What does this query return?",
            "code": (
                "-- loot\n"
                "--  day_no | gold\n"
                "--  1      | 10\n"
                "--  2      | 20\n"
                "--  4      | 40\n"
                "--  5      | 50\n"
                "SELECT SUM(gold) OVER (\n"
                "         ORDER BY day_no\n"
                "         RANGE BETWEEN 1 PRECEDING AND CURRENT ROW)\n"
                "FROM loot\n"
                "ORDER BY day_no;"
            ),
            "setup": (
                "CREATE TABLE loot (day_no INTEGER, gold INTEGER);\n"
                "INSERT INTO loot VALUES (1, 10), (2, 20), (4, 40), (5, 50);"
            ),
            "options": ["10, 30, 40, 90", "10, 30, 60, 90", "10, 30, 70, 120", "10, 20, 40, 50"],
            "answer": "10, 30, 40, 90",
            "explain": "RANGE counts in values of day_no, not in rows: day 4's frame is days 3 to 4, and "
                       "there's no day 3. ROWS would have taken day 2 instead.",
        },
    },
    ("easy", "castle"): {
        "scene": "dragon-gold", "scales": "as bright as the coins beneath it",
        "question": {
            "prompt": "What does this query return?",
            "code": (
                "-- court\n"
                "--  name   | post\n"
                "--  Bors   | knight\n"
                "--  Arthur | king\n"
                "--  Ada    | knight\n"
                "--  Gwen   | queen\n"
                "SELECT name FROM court\n"
                "ORDER BY CASE post WHEN 'king'  THEN 1\n"
                "                   WHEN 'queen' THEN 2\n"
                "                   ELSE 3 END,\n"
                "         name;"
            ),
            "setup": (
                "CREATE TABLE court (name VARCHAR(20), post VARCHAR(10));\n"
                "INSERT INTO court VALUES ('Bors', 'knight'), ('Arthur', 'king'),\n"
                "  ('Ada', 'knight'), ('Gwen', 'queen');"
            ),
            "options": [
                "Arthur, Gwen, Ada, Bors",
                "Ada, Arthur, Bors, Gwen",
                "Arthur, Gwen, Bors, Ada",
                "Ada, Bors, Arthur, Gwen",
            ],
            "answer": "Arthur, Gwen, Ada, Bors",
            "explain": "ORDER BY can sort by any expression. The CASE puts the king (1) and queen (2) "
                       "first, and the two knights (3) are then sorted by name.",
        },
    },
    ("medium", "castle"): {
        "scene": "dragon-silver", "scales": "gleaming like polished armor",
        "question": {
            "prompt": "What does this query return?",
            "code": (
                "-- chests\n"
                "--  owner | gold\n"
                "--  Ada   | 10\n"
                "--  Bors  | 20\n"
                "SELECT owner, COUNT(*) FROM chests\n"
                "WHERE gold > 50\n"
                "GROUP BY owner;"
            ),
            "setup": (
                "CREATE TABLE chests (owner VARCHAR(20), gold INTEGER);\n"
                "INSERT INTO chests VALUES ('Ada', 10), ('Bors', 20);"
            ),
            "options": ["No rows", "Ada 0, Bors 0", "NULL 0", "0"],
            "answer": "No rows",
            "explain": "GROUP BY makes one row per group, and WHERE left no rows to make groups from. Only "
                       "an aggregate with no GROUP BY always returns a row.",
        },
    },
    ("hard", "castle"): {
        "scene": "dragon-shadow", "scales": "as black as a moonless night",
        "question": {
            "prompt": "What does this query return?",
            "code": (
                "-- spans\n"
                "--  name | lo | hi\n"
                "--  Ada  | 1  | NULL\n"
                "--  Bors | 10 | NULL\n"
                "SELECT name FROM spans\n"
                "WHERE NOT (5 BETWEEN lo AND hi)\n"
                "ORDER BY name;"
            ),
            "setup": (
                "CREATE TABLE spans (name VARCHAR(20), lo INTEGER, hi INTEGER);\n"
                "INSERT INTO spans VALUES ('Ada', 1, NULL), ('Bors', 10, NULL);"
            ),
            "options": ["Bors", "No rows", "Ada, Bors", "Ada"],
            "answer": "Bors",
            "explain": "BETWEEN means 5 >= lo AND 5 <= hi. For Bors, 5 >= 10 is FALSE, and FALSE AND "
                       "UNKNOWN is FALSE, so NOT gives TRUE. Ada's stays UNKNOWN.",
        },
    },
}


# ------------------------------------------------------------------
# The final boss: the Cartesian Beast
# ------------------------------------------------------------------
# Only an explorer who completes every path on every level meets the Beast. It asks one of
# these nine, picked at random: the hardest questions in the game. Answer right and they
# become an ANSI SQL Master, with BOSS_POINTS (times the Hard multiplier) besides; answer
# wrong and all is lost: their score falls to zero, and they must start over.

BOSS_MOVE = "boss"
BOSS_POINTS = 100

# The page's own words for this game. The other games have their own, by the same keys.
TEXTS = {
    "title": "The Lost Standard of Sequelia",
    "language": "ANSI SQL",
    "intro": [
        "Long ago, the first keepers of data met in the high council of Sequelia and agreed on one "
        "Standard, a language every database would understand. They sealed it away, the Golden Standard, "
        "deep within this wild land. Its guardians still test every traveler with riddles written in that "
        "common tongue: ANSI SQL.",
        "One law holds in Sequelia: every riddle is pure standard SQL, true on any database that keeps the "
        "Standard. Answer wisely and choose your path carefully. Every wrong answer costs you a life, and "
        "some choices lead to certain doom...",
    ],
    "found": "Found the treasure",
    "master": "ANSI SQL Master",
    "lost_to_boss": "Lost to the Cartesian Beast",
    "hall_note": "Walk every path on every level to face the Cartesian Beast.",
    "boss_offer_title": "The final challenge: the Cartesian Beast",
    "boss_offer": "You have walked every path on every level, and the Cartesian Beast, which multiplies "
                  "every table it meets, is waiting. Answer its question, the hardest in all of Sequelia, "
                  "to earn the title of ANSI SQL Master and {points} points.",
    "boss_warning": "Beware: if you fail, all is lost. Your score falls to zero and you must start over.",
    "boss_button": "Face the Cartesian Beast",
    "boss_confirm": "Face the Cartesian Beast? If you fail, all is lost: your score falls to zero and you "
                    "must start over.",
    "boss_won": "You have defeated the Cartesian Beast. You are an ANSI SQL Master!",
    "boss_lost": "The Cartesian Beast has defeated you. All is lost: your score is gone, and you must "
                 "start over.",
    "conquered_every_path": "Every path on every level: you've explored all of Sequelia!",
    "conquered_every_level": "Easy, Medium and Hard: you've conquered every level of Sequelia!",
}

BOSS_QUESTIONS = [
    {
        "prompt": "What does this query return?",
        "code": (
            "-- roads\n"
            "--  src  | dst\n"
            "--  Keep | Mill\n"
            "--  Mill | Keep\n"
            "WITH RECURSIVE reach (place) AS (\n"
            "  SELECT src FROM roads WHERE src = 'Keep'\n"
            "  UNION\n"
            "  SELECT r.dst FROM roads r\n"
            "  JOIN reach ON r.src = reach.place\n"
            ")\n"
            "SELECT COUNT(*) FROM reach;"
        ),
        "setup": (
            "CREATE TABLE roads (src VARCHAR(10), dst VARCHAR(10));\n"
            "INSERT INTO roads VALUES ('Keep', 'Mill'), ('Mill', 'Keep');"
        ),
        "options": ["2", "It never ends", "3", "1"],
        "answer": "2",
        "explain": "With UNION (not UNION ALL), rows already found are thrown away. Coming back to Keep "
                   "adds nothing new, so the recursion stops at Keep and Mill.",
    },
    {
        "prompt": "What does this query return?",
        "code": (
            "-- relics\n"
            "--  name\n"
            "--  Dragon\n"
            "SELECT SUBSTRING(name FROM 0 FOR 3) FROM relics;"
        ),
        "setup": (
            "CREATE TABLE relics (name VARCHAR(20));\n"
            "INSERT INTO relics VALUES ('Dragon');"
        ),
        "options": ["Dr", "Dra", "rag", "Error"],
        "answer": "Dr",
        "explain": "FROM 0 FOR 3 means positions 0, 1 and 2. There's no character at 0, so only positions "
                   "1 and 2 are left: Dr.",
    },
    {
        "prompt": "What does this query return?",
        "code": (
            "-- north\n"
            "--  gem\n"
            "--  Ruby\n"
            "--  Ruby\n"
            "--  Ruby\n"
            "--  Opal\n"
            "--\n"
            "-- south\n"
            "--  gem\n"
            "--  Ruby\n"
            "--  Opal\n"
            "SELECT gem FROM north\n"
            "EXCEPT ALL SELECT gem FROM south\n"
            "ORDER BY gem;"
        ),
        "setup": (
            "CREATE TABLE north (gem VARCHAR(20));\n"
            "INSERT INTO north VALUES ('Ruby'), ('Ruby'), ('Ruby'), ('Opal');\n"
            "CREATE TABLE south (gem VARCHAR(20));\n"
            "INSERT INTO south VALUES ('Ruby'), ('Opal');"
        ),
        "options": ["Ruby, Ruby", "No rows", "Ruby", "Opal, Ruby, Ruby"],
        "answer": "Ruby, Ruby",
        "explain": "EXCEPT ALL takes away one copy for each copy on the right: 3 Rubys minus 1 leaves 2, "
                   "and 1 Opal minus 1 leaves none. Plain EXCEPT gives no rows.",
    },
    {
        "prompt": "What does this query return?",
        "code": (
            "-- loot\n"
            "--  kind | gold\n"
            "--  coin | 10\n"
            "--  coin | 20\n"
            "--  gem  | 15\n"
            "SELECT kind, SUM(gold), SUM(SUM(gold)) OVER ()\n"
            "FROM loot\n"
            "GROUP BY kind\n"
            "ORDER BY kind;"
        ),
        "setup": (
            "CREATE TABLE loot (kind VARCHAR(10), gold INTEGER);\n"
            "INSERT INTO loot VALUES ('coin', 10), ('coin', 20), ('gem', 15);"
        ),
        "options": [
            "coin 30 45, gem 15 45",
            "Error: aggregates can't be nested",
            "coin 30 30, gem 15 15",
            "coin 30 30, gem 15 45",
        ],
        "answer": "coin 30 45, gem 15 45",
        "explain": "Window functions run after GROUP BY, over the grouped rows, so they can take an "
                   "aggregate. OVER () is all the groups: 30 + 15 = 45 on each.",
    },
    {
        "prompt": "What does this query return?",
        "code": (
            "-- relics\n"
            "--  name | might\n"
            "--  Orb  | 5\n"
            "--  Ring | NULL\n"
            "--\n"
            "-- cursed (no rows)\n"
            "--  might\n"
            "SELECT COUNT(*) FROM relics\n"
            "WHERE might NOT IN (SELECT might FROM cursed);"
        ),
        "setup": (
            "CREATE TABLE relics (name VARCHAR(20), might INTEGER);\n"
            "INSERT INTO relics VALUES ('Orb', 5), ('Ring', NULL);\n"
            "CREATE TABLE cursed (might INTEGER);"
        ),
        "options": ["2", "1", "0", "Error"],
        "answer": "2",
        "explain": "NOT IN an empty set is TRUE for any value, even NULL: there is nothing to compare "
                   "with, so there is nothing UNKNOWN. Both relics count.",
    },
    {
        "prompt": "What does this query return?",
        "code": (
            "-- north\n"
            "--  rune\n"
            "--  Fire\n"
            "--  NULL\n"
            "--\n"
            "-- south\n"
            "--  rune\n"
            "--  NULL\n"
            "--  Ice\n"
            "SELECT COUNT(*) FROM (\n"
            "  SELECT rune FROM north\n"
            "  INTERSECT\n"
            "  SELECT rune FROM south\n"
            ") AS t;"
        ),
        "setup": (
            "CREATE TABLE north (rune VARCHAR(10));\n"
            "INSERT INTO north VALUES ('Fire'), (NULL);\n"
            "CREATE TABLE south (rune VARCHAR(10));\n"
            "INSERT INTO south VALUES (NULL), ('Ice');"
        ),
        "options": ["1", "0", "2", "3"],
        "answer": "1",
        "explain": "Set operations compare rows as 'not distinct', so the two NULLs count as the same row "
                   "and the NULL survives. A join ON north.rune = south.rune finds 0.",
    },
    {
        "prompt": "What does this query return?",
        "code": (
            "-- loot\n"
            "--  kind\n"
            "--  gem\n"
            "--  gem\n"
            "--  coin\n"
            "--  gem\n"
            "--  coin\n"
            "SELECT DISTINCT kind, COUNT(*) OVER () FROM loot\n"
            "ORDER BY kind;"
        ),
        "setup": (
            "CREATE TABLE loot (kind VARCHAR(10));\n"
            "INSERT INTO loot VALUES ('gem'), ('gem'), ('coin'), ('gem'), ('coin');"
        ),
        "options": ["coin 5, gem 5", "coin 2, gem 2", "coin 2, gem 3", "coin 1, gem 1"],
        "answer": "coin 5, gem 5",
        "explain": "The window is worked out on all 5 rows before DISTINCT removes the duplicate rows, so "
                   "every row says 5, and then only 2 distinct rows remain.",
    },
    {
        "prompt": "What does this query return?",
        "code": (
            "-- knights\n"
            "--  id | name\n"
            "--  1  | Ada\n"
            "--  2  | Bors\n"
            "--\n"
            "-- horses\n"
            "--  id | name    | knight_id\n"
            "--  1  | Swift   | 2\n"
            "--  2  | Thunder | 1\n"
            "SELECT COUNT(*) FROM knights NATURAL JOIN horses;"
        ),
        "setup": (
            "CREATE TABLE knights (id INTEGER, name VARCHAR(20));\n"
            "INSERT INTO knights VALUES (1, 'Ada'), (2, 'Bors');\n"
            "CREATE TABLE horses (id INTEGER, name VARCHAR(20), knight_id INTEGER);\n"
            "INSERT INTO horses VALUES (1, 'Swift', 2), (2, 'Thunder', 1);"
        ),
        "options": ["0", "2", "4", "Error: ambiguous column"],
        "answer": "0",
        "explain": "NATURAL JOIN matches on every column the tables share by name: both id and name. No "
                   "knight has a horse's name, so nothing matches.",
    },
    {
        "prompt": "What does this query return?",
        "code": (
            "-- north\n"
            "--  id | gem\n"
            "--  1  | Ruby\n"
            "--  2  | Opal\n"
            "--\n"
            "-- south\n"
            "--  id | coin\n"
            "--  2  | Gold\n"
            "--  3  | Silver\n"
            "SELECT id FROM north FULL JOIN south USING (id)\n"
            "ORDER BY id;"
        ),
        "setup": (
            "CREATE TABLE north (id INTEGER, gem VARCHAR(20));\n"
            "INSERT INTO north VALUES (1, 'Ruby'), (2, 'Opal');\n"
            "CREATE TABLE south (id INTEGER, coin VARCHAR(20));\n"
            "INSERT INTO south VALUES (2, 'Gold'), (3, 'Silver');"
        ),
        "options": ["1, 2, 3", "1, 2, NULL", "2", "Error: id is ambiguous"],
        "answer": "1, 2, 3",
        "explain": "With USING, the joined id column is one column, COALESCE(north.id, south.id), so it is "
                   "never NULL even on the rows only one side has.",
    },
]


# ------------------------------------------------------------------
# Scenes: each has a banner, a picture (static/img/adventure/, shared with the Python game
# but for the door and the boss) and a description of it
# ------------------------------------------------------------------

SCENES = {
    "start": ("The Lost Standard of Sequelia", "title.webp",
              "A moonlit jungle valley wrapped in mist, a golden temple glowing on a far hilltop"),
    "forest": ("The Relational Forest", "forest.webp",
               "Sunbeams falling through towering trees onto a stream, ferns and one giant mossy tree"),
    "waterfall": ("The Falls of UNION", "waterfall.webp",
                  "A roaring waterfall crashing into a green pool between mossy cliffs, a fallen log high "
                  "across the gorge"),
    "tree": ("The Top of the Tree of Hierarchies", "tree.webp",
             "A great owl on a mossy branch above a sea of mist at sunrise, a golden temple glinting in "
             "the distance"),
    "cave": ("The Subquery Caverns", "cave.webp",
             "A dark cave mouth framed by carved stone serpents, a torch burning beside it"),
    "dark": ("The NULL Pit", "pit.webp",
             "A deep pit in the floor of a rocky tunnel, the cave entrance glowing far behind"),
    "glyph": ("The Door of Constraints", "glyph-door-ansi-sql.webp",
              "A massive stone door glowing with lines of SQL, a CHECK constraint among them, fire bowls "
              "burning on either side"),
    "castle": ("The Ruins of Castle Codd", "castle.webp",
               "A ruined castle on a misty hilltop under a full moon, torches lighting the stone path that "
               "winds up to it"),
    "gate": ("The Castle Gate", "castle-gate.webp",
             "A great arched gate with a raised iron portcullis, griffin banners and blazing torches on "
             "ivy-covered walls"),
    "hall": ("The Hall of Relations", "great-hall.webp",
             "A ruined great hall of broken gothic arches, torches flickering beside an empty throne at "
             "the top of worn steps"),
    "ramparts": ("The Castle Ramparts", "ramparts.webp",
                 "Torch-lit battlements under a full moon, stone towers rising above a misty valley"),
    "gallery": ("The Gallery of Views", "gallery.webp",
                "A stone gallery high in a tower, ivy twisting around its pillars, the full moon over a "
                "misty valley beyond the balustrade"),
    "temple": ("The Temple of the Golden Standard", "temple.webp",
               "A torch-lit temple hall leading to a golden vault door guarded by two stone serpents, a "
               "jeweled chest by the path"),
    "victory": ("The Treasure Is Yours!", "treasure.webp",
                "The Golden Standard: a glowing golden orb wrapped by a serpent, on a stone pedestal among "
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
    "boss": ("The Cartesian Beast", "cartesian-beast.webp",
             "The Cartesian Beast: a huge horned purple beast with blazing eyes and great claws in a "
             "ruined hall hung with ANSI SQL banners, glowing tables A and B before it joined by a CROSS "
             "JOIN into a nine-row Cartesian product"),
    "game_over": ("Rolled Back", "game-over.webp",
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
    """An ANSI SQL challenge: the explorer picks an answer (moves "a" to "d")."""
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
# ANSI SQL challenges
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
    """Ask one ANSI SQL question: the next from the deck, or `question` (a dragon's or the
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
                      f"Sequelia with {quest.carried} points from your last quest, wondering "
                      "what waits down the way you didn't take. This time you turn toward "
                      f"{PATH_SIGHTS[quest.only_path]}"
                      f"{', where new riddles await' if quest.skip_questions else ''}.")
        yield Choice([PATHS[quest.only_path]])
        choice = str(list(PATHS).index(quest.only_path) + 1)
    else:
        if quest.carried:
            # A winner carrying their score up to the next level.
            quest.narrate(f"Welcome back, {quest.player['name']}! You return to the edge of "
                          f"Sequelia with {quest.carried} points from your last quest. Word of "
                          "your success has reached the guardians, and their riddles will be "
                          "harder this time. " + "Three paths lie before you once more: the Relational "
                                                 "Forest, the Subquery Caverns and the trail to the Ruins "
                                                 "of Castle Codd.")
        else:
            quest.narrate(f"Welcome, {quest.player['name']}! You arrive at the edge of Sequelia "
                          "with nothing but a backpack and your wits. " + "Three paths lie before you: the "
                                                                          "Relational Forest, where every "
                                                                          "tree is joined to another; the "
                                                                          "Subquery Caverns, a cave inside "
                                                                          "a cave inside a cave; and a "
                                                                          "torch-lit trail that climbs to "
                                                                          "the Ruins of Castle Codd, where "
                                                                          "the first tables were drawn.")
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
    quest.narrate("Towering trees close in around you, their roots and branches so tangled that you can't "
                  "tell where one tree ends and the next begins: here, every tree is joined to another. To "
                  "your left, a river murmurs through the ferns. To your right stands an ancient tree so "
                  "tall its top disappears into the mist. From up there, you could see for miles.")
    choice = yield Choice(["Follow the river", "Climb the giant tree"])
    if choice == "1":
        return (yield from river_route(quest))
    return (yield from tree_route(quest))


def river_route(quest):
    """The river leads to a waterfall and its guardian."""
    quest.banner("waterfall")
    quest.narrate("You follow the river to the Falls of UNION, where two streams pour over the cliff and "
                  "become one. The water swirls, rises, and takes the shape of a towering figure: the "
                  'River Guardian. "Two streams meet here, and only the worthy pass," it booms. "Answer my '
                  'riddle in the common tongue."')
    if not (yield from face_challenge(quest, "The River Guardian")):
        return game_over(quest, "The Guardian's patience runs dry. A great wave sweeps you downstream, far "
                                "away from the treasure.")

    quest.narrate("The Guardian bows and places a shimmering pearl in your hand. No two pearls in its "
                  "river are ever alike.")
    collect_relic(quest, "Pearl of Uniqueness")
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
    quest.narrate("You climb branch by branch, from parent to child to grandchild, until you break through "
                  "the mist. Far to the east, a golden temple roof glints above the trees. A great grey "
                  'owl lands beside you and blinks. "Hoo! Every branch of this tree knows its parent. Only '
                  'those who can follow them all, as a recursive query does, may learn the safe way down."')
    if not (yield from face_challenge(quest, "The Wise Owl")):
        return game_over(quest, "The owl ruffles its feathers and flies away. As you reach after it, the "
                                "branch beneath you snaps...")

    quest.narrate('"Well reasoned!" hoots the owl, and it plucks a quill from its wing for you.')
    collect_relic(quest, "Quill of Normal Form")
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
                  "around the entrance, and beyond it the cave opens into another cave, and that one into "
                  "another: a query within a query within a query. Just inside, you find an old torch and "
                  "a flint. Lighting it would help you see, but the light might also wake whatever is "
                  "hissing in the dark...")
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
                  "ground vanishes beneath your feet and you tumble into the NULL Pit, where nothing is "
                  "true, nothing is false, and everything is unknown!")
    if not lose_life(quest):
        return game_over(quest, "The NULL Pit is far too deep to climb out of without light. Your quest "
                                "ends here, in the unknown.")

    # A pause here, so the pit gets its moment on screen.
    yield Choice(["Climb out of the pit"])
    quest.narrate("Bruised but alive, you claw your way out and crawl back to the entrance. This time you "
                  "light the torch. Lesson learned! In its glow you can see the floor is riddled with "
                  "pits, and not one of them is equal to another, not even to itself.")
    return (yield from glyph_door(quest))


def glyph_door(quest):
    """Deep in the cave, a door sealed with an ANSI SQL puzzle."""
    quest.banner("glyph")
    quest.narrate("You weave between the pits until the tunnel ends at a massive stone door: the Door of "
                  "Constraints. Glowing glyphs crawl across its surface and arrange themselves into lines "
                  "of SQL, a table with a CHECK on the one key it will accept.")
    if not (yield from face_challenge(quest, "The Door of Constraints")):
        return game_over(quest, "The glyphs flash red: check constraint violated. With a deep rumble the "
                                "tunnel behind you seals shut, and your torch flickers out...")

    quest.narrate("The glyphs flash gold and the door grinds open. A small carved tablet falls from the "
                  "wall at your feet, a schema etched into its face.")
    collect_relic(quest, "Schema Tablet")
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
    quest.narrate("A winding stone trail climbs out of the mist to the Ruins of Castle Codd, where, the "
                  "old stories say, the first tables were drawn: relations of rows and columns, and "
                  "nothing else. Torches still burn along the way, though no one has lived here for a "
                  "thousand years. The trail ends at the great gate. Beside it, a crumbling stair climbs "
                  "the outer wall toward the ramparts.")
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
                  'drifts out of the stone. "Halt! I guard the integrity of this castle. Only a true coder '
                  'of the Standard may enter the Hall of Relations."')
    if not (yield from face_challenge(quest, "The Ghost Knight")):
        return game_over(quest, "The ghost knight raises its sword and the portcullis crashes down. You "
                                "are left outside in the dark, far from the treasure.")

    quest.narrate("The knight lowers its sword and presses a cold silver ring into your palm, a key carved "
                  "on its face.")
    collect_relic(quest, "Signet of Integrity")
    quest.banner("hall")
    quest.narrate("Beyond the gate lies the Hall of Relations, its arches broken and open to the sky. "
                  "Torches flicker beside an empty throne. Behind it, a narrow passage glows with a faint "
                  "golden light. To one side, a grand staircase climbs into the dark, its steps cracked "
                  "and crumbling.")
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
                  'eyes crack open and glow. "Answer me, climber, in the tongue every database shares, or '
                  'take the short way down."')
    if not (yield from face_challenge(quest, "The Stone Gargoyle")):
        return game_over(quest, "The gargoyle spreads its stone wings, and one great gust sweeps you off "
                                "the wall and into the mist.")

    quest.narrate("The gargoyle grinds out a laugh and drops a glittering stone from its claw.")
    collect_relic(quest, "Gargoyle's Eye")
    quest.banner("gallery")
    quest.narrate("The ramparts lead into a tall tower and up to the Gallery of Views, where every window "
                  "shows the valley a different way, though the valley itself never changes. Far below the "
                  "balustrade, a golden temple roof glints through the mist. Ivy as thick as rope hangs "
                  "over the edge, and a spiral stair winds down inside the tower.")
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
                  "the vault, its door sealed by two locks, each watched by a stone serpent: the Primary "
                  "Lock and the Foreign Lock. Beside the path sits a small jeweled chest with a riddle "
                  "carved into its lid. Solving it would earn you a rare relic, but a wrong answer will "
                  "cost you a life.")
    choice = yield Choice(["Try to open the jeweled chest",
                           "Ignore the chest and head for the vault"])
    if choice == "1":
        if (yield from ask_question(quest, "The Jeweled Chest")):
            quest.narrate('Click! The lid springs open, revealing a ring set with a blazing ruby. "All of '
                          'it, or none of it," says the writing inside the band.')
            collect_relic(quest, "Ring of Atomicity")
        else:
            if not lose_life(quest):
                return game_over(quest, "A dart coated in sleeping venom shoots from the lock. You doze "
                                        "off just steps away from the treasure...")
            quest.narrate("A tiny dart shoots from the lock and stings your hand. "
                          "The chest stays shut.")
    else:
        quest.narrate("You leave the chest alone. Sometimes the wisest move is not "
                      "to gamble.")

    quest.narrate("You approach the vault door. The eyes of the stone serpents begin to glow. The Primary "
                  "Lock opens only for a key that is unique and never NULL; the Foreign Lock, only for a "
                  "key the first one knows.")
    for lock in LOCKS:
        if not (yield from face_challenge(quest, lock)):
            return game_over(quest, "The serpent's eyes flash red and the vault seals itself forever. The "
                                    "treasure remains lost.")
        quest.note("info", f"{lock} slides open!")
    return victory(quest)


# The vault's two locks, in the order they're faced.
LOCKS = ["The Primary Lock", "The Foreign Lock"]


def victory(quest):
    """The vault opens! Award the end-of-quest bonuses."""
    player = quest.player
    quest.banner("victory")
    quest.narrate("The vault door swings open with a groan. Inside, resting on a pedestal of black stone, "
                  "sits the legendary Golden Standard, a golden orb in which every rule of SQL ever agreed "
                  "is written, humming with ancient power. Congratulations, {name}! Your name will be "
                  "carved among the great coders of Sequelia.".format(name=player["name"]))
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
    nine ultimate questions, picked at random. Right: the title of ANSI SQL Master and
    BOSS_POINTS besides. Wrong: all is lost, the score falls to zero. Returns "win", since
    the quest that led here was won."""
    quest.banner("boss")
    quest.narrate("You have walked every path in Sequelia. As you leave the temple for the last time, its "
                  "floor slides open onto a stair that winds down into a ruined hall without end, and "
                  "something vast stirs in it. The Cartesian Beast rises from the dark, a horned giant "
                  "with claws like scythes, and before it hang two glowing tables joined by nothing at "
                  "all: every row of one meets every row of the other, and the Beast feeds on all the rows "
                  'they make. It has never met a table it didn\'t multiply. "Every path, every level," it '
                  'roars. "One question remains. Answer it, and you are an ANSI SQL Master. Fail, and I '
                  'join your treasure to nothing."')
    question = quest.rng.choice(BOSS_QUESTIONS)
    if (yield from ask_question(quest, "The Cartesian Beast", question, BOSS_POINTS, "ANSI SQL Master")):
        quest.boss = "won"
        quest.narrate("The Beast lowers its great horned head until its blazing eyes are level with yours, "
                      'and the tables before it go dark. "Well answered, Master." From this day on, the '
                      "coders of Sequelia will know you by your new title.")
        quest.note("relic", "You are an ANSI SQL Master!")
    else:
        quest.boss = "lost"
        quest.player["score"] = 0
        quest.narrate("The Beast roars with laughter and CROSS JOINs your treasure with an empty table. "
                      "Every coin, relic and point you carried, times nothing, is nothing, and you wake at "
                      "the edge of Sequelia with nothing but a backpack and your wits.")
        quest.note("life", "All is lost! Your score falls to 0.")
    return "win"


def game_over(quest, message):
    """End the quest with a failure message."""
    quest.narrate(message)
    quest.banner("game_over")
    return "lose"
