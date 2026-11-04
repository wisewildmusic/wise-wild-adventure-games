"""Runs a throwaway local copy of the Wise Wild site for testing, at http://127.0.0.1:5055/.

The copy lives in a temporary folder (wiped and rebuilt on each start). It has three short
test tones instead of the real songs, fresh play and visitor logs, and its own song manager
password (TEST_PASSWORD below), so the manager can be tried out without the real password
and without touching the live site's music or counts.

Run it with Anaconda's Python, which has Flask:  python local_test_site.py
"""
import math
import os
import shutil
import stat
import sys
import tempfile
import wave
from pathlib import Path

from werkzeug.security import generate_password_hash

SITE = Path(__file__).resolve().parent.parent / "site"
WORK = Path(tempfile.gettempdir()) / "wisewild-local-test"
TEST_PASSWORD = "local-test-only"  # this local copy only; never the real site's password
PORT = 5055
TONES = {"Test Tone Alpha": 440, "Test Tone Beta": 554, "Test Tone Gamma": 659}


def make_tone(path, frequency, seconds=40, rate=8000):
    """A quiet sine-wave WAV, long enough to count as a play (30 seconds)."""
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(1)
        out.setframerate(rate)
        out.writeframes(bytes(128 + round(20 * math.sin(2 * math.pi * frequency * i / rate))
                              for i in range(seconds * rate)))


def make_writable_and_retry(func, path, _error):
    """Some site folders are marked read-only on Windows, which stops them being deleted."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def make_test_copy():
    """A fresh copy of the site with test songs and the test password; returns its folder."""
    if WORK.exists():
        shutil.rmtree(WORK, onexc=make_writable_and_retry)
    site = WORK / "site"
    shutil.copytree(SITE, site, ignore=shutil.ignore_patterns("*.db", "__pycache__", "sharpia", "visualia", "templaria", "scriptoria", "razoria", "seasonal"))
    (site / "music").mkdir()
    for title, frequency in TONES.items():
        make_tone(site / "music" / f"{title}.wav", frequency)
    (site / "manage_password.hash").write_text(generate_password_hash(TEST_PASSWORD))
    return site


def test_app():
    site = make_test_copy()
    # site/sharpia, site/visualia, site/templaria and site/razoria are Linux builds of the C#, VB.NET, C++ and
    # ASP.NET games; on this PC, their Windows builds run instead.
    os.environ.setdefault("SHARPIA_PROGRAM", str(SITE.parent / "csharp" / "build" / "win" / "sharpia.exe"))
    os.environ.setdefault("VISUALIA_PROGRAM", str(SITE.parent / "vbnet" / "build" / "win" / "visualia.exe"))
    os.environ.setdefault("TEMPLARIA_PROGRAM", str(SITE.parent / "cpp" / "build" / "win" / "templaria.exe"))
    os.environ.setdefault("RAZORIA_PROGRAM", str(SITE.parent / "aspnet" / "build" / "win" / "razoria.exe"))
    # The JavaScript game has nothing to build on this PC: scriptoria.cmd runs its source with this PC's Node.js.
    os.environ.setdefault("SCRIPTORIA_PROGRAM", str(SITE.parent / "javascript" / "Scriptoria" / "scriptoria.cmd"))
    sys.path.insert(0, str(site))
    from app import app
    app.config["SESSION_COOKIE_SECURE"] = False  # plain http on this computer
    return app


if __name__ == "__main__":
    app = test_app()
    print(f"Local test copy of the site in {WORK / 'site'}")
    app.run(host="127.0.0.1", port=PORT)
