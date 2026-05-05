"""Lightweight SQLite store for reports (SQLAlchemy-free for MVP)."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

DB_PATH = Path(__file__).resolve().parent.parent.parent / "plagguard.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = _get_conn()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                input_text TEXT NOT NULL,
                result_json TEXT NOT NULL,
                report_type TEXT NOT NULL DEFAULT 'detect',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


def save_report(report_id: str, input_text: str, result: dict[str, Any], report_type: str = "detect") -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT INTO reports (id, input_text, result_json, report_type) VALUES (?, ?, ?, ?)",
            (report_id, input_text, json.dumps(result, default=str), report_type),
        )


def get_report(report_id: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "input_text": row["input_text"],
            "result": json.loads(row["result_json"]),
            "report_type": row["report_type"],
            "created_at": row["created_at"],
        }


def list_reports(limit: int = 20) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, report_type, created_at FROM reports ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
