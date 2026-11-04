"""Checks every ASP.NET question in the game by really building it, running it and sending it requests.

Each snippet from aspnet/Razoria/Questions.cs becomes its own small ASP.NET Core project, on the web SDK with its
implicit usings. A "// --- name ---" line starts a file of that name; a snippet starting with @page is
Pages/Index.cshtml; and a project with no Program.cs of its own gets one that only maps its Razor Pages, as the game's
start page says. The app then runs for real, on Kestrel, in Production unless the snippet says otherwise, with logging
off so that its console holds only what the snippet writes.

The one thing changed in a snippet is its `app.Run();`, which becomes a call to Probe.cs below. That starts the app,
sends it the question's requests one at a time with a client that keeps cookies and doesn't follow redirects, and saves
what comes back. So what the game shows is what runs, apart from that one line.

The question's Check then says what has to match its answer: the body (white space tidied, "(empty)" if there's none),
the status code, both, or the console. An answer of "The app crashes at startup" must really end the app, with the very
exception the question names, and "Compile error" must fail with the very error it names.

Run tools/build-razoria.ps1 first. Takes a few minutes.

    python check-aspnet-questions.py               (every question)
    python check-aspnet-questions.py boss hard     (only those whose names hold these words)
"""
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
PROGRAM = ROOT / "aspnet" / "build" / "win" / "razoria.exe"
WORKERS = 6
CRASHES = "The app crashes at startup"
COMPILE_ERROR = "Compile error"

PROJECT = """<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <NuGetAudit>false</NuGetAudit>
    <NoWarn>$(NoWarn);CS9113;CS0649;CS1998;ASP0014;ASP0016;ASP0019</NoWarn>
  </PropertyGroup>
</Project>
"""

RAZOR_PROGRAM = """var builder = WebApplication.CreateBuilder(args);
builder.Services.AddRazorPages();
var app = builder.Build();
app.MapRazorPages();
app.Run();
"""

# Takes the place of the snippet's app.Run(). A request is "METHOD /path" and perhaps a body after it: JSON if it looks
# like JSON, otherwise an HTML form's fields.
PROBE = r"""
using System.Text;
using System.Text.Json;

static class Probe
{
    public static async Task Run(WebApplication app)
    {
        app.Urls.Add("http://127.0.0.1:0");
        await app.StartAsync();
        var address = app.Urls.First();
        using var http = new HttpClient(new HttpClientHandler { AllowAutoRedirect = false, UseCookies = true })
        {
            Timeout = TimeSpan.FromSeconds(30),
        };
        var results = new List<Dictionary<string, object>>();
        foreach (var line in File.ReadAllLines("requests.txt"))
        {
            var parts = line.Split(' ', 3);
            var request = new HttpRequestMessage(new HttpMethod(parts[0]), address + parts[1]);
            if (parts.Length > 2)
            {
                bool isJson = parts[2][0] is '{' or '[' or '"';
                request.Content = new StringContent(parts[2], Encoding.UTF8,
                    isJson ? "application/json" : "application/x-www-form-urlencoded");
            }
            var result = new Dictionary<string, object>();
            try
            {
                using var response = await http.SendAsync(request);
                result["status"] = (int)response.StatusCode;
                result["body"] = await response.Content.ReadAsStringAsync();
            }
            catch (Exception error)
            {
                result["failed"] = error.GetType().Name;
            }
            results.Add(result);
        }
        File.WriteAllText("responses.json", JsonSerializer.Serialize(results));
        await app.StopAsync();
    }
}
"""


def all_questions():
    answer = subprocess.run([PROGRAM], input=b'{"command": "questions"}', capture_output=True, check=True, timeout=60)
    data = json.loads(answer.stdout)
    questions = [(f"{level} #{n}", q) for level, listed in data["levels"].items() for n, q in enumerate(listed)]
    questions += [(f"dragon {d['level']} {d['path']}", d["question"]) for d in data["dragons"]]
    questions += [(f"boss #{n}", q) for n, q in enumerate(data["boss"])]
    return data, questions


def snippet_files(code):
    """The snippet's files: {name: contents}."""
    files, name = {}, None
    if not code.startswith("// --- "):
        name = "Pages/Index.cshtml" if code.startswith("@page") else "Program.cs"
        files[name] = []
    for line in code.split("\n"):
        heading = re.fullmatch(r"// --- (.+) ---", line)
        if heading:
            name = heading.group(1)
            files[name] = []
        else:
            files[name].append(line)
    return {file: "\n".join(lines) + "\n" for file, lines in files.items()}


def tidy(text):
    return " ".join(text.split()) or "(empty)"


def build_and_run(folder, code, send):
    """What really happens: (what it answered or the way it failed, details), and the responses and console if it ran."""
    folder.mkdir(parents=True)
    files = snippet_files(code)
    files.setdefault("Program.cs", RAZOR_PROGRAM)
    if files["Program.cs"].count("app.Run();") != 1:
        return ("no app.Run();", []), None, None
    files["Program.cs"] = files["Program.cs"].replace("app.Run();", "await Probe.Run(app);")
    files["Probe.cs"] = PROBE
    files["requests.txt"] = "\n".join(send) + "\n"
    files["q.csproj"] = PROJECT
    for name, text in files.items():
        (folder / name).parent.mkdir(parents=True, exist_ok=True)
        (folder / name).write_text(text, encoding="utf-8")

    built = subprocess.run(["dotnet", "build", "-v", "q", "--nologo", "-p:UseSharedCompilation=false", "-nodeReuse:false"],
                           cwd=folder, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    codes = sorted(set(re.findall(r"error ((?:CS|RZ|ASP)\d+)", built.stdout + built.stderr)))
    if codes:
        return (COMPILE_ERROR, codes), None, None
    if built.returncode:
        return (f"the build failed: {built.stdout[-300:]}", []), None, None

    environment = {key: value for key, value in os.environ.items()
                   if key not in ("ASPNETCORE_ENVIRONMENT", "DOTNET_ENVIRONMENT", "ASPNETCORE_URLS", "DOTNET_URLS")}
    environment["Logging__LogLevel__Default"] = "None"
    done = subprocess.run(["dotnet", str(Path("bin") / "Debug" / "net10.0" / "q.dll")], cwd=folder, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=120, env=environment)
    if done.returncode:
        crash = re.search(r"Unhandled exception\.\s*(?:[\w.]+\.)?(\w+Exception)", done.stderr)
        return (CRASHES, [crash.group(1) if crash else done.stderr[:300]]), None, None
    return None, json.loads((folder / "responses.json").read_text(encoding="utf-8")), done.stdout


def answered(check, responses, console):
    """What a question's Check says came back."""
    if check == "log":
        return tidy(console)
    failed = [r["failed"] for r in responses if "failed" in r]
    if failed:
        return f"the request failed: {failed}"
    if check == "body":
        return tidy(" ".join(r["body"] for r in responses))
    if check == "status":
        return " ".join(str(r["status"]) for r in responses)
    if check == "both":
        return " ".join(f"{r['status']} {tidy(r['body'])}" for r in responses)
    return f"unknown Check {check!r}"


def matches(check, actual, answer):
    """An answer for a single status can give the status's name too: 404 Not Found."""
    if check == "status" and " " not in actual and re.fullmatch(r"\d{3} [A-Z].*", answer):
        return answer.split()[0] == actual
    return actual == answer


def check(args):
    temp, number, where, question = args
    problems = []
    options, answer = question["options"], question["answer"]
    if len(options) != 4 or len(set(options)) != 4 or answer not in options:
        problems.append(f"options {options} / answer {answer!r}")
    if not question["explain"]:
        problems.append("no explanation")
    if question["code"]:
        folder = temp / f"q{number}"
        try:
            failure, responses, console = build_and_run(folder, question["code"], question["send"])
            if failure:
                happened, details = failure
                if happened != answer:
                    problems.append(f"really: {happened} {details}, answer says {answer!r}")
                elif happened == COMPILE_ERROR and details != [question["compileError"]]:
                    problems.append(f"expected compiler error {question['compileError']}, got {details}")
                elif happened == CRASHES and details != [question["crash"]]:
                    problems.append(f"expected it to crash with {question['crash']}, got {details}")
            else:
                actual = answered(question["check"], responses, console)
                if not matches(question["check"], actual, answer):
                    problems.append(f"really gives {actual!r}, answer says {answer!r}")
        except subprocess.TimeoutExpired as error:
            problems.append(f"timed out: {error.cmd}")
        finally:
            shutil.rmtree(folder, ignore_errors=True)
    return where, problems


def main():
    data, questions = all_questions()
    print(f"{len(questions)} questions: " + ", ".join(f"{k} {len(v)}" for k, v in data["levels"].items())
          + f", dragons {len(data['dragons'])}, boss {len(data['boss'])}")
    prompts = [(q["prompt"], q["code"]) for _, q in questions]
    repeats = {p for p in prompts if prompts.count(p) > 1}
    wanted = sys.argv[1:]
    chosen = [(where, q) for where, q in questions if not wanted or any(word in where for word in wanted)]
    with tempfile.TemporaryDirectory() as temp:
        with ThreadPoolExecutor(WORKERS) as pool:
            results = list(pool.map(check, [(Path(temp), n, where, q) for n, (where, q) in enumerate(chosen)]))
    failed = [(where, problems) for where, problems in results if problems]
    for where, problems in failed:
        print(f"FAIL  {where}: " + "; ".join(problems))
    if repeats:
        print("FAIL  the same question appears twice:", repeats)
    print(f"{len(results) - len(failed)} of {len(results)} questions right")
    return 1 if failed or repeats else 0


if __name__ == "__main__":
    sys.exit(main())
