# Wise Wild Adventure Games

The source code of the ten text adventures on the Wise Wild Music website. Each one teaches a
programming language, or the language of AI, through a quest of challenges that ends with a final boss.

| Game | Teaches | Written in | Source |
|---|---|---|---|
| The Lost Treasure of Pythonia | Python | Python | `site/pythonia.py` (adapted from `AdventuresInPython.py`) |
| The Lost Compiler of Sharpia | C# | C# | `csharp/Sharpia/` |
| The Lost Runtime of Visualia | VB.NET | VB.NET | `vbnet/Visualia/` |
| The Lost Standard of Sequelia | ANSI SQL | Python | `site/sequelia.py` |
| The Lost Commit of Transactia | T-SQL | Python | `site/transactia.py` |
| The Lost Package of Oraclia | PL/SQL | Python | `site/oraclia.py` |
| The Lost Pointer of Templaria | C++ | C++ | `cpp/Templaria/` |
| The Lost Promise of Scriptoria | JavaScript | JavaScript | `javascript/Scriptoria/` |
| The Lost Session of Razoria | ASP.NET | ASP.NET Core | `aspnet/Razoria/` |
| The Lost Weights of Neuralia | AI | Python | `site/neuralia.py` |

## How it fits together

- `site/` is the Flask website the games are played on. `app.py` holds the pages and saves each
  quest, `templates/` and `static/` hold the pages' look, scripts, fonts and pictures.
- The games written in Python are imported directly by `app.py`.
- The other games each run as a small program of their own. `site/compiled_game.py` starts the
  program, sends it one request as JSON and reads its answer.
- `tools/` holds the scripts that build the games, check every question's answer and run a local
  copy of the site.

## Running it locally

You need Python 3.12 or newer with Flask (`pip install -r site/requirements.txt`). Then:

```
python tools/local_test_site.py
```

This runs a throwaway copy of the site at http://127.0.0.1:5055/ on Windows, with short test tones
instead of songs. The five games written in Python need nothing else, the JavaScript game needs
Node.js, and the C#, VB.NET, C++ and ASP.NET games must be built first.

## Building the games

Run these in PowerShell on Windows. Each builds a Windows copy for local testing and a Linux program
for the server, placed in `site/`.

| Game | Script | Needs |
|---|---|---|
| C# | `tools/build-sharpia.ps1` | .NET 10 SDK |
| VB.NET | `tools/build-visualia.ps1` | .NET 10 SDK |
| ASP.NET | `tools/build-razoria.ps1` | .NET 10 SDK |
| C++ | `tools/build-templaria.ps1` | Visual Studio's compiler, and g++ in WSL for the Linux program |
| JavaScript | `tools/build-scriptoria.ps1` | gcc in WSL (Linux program only; locally it runs on Node.js) |

The JavaScript game's Linux program is built with [QuickJS](https://bellard.org/quickjs/), whose
source is in `javascript/build/quickjs/`.

## Checking the questions

Each `tools/check-*-questions.py` script runs every question's code and confirms its answer. They
need the matching compiler or database, listed at the top of each script.

## What isn't here

- The compiled programs, which the build scripts make.
- The songs, the visitor and quest databases, the site's private keys and its password.
- The song manager's pages, which the games don't use, so `/manage/` won't open in a copy made from
  this repository. Every page the games link to is here.
- The original full-size artwork. `site/static/img/adventure/` holds the finished pictures the games show.
- The scripts that publish the site to its server.

## Credits and licences

© 2026–2027 Wise Wild Music. All rights reserved, except as noted below.

- Fonts in `site/static/fonts/`: Archivo, Cormorant Garamond, Monoton and Wix Madefor Text, under the
  SIL Open Font License (the `OFL-*.txt` files there).
- QuickJS, by Fabrice Bellard and Charlie Gordon, under the MIT licence.
