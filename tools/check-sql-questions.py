"""Checks the SQL games' answers by running every question's code on a real database.

    python check-sql-questions.py ansi-sql        PostgreSQL and DuckDB (both must agree)
    python check-sql-questions.py t-sql           SQL Server (2022)
    python check-sql-questions.py pl-sql          Oracle (19c or later)

Each question's hidden "setup" runs first (it makes the tables the snippet's comment shows), then
its "code". What comes out is written the way the game's answers are (see "What an answer means",
below) and must be exactly the question's answer; a question whose "expect_error" is set must fail
instead. Questions without code (the plain questions) are listed, not run. It ends with a count, and
exits with 1 if anything didn't match.

Where the databases are (environment variables):
- ansi-sql: PG_DSN, a libpq connection string ("dbname=postgres user=postgres" if not set; the check
  makes and drops a database of its own), with `pip install "psycopg[binary]" duckdb`.
- t-sql: MSSQL_ODBC, an ODBC connection string, for example
  "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;Trusted_Connection=yes;TrustServerCertificate=yes"
  with `pip install pyodbc`. Each question gets a database of its own (AdventureCheck), made and dropped.
- pl-sql: ORACLE_USER, ORACLE_PASSWORD and ORACLE_DSN ("localhost/FREEPDB1"), with `pip install oracledb`.
  Each question's objects are dropped after it (anything the check's user didn't have before).

What an answer means: a query's rows, a row's values joined by spaces and the rows by ", " (NULL for a
null, "No rows" for none); printed lines (T-SQL's PRINT, PL/SQL's DBMS_OUTPUT.PUT_LINE) joined by
spaces, in the order they came out, with the rows of any SELECT in between.
"""
import datetime
import decimal
import importlib.util
import os
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
GAMES = {"ansi-sql": "sequelia", "t-sql": "transactia", "pl-sql": "oraclia"}


def load_game(key):
    path = SITE / f"{GAMES[key]}.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    game = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(game)
    return game


def every_question(game):
    for level, questions in game.QUESTIONS.items():
        for number, question in enumerate(questions):
            yield f"{level} #{number + 1}", question
    for (level, path), dragon in game.DRAGONS.items():
        yield f"dragon {level}/{path}", dragon["question"]
    for number, question in enumerate(game.BOSS_QUESTIONS):
        yield f"boss #{number + 1}", question


def show(value):
    """One value, as the answers write it."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, decimal.Decimal):
        return format(value.normalize(), "f") if value == value.to_integral_value() else str(value)
    if isinstance(value, datetime.datetime) and value.time() == datetime.time():
        return value.date().isoformat()
    return str(value)


def show_rows(rows):
    if not rows:
        return "No rows"
    return ", ".join(" ".join(show(value) for value in row) for row in rows)


def split_statements(sql):
    """Plain SQL statements, split at the semicolons that end them (not those inside quotes)."""
    statements, current, quoted = [], "", False
    for ch in sql:
        if ch == "'":
            quoted = not quoted
        if ch == ";" and not quoted:
            if current.strip():
                statements.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip():
        statements.append(current.strip())
    return statements


def without_comments(sql):
    return "\n".join(line for line in sql.split("\n") if not line.strip().startswith("--"))


# --- ANSI SQL: PostgreSQL and DuckDB -------------------------------------------------------------

def ansi_runners():
    import duckdb
    import psycopg

    dsn = os.environ.get("PG_DSN", "dbname=postgres user=postgres")
    admin = psycopg.connect(dsn, autocommit=True)
    admin.execute("DROP DATABASE IF EXISTS adventure_check")
    admin.execute("CREATE DATABASE adventure_check")
    check_dsn = re.sub(r"dbname=\S+", "dbname=adventure_check", dsn) if "dbname=" in dsn else dsn + " dbname=adventure_check"

    def run_pg(setup, code):
        with psycopg.connect(check_dsn, autocommit=True) as db:
            db.execute("DROP SCHEMA IF EXISTS quest CASCADE")
            db.execute("CREATE SCHEMA quest")
            db.execute("SET search_path TO quest")
            for statement in split_statements(setup or ""):
                db.execute(statement)
            rows = None
            for statement in split_statements(without_comments(code)):
                cursor = db.execute(statement)
                rows = cursor.fetchall() if cursor.description else rows
            return show_rows(rows or [])

    def run_duck(setup, code):
        db = duckdb.connect()
        for statement in split_statements(setup or ""):
            db.execute(statement)
        rows = None
        for statement in split_statements(without_comments(code)):
            cursor = db.execute(statement)
            rows = cursor.fetchall() if cursor.description else rows
        db.close()
        return show_rows(rows or [])

    def finish():
        admin.execute("DROP DATABASE IF EXISTS adventure_check")
        admin.close()

    return {"PostgreSQL": run_pg, "DuckDB": run_duck}, finish


# --- T-SQL: SQL Server ---------------------------------------------------------------------------

def tsql_runners():
    import pyodbc

    connection = os.environ["MSSQL_ODBC"]
    prefix = re.compile(r"^(\[[^\]]*\])+")

    def run(setup, code):
        admin = pyodbc.connect(connection, autocommit=True)
        admin.execute("IF DB_ID('AdventureCheck') IS NOT NULL BEGIN ALTER DATABASE AdventureCheck SET SINGLE_USER "
                      "WITH ROLLBACK IMMEDIATE; DROP DATABASE AdventureCheck; END")
        admin.execute("CREATE DATABASE AdventureCheck")
        try:
            db = pyodbc.connect(connection + ";DATABASE=AdventureCheck", autocommit=True)
            out = []
            batches = [(setup or "", False), (code, True)]
            for script, shown in batches:
                for batch in re.split(r"^\s*GO\s*$", script, flags=re.M | re.I):
                    if not batch.strip():
                        continue
                    cursor = db.cursor()
                    cursor.execute(batch)
                    while True:
                        for _, message in cursor.messages or []:
                            if shown:
                                out.append(prefix.sub("", message))
                        if cursor.description and shown:
                            out.append(show_rows([tuple(row) for row in cursor.fetchall()]))
                        if not cursor.nextset():
                            break
            db.close()
            return " ".join(out)
        finally:
            admin.execute("IF DB_ID('AdventureCheck') IS NOT NULL BEGIN ALTER DATABASE AdventureCheck SET "
                          "SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE AdventureCheck; END")
            admin.close()

    return {"SQL Server": run}, lambda: None


# --- PL/SQL: Oracle ------------------------------------------------------------------------------

def plsql_runners():
    import oracledb

    def connect():
        return oracledb.connect(user=os.environ["ORACLE_USER"], password=os.environ["ORACLE_PASSWORD"],
                                dsn=os.environ["ORACLE_DSN"])

    def units(script):
        """SQL*Plus-style: a PL/SQL unit (CREATE ... PROCEDURE/FUNCTION/PACKAGE/TRIGGER/TYPE BODY, or a
        block) runs to a line holding only "/"; anything else is plain statements ending in ";"."""
        found = []
        for chunk in re.split(r"^\s*/\s*$", script, flags=re.M):
            chunk = chunk.strip()
            if not chunk:
                continue
            plsql = re.match(r"(?is)(--[^\n]*\n\s*)*(DECLARE|BEGIN|<<|CREATE\s+(OR\s+REPLACE\s+)?"
                             r"(EDITIONABLE\s+)?(PROCEDURE|FUNCTION|PACKAGE|TRIGGER|TYPE))", chunk)
            if plsql:
                found.append(chunk)
            else:
                found.extend(split_statements(chunk))
        return found

    def run(setup, code):
        db = connect()
        cursor = db.cursor()
        before = {tuple(row) for row in cursor.execute("SELECT object_type, object_name FROM user_objects")}
        try:
            for unit in units(setup or ""):
                cursor.execute(unit)
            cursor.callproc("dbms_output.enable", [None])
            out = []
            line, status = cursor.var(str), cursor.var(int)
            for unit in units(code):
                cursor.execute(unit)
                if cursor.description:
                    out.append(show_rows(cursor.fetchall()))
                while True:
                    cursor.callproc("dbms_output.get_line", (line, status))
                    if status.getvalue() != 0:
                        break
                    out.append(line.getvalue() or "")
            return " ".join(out)
        finally:
            db.rollback()
            after = {tuple(row) for row in cursor.execute("SELECT object_type, object_name FROM user_objects")}
            for kind, name in sorted(after - before, key=lambda o: o[0] == "TABLE"):
                if kind in ("TABLE", "VIEW", "SEQUENCE", "PROCEDURE", "FUNCTION", "PACKAGE", "TYPE", "TRIGGER",
                            "SYNONYM"):
                    try:
                        cursor.execute(f'DROP {kind} "{name}"' + (" CASCADE CONSTRAINTS PURGE" if kind == "TABLE" else
                                                                  " FORCE" if kind == "TYPE" else ""))
                    except oracledb.DatabaseError:
                        pass
            db.close()

    return {"Oracle": run}, lambda: None


RUNNERS = {"ansi-sql": ansi_runners, "t-sql": tsql_runners, "pl-sql": plsql_runners}


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else ""
    if key not in GAMES:
        raise SystemExit(__doc__)
    game = load_game(key)
    runners, finish = RUNNERS[key]()
    passed = failed = plain = 0
    try:
        for where, question in every_question(game):
            if not question.get("code"):
                plain += 1
                print(f"  (not run) {where}: {question['prompt']}")
                continue
            for engine, run in runners.items():
                try:
                    got, error = run(question.get("setup"), question["code"]), None
                except Exception as problem:  # the database's own error
                    got, error = None, " ".join(str(problem).split())
                if question.get("expect_error"):
                    # An answer naming an Oracle error (ORA-06502, PLS-00363) must get that one.
                    named = re.search(r"\b(ORA|PLS)-\d{5}\b", question["answer"])
                    ok = error is not None and (not named or named.group(0) in error)
                    detail = f"expected {named.group(0) if named else 'an error'}, got {error or got!r}"
                else:
                    ok = error is None and got == question["answer"]
                    detail = f"error: {error}" if error else f"got {got!r}, expected {question['answer']!r}"
                if ok:
                    passed += 1
                else:
                    failed += 1
                    print(f"FAIL {where} on {engine}: {detail}")
    finally:
        finish()
    print(f"{key}: {passed} passed, {failed} failed ({len(runners)} database(s)); {plain} plain questions not run")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
