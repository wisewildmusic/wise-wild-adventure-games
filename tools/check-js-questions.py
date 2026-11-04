"""Checks every JavaScript question in the game by really running it.

Each snippet from javascript/Scriptoria/questions.js is saved as its own script (.cjs, so that it's an ordinary
script and not a module, and so in sloppy mode unless it says "use strict") and run by Node.js, as the game's start
page describes.

What it prints (lines joined by spaces, as the options write them) must be the answer, with no output at all being
"Nothing". An answer naming an error (TypeError, ReferenceError, SyntaxError...) means the script must die of that
error, uncaught, without having printed anything.

    python check-js-questions.py
"""
import json
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROGRAM = ROOT / "javascript" / "Scriptoria" / "main.js"
WORKERS = 8
TIMEOUT = 30


def all_questions():
    answer = subprocess.run(["node", PROGRAM], input=b'{"command": "questions"}', capture_output=True, check=True, timeout=60)
    data = json.loads(answer.stdout)
    questions = [(f"{level} #{n}", q) for level, listed in data["levels"].items() for n, q in enumerate(listed)]
    questions += [(f"dragon {d['level']} {d['path']}", d["question"]) for d in data["dragons"]]
    questions += [(f"boss #{n}", q) for n, q in enumerate(data["boss"])]
    return data, questions


def what_happened(returncode, stdout, stderr):
    """A finished run's result, as an answer would put it."""
    printed = " ".join(stdout.split())
    if returncode:
        # (Node prints the source line and a caret first, then "TypeError: Assignment to constant variable.")
        died_of = re.search(r"^(\w*Error)\b", stderr, re.MULTILINE)
        error = died_of.group(1) if died_of else f"exit {returncode}: {stderr[:300]}"
        return f"{printed} {error}".strip()
    return printed or "Nothing"


def check(args):
    folder, where, question = args
    problems = []
    if len(question["options"]) != 4 or len(set(question["options"])) != 4 or question["answer"] not in question["options"]:
        problems.append(f"options {question['options']} / answer {question['answer']!r}")
    if not question["explain"]:
        problems.append("no explanation")
    if question["code"]:
        path = folder / f"{re.sub(r'\W+', '_', where)}.cjs"
        path.write_text(question["code"] + "\n", encoding="utf-8", newline="\n")
        done = subprocess.run(["node", path], capture_output=True, text=True, encoding="utf-8", timeout=TIMEOUT)
        happened = what_happened(done.returncode, done.stdout, done.stderr)
        if happened != question["answer"]:
            problems.append(f"really gives {happened!r}, answer says {question['answer']!r}")
    return where, problems


def main():
    data, questions = all_questions()
    version = subprocess.run(["node", "--version"], capture_output=True, text=True, check=True).stdout.strip()
    print(f"{len(questions)} questions: " + ", ".join(f"{k} {len(v)}" for k, v in data["levels"].items())
          + f", dragons {len(data['dragons'])}, boss {len(data['boss'])}. Node.js {version}")
    prompts = [(q["prompt"], q["code"]) for _, q in questions]
    repeats = {p for p in prompts if prompts.count(p) > 1}
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
        with ThreadPoolExecutor(WORKERS) as pool:
            results = list(pool.map(check, [(Path(temp), where, q) for where, q in questions]))
    failed = [(where, problems) for where, problems in results if problems]
    for where, problems in failed:
        print(f"FAIL  {where}: " + "; ".join(problems))
    if repeats:
        print("FAIL  the same question appears twice:", repeats)
    print(f"{len(results) - len(failed)} of {len(results)} questions right")
    return 1 if failed or repeats else 0


if __name__ == "__main__":
    sys.exit(main())
