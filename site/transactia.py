"""
The Lost Commit of Transactia
-----------------------------
The T-SQL adventure: a copy of the Python game (pythonia.py), the same story in the same
places, played the same way, but with its own words and every riddle about Transact-SQL,
the dialect of Microsoft SQL Server (2022, with its default settings unless a riddle SETs
otherwise).

Like pythonia.py:
- Wherever a console game would wait for input(), these functions *yield* a prompt (a
  Choice or a Question) and the page's buttons send the explorer's answer back in.
- A quest is saved as its random seed plus the moves made so far, and replay() plays it
  again from the start with those moves for every page.
- A winner can carry their score on: to the next level (next_level()), or down a path not
  taken yet (paths_left()), without the questions the level's earlier paths asked.
- After a win, the explorer may wake that path and level's dragon (DRAGONS,
  dragon_battle()) for one bonus riddle.
- An explorer who completes every path on every level may face the Deadlock, the final
  boss (boss_battle()): one of the nine hardest questions (BOSS_QUESTIONS), for the title
  of T-SQL Master, or the loss of their whole score.

tools/check-sql-questions.py runs every snippet on a SQL Server to check its answer.
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
        "topics": "variables, PRINT, data types, + and NULL, string functions, TOP",
    },
    "medium": {
        "lives": 2,
        "multiplier": 2,
        "topics": "batches, WHILE, TRY...CATCH, dates, conversions, APPLY, CTEs",
    },
    "hard": {
        "lives": 1,
        "multiplier": 3,
        "topics": "transactions, error handling, IDENTITY, MERGE, PIVOT, NULL quirks",
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
    "forest": "Explore the #Temp Forest",
    "cave": "Enter the Cursor Caves",
    "castle": "Climb to the Ruins of Castle Sybase",
}
PATH_NAMES = {
    "forest": "the #Temp Forest",
    "cave": "the Cursor Caves",
    "castle": "the Ruins of Castle Sybase",
}
PATH_SIGHTS = {
    "forest": "the #Temp Forest, whose trees vanish the moment you leave",
    "cave": "the Cursor Caves, where travelers go one row at a time",
    "castle": "the torch-lit trail that climbs to the Ruins of Castle Sybase",
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
# T-SQL challenges for each difficulty level
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
            "code": "SELECT gold = 5 * 2;",
            "options": ["10", "1", "Error", "No rows"],
            "answer": "10",
            "explain": "In T-SQL, name = expression is another way to write a column alias, so this is 5 * "
                       "2 AS gold. It's only an assignment when the name starts with @.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "DECLARE @gold INT;\n"
                "SET @gold = @gold + 10;\n"
                "SELECT @gold;"
            ),
            "options": ["NULL", "10", "0", "Error"],
            "answer": "NULL",
            "explain": "A declared variable starts as NULL, not 0, and NULL + 10 is still NULL.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE @gold INT = 7;\n"
                "PRINT @gold / 2;"
            ),
            "options": ["3", "3.5", "4", "3.500000"],
            "answer": "3",
            "explain": "Both sides are integers, so / does integer division and drops the fraction.",
        },
        {
            "prompt": "What does this query return?",
            "code": "SELECT '5' + 3, '5' + '3';",
            "options": ["8 53", "53 53", "8 8", "Error"],
            "answer": "8 53",
            "explain": "INT has a higher data type precedence than VARCHAR, so '5' is converted to 5 and "
                       "added. With two strings, + joins them.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "DECLARE @title VARCHAR(20);\n"
                "SELECT 'Sir' + @title, CONCAT('Sir', @title);"
            ),
            "options": ["NULL Sir", "Sir Sir", "NULL NULL", "Sir NULL"],
            "answer": "NULL Sir",
            "explain": "Joining a NULL with + gives NULL (CONCAT_NULL_YIELDS_NULL is ON), but CONCAT "
                       "treats a NULL as an empty string.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "DECLARE @s NVARCHAR(10) = N'gem  ';  -- two trailing spaces\n"
                "SELECT LEN(@s), DATALENGTH(@s);"
            ),
            "options": ["3 10", "5 10", "3 5", "5 5"],
            "answer": "3 10",
            "explain": "LEN counts characters but ignores trailing spaces. DATALENGTH counts bytes, and "
                       "NVARCHAR uses 2 bytes per character: 5 x 2 = 10.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "DECLARE @gold INT = 10;\n"
                "SELECT IIF(@gold > 10, 'rich', 'poor');"
            ),
            "options": ["poor", "rich", "NULL", "Error"],
            "answer": "poor",
            "explain": "IIF(condition, a, b) is a shorthand CASE. 10 > 10 is false, so the third argument "
                       "is returned.",
        },
        {
            "prompt": "What does this query return?",
            "code": "SELECT CHOOSE(2, 'Orb', 'Ring', 'Crown');",
            "options": ["Ring", "Crown", "Orb", "2"],
            "answer": "Ring",
            "explain": "CHOOSE picks a value from its list by position, counting from 1, so 2 is the "
                       "second one.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "IF 'DRAGON' = 'dragon'\n"
                "    PRINT 'same'\n"
                "ELSE\n"
                "    PRINT 'different';"
            ),
            "options": ["same", "different", "Error", "Nothing is printed"],
            "answer": "same",
            "explain": "The default collation, SQL_Latin1_General_CP1_CI_AS, is case-insensitive (that's "
                       "the CI), so upper and lower case compare equal.",
        },
        {
            "prompt": "What does this query return?",
            "code": "SELECT CHARINDEX('z', 'Dragon');",
            "options": ["0", "NULL", "-1", "Error"],
            "answer": "0",
            "explain": "CHARINDEX gives the position of the first match, counting from 1, and 0 (not NULL "
                       "or -1) when there isn't one.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE @lit BIT = 5;\n"
                "PRINT @lit;"
            ),
            "options": ["1", "5", "0", "Error"],
            "answer": "1",
            "explain": "BIT holds only 0 and 1 (or NULL), and converting any nonzero number to BIT gives 1.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- knights\n"
                "--  name     | gold\n"
                "--  Arthur   | 40\n"
                "--  Gawain   | 90\n"
                "--  Lancelot | 70\n"
                "--  Percival | 10\n"
                "SELECT TOP 2 name FROM knights ORDER BY gold DESC;"
            ),
            "setup": (
                "CREATE TABLE knights (name VARCHAR(10), gold INT);\n"
                "INSERT INTO knights VALUES ('Arthur', 40), ('Gawain', 90), ('Lancelot', 70), ('Percival', 10);"
            ),
            "options": ["Gawain, Lancelot", "Arthur, Gawain", "Lancelot, Arthur", "Percival, Arthur"],
            "answer": "Gawain, Lancelot",
            "explain": "TOP 2 keeps the first two rows after ORDER BY, here the two richest knights. TOP "
                       "is T-SQL's way to say LIMIT.",
        },
        {
            "prompt": "In T-SQL, which name makes a temporary table that only your own session can see?",
            "options": ["#loot", "##loot", "@loot", "$loot"],
            "answer": "#loot",
            "explain": "One # makes a local temp table, just for your session. ## makes a global one that "
                       "every session can see, and @loot would be a table variable.",
        },
        {
            "prompt": "What is GO in a SQL Server script?",
            "options": [
                "A batch separator for tools like SSMS",
                "A statement that commits the transaction",
                "A statement that runs a procedure",
                "A label that GOTO can jump to",
            ],
            "answer": "A batch separator for tools like SSMS",
            "explain": "GO isn't T-SQL at all: SSMS and sqlcmd cut the script at each GO and send each "
                       "part to the server as a batch of its own.",
        },
        {
            "prompt": "Which FROM clause does SELECT 1 + 1; need in T-SQL?",
            "options": ["None: FROM is optional", "FROM DUAL", "FROM sys.dual", "FROM SYSIBM.SYSDUMMY1"],
            "answer": "None: FROM is optional",
            "explain": "SQL Server lets a SELECT run without any FROM clause, so there's no need for a "
                       "dummy table like Oracle's DUAL.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "IF '' IS NULL\n"
                "    PRINT 'null'\n"
                "ELSE\n"
                "    PRINT 'not null';"
            ),
            "options": ["not null", "null", "Error", "Nothing is printed"],
            "answer": "not null",
            "explain": "In SQL Server an empty string is a real value with length 0, not NULL (unlike "
                       "Oracle, where '' is NULL).",
        },
        {
            "prompt": "What does this query return?",
            "code": "SELECT 2 > 1;",
            "options": ["Error: incorrect syntax", "1", "true", "2"],
            "answer": "Error: incorrect syntax",
            "explain": "T-SQL has no Boolean type you can select. A comparison can only go where a "
                       "condition belongs, such as WHERE, IF or CASE WHEN.",
            "expect_error": True,
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE @gold INT = 10;\n"
                "SET @gold += 5;\n"
                "SET @gold *= 2;\n"
                "PRINT @gold;"
            ),
            "options": ["30", "20", "25", "15"],
            "answer": "30",
            "explain": "+= and *= are T-SQL's compound assignments: 10 + 5 is 15, then 15 * 2 is 30.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE @gems TABLE (name VARCHAR(10), value INT);\n"
                "INSERT INTO @gems\n"
                "VALUES ('Ruby', 5), ('Opal', 3), ('Jade', 8);\n"
                "UPDATE @gems SET value = value + 1 WHERE value > 4;\n"
                "PRINT @@ROWCOUNT;"
            ),
            "options": ["2", "3", "1", "0"],
            "answer": "2",
            "explain": "@@ROWCOUNT holds the number of rows the last statement affected: the UPDATE "
                       "changed Ruby and Jade.",
        },
        {
            "prompt": "What does this query return?",
            "code": "SELECT PATINDEX('%[0-9]%', 'Gate42');",
            "options": ["5", "6", "4", "0"],
            "answer": "5",
            "explain": "In T-SQL patterns, [0-9] matches any one digit. PATINDEX gives the position where "
                       "the first match starts: the 4 is the 5th character.",
        },
    ],
    "medium": [
        {
            "prompt": "What does this query return?",
            "code": "SELECT -7 / 2, -7 % 2;",
            "options": ["-3 -1", "-4 1", "-3 1", "-4 -1"],
            "answer": "-3 -1",
            "explain": "Integer division truncates toward zero, so -3.5 becomes -3, and % takes the sign "
                       "of the left number: -7 - (-3 * 2) = -1.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "DECLARE @code VARCHAR(2);\n"
                "SELECT ISNULL(@code, 'none'), COALESCE(@code, 'none');"
            ),
            "options": ["no none", "none none", "none no", "NULL none"],
            "answer": "no none",
            "explain": "ISNULL returns the type of its first argument, VARCHAR(2), so 'none' is cut to "
                       "'no'. COALESCE works like a CASE, long enough for every argument.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "DECLARE @chest TABLE (amount INT);  -- no rows\n"
                "DECLARE @a INT = 5, @b INT = 5;\n"
                "SELECT @a = amount FROM @chest;\n"
                "SET @b = (SELECT amount FROM @chest);\n"
                "SELECT @a, @b;"
            ),
            "options": ["5 NULL", "NULL NULL", "5 5", "NULL 5"],
            "answer": "5 NULL",
            "explain": "When SELECT @a = ... finds no rows, nothing is assigned and @a keeps its value. A "
                       "subquery that finds no rows is NULL, so SET makes @b NULL.",
        },
        {
            "prompt": "What happens when this runs?",
            "code": (
                "DECLARE @chest TABLE (amount INT);\n"
                "INSERT INTO @chest VALUES (10), (20);\n"
                "DECLARE @gold INT;\n"
                "SET @gold = (SELECT amount FROM @chest);"
            ),
            "options": [
                "Error: subquery returned more than 1 value",
                "@gold is 20",
                "@gold is 10",
                "@gold is NULL",
            ],
            "answer": "Error: subquery returned more than 1 value",
            "explain": "A subquery used as a value may return at most one row, so with two it fails (error "
                       "512). SELECT @gold = amount would quietly take one instead.",
            "expect_error": True,
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE @i INT = 0, @n INT = 0;\n"
                "WHILE @i < 3\n"
                "    SET @i += 1;\n"
                "    SET @n += 1;\n"
                "PRINT @n;"
            ),
            "options": ["1", "3", "0", "4"],
            "answer": "1",
            "explain": "Without BEGIN...END, WHILE repeats only the one statement after it. The indented "
                       "SET @n isn't in the loop (indentation means nothing to T-SQL).",
        },
        {
            "prompt": "What happens when this script runs in SSMS?",
            "code": (
                "DECLARE @gold INT = 5;\n"
                "GO\n"
                "PRINT @gold;"
            ),
            "options": ["Error: Must declare the scalar variable", "5", "NULL", "Nothing is printed"],
            "answer": "Error: Must declare the scalar variable",
            "explain": "A variable lives only in the batch that declares it. GO ends that batch, so the "
                       "second batch has never heard of @gold.",
            "expect_error": True,
        },
        {
            "prompt": "What does this query return?",
            "code": "SELECT DATEDIFF(year, '20251231', '20260101');",
            "options": ["1", "0", "NULL", "Error"],
            "answer": "1",
            "explain": "DATEDIFF counts the boundaries crossed, not whole periods. The dates are a day "
                       "apart, but they cross the start of a year, so the answer is 1.",
        },
        {
            "prompt": "What does this query return?",
            "code": "SELECT DAY(DATEADD(month, 1, '20260131'));",
            "options": ["28", "31", "3", "Error"],
            "answer": "28",
            "explain": "A month after 31 January would be a day February doesn't have, so DATEADD gives "
                       "the last day of February instead: the 28th in 2026.",
        },
        {
            "prompt": "What does this query return?",
            "code": "SELECT TRY_CAST('3.5' AS INT), TRY_CAST('35' AS INT);",
            "options": ["NULL 35", "3 35", "4 35", "Error"],
            "answer": "NULL 35",
            "explain": "A string with a decimal point can't be converted straight to INT (CAST would "
                       "fail), so TRY_CAST returns NULL instead of raising an error.",
        },
        {
            "prompt": "What does this query return?",
            "code": "SELECT CAST(9.99 AS INT), CAST(9.99 AS DECIMAL(3, 0));",
            "options": ["9 10", "10 10", "9 9", "10 9"],
            "answer": "9 10",
            "explain": "Converting a decimal to an integer type truncates, but converting it to a decimal "
                       "with fewer places rounds. Both rules are in the CAST docs.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE @x INT;\n"
                "BEGIN TRY\n"
                "    SET @x = 1 / 0;\n"
                "    PRINT 'after';\n"
                "END TRY\n"
                "BEGIN CATCH\n"
                "    PRINT ERROR_MESSAGE();\n"
                "END CATCH"
            ),
            "options": [
                "Divide by zero error encountered.",
                "after",
                "after Divide by zero error encountered.",
                "Error: divide by zero",
            ],
            "answer": "Divide by zero error encountered.",
            "explain": "The error jumps straight to the CATCH block, skipping the rest of TRY, and "
                       "ERROR_MESSAGE() gives the error's text.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- heroes: Arthur, Gawain, Percival\n"
                "-- deeds\n"
                "--  hero   | gold\n"
                "--  Arthur | 50\n"
                "--  Arthur | 20\n"
                "--  Gawain | 30\n"
                "SELECT h.name, d.gold\n"
                "FROM heroes AS h\n"
                "CROSS APPLY (SELECT TOP 1 gold FROM deeds\n"
                "             WHERE hero = h.name\n"
                "             ORDER BY gold DESC) AS d\n"
                "ORDER BY h.name;"
            ),
            "setup": (
                "CREATE TABLE heroes (name VARCHAR(10));\n"
                "INSERT INTO heroes VALUES ('Arthur'), ('Gawain'), ('Percival');\n"
                "CREATE TABLE deeds (hero VARCHAR(10), gold INT);\n"
                "INSERT INTO deeds VALUES ('Arthur', 50), ('Arthur', 20), ('Gawain', 30);"
            ),
            "options": [
                "Arthur 50, Gawain 30",
                "Arthur 50, Gawain 30, Percival NULL",
                "Arthur 20, Gawain 30",
                "Arthur 50, Arthur 20, Gawain 30",
            ],
            "answer": "Arthur 50, Gawain 30",
            "explain": "CROSS APPLY runs the subquery once per hero, using h.name inside it. Like an inner "
                       "join it drops heroes with no result (OUTER APPLY keeps them).",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- gem_names\n"
                "--  name\n"
                "--  Ruby\n"
                "--  NULL\n"
                "--  Jade\n"
                "SELECT STRING_AGG(name, '-')\n"
                "       WITHIN GROUP (ORDER BY name)\n"
                "FROM gem_names;"
            ),
            "setup": (
                "CREATE TABLE gem_names (name VARCHAR(10));\n"
                "INSERT INTO gem_names VALUES ('Ruby'), (NULL), ('Jade');"
            ),
            "options": ["Jade-Ruby", "-Jade-Ruby", "Jade--Ruby", "NULL"],
            "answer": "Jade-Ruby",
            "explain": "STRING_AGG skips NULLs completely, without adding a separator for them, and WITHIN "
                       "GROUP sets the order.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "SELECT AVG(gold)\n"
                "FROM (VALUES (1), (2)) AS v(gold);"
            ),
            "options": ["1", "1.5", "2", "1.500000"],
            "answer": "1",
            "explain": "In SQL Server, AVG of an INT column returns an INT, so 1.5 is truncated to 1. "
                       "AVG(gold * 1.0) would keep the decimals.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "SELECT LEFT(name, 1) AS initial, COUNT(*)\n"
                "FROM (VALUES ('Ruby'), ('Rose'), ('Opal')) AS g(name)\n"
                "GROUP BY initial;"
            ),
            "options": ["Error: Invalid column name 'initial'", "O 1, R 2", "R 3", "No rows"],
            "answer": "Error: Invalid column name 'initial'",
            "explain": "GROUP BY is processed before SELECT, so it can't see the alias. SQL Server makes "
                       "you repeat the expression: GROUP BY LEFT(name, 1).",
            "expect_error": True,
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "WITH n AS (\n"
                "    SELECT 1 AS i\n"
                "    UNION ALL\n"
                "    SELECT i + 1 FROM n WHERE i < 5\n"
                ")\n"
                "SELECT SUM(i) FROM n;"
            ),
            "options": ["15", "10", "5", "Error: RECURSIVE is missing"],
            "answer": "15",
            "explain": "T-SQL has no RECURSIVE keyword: a CTE that refers to itself is recursive. This one "
                       "makes 1 to 5, which add up to 15.",
        },
        {
            "prompt": "What does this return?",
            "code": (
                "DECLARE @gems TABLE (name VARCHAR(10), value INT);\n"
                "INSERT INTO @gems VALUES ('Ruby', 5), ('Opal', 3);\n"
                "UPDATE @gems\n"
                "SET value = value * 2\n"
                "OUTPUT deleted.value, inserted.value\n"
                "WHERE name = 'Ruby';"
            ),
            "options": ["5 10", "10 10", "10 5", "5 5"],
            "answer": "5 10",
            "explain": "The OUTPUT clause returns rows from the change itself: deleted holds each row as "
                       "it was before the UPDATE, and inserted as it is after.",
        },
        {
            "prompt": "Which T-SQL statement must always end with a semicolon?",
            "options": ["MERGE", "SELECT", "UPDATE", "INSERT"],
            "answer": "MERGE",
            "explain": "Semicolons are mostly optional in T-SQL, but MERGE requires one (error 10713 "
                       "without it). It's good style to end every statement with one.",
        },
        {
            "prompt": "Which of these must be the first statement in its batch?",
            "options": ["CREATE VIEW", "CREATE TABLE", "CREATE INDEX", "DECLARE"],
            "answer": "CREATE VIEW",
            "explain": "CREATE VIEW, PROCEDURE, FUNCTION and TRIGGER must each be the first statement in a "
                       "batch (error 111), which is why scripts put GO before them.",
        },
        {
            "prompt": "After an INSERT, which gives the IDENTITY value your own statement made, even if a "
                      "trigger then inserted into another table?",
            "options": ["SCOPE_IDENTITY()", "@@IDENTITY", "IDENT_CURRENT('t')", "@@ROWCOUNT"],
            "answer": "SCOPE_IDENTITY()",
            "explain": "@@IDENTITY is the last identity made in the session in any scope, so a trigger's "
                       "insert changes it. SCOPE_IDENTITY() stays in your own scope.",
        },
    ],
    "hard": [
        {
            "prompt": "What does this print?",
            "code": (
                "DECLARE @bonus INT;\n"
                "DECLARE @t TABLE (n INT);\n"
                "INSERT INTO @t VALUES (1), (2), (3);\n"
                "SET @bonus = 10;\n"
                "PRINT @@ROWCOUNT;"
            ),
            "options": ["1", "3", "0", "10"],
            "answer": "1",
            "explain": "@@ROWCOUNT is reset by almost every statement. A simple assignment like SET @bonus "
                       "= 10 always sets it to 1, so read it right after the INSERT.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- quests (id INT IDENTITY(1, 1), name) is empty\n"
                "BEGIN TRAN;\n"
                "INSERT INTO quests (name) VALUES ('Grail');\n"
                "ROLLBACK;\n"
                "INSERT INTO quests (name) VALUES ('Dragon');\n"
                "SELECT id, name FROM quests;"
            ),
            "setup": "CREATE TABLE quests (id INT IDENTITY(1, 1), name VARCHAR(10));",
            "options": ["2 Dragon", "1 Dragon", "1 Grail, 2 Dragon", "No rows"],
            "answer": "2 Dragon",
            "explain": "ROLLBACK removes the row but not the IDENTITY value it used. SQL Server never "
                       "hands that value out again, which is how gaps appear.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- loot (n INT) is an empty table\n"
                "DECLARE @bag TABLE (n INT);\n"
                "BEGIN TRAN;\n"
                "INSERT INTO loot VALUES (1);\n"
                "INSERT INTO @bag VALUES (1);\n"
                "ROLLBACK;\n"
                "SELECT (SELECT COUNT(*) FROM loot),\n"
                "       (SELECT COUNT(*) FROM @bag);"
            ),
            "setup": "CREATE TABLE loot (n INT);",
            "options": ["0 1", "0 0", "1 1", "1 0"],
            "answer": "0 1",
            "explain": "Table variables, like other variables, aren't affected by a ROLLBACK, so @bag "
                       "keeps its row while the insert into the real table is undone.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- treasure (n INT) is an empty table\n"
                "BEGIN TRAN;\n"
                "INSERT INTO treasure VALUES (1);\n"
                "BEGIN TRAN;\n"
                "INSERT INTO treasure VALUES (2);\n"
                "COMMIT;\n"
                "ROLLBACK;\n"
                "SELECT COUNT(*) FROM treasure;"
            ),
            "setup": "CREATE TABLE treasure (n INT);",
            "options": ["0", "1", "2", "Error"],
            "answer": "0",
            "explain": "SQL Server has no real nested transactions. The inner COMMIT only takes "
                       "@@TRANCOUNT from 2 to 1, so the ROLLBACK undoes both rows.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "BEGIN TRY\n"
                "    RAISERROR('A whisper', 10, 1);\n"
                "    PRINT 'still here';\n"
                "END TRY\n"
                "BEGIN CATCH\n"
                "    PRINT 'caught';\n"
                "END CATCH"
            ),
            "options": ["A whisper still here", "caught", "A whisper caught", "still here"],
            "answer": "A whisper still here",
            "explain": "Severity 10 or lower is just an informational message, sent like PRINT. CATCH only "
                       "catches severity 11 and up, so TRY carries on.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "BEGIN TRY\n"
                "    THROW 50001, 'The gate is sealed', 1;\n"
                "END TRY\n"
                "BEGIN CATCH\n"
                "    PRINT ERROR_SEVERITY();\n"
                "END CATCH"
            ),
            "options": ["16", "1", "10", "50001"],
            "answer": "16",
            "explain": "THROW has no severity argument (the 1 is the state): it always raises severity 16. "
                       "RAISERROR is the one where you choose.",
        },
        {
            "prompt": "What does this print?",
            "code": (
                "-- coffer (n INT PRIMARY KEY) is an empty table\n"
                "SET XACT_ABORT ON;\n"
                "BEGIN TRY\n"
                "    BEGIN TRAN;\n"
                "    INSERT INTO coffer VALUES (1);\n"
                "    INSERT INTO coffer VALUES (1);\n"
                "    COMMIT;\n"
                "END TRY\n"
                "BEGIN CATCH\n"
                "    PRINT XACT_STATE();\n"
                "    ROLLBACK;\n"
                "END CATCH"
            ),
            "setup": "CREATE TABLE coffer (n INT PRIMARY KEY);",
            "options": ["-1", "1", "0", "2"],
            "answer": "-1",
            "explain": "With XACT_ABORT ON, an error makes the open transaction uncommittable, or doomed: "
                       "XACT_STATE() is -1, and all you can do is ROLLBACK.",
        },
        {
            "prompt": "What does this return?",
            "code": (
                "-- vault (gem, qty): Ruby 1, Opal 2\n"
                "-- haul  (gem, qty): Ruby 4, Jade 3\n"
                "MERGE vault AS v\n"
                "USING haul AS h ON v.gem = h.gem\n"
                "WHEN MATCHED THEN\n"
                "    UPDATE SET qty = v.qty + h.qty\n"
                "WHEN NOT MATCHED THEN\n"
                "    INSERT (gem, qty) VALUES (h.gem, h.qty)\n"
                "WHEN NOT MATCHED BY SOURCE THEN\n"
                "    DELETE;\n"
                "SELECT gem, qty FROM vault ORDER BY gem;"
            ),
            "setup": (
                "CREATE TABLE vault (gem VARCHAR(10), qty INT);\n"
                "INSERT INTO vault VALUES ('Ruby', 1), ('Opal', 2);\n"
                "CREATE TABLE haul (gem VARCHAR(10), qty INT);\n"
                "INSERT INTO haul VALUES ('Ruby', 4), ('Jade', 3);"
            ),
            "options": ["Jade 3, Ruby 5", "Jade 3, Opal 2, Ruby 5", "Jade 3, Ruby 4", "Opal 2, Ruby 5"],
            "answer": "Jade 3, Ruby 5",
            "explain": "Ruby is in both, so it's updated to 1 + 4. Jade is only in the source, so it's "
                       "inserted. Opal is only in the target, so BY SOURCE deletes it.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "WITH n AS (\n"
                "    SELECT 1 AS i\n"
                "    UNION ALL\n"
                "    SELECT i + 1 FROM n WHERE i < 200\n"
                ")\n"
                "SELECT MAX(i) FROM n;"
            ),
            "options": ["Error: maximum recursion 100 exhausted", "200", "100", "101"],
            "answer": "Error: maximum recursion 100 exhausted",
            "explain": "A recursive CTE may only recurse 100 times by default. Adding OPTION (MAXRECURSION "
                       "200), or 0 for no limit, lets it go deeper.",
            "expect_error": True,
        },
        {
            "prompt": "What does this query return?",
            "code": "SELECT COALESCE(NULL, NULL);",
            "options": ["Error", "NULL", "0", "An empty string"],
            "answer": "Error",
            "explain": "COALESCE needs at least one argument that isn't the bare NULL keyword, to work out "
                       "its result type. ISNULL(NULL, NULL) would just return NULL.",
            "expect_error": True,
        },
        {
            "prompt": "What does this query return?",
            "code": "SELECT ISNUMERIC('$') + ISNUMERIC('-') + ISNUMERIC('gem');",
            "options": ["2", "0", "1", "3"],
            "answer": "2",
            "explain": "ISNUMERIC returns 1 for some strings that aren't numbers, such as a lone '-', '+' "
                       "or a currency sign like '$'. TRY_CAST is the safer test.",
        },
        {
            "prompt": "What does this query return?",
            "code": "SELECT GREATEST(3, NULL, 7);",
            "options": ["7", "NULL", "3", "Error"],
            "answer": "7",
            "explain": "SQL Server 2022's GREATEST ignores NULL arguments, and returns NULL only when "
                       "they're all NULL. Some other databases return NULL here.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- spoils\n"
                "--  knight | item | qty\n"
                "--  Arthur | gold | 5\n"
                "--  Arthur | gems | 2\n"
                "--  Gawain | gold | 3\n"
                "--  Arthur | gold | 1\n"
                "SELECT knight, gold, gems\n"
                "FROM spoils\n"
                "PIVOT (SUM(qty) FOR item IN (gold, gems)) AS p\n"
                "ORDER BY knight;"
            ),
            "setup": (
                "CREATE TABLE spoils (knight VARCHAR(10), item VARCHAR(10), qty INT);\n"
                "INSERT INTO spoils VALUES ('Arthur', 'gold', 5), ('Arthur', 'gems', 2), ('Gawain', 'gold', 3), ('Arthur', 'gold', 1);"
            ),
            "options": [
                "Arthur 6 2, Gawain 3 NULL",
                "Arthur 6 2, Gawain 3 0",
                "Arthur 5 2, Gawain 3 NULL",
                "Arthur 5 2, Arthur 1 NULL, Gawain 3 NULL",
            ],
            "answer": "Arthur 6 2, Gawain 3 NULL",
            "explain": "PIVOT groups by every column it doesn't use (knight), sums qty into one column per "
                       "IN value, and leaves NULL where a knight has none.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- gem_list: Ruby, Opal\n"
                "SELECT name\n"
                "FROM (SELECT name FROM gem_list\n"
                "      ORDER BY name) AS d;"
            ),
            "setup": (
                "CREATE TABLE gem_list (name VARCHAR(10));\n"
                "INSERT INTO gem_list VALUES ('Ruby'), ('Opal');"
            ),
            "options": ["Error: ORDER BY is invalid here", "Opal, Ruby", "Ruby, Opal", "No rows"],
            "answer": "Error: ORDER BY is invalid here",
            "explain": "A derived table, view or CTE is a set, with no order, so SQL Server rejects ORDER "
                       "BY there unless TOP, OFFSET or FOR XML is used too.",
            "expect_error": True,
        },
        {
            "prompt": "In SQL Server, how many NULLs can a column with a UNIQUE constraint hold?",
            "options": ["One", "Any number", "None", "Two"],
            "answer": "One",
            "explain": "SQL Server treats NULLs as equal for UNIQUE, so a second NULL is a duplicate. A "
                       "filtered unique index (WHERE col IS NOT NULL) allows many.",
        },
        {
            "prompt": "What does this query return?",
            "code": (
                "-- gold_bars holds 3 rows\n"
                "BEGIN TRAN;\n"
                "TRUNCATE TABLE gold_bars;\n"
                "ROLLBACK;\n"
                "SELECT COUNT(*) FROM gold_bars;"
            ),
            "setup": (
                "CREATE TABLE gold_bars (n INT);\n"
                "INSERT INTO gold_bars VALUES (1), (2), (3);"
            ),
            "options": ["3", "0", "Error", "1"],
            "answer": "3",
            "explain": "In SQL Server, TRUNCATE TABLE is fully transactional, so a ROLLBACK brings the "
                       "rows back. (In Oracle, TRUNCATE commits at once.)",
        },
        {
            "prompt": "What does this return?",
            "code": (
                "DECLARE @x INT;\n"
                "BEGIN TRY\n"
                "    SET @x = 1 / 0;\n"
                "END TRY\n"
                "BEGIN CATCH\n"
                "    SET @x = 0;\n"
                "    SELECT @@ERROR, ERROR_NUMBER();\n"
                "END CATCH"
            ),
            "options": ["0 8134", "8134 8134", "8134 0", "0 0"],
            "answer": "0 8134",
            "explain": "@@ERROR describes only the statement just run, and SET @x = 0 worked. "
                       "ERROR_NUMBER() keeps the caught error (8134) all through CATCH.",
        },
        {
            "prompt": "What happens when this runs?",
            "code": (
                "EXEC('CREATE TABLE #map (n INT)');\n"
                "SELECT COUNT(*) FROM #map;"
            ),
            "options": ["Error: Invalid object name '#map'", "0", "NULL", "No rows"],
            "answer": "Error: Invalid object name '#map'",
            "explain": "Dynamic SQL runs in a scope of its own, and a temp table is dropped when the scope "
                       "that made it ends. (One made outside is visible inside.)",
            "expect_error": True,
        },
        {
            "prompt": "With XACT_ABORT OFF (the default), an INSERT inside an open transaction fails with "
                      "a duplicate key. What happens?",
            "options": [
                "Only that INSERT fails; the tran goes on",
                "The whole transaction is rolled back",
                "The work so far is committed",
                "The connection is closed",
            ],
            "answer": "Only that INSERT fails; the tran goes on",
            "explain": "With XACT_ABORT OFF, an error like a constraint violation ends just that "
                       "statement. The transaction stays open, and COMMIT would save the rest.",
        },
        {
            "prompt": "Inside a CATCH block, what does THROW; with no arguments do?",
            "options": [
                "Re-raises the error being handled",
                "Raises a new error 50000",
                "Leaves the CATCH block quietly",
                "Rolls back and ends the batch",
            ],
            "answer": "Re-raises the error being handled",
            "explain": "THROW with no arguments raises the caught error again, with its own number and "
                       "message. It's only allowed inside a CATCH block.",
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
    "forest": "On your way back through the #Temp Forest, before it vanishes, a glint of gold catches your "
              "eye in a mossy hollow.",
    "cave": "On your way back out of the Cursor Caves, a glint of gold catches your eye in a side cavern, "
            "one row along.",
    "castle": "On your way back through Castle Sybase, a glint of gold catches your eye through a doorway: "
              "a forgotten treasury.",
}

DRAGONS = {
    ("easy", "cave"): {
        "scene": "dragon-emerald", "scales": "green as moss",
        "question": {
            "prompt": "What does this query return?",
            "code": (
                "DECLARE @name VARCHAR = 'Lancelot';\n"
                "SELECT @name;"
            ),
            "options": ["L", "Lancelot", "NULL", "Error"],
            "answer": "L",
            "explain": "VARCHAR with no length means VARCHAR(1) in a DECLARE, so the value is silently cut "
                       "to its first letter. (In CAST, the default is 30.)",
        },
    },
    ("medium", "cave"): {
        "scene": "dragon-ember", "scales": "glowing like hot coals",
        "question": {
            "prompt": "What does this print?",
            "code": (
                "DECLARE @i INT = 0, @sum INT = 0;\n"
                "WHILE @i < 10\n"
                "BEGIN\n"
                "    SET @i += 1;\n"
                "    IF @i % 2 = 0 CONTINUE;\n"
                "    IF @i > 7 BREAK;\n"
                "    SET @sum += @i;\n"
                "END\n"
                "PRINT @sum;"
            ),
            "options": ["16", "25", "9", "20"],
            "answer": "16",
            "explain": "CONTINUE skips the even numbers, and BREAK stops the loop at 9, before it's added. "
                       "So only 1 + 3 + 5 + 7 = 16.",
        },
    },
    ("hard", "cave"): {
        "scene": "dragon-frost", "scales": "glittering with ice",
        "question": {
            "prompt": "What does this query return?",
            "code": (
                "-- hoards\n"
                "--  knight | gold | gems\n"
                "--  Arthur | 5    | NULL\n"
                "--  Gawain | 3    | 2\n"
                "SELECT COUNT(*)\n"
                "FROM hoards\n"
                "UNPIVOT (qty FOR item IN (gold, gems)) AS u;"
            ),
            "setup": (
                "CREATE TABLE hoards (knight VARCHAR(10), gold INT, gems INT);\n"
                "INSERT INTO hoards VALUES ('Arthur', 5, NULL), ('Gawain', 3, 2);"
            ),
            "options": ["3", "4", "2", "Error"],
            "answer": "3",
            "explain": "UNPIVOT turns the gold and gems columns into rows, but silently drops any whose "
                       "value is NULL, so Arthur's gems vanish: 4 - 1 = 3.",
        },
    },
    ("easy", "forest"): {
        "scene": "dragon-pearl", "scales": "white as moonlight",
        "question": {
            "prompt": "What does this query return?",
            "code": "SELECT CHARINDEX('o', 'Dragon hoard', 6);",
            "options": ["9", "5", "4", "3"],
            "answer": "9",
            "explain": "The third argument says where to start looking (at the n), but the answer is still "
                       "counted from the start of the string: the o in hoard is 9th.",
        },
    },
    ("medium", "forest"): {
        "scene": "dragon-amethyst", "scales": "a deep, shimmering purple",
        "question": {
            "prompt": "What does this print?",
            "code": "PRINT 7 / 2.0;",
            "options": ["3.500000", "3.5", "3", "4"],
            "answer": "3.500000",
            "explain": "2.0 is a DECIMAL, so this is decimal division, not integer division. SQL Server "
                       "gives a decimal division at least 6 decimal places: 3.500000.",
        },
    },
    ("hard", "forest"): {
        "scene": "dragon-autumn", "scales": "the color of falling leaves",
        "question": {
            "prompt": "What does this query return?",
            "code": (
                "-- plunder (n INT) is an empty table\n"
                "BEGIN TRAN;\n"
                "BEGIN TRAN;\n"
                "INSERT INTO plunder VALUES (1);\n"
                "ROLLBACK;\n"
                "SELECT @@TRANCOUNT, COUNT(*) FROM plunder;"
            ),
            "setup": "CREATE TABLE plunder (n INT);",
            "options": ["0 0", "1 0", "1 1", "0 1"],
            "answer": "0 0",
            "explain": "A plain ROLLBACK always rolls back the outermost transaction, however deep the "
                       "nesting, and sets @@TRANCOUNT to 0.",
        },
    },
    ("easy", "castle"): {
        "scene": "dragon-gold", "scales": "as bright as the coins beneath it",
        "question": {
            "prompt": "What does this query return?",
            "code": (
                "-- champions\n"
                "--  name     | wins\n"
                "--  Arthur   | 9\n"
                "--  Gawain   | 7\n"
                "--  Lancelot | 7\n"
                "--  Percival | 3\n"
                "SELECT COUNT(*) FROM (\n"
                "    SELECT TOP 2 WITH TIES name\n"
                "    FROM champions\n"
                "    ORDER BY wins DESC\n"
                ") AS t;"
            ),
            "setup": (
                "CREATE TABLE champions (name VARCHAR(10), wins INT);\n"
                "INSERT INTO champions VALUES ('Arthur', 9), ('Gawain', 7), ('Lancelot', 7), ('Percival', 3);"
            ),
            "options": ["3", "2", "4", "Error"],
            "answer": "3",
            "explain": "WITH TIES also keeps every row that ties with the last one kept. The 2nd row has 7 "
                       "wins, and another knight has 7 too, so 3 rows.",
        },
    },
    ("medium", "castle"): {
        "scene": "dragon-silver", "scales": "gleaming like polished armor",
        "question": {
            "prompt": "What does this print?",
            "code": (
                "BEGIN TRY\n"
                "    RAISERROR('%d dragons block the %s', 16, 1, 3, 'bridge');\n"
                "END TRY\n"
                "BEGIN CATCH\n"
                "    PRINT ERROR_MESSAGE();\n"
                "END CATCH"
            ),
            "options": [
                "3 dragons block the bridge",
                "%d dragons block the %s",
                "16 dragons block the 1",
                "Error: dragons block the bridge",
            ],
            "answer": "3 dragons block the bridge",
            "explain": "RAISERROR fills in printf-style placeholders from the arguments after the state: "
                       "%d takes 3 and %s takes 'bridge'. Severity 16 is caught.",
        },
    },
    ("hard", "castle"): {
        "scene": "dragon-shadow", "scales": "as black as a moonless night",
        "question": {
            "prompt": "What happens when this runs?",
            "code": (
                "-- armory   (item, qty): Sword 1\n"
                "-- delivery (item, qty): Sword 2, Sword 5\n"
                "MERGE armory AS a\n"
                "USING delivery AS d ON a.item = d.item\n"
                "WHEN MATCHED THEN\n"
                "    UPDATE SET qty = a.qty + d.qty;"
            ),
            "setup": (
                "CREATE TABLE armory (item VARCHAR(10), qty INT);\n"
                "INSERT INTO armory VALUES ('Sword', 1);\n"
                "CREATE TABLE delivery (item VARCHAR(10), qty INT);\n"
                "INSERT INTO delivery VALUES ('Sword', 2), ('Sword', 5);"
            ),
            "options": [
                "Error: target row matched more than once",
                "The Sword's qty becomes 8",
                "The Sword's qty becomes 6",
                "The Sword's qty becomes 3",
            ],
            "answer": "Error: target row matched more than once",
            "explain": "MERGE refuses to update the same target row twice (error 8672) when two source "
                       "rows match it. An UPDATE ... FROM wouldn't complain.",
            "expect_error": True,
        },
    },
}


# ------------------------------------------------------------------
# The final boss: the Deadlock
# ------------------------------------------------------------------
# Only an explorer who completes every path on every level meets the Deadlock. It asks one of
# these nine, picked at random: the hardest questions in the game. Answer right and they
# become a T-SQL Master, with BOSS_POINTS (times the Hard multiplier) besides; answer
# wrong and all is lost: their score falls to zero, and they must start over.

BOSS_MOVE = "boss"
BOSS_POINTS = 100

# The page's own words for this game. The other games have their own, by the same keys.
TEXTS = {
    "title": "The Lost Commit of Transactia",
    "language": "T-SQL",
    "intro": [
        "Long ago, the old servers of Transactia began the greatest transaction ever written, and hid its "
        "last line, the Golden Commit, deep within this wild land, where it waits still. Its guardians "
        "test every traveler with riddles written in the language of the servers: Transact-SQL.",
        "One law holds in Transactia: the server keeps its default settings (SQL Server 2022, a "
        "case-insensitive collation, ANSI_NULLS ON) unless a riddle SETs otherwise. Answer wisely and "
        "choose your path carefully. Every wrong answer costs you a life, and some choices lead to certain "
        "doom...",
    ],
    "found": "Found the treasure",
    "master": "T-SQL Master",
    "lost_to_boss": "Lost to the Deadlock",
    "hall_note": "Walk every path on every level to face the Deadlock.",
    "boss_offer_title": "The final challenge: the Deadlock",
    "boss_offer": "You have walked every path on every level, and the Deadlock, whose two transactions "
                  "wait on each other forever, is waiting. Answer its question, the hardest in all of "
                  "Transactia, to earn the title of T-SQL Master and {points} points.",
    "boss_warning": "Beware: if you fail, all is lost. You'll be chosen as the deadlock victim: your score "
                    "is rolled back to zero and you must start over.",
    "boss_button": "Face the Deadlock",
    "boss_confirm": "Face the Deadlock? If you fail, all is lost: your score is rolled back to zero and "
                    "you must start over.",
    "boss_won": "You have broken the Deadlock. You are a T-SQL Master!",
    "boss_lost": "You were chosen as the deadlock victim. All is lost: your score is rolled back, and you "
                 "must start over.",
    "conquered_every_path": "Every path on every level: you've explored all of Transactia!",
    "conquered_every_level": "Easy, Medium and Hard: you've conquered every level of Transactia!",
}

BOSS_QUESTIONS = [
    {
        "prompt": "What does this return?",
        "code": (
            "DECLARE @x INT;\n"
            "BEGIN TRY\n"
            "    SET @x = 1 / 0;\n"
            "END TRY\n"
            "BEGIN CATCH\n"
            "    SELECT 'caught'\n"
            "    THROW;\n"
            "END CATCH"
        ),
        "options": ["caught", "Error: divide by zero", "THROW", "No rows"],
        "answer": "caught",
        "explain": "With no semicolon after SELECT 'caught', THROW is read as a column alias (SELECT "
                   "'caught' AS THROW), so nothing is re-raised. That's why the statement before THROW "
                   "must end with a semicolon.",
    },
    {
        "prompt": "What happens when this runs?",
        "code": (
            "BEGIN TRY\n"
            "    SELECT name FROM no_such_hoard;\n"
            "END TRY\n"
            "BEGIN CATCH\n"
            "    PRINT 'caught';\n"
            "END CATCH"
        ),
        "options": ["Error: Invalid object name", "caught", "No rows", "Nothing is printed"],
        "answer": "Error: Invalid object name",
        "explain": "A missing table is only found when the statement is compiled at run time (deferred "
                   "name resolution), and TRY...CATCH can't catch compile errors at its own level. Only an "
                   "outer scope's CATCH could.",
        "expect_error": True,
    },
    {
        "prompt": "What does this query return?",
        "code": (
            "IF 1 = 0\n"
            "BEGIN\n"
            "    DECLARE @gem VARCHAR(10) = 'Ruby';\n"
            "END\n"
            "SELECT ISNULL(@gem, 'none');"
        ),
        "options": ["none", "Ruby", "Error: Must declare the scalar variable", "NULL"],
        "answer": "none",
        "explain": "A variable belongs to the whole batch from its DECLARE onwards, not to the BEGIN...END "
                   "block, even when the IF skips it. Only the = 'Ruby' assignment is skipped, so @gem is "
                   "NULL.",
    },
    {
        "prompt": "What does this print?",
        "code": (
            "DECLARE @n INT = 1;\n"
            "EXEC sp_executesql\n"
            "    N'SET @out = 42;',\n"
            "    N'@out INT OUTPUT',\n"
            "    @out = @n;\n"
            "PRINT @n;"
        ),
        "options": ["1", "42", "NULL", "Error"],
        "answer": "1",
        "explain": "OUTPUT is needed in both places: in the parameter list and again after @n in the call. "
                   "Without the second, @n is only passed in, and 42 never comes back.",
    },
    {
        "prompt": "What does this query return?",
        "code": (
            "DECLARE @d DATETIME = '2026-01-31T23:59:59.999';\n"
            "SELECT MONTH(@d), DAY(@d);"
        ),
        "options": ["2 1", "1 31", "1 30", "Error"],
        "answer": "2 1",
        "explain": "DATETIME is only accurate to 1/300 of a second (.000, .003, .007), so .999 rounds up "
                   "to midnight on 1 February. DATETIME2 would keep the 31st.",
    },
    {
        "prompt": "What does this query return?",
        "code": (
            "-- hoard (n INT) is an empty table\n"
            "BEGIN TRAN;\n"
            "INSERT INTO hoard VALUES (1);\n"
            "SAVE TRAN half;\n"
            "INSERT INTO hoard VALUES (2);\n"
            "ROLLBACK TRAN half;\n"
            "SELECT @@TRANCOUNT, COUNT(*) FROM hoard;\n"
            "COMMIT;"
        ),
        "setup": "CREATE TABLE hoard (n INT);",
        "options": ["1 1", "0 1", "1 2", "0 0"],
        "answer": "1 1",
        "explain": "Rolling back to a savepoint undoes only the work after SAVE TRAN, and doesn't change "
                   "@@TRANCOUNT: the transaction is still open, holding the first row.",
    },
    {
        "prompt": "What does this query return?",
        "code": (
            "SET DATEFIRST 1;  -- weeks start on Monday\n"
            "-- 3 Jan 2026 is a Saturday, 4 Jan is a Sunday\n"
            "SELECT DATEDIFF(week, '20260103', '20260104');"
        ),
        "options": ["1", "0", "7", "Error"],
        "answer": "1",
        "explain": "DATEDIFF(week, ...) always counts the Sunday boundaries crossed: it ignores DATEFIRST "
                   "so that it stays deterministic. Saturday to Sunday crosses one.",
    },
    {
        "prompt": "What does this query return?",
        "code": (
            "DECLARE @gold INT = 5;\n"
            "SELECT CASE WHEN @gold > 3 THEN 'rich'\n"
            "            ELSE 0\n"
            "       END;"
        ),
        "options": ["Error: conversion failed for 'rich'", "rich", "0", "NULL"],
        "answer": "Error: conversion failed for 'rich'",
        "explain": "A CASE has one result type: the highest-precedence type of all its branches. INT beats "
                   "VARCHAR, so 'rich' has to become an INT, and that fails.",
        "expect_error": True,
    },
    {
        "prompt": "What does this query return?",
        "code": (
            "SELECT IIF('gem' = 'gem ', 'yes', 'no'),\n"
            "       IIF('gem' LIKE 'gem ', 'yes', 'no');"
        ),
        "options": ["yes no", "no no", "yes yes", "no yes"],
        "answer": "yes no",
        "explain": "For =, SQL Server pads the shorter string with spaces (as the ANSI standard says), so "
                   "trailing spaces don't count. LIKE is the exception: every character of the pattern "
                   "counts, trailing spaces too.",
    },
]


# ------------------------------------------------------------------
# Scenes: each has a banner, a picture (static/img/adventure/, shared with the Python game
# but for the door and the boss) and a description of it
# ------------------------------------------------------------------

SCENES = {
    "start": ("The Lost Commit of Transactia", "title.webp",
              "A moonlit jungle valley wrapped in mist, a golden temple glowing on a far hilltop"),
    "forest": ("The #Temp Forest", "forest.webp",
               "Sunbeams falling through towering trees onto a stream, ferns and one giant mossy tree"),
    "waterfall": ("The Falls of WHILE", "waterfall.webp",
                  "A roaring waterfall crashing into a green pool between mossy cliffs, a fallen log high "
                  "across the gorge"),
    "tree": ("The Top of the Giant Tree", "tree.webp",
             "A great owl on a mossy branch above a sea of mist at sunrise, a golden temple glinting in "
             "the distance"),
    "cave": ("The Cursor Caves", "cave.webp",
             "A dark cave mouth framed by carved stone serpents, a torch burning beside it"),
    "dark": ("The Pit of Implicit Conversion", "pit.webp",
             "A deep pit in the floor of a rocky tunnel, the cave entrance glowing far behind"),
    "glyph": ("The TRY...CATCH Door", "glyph-door-t-sql.webp",
              "A massive stone door glowing with lines of T-SQL, a TRY and a CATCH, fire bowls burning on "
              "either side"),
    "castle": ("The Ruins of Castle Sybase", "castle.webp",
               "A ruined castle on a misty hilltop under a full moon, torches lighting the stone path that "
               "winds up to it"),
    "gate": ("The Castle Gate", "castle-gate.webp",
             "A great arched gate with a raised iron portcullis, griffin banners and blazing torches on "
             "ivy-covered walls"),
    "hall": ("The Hall of Stored Procedures", "great-hall.webp",
             "A ruined great hall of broken gothic arches, torches flickering beside an empty throne at "
             "the top of worn steps"),
    "ramparts": ("The Castle Ramparts", "ramparts.webp",
                 "Torch-lit battlements under a full moon, stone towers rising above a misty valley"),
    "gallery": ("The Moonlit Gallery", "gallery.webp",
                "A stone gallery high in a tower, ivy twisting around its pillars, the full moon over a "
                "misty valley beyond the balustrade"),
    "temple": ("The Temple of the Golden Commit", "temple.webp",
               "A torch-lit temple hall leading to a golden vault door guarded by two stone serpents, a "
               "jeweled chest by the path"),
    "victory": ("The Treasure Is Yours!", "treasure.webp",
                "The Golden Commit: a glowing golden orb wrapped by a serpent, on a stone pedestal among "
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
    "boss": ("The Deadlock", "deadlock.webp",
             "The Deadlock: a hulking iron golem bound in padlocked chains, tags for transactions A and B "
             "on its shoulders, its claws gripping glowing tables A and B, a terminal at each side waiting "
             "on the other"),
    "game_over": ("Msg 8134: Divide by Zero", "game-over.webp",
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
    """A T-SQL challenge: the explorer picks an answer (moves "a" to "d")."""
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
# T-SQL challenges
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
    """Ask one T-SQL question: the next from the deck, or `question` (a dragon's or the
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
                      f"Transactia with {quest.carried} points from your last quest, wondering "
                      "what waits down the way you didn't take. This time you turn toward "
                      f"{PATH_SIGHTS[quest.only_path]}"
                      f"{', where new riddles await' if quest.skip_questions else ''}.")
        yield Choice([PATHS[quest.only_path]])
        choice = str(list(PATHS).index(quest.only_path) + 1)
    else:
        if quest.carried:
            # A winner carrying their score up to the next level.
            quest.narrate(f"Welcome back, {quest.player['name']}! You return to the edge of "
                          f"Transactia with {quest.carried} points from your last quest. Word of "
                          "your success has reached the guardians, and their riddles will be "
                          "harder this time. " + "Three paths lie before you once more: the #Temp Forest, "
                                                 "the Cursor Caves and the trail to the Ruins of Castle "
                                                 "Sybase.")
        else:
            quest.narrate(f"Welcome, {quest.player['name']}! You arrive at the edge of Transactia "
                          "with nothing but a backpack and your wits. " + "Three paths lie before you: the "
                                                                          "#Temp Forest, whose trees "
                                                                          "vanish the moment you leave; "
                                                                          "the Cursor Caves, where "
                                                                          "travelers go one row at a time; "
                                                                          "and a torch-lit trail that "
                                                                          "climbs to the Ruins of Castle "
                                                                          "Sybase, where the language of "
                                                                          "Transactia was born.")
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
    quest.narrate("Towering trees close in around you, though a sign at the edge warns that none of them "
                  "will still be here once you've gone: this whole forest lives in tempdb. To your left, a "
                  "river murmurs through the ferns. To your right stands an ancient tree so tall its top "
                  "disappears into the mist. From up there, you could see for miles.")
    choice = yield Choice(["Follow the river", "Climb the giant tree"])
    if choice == "1":
        return (yield from river_route(quest))
    return (yield from tree_route(quest))


def river_route(quest):
    """The river leads to a waterfall and its guardian."""
    quest.banner("waterfall")
    quest.narrate("You follow the river until it plunges over a cliff at the Falls of WHILE, which have "
                  "been falling, from BEGIN to END and back again, for as long as anyone remembers. The "
                  "water swirls, rises, and takes the shape of a towering figure: the River Guardian. "
                  '"None may pass without answering my riddle," it booms, "and I will not BREAK until you '
                  'do."')
    if not (yield from face_challenge(quest, "The River Guardian")):
        return game_over(quest, "The Guardian's patience runs dry. A great wave sweeps you downstream, far "
                                "away from the treasure.")

    quest.narrate("The Guardian bows and places a shimmering pearl in your hand, numbered one more than "
                  "the last pearl it gave away.")
    collect_relic(quest, "Identity Pearl")
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
                  "I have watched over this server since it was SQL Server 6.5. Only those who think in "
                  'sets, not in rows, may learn the safe way down."')
    if not (yield from face_challenge(quest, "The Wise Owl")):
        return game_over(quest, "The owl ruffles its feathers and flies away. As you reach after it, the "
                                "branch beneath you snaps...")

    quest.narrate('"Well reasoned!" hoots the owl, and it plucks a quill from its wing for you.')
    collect_relic(quest, "Owl's Quill")
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
                  "around the entrance, and beneath them two words are carved: DECLARE CURSOR. Those who "
                  "go in, it's said, go one row at a time, FETCH NEXT after FETCH NEXT. Just inside, you "
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
    quest.narrate("You creep forward in total darkness, one row at a time, one hand on the cold, damp "
                  "wall. Suddenly the ground vanishes beneath your feet and you tumble into the Pit of "
                  "Implicit Conversion, where nothing is quite the type it seems!")
    if not lose_life(quest):
        return game_over(quest, "The pit is far too deep to climb out of without light. Conversion failed, "
                                "and your quest ends here, in the dark.")

    # A pause here, so the pit gets its moment on screen.
    yield Choice(["Climb out of the pit"])
    quest.narrate("Bruised but alive, you claw your way out and crawl back to the entrance. This time you "
                  "light the torch. Lesson learned! In its glow you can see the floor is riddled with pits.")
    return (yield from glyph_door(quest))


def glyph_door(quest):
    """Deep in the cave, a door sealed with a T-SQL puzzle."""
    quest.banner("glyph")
    quest.narrate("You weave between the pits until the tunnel ends at a massive stone door: the "
                  "TRY...CATCH Door. Glowing glyphs crawl across its surface and arrange themselves into "
                  "lines of T-SQL. Whatever goes wrong in its TRY, its CATCH is waiting.")
    if not (yield from face_challenge(quest, "The TRY...CATCH Door")):
        return game_over(quest, "The glyphs flash red, and the door THROWs your answer back at you. With a "
                                "deep rumble the tunnel behind you seals shut, and your torch flickers "
                                "out...")

    quest.narrate("The glyphs flash gold and the door grinds open. A small carved tablet falls from the "
                  "wall at your feet, with the number 50000 on its face, where the errors you raise "
                  "yourself begin.")
    collect_relic(quest, "Tablet of 50000")
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
    quest.narrate("A winding stone trail climbs out of the mist to the Ruins of Castle Sybase, where the "
                  "language of Transactia was first spoken, long before Transactia had a name of its own. "
                  "Torches still burn along the way. The trail ends at the great gate. Beside it, a "
                  "crumbling stair climbs the outer wall toward the ramparts.")
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
                  'drifts out of the stone. "Halt! None may enter the Hall of Stored Procedures without '
                  'EXECUTE permission. Prove you are a true coder of Transactia."')
    if not (yield from face_challenge(quest, "The Ghost Knight")):
        return game_over(quest, "The ghost knight raises its sword and the portcullis crashes down. You "
                                "are left outside in the dark, far from the treasure.")

    quest.narrate("The knight lowers its sword and presses a cold silver ring into your palm, two letters "
                  "carved on its face: sa.")
    collect_relic(quest, "Signet of sa")
    quest.banner("hall")
    quest.narrate("Beyond the gate lies the Hall of Stored Procedures, its arches broken and open to the "
                  "sky, its walls lined with niches named sp_this and sp_that. Torches flicker beside an "
                  "empty throne. Behind it, a narrow passage glows with a faint golden light. To one side, "
                  "a grand staircase climbs into the dark, its steps cracked and crumbling.")
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
    quest.narrate("The ramparts lead into a tall tower and up to a moonlit gallery, its pillars carved "
                  "with execution plans whose arrows all point from right to left. Far below the "
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
                  "the vault, its door sealed by two locks, each watched by a stone serpent: the Shared "
                  "Lock and the Exclusive Lock. Beside the path sits a small jeweled chest with a riddle "
                  "carved into its lid. Solving it would earn you a rare relic, but a wrong answer will "
                  "cost you a life.")
    choice = yield Choice(["Try to open the jeweled chest",
                           "Ignore the chest and head for the vault"])
    if choice == "1":
        if (yield from ask_question(quest, "The Jeweled Chest")):
            quest.narrate("Click! The lid springs open, revealing a ring set with a blazing ruby, three "
                          "words engraved inside the band: BEGIN, COMMIT, ROLLBACK.")
            collect_relic(quest, "Transaction Ring")
        else:
            if not lose_life(quest):
                return game_over(quest, "A dart coated in sleeping venom shoots from the lock. You doze "
                                        "off just steps away from the treasure...")
            quest.narrate("A tiny dart shoots from the lock and stings your hand. "
                          "The chest stays shut.")
    else:
        quest.narrate("You leave the chest alone. Sometimes the wisest move is not "
                      "to gamble.")

    quest.narrate("You approach the vault door. The eyes of the stone serpents begin to glow. The Shared "
                  "Lock lets many readers in at once; the Exclusive Lock lets in only one, and only when "
                  "nobody holds the other.")
    for lock in LOCKS:
        if not (yield from face_challenge(quest, lock)):
            return game_over(quest, "The serpent's eyes flash red and the vault seals itself forever. The "
                                    "treasure remains lost.")
        quest.note("info", f"{lock} slides open!")
    return victory(quest)


# The vault's two locks, in the order they're faced.
LOCKS = ["The Shared Lock", "The Exclusive Lock"]


def victory(quest):
    """The vault opens! Award the end-of-quest bonuses."""
    player = quest.player
    quest.banner("victory")
    quest.narrate("The vault door swings open with a groan. Inside, resting on a pedestal of black stone, "
                  "sits the legendary Golden Commit, a golden orb holding the one COMMIT TRANSACTION the "
                  "old servers of Transactia never ran, humming with ancient power. Congratulations, "
                  "{name}! Your name will be carved among the great coders of Transactia, and this time "
                  "it's committed.".format(name=player["name"]))
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
    nine ultimate questions, picked at random. Right: the title of T-SQL Master and
    BOSS_POINTS besides. Wrong: all is lost, the score falls to zero. Returns "win", since
    the quest that led here was won."""
    quest.banner("boss")
    quest.narrate("You have walked every path in Transactia. As you leave the temple for the last time, "
                  "its floor slides open onto a stair that winds down into a server room older than the "
                  "ruins themselves. In the middle of it stands the Deadlock: a hulking iron giant bound "
                  "in padlocked chains, Transaction A on one shoulder and Transaction B on the other. One "
                  "claw grips TableA and the other TableB, and each transaction is waiting for the other "
                  'to let go. Neither ever will. "Every path, every level," it grinds. "One question '
                  "remains. Answer it, and you are a T-SQL Master. Fail, and you will be chosen as the "
                  'deadlock victim."')
    question = quest.rng.choice(BOSS_QUESTIONS)
    if (yield from ask_question(quest, "The Deadlock", question, BOSS_POINTS, "T-SQL Master")):
        quest.boss = "won"
        quest.narrate("The great padlock on its chest springs open, the chains fall away, and both claws "
                      'let go at once. The Deadlock bows. "Well answered, Master." From this day on, the '
                      "coders of Transactia will know you by your new title.")
        quest.note("relic", "You are a T-SQL Master!")
    else:
        quest.boss = "lost"
        quest.player["score"] = 0
        quest.narrate('The Deadlock\'s eyes flash red. "Transaction (Process ID 52) was deadlocked on lock '
                      "resources with another process and has been chosen as the deadlock victim. Rerun "
                      'the transaction." Every coin, relic and point you carried is rolled back, and you '
                      "wake at the edge of Transactia with nothing but a backpack and your wits.")
        quest.note("life", "All is lost! Your score is rolled back to 0.")
    return "win"


def game_over(quest, message):
    """End the quest with a failure message."""
    quest.narrate(message)
    quest.banner("game_over")
    return "lose"
