from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from cryptography.fernet import Fernet, InvalidToken

from backend.services.workspace_store import DB_PATH

KEY_PATH = DB_PATH.parent / ".integration_key"
KEY_PATH.parent.mkdir(parents=True, exist_ok=True)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


def _cipher() -> Fernet:
    configured = os.getenv("CAREERPILOT_TOKEN_ENCRYPTION_KEY", "").strip()
    if configured:
        try:
            return Fernet(configured.encode("ascii"))
        except Exception as exc:
            raise RuntimeError("CAREERPILOT_TOKEN_ENCRYPTION_KEY must be a valid Fernet key.") from exc

    if KEY_PATH.exists():
        value = KEY_PATH.read_text(encoding="utf-8").strip()
    else:
        value = Fernet.generate_key().decode("ascii")
        KEY_PATH.write_text(value + "\n", encoding="utf-8")
        try:
            os.chmod(KEY_PATH, 0o600)
        except OSError:
            pass
    return Fernet(value.encode("ascii"))


def encrypt(value: str | None) -> str | None:
    if not value:
        return None
    return _cipher().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return _cipher().decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError):
        return None


@contextmanager
def integration_db() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize() -> None:
    with integration_db() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS integration_connections (
                candidate_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                access_token TEXT,
                refresh_token TEXT,
                expires_at TEXT,
                scope TEXT,
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY(candidate_id, provider)
            );

            CREATE TABLE IF NOT EXISTS integration_oauth_states (
                state_hash TEXT PRIMARY KEY,
                candidate_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                code_verifier TEXT,
                metadata TEXT NOT NULL DEFAULT '{}',
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS integration_clipper_tokens (
                token_hash TEXT PRIMARY KEY,
                candidate_id TEXT NOT NULL,
                label TEXT NOT NULL,
                created_at TEXT NOT NULL,
                revoked_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_integration_connections_candidate
                ON integration_connections(candidate_id, provider);
            CREATE INDEX IF NOT EXISTS idx_oauth_states_expiry
                ON integration_oauth_states(expires_at);
            CREATE INDEX IF NOT EXISTS idx_clipper_candidate
                ON integration_clipper_tokens(candidate_id, revoked_at);
            """
        )


def _state_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def create_oauth_state(candidate_id: str, provider: str, *, metadata: dict[str, Any] | None = None, code_verifier: str | None = None) -> str:
    initialize()
    state = secrets.token_urlsafe(32)
    timestamp = now_utc()
    with integration_db() as connection:
        connection.execute(
            "DELETE FROM integration_oauth_states WHERE expires_at < ?",
            (timestamp.isoformat(),),
        )
        connection.execute(
            "INSERT INTO integration_oauth_states(state_hash,candidate_id,provider,code_verifier,metadata,expires_at,created_at) VALUES(?,?,?,?,?,?,?)",
            (
                _state_hash(state),
                candidate_id,
                provider,
                code_verifier,
                json.dumps(metadata or {}, separators=(",", ":")),
                (timestamp + timedelta(minutes=10)).isoformat(),
                timestamp.isoformat(),
            ),
        )
    return state


def consume_oauth_state(state: str, provider: str, candidate_id: str) -> dict[str, Any] | None:
    initialize()
    with integration_db() as connection:
        row = connection.execute(
            "SELECT * FROM integration_oauth_states WHERE state_hash = ? AND provider = ? AND candidate_id = ?",
            (_state_hash(state), provider, candidate_id),
        ).fetchone()
        connection.execute("DELETE FROM integration_oauth_states WHERE state_hash = ?", (_state_hash(state),))
    if not row:
        return None
    try:
        expires_at = datetime.fromisoformat(str(row["expires_at"]))
        if expires_at < now_utc():
            return None
        metadata = json.loads(row["metadata"] or "{}")
    except Exception:
        return None
    return {"code_verifier": row["code_verifier"], "metadata": metadata}


def save_connection(
    candidate_id: str,
    provider: str,
    *,
    access_token: str | None,
    refresh_token: str | None,
    expires_at: str | None,
    scope: str | None,
    metadata: dict[str, Any] | None = None,
) -> None:
    initialize()
    timestamp = now_iso()
    with integration_db() as connection:
        connection.execute(
            """
            INSERT INTO integration_connections
                (candidate_id,provider,access_token,refresh_token,expires_at,scope,metadata,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?)
            ON CONFLICT(candidate_id,provider) DO UPDATE SET
                access_token=excluded.access_token,
                refresh_token=COALESCE(excluded.refresh_token,integration_connections.refresh_token),
                expires_at=excluded.expires_at,
                scope=excluded.scope,
                metadata=excluded.metadata,
                updated_at=excluded.updated_at
            """,
            (
                candidate_id,
                provider,
                encrypt(access_token),
                encrypt(refresh_token),
                expires_at,
                scope,
                json.dumps(metadata or {}, separators=(",", ":")),
                timestamp,
                timestamp,
            ),
        )


def get_connection(candidate_id: str, provider: str) -> dict[str, Any] | None:
    initialize()
    with integration_db() as connection:
        row = connection.execute(
            "SELECT * FROM integration_connections WHERE candidate_id = ? AND provider = ?",
            (candidate_id, provider),
        ).fetchone()
    if not row:
        return None
    try:
        metadata = json.loads(row["metadata"] or "{}")
    except Exception:
        metadata = {}
    return {
        "candidate_id": row["candidate_id"],
        "provider": row["provider"],
        "access_token": decrypt(row["access_token"]),
        "refresh_token": decrypt(row["refresh_token"]),
        "expires_at": row["expires_at"],
        "scope": row["scope"],
        "metadata": metadata,
        "updated_at": row["updated_at"],
    }


def list_connections(candidate_id: str) -> list[dict[str, Any]]:
    initialize()
    with integration_db() as connection:
        rows = connection.execute(
            "SELECT provider,scope,expires_at,metadata,updated_at FROM integration_connections WHERE candidate_id = ? ORDER BY provider",
            (candidate_id,),
        ).fetchall()
    values: list[dict[str, Any]] = []
    for row in rows:
        try:
            metadata = json.loads(row["metadata"] or "{}")
        except Exception:
            metadata = {}
        values.append({
            "provider": row["provider"],
            "scope": row["scope"],
            "expires_at": row["expires_at"],
            "metadata": metadata,
            "updated_at": row["updated_at"],
            "connected": True,
        })
    return values


def delete_connection(candidate_id: str, provider: str) -> bool:
    initialize()
    with integration_db() as connection:
        cursor = connection.execute(
            "DELETE FROM integration_connections WHERE candidate_id = ? AND provider = ?",
            (candidate_id, provider),
        )
        return cursor.rowcount > 0


def create_clipper_token(candidate_id: str, label: str = "CareerPilot browser extension") -> str:
    initialize()
    token = "cpclip_" + secrets.token_urlsafe(32)
    with integration_db() as connection:
        connection.execute(
            "INSERT INTO integration_clipper_tokens(token_hash,candidate_id,label,created_at,revoked_at) VALUES(?,?,?,?,NULL)",
            (_state_hash(token), candidate_id, label.strip()[:100] or "CareerPilot browser extension", now_iso()),
        )
    return token


def verify_clipper_token(token: str) -> str | None:
    initialize()
    if not token:
        return None
    with integration_db() as connection:
        row = connection.execute(
            "SELECT candidate_id FROM integration_clipper_tokens WHERE token_hash = ? AND revoked_at IS NULL",
            (_state_hash(token),),
        ).fetchone()
    return str(row["candidate_id"]) if row else None


def revoke_clipper_tokens(candidate_id: str) -> int:
    initialize()
    with integration_db() as connection:
        cursor = connection.execute(
            "UPDATE integration_clipper_tokens SET revoked_at = ? WHERE candidate_id = ? AND revoked_at IS NULL",
            (now_iso(), candidate_id),
        )
        return cursor.rowcount


initialize()
