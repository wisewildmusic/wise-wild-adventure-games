"""Checks every C# question in the game by really compiling and running it.

Each snippet from csharp/Sharpia/Questions.cs is saved as its own .cs file and run with .NET's
`dotnet run file.cs`, as the modern C# program the game shows: top-level statements and implicit
usings. What it prints (lines joined by spaces, as the options write them) must be the answer, an
unhandled exception's type must be the answer, and when the answer is "Compile error" the compiler
must refuse it with the very error the question expects, not some accident in the snippet.

Run csharp/build/win/sharpia.exe first (tools/build-sharpia.ps1). Takes a few minutes.
"""
import json
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROGRAM = ROOT / "csharp" / "build" / "win" / "sharpia.exe"
WORKERS = 6


def all_questions():
    answer = subprocess.run([PROGRAM], input=b'{"command": "questions"}', capture_output=True, check=True, timeout=60)
    data = json.loads(answer.stdout)
    questions = [(f"{level} #{n}", q) for level, listed in data["levels"].items() for n, q in enumerate(listed)]
    questions += [(f"dragon {d['level']} {d['path']}", d["question"]) for d in data["dragons"]]
    questions += [(f"boss #{n}", q) for n, q in enumerate(data["boss"])]
    return data, questions


def run_snippet(folder, where, question):
    """What really happens when a snippet runs: its printed text, an exception's type, or
    ("Compile error", codes)."""
    source = folder / (re.sub(r"\W+", "_", where) + ".cs")
    source.write_text(question["code"], encoding="utf-8")
    done = subprocess.run(["dotnet", "run", source.name], cwd=folder, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=300)
    codes = sorted(set(re.findall(r"error (CS\d+)", done.stdout + done.stderr)))
    if codes:
        return "Compile error", codes
    crash = re.search(r"Unhandled exception\.\s*(?:[\w.]+\.)?(\w+Exception)", done.stderr)
    if crash:
        return crash.group(1), []
    if done.returncode:
        return f"exit {done.returncode}: {done.stderr[:200]}", []
    return " ".join(done.stdout.split()), []


def check(args):
    folder, where, question = args
    problems = []
    if len(question["options"]) != 4 or len(set(question["options"])) != 4 or question["answer"] not in question["options"]:
        problems.append(f"options {question['options']} / answer {question['answer']!r}")
    if not question["explain"]:
        problems.append("no explanation")
    if question["code"]:
        happened, codes = run_snippet(folder, where, question)
        if happened != question["answer"]:
            problems.append(f"really gives {happened!r} {codes or ''}, answer says {question['answer']!r}")
        elif question["compileError"] and codes != [question["compileError"]]:
            problems.append(f"expected compiler error {question['compileError']}, got {codes}")
        elif happened == "Compile error" and not question["compileError"]:
            problems.append(f"doesn't compile {codes}, and no error is expected")
    return where, problems


def main():
    data, questions = all_questions()
    print(f"{len(questions)} questions: " + ", ".join(f"{k} {len(v)}" for k, v in data["levels"].items())
          + f", dragons {len(data['dragons'])}, boss {len(data['boss'])}")
    prompts = [(q["prompt"], q["code"]) for _, q in questions]
    repeats = {p for p in prompts if prompts.count(p) > 1}
    with tempfile.TemporaryDirectory() as temp:
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
