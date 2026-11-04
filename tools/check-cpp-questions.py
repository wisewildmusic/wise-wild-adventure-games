"""Checks every C++ question in the game by really compiling and running it.

Each snippet from cpp/Templaria/Questions.cpp is saved as its own .cpp file, as the game's start page describes
it: standard C++20 with the headers it needs, plain statements standing for the inside of main(), and a snippet
with its own main() being the whole program. It's built and run on up to two compilers, which must both agree:

  - MSVC, with Visual Studio on this PC;
  - g++, in WSL, if it's there (tools/build-templaria.ps1 says how to get it).

What it prints (lines joined by spaces, as the options write them) must be the answer, with no output at all
being "Nothing". C++ has three more answers a program can't print:

  - "Compile error": the compiler must refuse it. MSVC must refuse it with the very error the question expects,
    not some accident in the snippet.
  - "Undefined behavior": the program runs with the compilers' sanitizers on, which must catch it doing exactly
    what the question expects. Every other snippet runs with them on too, and must run clean, so a question can't
    be undefined behavior by accident. MSVC has only the address sanitizer, so a question about signed overflow
    can be proved only by g++, and without g++ it's listed as unproved.
  - "std::terminate is called": the program must be ended by it.

Run cpp/build/win/templaria.exe first (tools/build-templaria.ps1). Takes a few minutes.
    python check-cpp-questions.py [msvc] [gcc]        (default: every compiler there is)
"""
import ctypes
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROGRAM = ROOT / "cpp" / "build" / "win" / "templaria.exe"
VSWHERE = Path(os.environ["ProgramFiles(x86)"]) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
WORKERS = 6
TIMEOUT = 300

HEADERS = """algorithm any array bit climits cstdint deque exception functional iomanip iostream iterator limits list map
memory numeric optional ranges set span sstream stdexcept string string_view tuple type_traits unordered_map utility
variant vector""".split()
PRELUDE = "".join(f"#include <{header}>\n" for header in HEADERS)

# What each compiler's sanitizers say for what a question expects. (None: this compiler can't prove it.)
FINDINGS = {
    "msvc": {
        "heap-use-after-free": r"AddressSanitizer: heap-use-after-free",
        "dangling-temporary": r"AddressSanitizer: (stack-use-after-scope|heap-use-after-free)",
        "out-of-bounds": r"AddressSanitizer: stack-buffer-overflow",
        "new-delete-type-mismatch": r"AddressSanitizer: new-delete-type-mismatch",
        "signed-integer-overflow": None,
    },
    "gcc": {
        "heap-use-after-free": r"AddressSanitizer: heap-use-after-free",
        "dangling-temporary": r"AddressSanitizer: (stack-use-after-scope|heap-use-after-free)",
        "out-of-bounds": r"AddressSanitizer: stack-buffer-overflow|index \d+ out of bounds",
        "new-delete-type-mismatch": r"AddressSanitizer: new-delete-type-mismatch",
        "signed-integer-overflow": r"runtime error: signed integer overflow",
    },
}
ANY_SANITIZER = r"AddressSanitizer|runtime error:"


def msvc_environment():
    """The environment Visual Studio's compiler needs, as its own batch file sets it up."""
    found = subprocess.run([VSWHERE, "-latest", "-products", "*", "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                            "-property", "installationPath"], capture_output=True, text=True, check=True).stdout.strip()
    vcvars = Path(found) / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    shown = subprocess.run(f'"{vcvars}" >nul && set', capture_output=True, text=True, shell=True, check=True).stdout
    return {name.upper(): value for name, value in (line.split("=", 1) for line in shown.splitlines() if "=" in line)}


def have_gcc():
    return subprocess.run(["wsl", "-d", "Ubuntu", "--", "which", "g++"], capture_output=True).returncode == 0


def all_questions():
    answer = subprocess.run([PROGRAM], input=b'{"command": "questions"}', capture_output=True, check=True, timeout=60)
    data = json.loads(answer.stdout)
    questions = [(f"{level} #{n}", q) for level, listed in data["levels"].items() for n, q in enumerate(listed)]
    questions += [(f"dragon {d['level']} {d['path']}", d["question"]) for d in data["dragons"]]
    questions += [(f"boss #{n}", q) for n, q in enumerate(data["boss"])]
    return data, questions


def source_for(code):
    """A snippet as the program it stands for."""
    if re.search(r"\bint main\s*\(", code):
        return PRELUDE + code + "\n"
    return PRELUDE + "int main() {\n" + code + "\n}\n"


def what_happened(returncode, stdout, stderr, terminated):
    """A finished run's result, as an answer would put it."""
    if re.search(ANY_SANITIZER, stdout + stderr):
        return "Undefined behavior"
    if terminated:
        return "std::terminate is called"
    if returncode:
        return f"exit {returncode}: {stderr[:300]}"
    return " ".join(stdout.split()) or "Nothing"


def run_msvc(folder, name, source, environment):
    """(result, compiler error codes, sanitizer output) with MSVC, its address sanitizer on."""
    path = folder / f"{name}.cpp"
    path.write_text(source, encoding="utf-8")
    # (Windows looks for a program in this process's PATH, not the one being handed on, so it's found here.)
    compiler = shutil.which("cl", path=environment["PATH"])
    built = subprocess.run([compiler, "/nologo", "/std:c++20", "/EHsc", "/utf-8", "/W0", "/permissive-", "/fsanitize=address",
                            path.name, f"/Fe:{name}.exe", f"/Fo:{name}.obj"],
                           cwd=folder, env=environment, capture_output=True, text=True, errors="replace", timeout=TIMEOUT)
    codes = sorted(set(re.findall(r"error (C\d+)", built.stdout + built.stderr)))
    if built.returncode:
        return "Compile error", codes, ""
    done = subprocess.run([folder / f"{name}.exe"], cwd=folder, env=environment, capture_output=True, text=True, errors="replace",
                          timeout=TIMEOUT)
    # abort() ends a program with 3, or with the code for a fast fail, depending on how it was reached.
    terminated = done.returncode in (3, 0xC0000409, -1073740791)
    return what_happened(done.returncode, done.stdout, done.stderr, terminated), [], done.stdout + done.stderr


def windows_path_in_wsl(path):
    text = str(path).replace("\\", "/")
    return f"/mnt/{text[0].lower()}{text[2:]}"


def run_gcc(folder, name, source):
    """(result, compiler error codes, sanitizer output) with g++ in WSL, its sanitizers on."""
    path = folder / f"{name}.gcc.cpp"
    path.write_text(source, encoding="utf-8", newline="\n")
    target = f"{name}.gcc.out"
    built = subprocess.run(["wsl", "-d", "Ubuntu", "--cd", windows_path_in_wsl(folder), "--", "g++", "-std=c++20", "-w", "-g",
                            "-fsanitize=address,undefined", "-fno-sanitize-recover=all", path.name, "-o", target],
                           capture_output=True, text=True, errors="replace", timeout=TIMEOUT)
    if built.returncode:
        return "Compile error", [], ""
    # (A shared_ptr cycle is a question's whole point, so leaks don't count as a failure.)
    done = subprocess.run(["wsl", "-d", "Ubuntu", "--cd", windows_path_in_wsl(folder), "--", "env", "ASAN_OPTIONS=detect_leaks=0",
                           f"./{target}"], capture_output=True, text=True, errors="replace", timeout=TIMEOUT)
    terminated = "terminate called" in done.stderr
    return what_happened(done.returncode, done.stdout, done.stderr, terminated), [], done.stdout + done.stderr


def check_on(compiler, happened, codes, output, question, problems, unproved, where):
    expected = question["undefined"]
    if question["answer"] == "Undefined behavior":
        wanted = FINDINGS[compiler][expected]
        if wanted is None:
            unproved.append(f"{where} ({expected}, on {compiler}): really gives {happened!r}")
        elif not re.search(wanted, output):
            problems.append(f"{compiler}: expected the sanitizers to catch {expected}, but got {happened!r}\n{output[:300]}")
    elif happened != question["answer"]:
        problems.append(f"{compiler}: really gives {happened!r} {codes or ''}, answer says {question['answer']!r}")
    elif compiler == "msvc" and question["compileError"] and question["compileError"] not in codes:
        problems.append(f"expected compiler error {question['compileError']}, got {codes}")
    if happened == "Compile error" and question["answer"] != "Compile error":
        problems.append(f"{compiler}: doesn't compile {codes}, and no error is expected")


def check(args):
    folder, where, question, compilers, environment = args
    problems, unproved = [], []
    if len(question["options"]) != 4 or len(set(question["options"])) != 4 or question["answer"] not in question["options"]:
        problems.append(f"options {question['options']} / answer {question['answer']!r}")
    if not question["explain"]:
        problems.append("no explanation")
    if question["code"]:
        name = re.sub(r"\W+", "_", where)
        source = source_for(question["code"])
        if "msvc" in compilers:
            check_on("msvc", *run_msvc(folder, name, source, environment), question, problems, unproved, where)
        if "gcc" in compilers:
            check_on("gcc", *run_gcc(folder, name, source), question, problems, unproved, where)
            unproved = []  # g++'s sanitizers can prove all of them, so it's settled either way
    return where, problems, unproved


def main():
    ctypes.windll.kernel32.SetErrorMode(0x8003)  # no "stopped working" windows from the programs that crash on purpose
    wanted = sys.argv[1:] or ["msvc", "gcc"]
    compilers = [c for c in wanted if c != "gcc" or have_gcc()]
    if "gcc" in wanted and "gcc" not in compilers:
        print("No g++ in WSL, so this checks with MSVC alone. See tools/build-templaria.ps1 for how to get it.")
    environment = msvc_environment() if "msvc" in compilers else None
    data, questions = all_questions()
    print(f"{len(questions)} questions: " + ", ".join(f"{k} {len(v)}" for k, v in data["levels"].items())
          + f", dragons {len(data['dragons'])}, boss {len(data['boss'])}. Compilers: {', '.join(compilers)}")
    prompts = [(q["prompt"], q["code"]) for _, q in questions]
    repeats = {p for p in prompts if prompts.count(p) > 1}
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
        with ThreadPoolExecutor(WORKERS) as pool:
            results = list(pool.map(check, [(Path(temp), where, q, compilers, environment) for where, q in questions]))
    failed = [(where, problems) for where, problems, _ in results if problems]
    for where, problems in failed:
        print(f"FAIL  {where}: " + "; ".join(problems))
    for _, _, unproved in results:
        for note in unproved:
            print(f"UNPROVED  {note}")
    if repeats:
        print("FAIL  the same question appears twice:", repeats)
    print(f"{len(results) - len(failed)} of {len(results)} questions right")
    return 1 if failed or repeats else 0


if __name__ == "__main__":
    sys.exit(main())
