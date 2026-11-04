"""Checks every VB.NET question in the game by really compiling and running it.

VB has no top-level statements and `dotnet run` can't take a lone .vb file, so each snippet from
vbnet/Visualia/Questions.vb becomes its own small project: plain statements go inside a Sub Main,
and a snippet showing its own Sub Main goes inside a Module, with any Option line first. Each runs
with Option Strict On unless it says otherwise, the law of the game. What it prints (lines joined
by spaces, as the options write them) must be the answer, an unhandled exception's type must be the
answer, and when the answer is "Compile error" the compiler must refuse it with the very error the
question expects, not some accident in the snippet.

Run vbnet/build/win/visualia.exe first (tools/build-visualia.ps1). Takes a few minutes.
"""
import json
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROGRAM = ROOT / "vbnet" / "build" / "win" / "visualia.exe"
WORKERS = 6
PROJECT = """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net10.0</TargetFramework>
    <RootNamespace></RootNamespace>
    <OptionStrict>On</OptionStrict>
    <OptionExplicit>On</OptionExplicit>
    <OptionInfer>On</OptionInfer>
    <UseAppHost>false</UseAppHost>
  </PropertyGroup>
</Project>
"""


def all_questions():
    answer = subprocess.run([PROGRAM], input=b'{"command": "questions"}', capture_output=True, check=True, timeout=60)
    data = json.loads(answer.stdout)
    questions = [(f"{level} #{n}", q) for level, listed in data["levels"].items() for n, q in enumerate(listed)]
    questions += [(f"dragon {d['level']} {d['path']}", d["question"]) for d in data["dragons"]]
    questions += [(f"boss #{n}", q) for n, q in enumerate(data["boss"])]
    return data, questions


def as_program(code):
    """The whole VB file a snippet stands for."""
    lines = code.split("\n")
    options = [line for line in lines if line.startswith("Option ")]
    body = "\n".join(line for line in lines if line not in options)
    if not re.search(r"^\s*Sub Main\b", body, re.MULTILINE):
        body = f"Sub Main()\n{body}\nEnd Sub"
    return "\n".join([*options, "Module Program", body, "End Module", ""])


def run_snippet(folder, where, question):
    """What really happens when a snippet runs: its printed text, an exception's type, or
    ("Compile error", codes)."""
    project = folder / re.sub(r"\W+", "_", where)
    project.mkdir()
    (project / "check.vbproj").write_text(PROJECT, encoding="utf-8")
    (project / "Program.vb").write_text(as_program(question["code"]), encoding="utf-8")
    done = subprocess.run(["dotnet", "run", "--project", str(project)], cwd=folder, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=300)
    codes = sorted(set(re.findall(r"error (BC\d+)", done.stdout + done.stderr)))
    if codes:
        return "Compile error", codes
    crash = re.search(r"Unhandled exception\.\s*(?:[\w.]+\.)?(\w+Exception)", done.stderr)
    if crash:
        return crash.group(1), []
    if done.returncode:
        return f"exit {done.returncode}: {done.stderr[:200]}", []
    # `dotnet run` prints the compiler's warnings among what the program prints.
    printed = [line for line in done.stdout.splitlines() if not re.search(r"warning BC\d+", line)]
    return " ".join(" ".join(printed).split()), []


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
