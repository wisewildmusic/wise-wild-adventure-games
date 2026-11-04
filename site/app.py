"""Wise Wild: a small Flask site, run by gunicorn as the "Wise Wild Website" Pelican server.

Apache on outpost :8088 forwards to it. Restart the server in the Pelican panel after edits.
"""
import hashlib
import json
import math
import re
import secrets
import sqlite3
import time
from contextlib import closing, contextmanager
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from types import SimpleNamespace

from flask import (
    Flask, abort, flash, g, jsonify, redirect, render_template, request, send_from_directory,
    session, url_for,
)
from itsdangerous import BadSignature, URLSafeTimedSerializer
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash

import neuralia
import oraclia
import pythonia
import sequelia
import transactia
from compiled_game import CompiledGame, Unavailable

app = Flask(__name__)
# Apache tells the site (X-Forwarded-Proto) that visitors arrive over https, so redirects
# such as /manage -> /manage/ stay on https.
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)

# Audio files dropped into this folder are listed in the music library (/music/).
MUSIC_DIR = Path(app.root_path) / "music"
AUDIO_TYPES = {".mp3", ".m4a", ".aac", ".ogg", ".oga", ".opus", ".wav", ".flac", ".webm"}

# Song manager (/manage/). Archived songs are moved here, out of the site's reach.
ARCHIVE_DIR = Path(app.root_path) / "archives"
# Hash of the manager password, written by the server's `wisewild-manage-password` helper
# (see tools/set-manage-password.ps1). Without this file the manager stays locked.
PASSWORD_FILE = Path(app.root_path) / "manage_password.hash"
SECRET_KEY_FILE = Path(app.root_path) / "secret_key"

app.config.update(
    SECRET_KEY=SECRET_KEY_FILE.read_text().strip() if SECRET_KEY_FILE.exists() else secrets.token_hex(32),
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True,  # the sign-in cookie only ever travels over https
    MAX_CONTENT_LENGTH=200 * 1024 * 1024,  # per upload
)

LIBRARY_ART = "img/alien-saucer.jpg"

# Song links carry a signed code that expires after LINK_MINUTES and only works for the
# browser it was made for, so a copied or shared song address stops working. The site's
# players fetch fresh links as they go (static/player.js).
LINK_MINUTES = 10
link_signer = URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="song-link")

# Footer "Welcome Human Visitor # N": a count per page, kept in this SQLite file.
VISITS_DB = Path(app.root_path) / "visitors.db"
# Robots, previews and command-line tools aren't human visitors, so they aren't counted.
NOT_HUMAN = re.compile(
    r"bot|crawl|spider|slurp|fetch|preview|scan|curl|wget|python|httpclient|headless|lighthouse|monitor",
    re.IGNORECASE,
)

# The music database (SQLite). Every song file the site has seen, in the music folder or the
# archives, has a record in its `tracks` table with a permanent ID number, never changed or
# reused, which the whole site uses to tell songs apart, whatever they're called. Players
# report a song once it has been heard for 30 seconds (static/player.js), and each play is
# logged in `plays` against that ID. (The file keeps the name it had when it held only the
# play log.)
MUSIC_DB = Path(app.root_path) / "plays.db"
SCHEMA_VERSION = 1
POPULARITY_BARS = 7
REPLAY_GAP = timedelta(seconds=90)  # the same listener replaying a song sooner counts once

PLAYLIST_URL = "https://suno.com/playlist/1a581606-0b50-4657-b4c8-b0b48d2a667c"

# Hero artwork copied from wisewildmusic.com (paths under static/).
# hero.jpg is the web-sized copy; hero-original.png is the full-quality original.
HERO_IMAGE = "img/hero.jpg"

INTRO = (
    "Every track dropped is like a journey through a colorful playground of audio, "
    "where we explore sound and see where the rhythm goes for the love of musical "
    "experimentation. It is all about having a good time with the wild world of sound."
)

# The card buttons and social icons currently all play the music loop (static/player.js);
# their "url" values are kept here for when they become links again.
CHANNELS = [
    {
        "title": "Streaming",
        "text": "Access the full sonic spectrum via curated digital platforms. "
                "High-fidelity experimental output available for global listeners.",
        "cta": "Stream now",
        "url": PLAYLIST_URL,
    },
    {
        "title": "Printed media",
        "text": "Physical vinyl and cassette releases. Limited edition drops featuring "
                "experimental soundscapes and raw sonic textures.",
        "cta": "Shop store",
        "url": PLAYLIST_URL,
    },
    {
        "title": "Community",
        "text": "Join the collective. Engage with the artist's output through live "
                "broadcasts, experimental workshops, and sonic events.",
        "cta": "Join now",
        "url": PLAYLIST_URL,
    },
]

# Placeholder URLs copied from the Wix site; swap in real profile links.
SOCIALS = [
    {"name": "Facebook", "glyph": "f", "url": "https://www.facebook.com/", "color": "#1877f2"},
    {"name": "Instagram", "glyph": "ig", "url": "https://www.instagram.com/", "color": "#e1306c"},
    {"name": "YouTube", "glyph": "▶", "url": "https://www.youtube.com/", "color": "#ff0000"},
    {"name": "X", "glyph": "\U0001d54f", "url": "https://x.com/", "color": "#000000"},
    {"name": "LinkedIn", "glyph": "in", "url": "https://www.linkedin.com/", "color": "#0a66c2"},
    {"name": "TikTok", "glyph": "♪", "url": "https://www.tiktok.com/", "color": "#000000"},
]


def visits_db():
    db = sqlite3.connect(VISITS_DB, timeout=5)
    db.execute("CREATE TABLE IF NOT EXISTS visits (page TEXT PRIMARY KEY, count INTEGER NOT NULL)")
    return db


def visitor_number():
    """This visitor's number on the current page, counting each human once per page."""
    page = g.get("page_key") or request.endpoint or "not_found"
    seen = session.get("visitor", {})
    if page in seen:
        return seen[page]
    agent = request.headers.get("User-Agent", "")
    prefetch = "prefetch" in request.headers.get("Sec-Purpose", "") + request.headers.get("Purpose", "")
    with closing(visits_db()) as db:
        if request.method != "GET" or not agent or NOT_HUMAN.search(agent) or prefetch:
            row = db.execute("SELECT count FROM visits WHERE page = ?", (page,)).fetchone()
            return row[0] if row else 0
        number = db.execute(
            "INSERT INTO visits (page, count) VALUES (?, 1) "
            "ON CONFLICT(page) DO UPDATE SET count = count + 1 RETURNING count",
            (page,),
        ).fetchone()[0]
        db.commit()
    session["visitor"] = {**seen, page: number}
    return number


def listener_id():
    """A random id for this browser, kept in its session cookie; song links are tied to it."""
    if "listener" not in session:
        session["listener"] = secrets.token_urlsafe(9)
    return session["listener"]


def song_link(track_id):
    """An address for one song (by its ID) that expires after LINK_MINUTES and only works in
    this browser."""
    return url_for("track_file", track_id=track_id, t=link_signer.dumps([track_id, listener_id()]))


# The site's own files (scripts, styles, pictures) are addressed with their last-change time,
# e.g. /static/adventure.js?v=1793480000, so after an update every browser fetches the new
# copy and never mixes an old saved script with a new page.
@app.url_defaults
def static_file_version(endpoint, values):
    if endpoint == "static" and "filename" in values and "v" not in values:
        try:
            values["v"] = int((Path(app.static_folder) / values["filename"]).stat().st_mtime)
        except OSError:
            pass


@app.context_processor
def site_globals():
    return {
        "playlist_url": PLAYLIST_URL, "socials": SOCIALS,
        "visitor_number": visitor_number, "song_link": song_link,
    }


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(Path(app.root_path) / "static", "favicon.ico", mimetype="image/vnd.microsoft.icon")


@app.route("/")
def home():
    return render_template("index.html", hero_image=HERO_IMAGE, intro=INTRO, channels=CHANNELS)


@app.route("/about/")
def about():
    return render_template("about.html")


def song_title(filename):
    """A song's title is its file name, without the extension."""
    return Path(filename).stem.replace("_", " ")


# --- The music database ---------------------------------------------------------------------

def music_db():
    db = sqlite3.connect(MUSIC_DB, timeout=10, isolation_level=None)  # transactions are explicit
    db.row_factory = sqlite3.Row
    return db


@contextmanager
def transaction(db):
    """Changes made inside are saved together or not at all, one writer at a time."""
    db.execute("BEGIN IMMEDIATE")
    try:
        yield db
    except BaseException:
        db.execute("ROLLBACK")
        raise
    db.execute("COMMIT")


TRACKS_TABLE = """
    CREATE TABLE IF NOT EXISTS tracks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- the song's permanent ID, never changed or reused
        status TEXT NOT NULL,       -- 'active' (in the music folder), 'archived' or 'missing'
        file TEXT NOT NULL,         -- its file name in the music or archives folder (last known, if missing)
        title TEXT NOT NULL,        -- its title: the file name without the extension
        sha TEXT NOT NULL,          -- fingerprint (sha256) of the file's contents
        size INTEGER NOT NULL,      -- size and modification time: when either changes, the
        mtime_ns INTEGER NOT NULL,  --   fingerprint is worked out again
        added_at TEXT NOT NULL,     -- when it was added (the file's date), UTC, ISO 8601
        changed_at TEXT NOT NULL    -- when its record last changed (rename, archive...), UTC
    )"""
PLAYS_TABLE = """
    CREATE TABLE IF NOT EXISTS plays (
        id INTEGER PRIMARY KEY,
        track INTEGER REFERENCES tracks (id),  -- the song's ID
        song TEXT NOT NULL,       -- fingerprint of its file when played
        title TEXT NOT NULL,      -- its title (updated when the song is renamed)
        played_at TEXT NOT NULL,  -- UTC, ISO 8601
        listener TEXT NOT NULL    -- random per-browser id (see listener_id)
    )"""


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def file_facts(path):
    stat = path.stat()
    return {"sha": hashlib.sha256(path.read_bytes()).hexdigest(), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def add_track(db, path, status):
    """A new record (and ID) for a song file; returns the ID."""
    facts = file_facts(path)
    added = datetime.fromtimestamp(facts["mtime_ns"] / 1e9, timezone.utc).isoformat(timespec="seconds")
    return db.execute(
        "INSERT INTO tracks (status, file, title, sha, size, mtime_ns, added_at, changed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (status, path.name, song_title(path.name), facts["sha"], facts["size"], facts["mtime_ns"], added, utc_now()),
    ).lastrowid


def audio_files(folder):
    return [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in AUDIO_TYPES] if folder.is_dir() else []


def setup_music_db():
    """Create the music database when the site starts, or bring an older one up to date."""
    with closing(music_db()) as db, transaction(db):
        version = db.execute("PRAGMA user_version").fetchone()[0]
        db.execute(TRACKS_TABLE)
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS tracks_in_music ON tracks (file) WHERE status = 'active'")
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS tracks_in_archives ON tracks (file) WHERE status = 'archived'")
        db.execute("CREATE INDEX IF NOT EXISTS tracks_by_sha ON tracks (sha)")
        db.execute(PLAYS_TABLE)
        if "track" not in [row["name"] for row in db.execute("PRAGMA table_info(plays)")]:
            db.execute("ALTER TABLE plays ADD COLUMN track INTEGER REFERENCES tracks (id)")
        db.execute("CREATE INDEX IF NOT EXISTS plays_by_track ON plays (track, listener, played_at)")
        if version < 1:
            give_existing_songs_ids(db)
        db.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def give_existing_songs_ids(db):
    """Version 1 (2026-10-27): every song file, in the music folder and the archives, gets an ID,
    numbered in the order the files were added, and every logged play is linked to its song's ID.
    Before then songs were known by file name, and plays by the song's fingerprint."""
    found = [(f.stat().st_mtime_ns, f.name.lower(), f, "active") for f in audio_files(MUSIC_DIR)]
    found += [(f.stat().st_mtime_ns, f.name.lower(), f, "archived") for f in audio_files(ARCHIVE_DIR)]
    for _, _, path, status in sorted(found, key=lambda item: item[:2]):
        add_track(db, path, status)
    for play in db.execute("SELECT id, song, title, played_at FROM plays WHERE track IS NULL").fetchall():
        # The song with that fingerprint; if identical copies have one each, the one with the
        # title it was played under; if no file has it any more, a 'missing' record for it.
        copies = db.execute(
            "SELECT id, title FROM tracks WHERE sha = ? ORDER BY status = 'active' DESC, id", (play["song"],),
        ).fetchall()
        track = next((c["id"] for c in copies if c["title"] == play["title"]), copies[0]["id"] if copies else None)
        if track is None:
            track = db.execute(
                "INSERT INTO tracks (status, file, title, sha, size, mtime_ns, added_at, changed_at) "
                "VALUES ('missing', ?, ?, ?, 0, 0, ?, ?)",
                (play["title"], play["title"], play["song"], play["played_at"], utc_now()),
            ).lastrowid
        db.execute("UPDATE plays SET track = ? WHERE id = ?", (track, play["id"]))
    db.execute("DROP INDEX IF EXISTS plays_by_song")
    db.execute("DROP TABLE IF EXISTS fingerprints")  # replaced by the fingerprints kept in tracks
    db.execute("DROP TABLE IF EXISTS renames")       # IDs make the old-name lookups unnecessary


def active_tracks(db):
    return {row["file"]: row for row in db.execute("SELECT * FROM tracks WHERE status = 'active'")}


def sync_tracks(db):
    """The active songs' records, after bringing the database in step with the music folder.

    Songs added, renamed, removed or put back outside the song manager (by hand, or by the
    new-music script) are noticed here: a new file gets a new ID, unless its contents match a
    song whose file went missing or was archived and has since left the archives, in which
    case that song keeps its ID under the new name."""
    files = {f.name: f.stat() for f in audio_files(MUSIC_DIR)}
    active = active_tracks(db)
    if files.keys() == active.keys() and all(
        (stat.st_size, stat.st_mtime_ns) == (active[name]["size"], active[name]["mtime_ns"]) for name, stat in files.items()
    ):
        return list(active.values())

    with transaction(db):
        files = {f.name: f for f in audio_files(MUSIC_DIR)}  # again, now that no one else is writing
        gone = active_tracks(db)
        arrived = []
        for name, path in files.items():
            row = gone.pop(name, None)
            if row is None:
                arrived.append(path)
                continue
            stat = path.stat()
            if (stat.st_size, stat.st_mtime_ns) != (row["size"], row["mtime_ns"]):  # replaced by hand
                facts = file_facts(path)
                db.execute(
                    "UPDATE tracks SET sha = ?, size = ?, mtime_ns = ?, changed_at = ? WHERE id = ?",
                    (facts["sha"], facts["size"], facts["mtime_ns"], utc_now(), row["id"]),
                )
        for path in sorted(arrived, key=lambda p: (p.stat().st_mtime_ns, p.name.lower())):
            facts = file_facts(path)
            match = next((row for row in gone.values() if row["sha"] == facts["sha"]), None)
            if match:
                del gone[match["file"]]
            else:
                earlier = db.execute(
                    "SELECT * FROM tracks WHERE sha = ? AND status IN ('archived', 'missing') ORDER BY id", (facts["sha"],),
                ).fetchall()
                match = next((
                    row for row in earlier if row["status"] == "missing" or not (ARCHIVE_DIR / row["file"]).is_file()
                ), None)
            if match:
                db.execute(
                    "UPDATE tracks SET status = 'active', file = ?, title = ?, sha = ?, size = ?, mtime_ns = ?, changed_at = ? "
                    "WHERE id = ?",
                    (path.name, song_title(path.name), facts["sha"], facts["size"], facts["mtime_ns"], utc_now(), match["id"]),
                )
                db.execute("UPDATE plays SET title = ? WHERE track = ?", (song_title(path.name), match["id"]))
            else:
                add_track(db, path, "active")
        for row in gone.values():
            db.execute("UPDATE tracks SET status = 'missing', changed_at = ? WHERE id = ?", (utc_now(), row["id"]))
    return list(active_tracks(db).values())


def music_tracks():
    """The songs in the music folder, each with its ID, sorted by title."""
    with closing(music_db()) as db:
        rows = sync_tracks(db)
    tracks = [{
        "id": row["id"],
        "file": row["file"],
        "title": row["title"],
        "size": row["size"],
        "added": datetime.fromtimestamp(row["mtime_ns"] / 1e9),
    } for row in rows]
    return sorted(tracks, key=lambda t: t["title"].lower())


def find_track(db, track_id):
    """An active song's record by its ID, or None."""
    try:
        track_id = int(track_id)
    except (TypeError, ValueError):
        return None
    return db.execute("SELECT * FROM tracks WHERE id = ? AND status = 'active'", (track_id,)).fetchone()


def with_popularity(tracks):
    """Add each song's play count and popularity bars (0-7, relative to the most-played song)."""
    with closing(music_db()) as db:
        counts = {row[0]: row[1] for row in db.execute("SELECT track, COUNT(*) FROM plays GROUP BY track")}
    for t in tracks:
        t["plays"] = counts.get(t["id"], 0)
    top = max((t["plays"] for t in tracks), default=0)
    for t in tracks:
        t["bars"] = math.ceil(POPULARITY_BARS * t["plays"] / top) if t["plays"] else 0
    return tracks


setup_music_db()


# --- Word tags --------------------------------------------------------------------------------
# Descriptive word tags ("Lullaby", "Chill", "Metal"...), kept in their own database file. A
# song can have any number of tags and a tag can be on any number of songs. Songs are linked
# by their IDs in the music database. The song manager adds and edits tags; visitors pick a
# tag in the music library to hear every song that has it.
TAGS_DB = Path(app.root_path) / "tags.db"
TAG_MAX_LENGTH = 32


def tags_db():
    db = sqlite3.connect(TAGS_DB, timeout=10, isolation_level=None)  # transactions are explicit
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def setup_tags_db():
    with closing(tags_db()) as db, transaction(db):
        db.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,  -- the tag's permanent ID, never reused
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,  -- as typed; "chill" and "Chill" are one tag
                created_at TEXT NOT NULL               -- UTC, ISO 8601
            )""")
        db.execute("""
            CREATE TABLE IF NOT EXISTS track_tags (
                track INTEGER NOT NULL,  -- a song's ID in the music database (tracks.id in plays.db)
                tag INTEGER NOT NULL REFERENCES tags (id) ON DELETE CASCADE,
                tagged_at TEXT NOT NULL,  -- UTC, ISO 8601
                PRIMARY KEY (track, tag)
            )""")
        db.execute("CREATE INDEX IF NOT EXISTS track_tags_by_tag ON track_tags (tag, track)")
        db.execute("PRAGMA user_version = 1")


setup_tags_db()


def clean_tag(raw):
    """A tag as typed, tidied: no commas (they separate tags), control characters, angle
    brackets or leading #, and single spaces."""
    name = re.sub(r"[\x00-\x1f,<>]", "", raw)
    name = re.sub(r"\s+", " ", name).strip().lstrip("#").strip()
    return name[:TAG_MAX_LENGTH].strip()


def split_tags(raw):
    """Tags typed into one box, separated by commas, without repeats."""
    names = {}
    for part in str(raw).split(","):
        name = clean_tag(part)
        if name:
            names.setdefault(name.lower(), name)
    return list(names.values())


def tag_overview(active_ids, include_unused=False):
    """Every tag with how many songs in the music folder have it (tags on no such song only if
    include_unused), and each of those songs' tags, alphabetically."""
    with closing(tags_db()) as db:
        tags = {row["id"]: {"id": row["id"], "name": row["name"], "count": 0} for row in db.execute("SELECT id, name FROM tags")}
        per_track = {}
        for row in db.execute("SELECT track, tag FROM track_tags"):
            if row["track"] in active_ids:
                tags[row["tag"]]["count"] += 1
                per_track.setdefault(row["track"], []).append(tags[row["tag"]])
    by_name = lambda tag: tag["name"].lower()  # noqa: E731
    listed = sorted((tag for tag in tags.values() if include_unused or tag["count"]), key=by_name)
    return listed, {track: sorted(found, key=by_name) for track, found in per_track.items()}


def with_tags(tracks, include_unused=False):
    """Add each song's tags; returns the tags list for the page (see tag_overview)."""
    listed, per_track = tag_overview({t["id"] for t in tracks}, include_unused)
    for t in tracks:
        t["tags"] = per_track.get(t["id"], [])
    return listed


@app.template_filter("filesize")
def filesize(num_bytes):
    return f"{num_bytes / (1024 * 1024):.1f} MB"


@app.template_filter("shortdate")
def shortdate(moment):
    return f"{moment:%b} {moment.day}, {moment.year}"


# Music library: every song in the music folder in a table, over the alien/saucer artwork.
@app.route("/music/")
def songs():
    tracks = with_popularity(music_tracks())
    tags = with_tags(tracks)
    return render_template("songs.html", tracks=tracks, tags=tags, background=LIBRARY_ART)


# The music library's address until 2026-10-24.
@app.route("/songs/")
def old_songs_address():
    return redirect(url_for("songs"), code=301)


# --- Song manager: password-protected copy of the library with upload, rename and archive ---

def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


def check_csrf():
    expected = session.get("csrf")
    if not expected or not secrets.compare_digest(request.form.get("csrf", ""), expected):
        abort(400)


SIGN_IN_HOURS = 12


def password_fingerprint():
    """Changes whenever the password does, which signs everyone out."""
    return hashlib.sha256(PASSWORD_FILE.read_bytes()).hexdigest()[:16] if PASSWORD_FILE.exists() else None


def signed_in():
    fingerprint = password_fingerprint()
    return bool(
        fingerprint
        and session.get("manager") == fingerprint
        and time.time() - session.get("since", 0) < SIGN_IN_HOURS * 3600
    )


def manager_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not signed_in():
            session.pop("manager", None)
            return redirect(url_for("manage_login"))
        return view(*args, **kwargs)
    return wrapped


def free_path(folder, name):
    """folder/name, or a numbered variant such as "Song (2).mp3" if that name is taken."""
    path = folder / name
    number = 2
    while path.exists():
        path = folder / f"{Path(name).stem} ({number}){Path(name).suffix}"
        number += 1
    return path


UNSAFE_NAME_CHARS = re.compile(r'[\x00-\x1f<>:"/\\|?*]')


def clean_upload_name(raw):
    """The uploaded file's own name (spaces and all), minus folders and unsafe characters."""
    name = UNSAFE_NAME_CHARS.sub("", raw.replace("\\", "/").rsplit("/", 1)[-1])
    return name.strip().lstrip(".")[:150]


def looks_like_mp3(stream):
    head = stream.read(3)
    stream.seek(0)
    return head == b"ID3" or (len(head) >= 2 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0)


@app.route("/manage/login", methods=["GET", "POST"])
def manage_login():
    if signed_in():
        return redirect(url_for("manage"))
    locked = not PASSWORD_FILE.exists()
    if request.method == "POST" and not locked:
        check_csrf()
        if check_password_hash(PASSWORD_FILE.read_text().strip(), request.form.get("password", "")):
            session.clear()
            session["manager"] = password_fingerprint()
            session["since"] = time.time()
            session["csrf"] = secrets.token_urlsafe(32)
            app.logger.warning("manage: signed in")
            return redirect(url_for("manage"))
        time.sleep(1.5)  # slows down password guessing
        app.logger.warning("manage: wrong password")
        flash("Wrong password.", "error")
    return render_template("manage_login.html", locked=locked, background=LIBRARY_ART)


@app.post("/manage/logout")
@manager_required
def manage_logout():
    check_csrf()
    session.clear()
    return redirect(url_for("manage_login"))


@app.route("/manage/")
@manager_required
def manage():
    archived = sum(1 for f in ARCHIVE_DIR.iterdir() if f.is_file()) if ARCHIVE_DIR.is_dir() else 0
    tracks = with_popularity(music_tracks())
    tags = with_tags(tracks, include_unused=True)
    return render_template(
        "manage.html", tracks=tracks, tags=tags, archived=archived, background=LIBRARY_ART,
    )


@app.post("/manage/archive")
@manager_required
def manage_archive():
    check_csrf()
    with closing(music_db()) as db, transaction(db):
        row = find_track(db, request.form.get("track"))
        if not row or not (MUSIC_DIR / row["file"]).is_file():
            abort(404)
        # Archived songs whose files have since been taken out of the archives by hand are
        # missing now (which also frees their names for reuse in the archives).
        for old in db.execute("SELECT id, file FROM tracks WHERE status = 'archived'").fetchall():
            if not (ARCHIVE_DIR / old["file"]).is_file():
                db.execute("UPDATE tracks SET status = 'missing', changed_at = ? WHERE id = ?", (utc_now(), old["id"]))
        ARCHIVE_DIR.mkdir(exist_ok=True)
        target = free_path(ARCHIVE_DIR, row["file"])
        (MUSIC_DIR / row["file"]).rename(target)
        db.execute("UPDATE tracks SET status = 'archived', file = ?, changed_at = ? WHERE id = ?",
                   (target.name, utc_now(), row["id"]))
    app.logger.warning("manage: archived track %s, %s -> archives/%s", row["id"], row["file"], target.name)
    flash(f"Archived “{row['title']}” (#{row['id']}, moved to the archives folder).", "ok")
    return redirect(url_for("manage"))


def clean_title(raw, suffix):
    """A new song title as typed: unsafe characters and extra spaces removed, and the file
    extension dropped if it was typed too. Underscores become spaces, since titles show them
    that way."""
    title = UNSAFE_NAME_CHARS.sub("", raw).replace("_", " ")
    title = re.sub(r"\s+", " ", title).strip().lstrip(".").rstrip(". ")
    if title.lower().endswith(suffix.lower()):
        title = title[: -len(suffix)].rstrip(". ")
    return title[:140]


# Renaming changes the song's file name and title, shown everywhere: the library, the
# manager, the playlists and the header's now-playing title. Its ID stays the same, so its
# date, play count, popularity and play log all stay with it (the log takes the new title).
@app.post("/manage/rename")
@manager_required
def manage_rename():
    check_csrf()
    with closing(music_db()) as db, transaction(db):
        row = find_track(db, request.form.get("track"))
        song = MUSIC_DIR / row["file"] if row else None
        if not song or not song.is_file():
            abort(404)
        title = clean_title(request.form.get("title", ""), song.suffix)
        if not title:
            flash(f"“{row['title']}” wasn't renamed: the new name was empty.", "error")
            return redirect(url_for("manage"))
        target = MUSIC_DIR / f"{title}{song.suffix}"
        if target.name == song.name:
            return redirect(url_for("manage"))
        taken = {f.name.lower() for f in MUSIC_DIR.iterdir() if f.name != song.name}
        if target.name.lower() in taken:
            flash(f"“{row['title']}” wasn't renamed: another song is already called “{title}”.", "error")
            return redirect(url_for("manage"))
        song.rename(target)  # keeps the file's date
        title = song_title(target.name)
        db.execute("UPDATE tracks SET file = ?, title = ?, changed_at = ? WHERE id = ?",
                   (target.name, title, utc_now(), row["id"]))
        db.execute("UPDATE plays SET title = ? WHERE track = ?", (title, row["id"]))
    app.logger.warning("manage: renamed track %s, %s -> %s", row["id"], song.name, target.name)
    flash(f"Renamed “{row['title']}” (#{row['id']}) to “{title}”.", "ok")
    return redirect(url_for("manage"))


# Each uploaded song gets its record and ID as soon as it's saved.
@app.post("/manage/upload")
@manager_required
def manage_upload():
    check_csrf()
    MUSIC_DIR.mkdir(exist_ok=True)
    added, skipped = [], []
    with closing(music_db()) as db:
        sync_tracks(db)  # songs added by hand get their IDs first, so numbers follow arrival order
        for upload in request.files.getlist("songs"):
            name = clean_upload_name(upload.filename or "")
            if not name.lower().endswith(".mp3") or not looks_like_mp3(upload.stream):
                skipped.append(f"{upload.filename or 'a file'}: not an MP3")
                continue
            with transaction(db):
                if name.lower() in {f.name.lower() for f in MUSIC_DIR.iterdir()}:
                    skipped.append(f"{name}: a song with that name is already in the music folder")
                    continue
                target = MUSIC_DIR / name
                partial = MUSIC_DIR / f".{name}.part"  # hidden from the site until complete
                upload.save(partial)
                partial.replace(target)
                track_id = add_track(db, target, "active")
            added.append(f"{song_title(name)} (#{track_id})")
            app.logger.warning("manage: uploaded %s as track %s", name, track_id)
    if added:
        flash(f"Uploaded {len(added)} song{'' if len(added) == 1 else 's'}: {', '.join(added)}.", "ok")
    for reason in skipped:
        flash(f"Skipped {reason}.", "error")
    if not added and not skipped:
        flash("No files were chosen.", "error")
    return redirect(url_for("manage"))


# Tagging songs. The manager page's script sends these with "Accept: application/json" and
# gets the song's tags back, so chips update without reloading; without the script, the forms
# work as ordinary posts that return to the page.
def wants_json():
    return request.accept_mimetypes.best == "application/json"


def tag_reply(track_id, message, category="ok"):
    if wants_json():
        if category == "error":
            return jsonify(error=message), 400
        with closing(tags_db()) as db:
            tags = db.execute(
                "SELECT tags.id, tags.name FROM track_tags JOIN tags ON tags.id = track_tags.tag "
                "WHERE track_tags.track = ? ORDER BY tags.name COLLATE NOCASE", (track_id,),
            ).fetchall()
            names = [row["name"] for row in db.execute("SELECT name FROM tags ORDER BY name COLLATE NOCASE")]
        return jsonify(tags=[dict(row) for row in tags], all=names)
    flash(message, category)
    return redirect(url_for("manage"))


def tagged_track():
    """The song a tag change is for (in the music folder), or a 404."""
    with closing(music_db()) as db:
        row = find_track(db, request.form.get("track"))
    if not row:
        abort(404)
    return row


@app.post("/manage/tags/add")
@manager_required
def manage_tag_add():
    check_csrf()
    track = tagged_track()
    names = split_tags(request.form.get("names", ""))
    if not names:
        return tag_reply(track["id"], "No tag was typed.", "error")
    with closing(tags_db()) as db, transaction(db):
        for name in names:
            existing = db.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()  # any capitals
            tag_id = existing["id"] if existing else db.execute(
                "INSERT INTO tags (name, created_at) VALUES (?, ?)", (name, utc_now())).lastrowid
            db.execute("INSERT OR IGNORE INTO track_tags (track, tag, tagged_at) VALUES (?, ?, ?)",
                       (track["id"], tag_id, utc_now()))
    app.logger.warning("manage: tagged track %s: %s", track["id"], ", ".join(names))
    return tag_reply(track["id"], f"Tagged “{track['title']}”: {', '.join(names)}.")


@app.post("/manage/tags/remove")
@manager_required
def manage_tag_remove():
    check_csrf()
    track = tagged_track()
    with closing(tags_db()) as db, transaction(db):
        tag = db.execute("SELECT id, name FROM tags WHERE id = ?", (request.form.get("tag", type=int),)).fetchone()
        if tag:
            db.execute("DELETE FROM track_tags WHERE track = ? AND tag = ?", (track["id"], tag["id"]))
    if not tag:
        abort(404)
    app.logger.warning("manage: untagged track %s: %s", track["id"], tag["name"])
    return tag_reply(track["id"], f"Took the tag “{tag['name']}” off “{track['title']}”.")


# Renaming a tag to another tag's name merges the two; deleting a tag takes it off every song.
@app.post("/manage/tags/rename")
@manager_required
def manage_tag_rename():
    check_csrf()
    name = clean_tag(request.form.get("name", ""))
    with closing(tags_db()) as db, transaction(db):
        tag = db.execute("SELECT id, name FROM tags WHERE id = ?", (request.form.get("tag", type=int),)).fetchone()
        if not tag:
            abort(404)
        if not name:
            flash(f"The tag “{tag['name']}” wasn't renamed: the new name was empty.", "error")
            return redirect(url_for("manage", _anchor="tags"))
        other = db.execute("SELECT id, name FROM tags WHERE name = ? AND id != ?", (name, tag["id"])).fetchone()
        if other:
            db.execute("INSERT OR IGNORE INTO track_tags (track, tag, tagged_at) "
                       "SELECT track, ?, tagged_at FROM track_tags WHERE tag = ?", (other["id"], tag["id"]))
            db.execute("DELETE FROM tags WHERE id = ?", (tag["id"],))
            message = f"Merged the tag “{tag['name']}” into “{other['name']}”."
        elif name != tag["name"]:
            db.execute("UPDATE tags SET name = ? WHERE id = ?", (name, tag["id"]))
            message = f"Renamed the tag “{tag['name']}” to “{name}”."
        else:
            return redirect(url_for("manage", _anchor="tags"))
    app.logger.warning("manage: %s", message)
    flash(message, "ok")
    return redirect(url_for("manage", _anchor="tags"))


@app.post("/manage/tags/delete")
@manager_required
def manage_tag_delete():
    check_csrf()
    with closing(tags_db()) as db, transaction(db):
        tag = db.execute("SELECT id, name FROM tags WHERE id = ?", (request.form.get("tag", type=int),)).fetchone()
        if not tag:
            abort(404)
        songs = db.execute("SELECT COUNT(*) FROM track_tags WHERE tag = ?", (tag["id"],)).fetchone()[0]
        db.execute("DELETE FROM tags WHERE id = ?", (tag["id"],))  # its song links go with it
    app.logger.warning("manage: deleted tag %s (%s)", tag["name"], songs)
    flash(f"Deleted the tag “{tag['name']}” (it was on {songs} song{'' if songs == 1 else 's'}).", "ok")
    return redirect(url_for("manage", _anchor="tags"))


@app.errorhandler(413)
def upload_too_large(error):
    flash("That upload was too big: up to 200 MB at a time.", "error")
    return redirect(url_for("manage"))


# Read by the "Explore creations" button each time it starts a loop through the songs.
@app.route("/api/playlist")
def playlist():
    return jsonify([
        {"id": t["id"], "title": t["title"], "url": song_link(t["id"])}
        for t in music_tracks()
    ])


def track_for(db, data):
    """The active song a player means: by ID, or by file name from pages opened before songs
    had IDs (2026-10-27)."""
    if data.get("track") is not None:
        return find_track(db, data.get("track"))
    if data.get("file"):
        sync_tracks(db)
        return active_tracks(db).get(str(data.get("file")))
    return None


# A player reports a song it has played for 30 seconds. The report carries the song link's
# code, so only this site's players (in the browser the link was made for) can log plays.
# Answers with everyone's current popularity bars (by song ID), so meters on the page can update.
@app.post("/api/played")
def song_played():
    if request.headers.get("Sec-Fetch-Site", "same-origin") != "same-origin":
        abort(403)
    data = request.get_json(silent=True) or {}
    try:
        linked, listener = link_signer.loads(str(data.get("t", "")), max_age=LINK_MINUTES * 60 + 3600)
    except (BadSignature, ValueError):
        abort(403)
    agent = request.headers.get("User-Agent", "")
    counted = bool(agent) and not NOT_HUMAN.search(agent) and not str(data.get("page", "")).startswith("/manage")
    now = datetime.now(timezone.utc)
    with closing(music_db()) as db:
        row = track_for(db, data)
        if not row or not (MUSIC_DIR / row["file"]).is_file():
            abort(404)
        if linked != row["id"] or listener != session.get("listener"):
            abort(403)
        if counted:
            with transaction(db):
                recent = db.execute(
                    "SELECT 1 FROM plays WHERE track = ? AND listener = ? AND played_at > ?",
                    (row["id"], listener, (now - REPLAY_GAP).isoformat(timespec="seconds")),
                ).fetchone()
                counted = recent is None
                if counted:
                    db.execute(
                        "INSERT INTO plays (track, song, title, played_at, listener) VALUES (?, ?, ?, ?, ?)",
                        (row["id"], row["sha"], row["title"], now.isoformat(timespec="seconds"), listener),
                    )
    tracks = with_popularity(music_tracks())
    return jsonify(counted=counted, bars={t["id"]: t["bars"] for t in tracks})


# A fresh link for one song (?track=ID), asked for by the site's players before playing it and
# when an old link has expired. The answer includes the song's title now, so a player shows
# the right name even if the song was renamed after its page was opened.
@app.route("/api/song-link")
def fresh_song_link():
    with closing(music_db()) as db:
        row = track_for(db, request.args)
    if not row:
        abort(404)
    return jsonify({"id": row["id"], "title": row["title"], "url": song_link(row["id"])})


@app.route("/music/track/<int:track_id>")
def track_file(track_id):
    # Browsers say what a request is for. Only hand songs to audio players on this site, so
    # opening a song's address in a tab, "Save link as" or another website gets refused.
    if request.headers.get("Sec-Fetch-Dest", "audio") != "audio":
        abort(403)
    if request.headers.get("Sec-Fetch-Site", "same-origin") != "same-origin":
        abort(403)
    # The link must be current and made for this browser. (Some phone browsers fetch audio
    # without sending the site's cookie at all; then only the expiry applies.)
    try:
        linked, listener = link_signer.loads(request.args.get("t", ""), max_age=LINK_MINUTES * 60)
    except (BadSignature, ValueError):
        abort(403)
    has_cookie = app.config["SESSION_COOKIE_NAME"] in request.cookies
    if linked != track_id or (has_cookie and listener != session.get("listener")):
        abort(403)
    with closing(music_db()) as db:
        row = find_track(db, track_id)
    if not row:
        abort(404)
    return send_from_directory(MUSIC_DIR, row["file"])


# Song addresses named the file until songs had IDs (2026-10-27). Pages opened before then
# get a new address from /api/song-link when one of these fails.
@app.route("/music/<path:filename>")
def old_song_address(filename):
    return "", 404


# --- The adventure games (/adventure/) ----------------------------------------------------
# Text adventures with programming challenges: first a page to choose one, then the game.
# - The Lost Treasure of Pythonia (/adventure/python/): all about Python, written in Python
#   (pythonia.py, adapted from AdventuresInPython.py).
# - The Lost Compiler of Sharpia (/adventure/csharp/): all about C#, written in C#
#   (csharp/Sharpia, a compiled program, reached through compiled_game.py).
# - The Lost Runtime of Visualia (/adventure/vbnet/): all about VB.NET, written in VB.NET
#   (vbnet/Visualia, a compiled program, reached the same way).
# - Three games about SQL, all written in Python as copies of pythonia.py, since SQL can't run
#   a game page by page: The Lost Standard of Sequelia (/adventure/ansi-sql/, sequelia.py), The
#   Lost Commit of Transactia (/adventure/t-sql/, transactia.py) and The Lost Package of Oraclia
#   (/adventure/pl-sql/, oraclia.py).
# - The Lost Pointer of Templaria (/adventure/cpp/): all about C++, written in C++
#   (cpp/Templaria, a compiled program, reached through compiled_game.py).
# - The Lost Promise of Scriptoria (/adventure/javascript/): all about JavaScript, written in JavaScript
#   (javascript/Scriptoria, a program of its own, reached the same way).
# - The Lost Session of Razoria (/adventure/aspnet/): all about ASP.NET, written in ASP.NET
#   (aspnet/Razoria, a compiled program, reached the same way).
# - The Lost Weights of Neuralia (/adventure/ai/): all about AI, written in Python as a copy of pythonia.py, and far the
#   longest of them (neuralia.py). Its panel is the hub at the very center of the choice page's flying saucer.
# They play the same way and share these pages, since each game's `engine` offers the same names.
# Each quest is a row in its game's own database, holding its random seed and the moves made so
# far, which engine.replay() plays through for every page. Finished quests are the score log,
# shared by every explorer as that game's Hall of Explorers. A won quest can be carried on: a new
# quest that starts with its score, on the next level (after Easy or Medium) or down a path
# (forest, cave or castle) the explorer hasn't taken yet on that level. Each quest's
# `continues` points back to the win it carried on from, so a whole run can be traced.
ADVENTURE_GAMES = {
    "python": SimpleNamespace(
        key="python", engine=pythonia, database=Path(app.root_path) / "adventure.db", session_quest="quest",
        page_key="adventure", language="Python", title="The Lost Treasure of Pythonia",
        art="img/adventure/python.webp", master="Python Master",
        blurb="Riddles written in the language of the serpent, in a game written in Python.",
    ),
    "csharp": SimpleNamespace(
        key="csharp", engine=CompiledGame("C#", "sharpia", "SHARPIA_PROGRAM"),
        database=Path(app.root_path) / "adventure-csharp.db", session_quest="quest_csharp",
        page_key="adventure_csharp", language="C#", title="The Lost Compiler of Sharpia",
        art="img/adventure/garbage-collector.webp", master="C# Master",
        blurb="Riddles that must compile, in a game written in C#.",
    ),
    "vbnet": SimpleNamespace(
        key="vbnet", engine=CompiledGame("VB.NET", "visualia", "VISUALIA_PROGRAM"),
        database=Path(app.root_path) / "adventure-vbnet.db", session_quest="quest_vbnet",
        page_key="adventure_vbnet", language="VB.NET", title="The Lost Runtime of Visualia",
        art="img/adventure/nothing.webp", master="VB.NET Master",
        blurb="Riddles that read almost like plain English, in a game written in VB.NET.",
    ),
    "ansi-sql": SimpleNamespace(
        key="ansi-sql", engine=sequelia, database=Path(app.root_path) / "adventure-ansi-sql.db",
        session_quest="quest_ansi_sql", page_key="adventure_ansi_sql", language="ANSI SQL",
        title="The Lost Standard of Sequelia", art="img/adventure/cartesian-beast.webp", master="ANSI SQL Master",
        blurb="Riddles in the common tongue of every database, in a game written in Python.",
    ),
    "t-sql": SimpleNamespace(
        key="t-sql", engine=transactia, database=Path(app.root_path) / "adventure-t-sql.db",
        session_quest="quest_t_sql", page_key="adventure_t_sql", language="T-SQL",
        title="The Lost Commit of Transactia", art="img/adventure/deadlock.webp", master="T-SQL Master",
        blurb="Riddles in SQL Server's own dialect, in a game written in Python.",
    ),
    "pl-sql": SimpleNamespace(
        key="pl-sql", engine=oraclia, database=Path(app.root_path) / "adventure-pl-sql.db",
        session_quest="quest_pl_sql", page_key="adventure_pl_sql", language="PL/SQL",
        title="The Lost Package of Oraclia", art="img/adventure/mutating-table.webp", master="PL/SQL Master",
        blurb="Riddles in Oracle's blocks of BEGIN and END, in a game written in Python.",
    ),
    "cpp": SimpleNamespace(
        key="cpp", engine=CompiledGame("C++", "templaria", "TEMPLARIA_PROGRAM"),
        database=Path(app.root_path) / "adventure-cpp.db", session_quest="quest_cpp",
        page_key="adventure_cpp", language="C++", title="The Lost Pointer of Templaria",
        art="img/adventure/undefined-behavior.webp", master="C++ Master",
        blurb="Riddles with no safety net, in a game written in C++.",
    ),
}
# Games the choice page's flying saucer has a panel for but that can't run here. All the panels now have games, so this
# only ever holds the two below, on a site without their programs. (Their shapes are in style.css.)
ADVENTURE_COMING = []
# The JavaScript game appears only where its program is there to run it: until site/scriptoria is uploaded, a site
# with this file still shows its panel as coming soon, so the other games can go live without it.
_scriptoria = CompiledGame("JavaScript", "scriptoria", "SCRIPTORIA_PROGRAM")
if _scriptoria.program.exists():
    ADVENTURE_GAMES["javascript"] = SimpleNamespace(
        key="javascript", engine=_scriptoria, database=Path(app.root_path) / "adventure-javascript.db",
        session_quest="quest_javascript", page_key="adventure_javascript", language="JavaScript",
        title="The Lost Promise of Scriptoria", art="img/adventure/pyramid-of-doom.webp", master="JavaScript Master",
        blurb="Riddles full of promises, in a game written in JavaScript.",
    )
else:
    ADVENTURE_COMING.append(SimpleNamespace(key="javascript", language="JS"))
# The same for the ASP.NET game and site/razoria.
_razoria = CompiledGame("ASP.NET", "razoria", "RAZORIA_PROGRAM")
if _razoria.program.exists():
    ADVENTURE_GAMES["aspnet"] = SimpleNamespace(
        key="aspnet", engine=_razoria, database=Path(app.root_path) / "adventure-aspnet.db",
        session_quest="quest_aspnet", page_key="adventure_aspnet", language="ASP.NET",
        title="The Lost Session of Razoria", art="img/adventure/yellow-screen-of-death.webp", master="ASP.NET Master",
        blurb="Riddles that must survive a real request, in a game written in ASP.NET.",
    )
else:
    ADVENTURE_COMING.append(SimpleNamespace(key="aspnet", language="ASP.NET"))
# The AI game is the saucer's hub, and comes last in the list under it (key 0, since it's the tenth).
ADVENTURE_GAMES["ai"] = SimpleNamespace(
    key="ai", engine=neuralia, database=Path(app.root_path) / "adventure-ai.db",
    session_quest="quest_ai", page_key="adventure_ai", language="AI",
    title="The Lost Weights of Neuralia", art="img/adventure/ai.webp", master="AI Master",
    blurb="The longest road of all: every great term of AI, in a game written in Python.",
)
# For the addresses: /adventure/<game key>/...
GAME_KEYS = ", ".join(f"'{key}'" for key in ADVENTURE_GAMES)
ADVENTURE_DB_VERSION = 5
RECENT_QUESTS = 5
STALE_QUEST_DAYS = 7


def adventure_db(game):
    db = sqlite3.connect(game.database, timeout=10, isolation_level=None)  # transactions are explicit
    db.row_factory = sqlite3.Row
    return db


def setup_adventure_db(game):
    """Create a game's database when the site starts, or bring an older one up to date."""
    with closing(adventure_db(game)) as db, transaction(db):
        version = db.execute("PRAGMA user_version").fetchone()[0]
        db.execute("""
            CREATE TABLE IF NOT EXISTS quests (
                id TEXT PRIMARY KEY,       -- random; the explorer's session cookie holds it
                explorer TEXT NOT NULL,    -- name: letters, numbers and spaces only (pythonia.clean_name)
                difficulty TEXT NOT NULL,  -- easy, medium or hard
                seed INTEGER NOT NULL,     -- with the moves, replays the quest exactly
                moves TEXT NOT NULL,       -- JSON list of the explorer's choices and answers
                version INTEGER NOT NULL,  -- the engine's GAME_VERSION when it started
                status TEXT NOT NULL,      -- 'playing', 'win' or 'lose'
                score INTEGER NOT NULL,
                new_high INTEGER NOT NULL DEFAULT 0,  -- 1 if it set a new high score for its level
                started_at TEXT NOT NULL,  -- UTC, ISO 8601
                finished_at TEXT           -- UTC, ISO 8601
            )""")
        db.execute("CREATE INDEX IF NOT EXISTS quests_by_level ON quests (difficulty, status, score)")
        if version < 2:
            # Version 2 (2026-11-01): winners can carry their score up to the next level.
            db.execute("ALTER TABLE quests ADD COLUMN carried INTEGER NOT NULL DEFAULT 0")  # score it started with
            db.execute("ALTER TABLE quests ADD COLUMN continues TEXT")  # the won quest it carries on from
            db.execute("ALTER TABLE quests ADD COLUMN began_on TEXT")   # the level the explorer's run began on
            db.execute("UPDATE quests SET began_on = difficulty")
        if version < 3:
            # Version 3 (2026-11-01): winners can go back for the path they didn't take.
            db.execute("ALTER TABLE quests ADD COLUMN only_path TEXT")  # 'forest' or 'cave' for such a quest
        if version < 4:
            # Version 4 (2026-11-01): ...and aren't asked the first path's questions again.
            db.execute("ALTER TABLE quests ADD COLUMN skip_questions TEXT")  # JSON list of question numbers
        if version < 5:
            # Version 5 (2026-11-01): the final boss. (Named for Python, the first of them; the
            # C# game's database has the same columns for its own boss.)
            db.execute("ALTER TABLE quests ADD COLUMN final INTEGER NOT NULL DEFAULT 0")  # 1: completes every path on every level
            db.execute("ALTER TABLE quests ADD COLUMN python TEXT")     # 'won' or 'lost' once its winner faced the boss
            db.execute("ALTER TABLE quests ADD COLUMN python_at TEXT")  # when (UTC, ISO 8601)
            # A run already on its last path when Python arrived gets its chance too.
            for row in db.execute("SELECT * FROM quests WHERE difficulty = 'hard' AND only_path IS NOT NULL").fetchall():
                if every_path_done(game, journey(game, db, row)):
                    db.execute("UPDATE quests SET final = 1 WHERE id = ?", (row["id"],))
        # A won quest can be carried on only once.
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS quests_carried_on ON quests (continues) WHERE continues IS NOT NULL")
        db.execute(f"PRAGMA user_version = {ADVENTURE_DB_VERSION}")


def every_path_done(game, stages):
    """Whether a run's stages take in every path on every level: the way to the final boss."""
    return len(set(stages)) == len(game.engine.DIFFICULTY_SETTINGS) * len(game.engine.PATHS)


def journey(game, db, row):
    """An explorer's run, from where it began up to this quest, as (level, path) pairs:
    [("easy", "cave"), ("easy", "forest"), ("medium", "forest")]. Each quest is followed
    back to the win it carried on from."""
    chain = db.execute(
        "WITH RECURSIVE run (id, continues, difficulty, moves, only_path, depth) AS ("
        "  SELECT id, continues, difficulty, moves, only_path, 0 FROM quests WHERE id = ?"
        "  UNION ALL"
        "  SELECT q.id, q.continues, q.difficulty, q.moves, q.only_path, run.depth + 1"
        "  FROM quests q JOIN run ON q.id = run.continues WHERE run.depth < 20"
        ") SELECT difficulty, moves, only_path FROM run ORDER BY depth DESC",
        (row["id"],),
    ).fetchall()
    return [(r["difficulty"], game.engine.path_taken(json.loads(r["moves"]), r["only_path"])) for r in chain]


def journey_label(stages):
    """A run for the page: "Easy (Cave, Forest) → Medium (Forest)"."""
    groups = []
    for level, path in stages:
        if not groups or groups[-1][0] != level:
            groups.append((level, []))
        if path:
            groups[-1][1].append(path.title())
    return " → ".join(level.title() + (f" ({', '.join(paths)})" if paths else "") for level, paths in groups)


def replay_quest(game, row, moves=None):
    """The saved quest (a row of its game's database), played through to where it stands, or
    with `moves` instead of its saved ones."""
    return game.engine.replay(row["explorer"], row["difficulty"], row["seed"],
                              json.loads(row["moves"]) if moves is None else moves, row["carried"], row["only_path"],
                              json.loads(row["skip_questions"] or "[]"), row["version"], bool(row["final"]))


def paths_done(stages):
    """The paths a run has taken on the level it's on now (its last stages)."""
    return [path for level, path in stages if level == stages[-1][0]] if stages else []


for _game in ADVENTURE_GAMES.values():  # (here, after journey(), which the version 5 upgrade uses)
    setup_adventure_db(_game)


def hall_of_explorers(game, db):
    """The console game's score log, shared by every explorer: each level's quests played,
    wins, latest and high score (and who holds it), plus the latest finished quests.
    A high score belongs to the latest explorer to reach it, so matching it takes it over."""
    levels = {}
    for level in game.engine.DIFFICULTY_SETTINGS:
        done = "difficulty = ? AND status != 'playing'"
        played, wins = db.execute(f"SELECT COUNT(*), COALESCE(SUM(status = 'win'), 0) FROM quests WHERE {done}", (level,)).fetchone()
        latest = db.execute(f"SELECT score FROM quests WHERE {done} ORDER BY finished_at DESC, rowid DESC LIMIT 1", (level,)).fetchone()
        best = db.execute(f"SELECT id, explorer, score FROM quests WHERE {done} ORDER BY score DESC, finished_at DESC, rowid DESC LIMIT 1", (level,)).fetchone()
        holder = best if best and best["score"] else None  # a high score of 0 belongs to nobody
        levels[level] = {
            "played": played, "wins": wins, "latest": latest["score"] if latest else 0,
            "high": best["score"] if best else 0, "best": holder["explorer"] if holder else "",
            "best_id": holder["id"] if holder else None,
        }
    # Masters (Python Master, C# Master, VB.NET Master, ANSI SQL Master...): like a level, but counting the battles with the final
    # boss. Its high score belongs to the latest explorer to defeat the boss with it.
    faced = "python IS NOT NULL"
    played, wins = db.execute(f"SELECT COUNT(*), COALESCE(SUM(python = 'won'), 0) FROM quests WHERE {faced}").fetchone()
    latest = db.execute(f"SELECT score FROM quests WHERE {faced} ORDER BY python_at DESC, rowid DESC LIMIT 1").fetchone()
    best = adventure_champion(db)
    master = {
        "played": played, "wins": wins, "latest": latest["score"] if latest else 0,
        "high": best["score"] if best else 0, "best": best["explorer"] if best else "",
        "best_id": best["id"] if best else None,
    }
    recent = [
        {**dict(row), "finished": datetime.fromisoformat(row["finished_at"]), "journey": journey_label(journey(game, db, row))}
        for row in db.execute(
            "SELECT id, explorer, difficulty, score, status, python, finished_at FROM quests WHERE status != 'playing' "
            "ORDER BY finished_at DESC, rowid DESC LIMIT ?", (RECENT_QUESTS,))
    ]
    return levels, recent, master


def adventure_champion(db):
    """The quest holding a game's master title: the top score, the latest to reach it."""
    return db.execute("SELECT id, explorer, score FROM quests WHERE python = 'won' "
                      "ORDER BY score DESC, python_at DESC, rowid DESC LIMIT 1").fetchone()


# The "Adventure" link: choose your language. It only reads the games' databases, so the choice
# still opens if one game can't run.
@app.route("/adventure/")
def adventure():
    g.page_key = "adventure_choose"
    choices = []
    for game in ADVENTURE_GAMES.values():
        with closing(adventure_db(game)) as db:
            in_play = db.execute("SELECT 1 FROM quests WHERE id = ? AND status = 'playing'",
                                 (session.get(game.session_quest),)).fetchone()
            choices.append({"game": game, "champion": adventure_champion(db), "in_play": bool(in_play)})
    return render_template("adventure-choose.html", choices=choices, coming=ADVENTURE_COMING)


@app.route(f"/adventure/<any({GAME_KEYS}):game_key>/")
def adventure_game(game_key):
    game = ADVENTURE_GAMES[game_key]
    engine = game.engine
    g.page_key = game.page_key
    row = quest = carried_on = None
    stages = []
    with closing(adventure_db(game)) as db:
        if session.get(game.session_quest):
            row = db.execute("SELECT * FROM quests WHERE id = ?", (session[game.session_quest],)).fetchone()
        if row and engine.can_replay(row["version"]):
            quest = replay_quest(game, row)
            stages = journey(game, db, row)
            carried_on = db.execute("SELECT 1 FROM quests WHERE continues = ?", (row["id"],)).fetchone()
        levels, recent, master = hall_of_explorers(game, db)
    finished_win = quest is not None and quest.result == "win"
    # A win offers more (the dragon, other paths, the next level) until it's been carried on.
    won = finished_win and not carried_on
    every_level = {level for level, _ in stages} == set(engine.DIFFICULTY_SETTINGS)
    every_path = every_path_done(game, stages)
    return render_template(
        "adventure.html", game_key=game.key, texts=engine.TEXTS, boss_picture=game.art,
        row=row if quest else None, quest=quest, step=len(json.loads(row["moves"])) if quest else 0,
        journey=journey_label(stages),
        # A winner can carry their score on: up to the next level (after Easy or Medium) and
        # down any path not taken yet on this level.
        next_level=engine.next_level(row["difficulty"]) if won else None,
        untaken=engine.paths_left(paths_done(stages)) if won else [],
        # ...and first, if they like, wake the dragon of this path and level for a bonus.
        dragon=quest.dragon_awaits() if won else None,
        dragon_points=engine.DRAGON_POINTS * engine.DIFFICULTY_SETTINGS[row["difficulty"]]["multiplier"] if quest else 0,
        # After the win that completes every path on every level: the final boss.
        boss=quest.boss_awaits() if won else False,
        boss_move=engine.BOSS_MOVE,
        boss_points=engine.BOSS_POINTS * engine.DIFFICULTY_SETTINGS["hard"]["multiplier"],
        conquered=("every path" if every_path else "every level" if every_level else None) if finished_win else None,
        paths=engine.PATHS, path_names=engine.PATH_NAMES,
        levels=levels, recent=recent, master=master, settings=engine.DIFFICULTY_SETTINGS, scenes=engine.SCENES,
        explorer=session.get("explorer", ""), name_max=engine.NAME_MAX_LENGTH,
    )


def new_quest(game, db, explorer, difficulty, carried=0, continues=None, began_on=None, only_path=None,
              skip_questions=None, final=False):
    """Save a quest about to begin, and clear away quests abandoned long ago. Returns its id."""
    quest_id = secrets.token_urlsafe(16)
    stale = (datetime.now(timezone.utc) - timedelta(days=STALE_QUEST_DAYS)).isoformat(timespec="seconds")
    db.execute("DELETE FROM quests WHERE status = 'playing' AND started_at < ?", (stale,))
    db.execute(
        "INSERT INTO quests (id, explorer, difficulty, seed, moves, version, status, score, carried, continues, "
        "began_on, only_path, skip_questions, final, started_at) VALUES (?, ?, ?, ?, '[]', ?, 'playing', ?, ?, ?, ?, ?, ?, ?, ?)",
        (quest_id, explorer, difficulty, secrets.randbits(32), game.engine.GAME_VERSION, carried, carried, continues,
         began_on or difficulty, only_path, json.dumps(skip_questions) if skip_questions else None, int(final), utc_now()),
    )
    return quest_id


def adventure_page(game):
    """The address of a game's page, where every move comes back to."""
    return redirect(url_for("adventure_game", game_key=game.key))


# Starting a quest: the name must pass clean_name (letters, numbers and spaces only), checked
# here on the server whatever the page's own checks did.
@app.post(f"/adventure/<any({GAME_KEYS}):game_key>/start")
def adventure_start(game_key):
    check_csrf()
    game = ADVENTURE_GAMES[game_key]
    name = game.engine.clean_name(request.form.get("explorer", ""))
    difficulty = request.form.get("difficulty", "")
    if name is None:
        flash(f"Names can only use letters, numbers and spaces (up to {game.engine.NAME_MAX_LENGTH}), "
              "starting with a letter.", "error")
        return adventure_page(game)
    if difficulty not in game.engine.DIFFICULTY_SETTINGS:
        flash("Choose a difficulty to begin your quest.", "error")
        return adventure_page(game)
    with closing(adventure_db(game)) as db, transaction(db):
        quest_id = new_quest(game, db, name, difficulty)
    session[game.session_quest], session["explorer"] = quest_id, name
    return adventure_page(game)


# Carrying on after a win: a new quest for the same explorer that starts with the won
# quest's score, either on the next level (after Easy or Medium) or, with to=other-path and
# path=forest, cave or castle, down a path not taken yet on the same level, without the
# questions the level's earlier paths asked. (Pages from before the castle send no path:
# they meant the first path left, the one their button named.) Only the quest this
# browser just won can be carried on, and only once, so a score can't be carried on twice.
@app.post(f"/adventure/<any({GAME_KEYS}):game_key>/advance")
def adventure_advance(game_key):
    check_csrf()
    game = ADVENTURE_GAMES[game_key]
    engine = game.engine
    with closing(adventure_db(game)) as db, transaction(db):
        row = db.execute("SELECT * FROM quests WHERE id = ? AND status = 'win'", (session.get(game.session_quest),)).fetchone()
        if (not row or not engine.can_replay(row["version"])
                or db.execute("SELECT 1 FROM quests WHERE continues = ?", (row["id"],)).fetchone()
                or replay_quest(game, row).prompt):  # a dragon's riddle still to answer
            return adventure_page(game)
        skip = None
        if request.form.get("to") == "other-path":
            level = row["difficulty"]
            left = engine.paths_left(paths_done(journey(game, db, row)))
            path = request.form.get("path") or (left[0] if left else None)
            if path not in left:  # every path done on this level, or not a path
                return adventure_page(game)
            skip = json.loads(row["skip_questions"] or "[]") + replay_quest(game, row).asked
        else:
            level, path = engine.next_level(row["difficulty"]), None
            if not level:
                return adventure_page(game)
        # The quest that would complete every path on every level leads, if won, to the boss.
        final = bool(path) and every_path_done(game, journey(game, db, row) + [(level, path)])
        quest_id = new_quest(game, db, row["explorer"], level, carried=row["score"], continues=row["id"],
                             began_on=row["began_on"] or row["difficulty"], only_path=path, skip_questions=skip,
                             final=final)
    session[game.session_quest] = quest_id
    return adventure_page(game)


# A choice or an answer. Only a move the quest is waiting for is taken, and only from the
# latest page (step = moves made so far), so going back or clicking twice changes nothing.
# After a win, the only moves are the bonus dragon's (waking it, then the answer), and only
# until the quest has been carried on, since the next quest started with its score; and,
# after the win that completes every path on every level, the final boss's (facing it, then
# the answer: a master's title, or the whole score lost).
@app.post(f"/adventure/<any({GAME_KEYS}):game_key>/move")
def adventure_move(game_key):
    check_csrf()
    game = ADVENTURE_GAMES[game_key]
    engine = game.engine
    move = request.form.get("move", "")
    with closing(adventure_db(game)) as db, transaction(db):
        row = db.execute("SELECT * FROM quests WHERE id = ? AND status IN ('playing', 'win')",
                         (session.get(game.session_quest),)).fetchone()
        if row and row["status"] == "win" and db.execute("SELECT 1 FROM quests WHERE continues = ?", (row["id"],)).fetchone():
            row = None
        if row and engine.can_replay(row["version"]):
            moves = json.loads(row["moves"])
            quest = replay_quest(game, row)
            wanted = ((quest.prompt and quest.prompt.accepts(move))
                      or (move == engine.DRAGON_MOVE and quest.dragon_awaits())
                      or (move == engine.BOSS_MOVE and quest.boss_awaits()))
            if request.form.get("step") == str(len(moves)) and wanted:
                moves.append(move)
                quest = replay_quest(game, row, moves)
                score = quest.player["score"]
                if row["status"] == "win":
                    # A dragon's treasure or the boss's verdict changes a finished quest's score:
                    # perhaps to a new high score, or, when the boss wins, to zero.
                    high = db.execute(
                        "SELECT COALESCE(MAX(score), 0) FROM quests WHERE difficulty = ? AND status != 'playing' AND id != ?",
                        (row["difficulty"], row["id"]),
                    ).fetchone()[0]
                    new_high = 0 if quest.boss == "lost" else max(row["new_high"], int(score > high))
                    db.execute("UPDATE quests SET moves = ?, score = ?, new_high = ? WHERE id = ?",
                               (json.dumps(moves), score, new_high, row["id"]))
                    if quest.boss and not row["python"]:
                        db.execute("UPDATE quests SET python = ?, python_at = ? WHERE id = ?",
                                   (quest.boss, utc_now(), row["id"]))
                elif quest.result:
                    high = db.execute(
                        "SELECT COALESCE(MAX(score), 0) FROM quests WHERE difficulty = ? AND status != 'playing'",
                        (row["difficulty"],),
                    ).fetchone()[0]
                    db.execute(
                        "UPDATE quests SET moves = ?, status = ?, score = ?, new_high = ?, finished_at = ? WHERE id = ?",
                        (json.dumps(moves), quest.result, score, int(score > high), utc_now(), row["id"]),
                    )
                else:
                    db.execute("UPDATE quests SET moves = ?, score = ? WHERE id = ?", (json.dumps(moves), score, row["id"]))
    return adventure_page(game)


# Play again, or leave a quest: back to the start, with the name kept for next time.
@app.post(f"/adventure/<any({GAME_KEYS}):game_key>/new")
def adventure_new(game_key):
    check_csrf()
    game = ADVENTURE_GAMES[game_key]
    session.pop(game.session_quest, None)
    return adventure_page(game)


# The Python game's forms used to post to these addresses, and pages opened back then still do.
for _view in (adventure_start, adventure_advance, adventure_move, adventure_new):
    _action = _view.__name__.removeprefix("adventure_")
    app.add_url_rule(f"/adventure/{_action}", f"{_view.__name__}_old", _view, methods=["POST"], defaults={"game_key": "python"})


# If a game's program can't run, say so and go back to the choice, where the other games still work.
@app.errorhandler(Unavailable)
def game_unavailable(error):
    app.logger.error("%s", error)
    flash(f"The {error.language} game isn't available just now. Please try again soon.", "error")
    return redirect(url_for("adventure"))


@app.errorhandler(404)
def not_found(error):
    g.page_key = "not_found"  # count every missing page on the "page not found" counter
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
