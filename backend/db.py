"""SQLite access layer. Stdlib sqlite3 only, no ORM.

One connection per request/script is fine at this scale, so callers
open a connection, do work, and close it (or use it as a context manager).
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).parent / "waymark.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES sources(id),
    claim TEXT NOT NULL,
    rationale TEXT NOT NULL DEFAULT '',
    referenced_entities TEXT NOT NULL DEFAULT '[]',
    confidence REAL NOT NULL DEFAULT 0.5,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contradictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_a_id INTEGER NOT NULL REFERENCES statements(id),
    statement_b_id INTEGER NOT NULL REFERENCES statements(id),
    explanation TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS staleness_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_id INTEGER NOT NULL REFERENCES statements(id),
    entity TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entity_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('active', 'retired'))
);

-- Plain (non content-linked) FTS5 index, kept in sync by insert_statement.
-- Statements are append only in this app, so no update/delete triggers.
CREATE VIRTUAL TABLE IF NOT EXISTS statements_fts USING fts5(
    claim, rationale, statement_id UNINDEXED
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def insert_source(conn: sqlite3.Connection, label: str, raw_text: str) -> int:
    cur = conn.execute(
        "INSERT INTO sources (label, raw_text, created_at) VALUES (?, ?, ?)",
        (label, raw_text, now()),
    )
    conn.commit()
    return cur.lastrowid


def insert_statement(
    conn: sqlite3.Connection,
    source_id: int,
    claim: str,
    rationale: str,
    referenced_entities: list[str],
    confidence: float,
) -> int:
    cur = conn.execute(
        """INSERT INTO statements
           (source_id, claim, rationale, referenced_entities, confidence, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (source_id, claim, rationale, json.dumps(referenced_entities), confidence, now()),
    )
    statement_id = cur.lastrowid
    conn.execute(
        "INSERT INTO statements_fts (rowid, claim, rationale, statement_id) VALUES (?, ?, ?, ?)",
        (statement_id, claim, rationale, statement_id),
    )
    conn.commit()
    return statement_id


def statements_referencing(conn: sqlite3.Connection, entity: str, exclude_id: int | None = None) -> list[sqlite3.Row]:
    """All statements whose referenced_entities json array contains entity."""
    rows = conn.execute(
        """SELECT s.* FROM statements s, json_each(s.referenced_entities) je
           WHERE je.value = ? AND s.id != ?""",
        (entity, exclude_id or -1),
    ).fetchall()
    return rows


def insert_contradiction(conn: sqlite3.Connection, statement_a_id: int, statement_b_id: int, explanation: str) -> int:
    cur = conn.execute(
        """INSERT INTO contradictions (statement_a_id, statement_b_id, explanation, created_at)
           VALUES (?, ?, ?, ?)""",
        (statement_a_id, statement_b_id, explanation, now()),
    )
    conn.commit()
    return cur.lastrowid


def insert_staleness_flag(conn: sqlite3.Connection, statement_id: int, entity: str, reason: str) -> int:
    cur = conn.execute(
        """INSERT INTO staleness_flags (statement_id, entity, reason, created_at)
           VALUES (?, ?, ?, ?)""",
        (statement_id, entity, reason, now()),
    )
    conn.commit()
    return cur.lastrowid


def all_statements(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM statements ORDER BY id DESC").fetchall()


def all_contradictions(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM contradictions ORDER BY id DESC").fetchall()


def staleness_for_statement(conn: sqlite3.Connection, statement_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM staleness_flags WHERE statement_id = ?", (statement_id,)
    ).fetchall()


def contradictions_for_statement(conn: sqlite3.Connection, statement_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM contradictions WHERE statement_a_id = ? OR statement_b_id = ?",
        (statement_id, statement_id),
    ).fetchall()


def search_statements(conn: sqlite3.Connection, query: str, limit: int = 8) -> list[sqlite3.Row]:
    rows = conn.execute(
        """SELECT s.* FROM statements s
           JOIN statements_fts f ON f.statement_id = s.id
           WHERE statements_fts MATCH ?
           ORDER BY rank LIMIT ?""",
        (query, limit),
    ).fetchall()
    return rows
