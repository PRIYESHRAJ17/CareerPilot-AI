from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "careerpilot_workspace.sqlite3"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize() -> None:
    with db() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                account_id TEXT PRIMARY KEY,
                candidate_id TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS records (
                candidate_id TEXT NOT NULL,
                entity TEXT NOT NULL,
                record_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (candidate_id, entity, record_id)
            );

            CREATE INDEX IF NOT EXISTS idx_records_candidate_entity
                ON records(candidate_id, entity, updated_at DESC);

            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                candidate_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                summary TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_events_candidate_created
                ON events(candidate_id, created_at DESC);
            """
        )


def _hash_password(password: str, salt: bytes | None = None) -> str:
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
    )
    return f"scrypt${salt.hex()}${digest.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        _, salt_hex, digest_hex = encoded.split("$", 2)
        actual = _hash_password(password, bytes.fromhex(salt_hex)).split("$", 2)[2]
        return secrets.compare_digest(actual, digest_hex)
    except (ValueError, TypeError):
        return False


def create_account(email: str, password: str) -> dict[str, str]:
    initialize()
    normalized = email.strip().lower()
    if not normalized or "@" not in normalized:
        raise ValueError("Enter a valid email address.")
    candidate_id = str(uuid.uuid4())
    account_id = str(uuid.uuid4())
    timestamp = now_iso()
    with db() as connection:
        try:
            connection.execute(
                "INSERT INTO accounts(account_id, candidate_id, email, password_hash, created_at, updated_at) VALUES(?,?,?,?,?,?)",
                (account_id, candidate_id, normalized, _hash_password(password), timestamp, timestamp),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("An account with that email already exists.") from exc
    return {"account_id": account_id, "candidate_id": candidate_id, "email": normalized}


def authenticate(email: str, password: str) -> dict[str, str] | None:
    initialize()
    normalized = email.strip().lower()
    with db() as connection:
        row = connection.execute(
            "SELECT account_id, candidate_id, email, password_hash FROM accounts WHERE email = ?",
            (normalized,),
        ).fetchone()
    if not row or not _verify_password(password, row["password_hash"]):
        return None
    return {
        "account_id": row["account_id"],
        "candidate_id": row["candidate_id"],
        "email": row["email"],
    }


def account_for_candidate(candidate_id: str) -> dict[str, str] | None:
    initialize()
    with db() as connection:
        row = connection.execute(
            "SELECT account_id, candidate_id, email FROM accounts WHERE candidate_id = ?",
            (candidate_id,),
        ).fetchone()
    return dict(row) if row else None


def upsert_record(candidate_id: str, entity: str, payload: dict[str, Any], record_id: str | None = None) -> dict[str, Any]:
    initialize()
    identifier = str(record_id or payload.get("id") or uuid.uuid4())
    timestamp = now_iso()
    payload = dict(payload)
    payload["id"] = identifier
    with db() as connection:
        existing = connection.execute(
            "SELECT created_at FROM records WHERE candidate_id=? AND entity=? AND record_id=?",
            (candidate_id, entity, identifier),
        ).fetchone()
        created_at = existing["created_at"] if existing else timestamp
        connection.execute(
            """
            INSERT INTO records(candidate_id, entity, record_id, payload, created_at, updated_at)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(candidate_id, entity, record_id) DO UPDATE SET
                payload=excluded.payload,
                updated_at=excluded.updated_at
            """,
            (candidate_id, entity, identifier, json.dumps(payload, ensure_ascii=False), created_at, timestamp),
        )
    return payload | {"created_at": created_at, "updated_at": timestamp}


def get_record(candidate_id: str, entity: str, record_id: str) -> dict[str, Any] | None:
    initialize()
    with db() as connection:
        row = connection.execute(
            "SELECT payload, created_at, updated_at FROM records WHERE candidate_id=? AND entity=? AND record_id=?",
            (candidate_id, entity, record_id),
        ).fetchone()
    if not row:
        return None
    payload = json.loads(row["payload"])
    payload.update(created_at=row["created_at"], updated_at=row["updated_at"])
    return payload


def list_records(candidate_id: str, entity: str, limit: int = 200) -> list[dict[str, Any]]:
    initialize()
    limit = min(max(limit, 1), 500)
    with db() as connection:
        rows = connection.execute(
            "SELECT payload, created_at, updated_at FROM records WHERE candidate_id=? AND entity=? ORDER BY updated_at DESC LIMIT ?",
            (candidate_id, entity, limit),
        ).fetchall()
    result: list[dict[str, Any]] = []
    for row in rows:
        payload = json.loads(row["payload"])
        payload.update(created_at=row["created_at"], updated_at=row["updated_at"])
        result.append(payload)
    return result


def delete_record(candidate_id: str, entity: str, record_id: str) -> bool:
    initialize()
    with db() as connection:
        cursor = connection.execute(
            "DELETE FROM records WHERE candidate_id=? AND entity=? AND record_id=?",
            (candidate_id, entity, record_id),
        )
    return cursor.rowcount > 0


def append_event(candidate_id: str, event_type: str, summary: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    initialize()
    event = {
        "id": str(uuid.uuid4()),
        "event_type": event_type,
        "summary": summary,
        "payload": payload or {},
        "created_at": now_iso(),
    }
    with db() as connection:
        connection.execute(
            "INSERT INTO events(event_id, candidate_id, event_type, summary, payload, created_at) VALUES(?,?,?,?,?,?)",
            (event["id"], candidate_id, event_type, summary, json.dumps(payload or {}, ensure_ascii=False), event["created_at"]),
        )
    return event


def list_events(candidate_id: str, limit: int = 50) -> list[dict[str, Any]]:
    initialize()
    limit = min(max(limit, 1), 200)
    with db() as connection:
        rows = connection.execute(
            "SELECT event_id, event_type, summary, payload, created_at FROM events WHERE candidate_id=? ORDER BY created_at DESC LIMIT ?",
            (candidate_id, limit),
        ).fetchall()
    return [
        {
            "id": row["event_id"],
            "event_type": row["event_type"],
            "summary": row["summary"],
            "payload": json.loads(row["payload"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


initialize()
