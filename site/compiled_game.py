"""The website's connection to the adventure games that run as programs of their own: The Lost Compiler of
Sharpia (C#, in csharp/Sharpia), The Lost Runtime of Visualia (VB.NET, in vbnet/Visualia), The Lost
Pointer of Templaria (C++, in cpp/Templaria), The Lost Promise of Scriptoria (JavaScript, in
javascript/Scriptoria) and The Lost Session of Razoria (ASP.NET, in aspnet/Razoria).

Each game itself (story, questions, rules, scoring) is written in its own language, and runs as its own
program, a file beside this one: `sharpia`, `visualia`, `templaria`, `scriptoria` and `razoria` (tools/build-sharpia.ps1,
tools/build-visualia.ps1, tools/build-templaria.ps1, tools/build-scriptoria.ps1 and tools/build-razoria.ps1 build
them). A CompiledGame starts its program when the site needs the game, and offers the same names as pythonia.py, so
the site's adventure pages work with any of the games.

A program keeps nothing between runs, and a replay's answer depends only on what it's asked, so
answers are remembered here: a move's page usually needs each replay only once.

If a program can't run, Unavailable is raised and the site's pages turn the visitor back to the
choice of games. Nothing else on the site depends on it, so that can't affect the rest.
"""
import json
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

from pythonia import NAME_MAX_LENGTH, clean_name  # the name rules belong to the website's forms

_HERE = Path(__file__).resolve().parent
TIMEOUT_SECONDS = 15
_ENVIRONMENT = {
    **({"SystemRoot": os.environ["SystemRoot"], "ProgramFiles": os.environ.get("ProgramFiles", "")} if sys.platform == "win32" else {}),
    "DOTNET_EnableDiagnostics": "0",  # no debugging pipes in /tmp for a program that lives a moment
    "DOTNET_TieredPGO": "0",
}


class Unavailable(RuntimeError):
    """A game's program can't be run, or gave an answer that makes no sense."""

    def __init__(self, language, reason):
        super().__init__(f"the {language} game can't run: {reason}")
        self.language = language


# The game's settings, asked of its program the first time they're needed.
_NAMED = {
    "GAME_VERSION": lambda i: i["gameVersion"],
    "QUESTION_COUNTS": lambda i: {int(version): count for version, count in i["questionCounts"].items()},
    "DIFFICULTY_SETTINGS": lambda i: {
        level["key"]: {"lives": level["lives"], "multiplier": level["multiplier"], "topics": level["topics"]}
        for level in i["levels"]
    },
    "PATHS": lambda i: {path["key"]: path["label"] for path in i["paths"]},
    "PATH_NAMES": lambda i: {path["key"]: path["name"] for path in i["paths"]},
    "SCENES": lambda i: {key: tuple(scene) for key, scene in i["scenes"].items()},
    "DRAGON_MOVE": lambda i: i["dragonMove"],
    "DRAGON_POINTS": lambda i: i["dragonPoints"],
    "BOSS_MOVE": lambda i: i["bossMove"],
    "BOSS_POINTS": lambda i: i["bossPoints"],
    "TEXTS": lambda i: i["texts"],
}


class _Prompt:
    """What the game is waiting for, as its program described it."""

    def __init__(self, answer):
        self.kind = answer["kind"]
        self.moves = answer["moves"]
        self.options = answer["options"]
        self.challenger = answer.get("challenger")
        self.prompt = answer.get("prompt")
        self.code = answer.get("code")

    def accepts(self, move):
        return move in self.moves


class _Quest:
    """A quest as the program left it, with the same parts as a pythonia.Quest."""

    def __init__(self, answer):
        self.scene = answer["scene"]
        self.result = answer["result"]
        self.player = answer["player"]
        self.log = [tuple(entry) for entry in answer["log"]]
        self.asked = answer["asked"]
        self.path = answer["path"]
        self.dragon = answer["dragon"]
        self.boss = answer["boss"]
        self.prompt = _Prompt(answer["prompt"]) if answer["prompt"] else None
        self._dragon_awaits = answer["dragonAwaits"]
        self._boss_awaits = answer["bossAwaits"]

    def dragon_awaits(self):
        """After a win, the dragon of this path and level, until it's woken."""
        return {"scene": self._dragon_awaits} if self._dragon_awaits else None

    def boss_awaits(self):
        """After the win that completes every path on every level: the boss, until faced."""
        return self._boss_awaits


class CompiledGame:
    """One game's compiled program, offering the same names as pythonia.py."""

    NAME_MAX_LENGTH = NAME_MAX_LENGTH
    clean_name = staticmethod(clean_name)

    def __init__(self, language, program, test_setting):
        self.language = language
        # test_setting names an environment variable, for testing on Windows, where the program
        # beside this file (a Linux one) can't run.
        self.program = Path(os.environ.get(test_setting) or _HERE / program)
        self._info = lru_cache(maxsize=1)(lambda: self._ask(json.dumps({"command": "info"})))
        self._replay = lru_cache(maxsize=2048)(self._ask)

    def _ask(self, request):
        """Sends the program one request, and returns its answer."""
        try:
            done = subprocess.run([self.program], input=request.encode(), capture_output=True, timeout=TIMEOUT_SECONDS,
                                  env=_ENVIRONMENT, check=True)
            return json.loads(done.stdout)
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            raise Unavailable(self.language, error) from error

    def __getattr__(self, name):
        if name in _NAMED:
            return _NAMED[name](self._info())
        raise AttributeError(name)

    def can_replay(self, version):
        """Whether a quest saved by this version of the game can still be played."""
        return version in self.QUESTION_COUNTS

    def next_level(self, difficulty):
        """The level a winner can go on to (easy -> medium -> hard), or None after the hardest."""
        levels = list(self.DIFFICULTY_SETTINGS)
        position = levels.index(difficulty) + 1
        return levels[position] if position < len(levels) else None

    def path_taken(self, moves, only_path=None):
        """The path a quest went down: the one it was sent on, or else the one its first move
        picked. None before the first move."""
        if only_path:
            return only_path
        paths = list(self.PATHS)
        if moves and moves[0] in [str(number) for number in range(1, len(paths) + 1)]:
            return paths[int(moves[0]) - 1]
        return None

    def paths_left(self, done):
        """The paths not taken yet (of those in `done`), in the order the first choice offers them."""
        return [path for path in self.PATHS if path not in done]

    def replay(self, name, difficulty, seed, moves, carried=0, only_path=None, skip_questions=(), version=None, final=False):
        """Plays a quest from the start with the moves made so far, in the game's own language, and
        returns it as it stands now (see pythonia.replay, and Game.Replay in each game's source)."""
        return _Quest(self._replay(json.dumps({
            "command": "replay", "name": name, "difficulty": difficulty, "seed": seed, "moves": list(moves),
            "carried": carried, "onlyPath": only_path, "skipQuestions": list(skip_questions),
            "version": self.GAME_VERSION if version is None else version, "final": final,
        })))
