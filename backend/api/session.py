from __future__ import annotations

import hashlib
import hmac
import os
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from backend.services.workspace_store import authenticate, create_account, account_for_candidate

COOKIE_NAME = "careerpilot_session"

SECRET_VALUE = os.getenv("CAREERPILOT_SESSION_SECRET")
if not SECRET_VALUE and os.getenv("ENVIRONMENT", "development").lower() == "production":
    raise RuntimeError("CAREERPILOT_SESSION_SECRET must be configured in production.")
SECRET_VALUE = SECRET_VALUE or "careerpilot-local-development-secret"
SECRET = SECRET_VALUE.encode("utf-8")

router = APIRouter(prefix="/session", tags=["Authentication"])


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)


class SessionEnvelope(BaseModel):
    authenticated: bool
    candidate_id: str
    email: str | None = None
    account_id: str | None = None


def _sign(candidate_id: str) -> str:
    signature = hmac.new(SECRET, candidate_id.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{candidate_id}.{signature}"


def _verify(value: str | None) -> str | None:
    if not value or "." not in value:
        return None
    raw, signature = value.rsplit(".", 1)
    expected = hmac.new(SECRET, raw.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        uuid.UUID(raw)
    except ValueError:
        return None
    return raw


def get_candidate_id(request: Request) -> str:
    candidate_id = _verify(request.cookies.get(COOKIE_NAME))
    if not candidate_id:
        raise HTTPException(status_code=401, detail="Career session is not authenticated.")
    return candidate_id


def ensure_session(request: Request, response: Response) -> str:
    existing = _verify(request.cookies.get(COOKIE_NAME))
    if existing:
        return existing
    candidate_id = str(uuid.uuid4())
    response.set_cookie(
        COOKIE_NAME,
        _sign(candidate_id),
        httponly=True,
        secure=os.getenv("ENVIRONMENT", "development").lower() == "production",
        samesite="lax",
        max_age=31536000,
        path="/",
    )
    return candidate_id


def _set_session(response: Response, candidate_id: str) -> None:
    response.set_cookie(
        COOKIE_NAME,
        _sign(candidate_id),
        httponly=True,
        secure=os.getenv("ENVIRONMENT", "development").lower() == "production",
        samesite="lax",
        max_age=31536000,
        path="/",
    )


@router.get("/me", response_model=SessionEnvelope)
def me(request: Request, response: Response) -> SessionEnvelope:
    candidate_id = _verify(request.cookies.get(COOKIE_NAME))
    if not candidate_id:
        return SessionEnvelope(authenticated=False, candidate_id="")
    account = account_for_candidate(candidate_id)
    return SessionEnvelope(
        authenticated=bool(account),
        candidate_id=candidate_id,
        email=account["email"] if account else None,
        account_id=account["account_id"] if account else None,
    )


@router.post("/signup", response_model=SessionEnvelope)
def signup(credentials: Credentials, response: Response) -> SessionEnvelope:
    try:
        account = create_account(credentials.email, credentials.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _set_session(response, account["candidate_id"])
    return SessionEnvelope(
        authenticated=True,
        candidate_id=account["candidate_id"],
        email=account["email"],
        account_id=account["account_id"],
    )


@router.post("/login", response_model=SessionEnvelope)
def login(credentials: Credentials, response: Response) -> SessionEnvelope:
    account = authenticate(credentials.email, credentials.password)
    if not account:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    _set_session(response, account["candidate_id"])
    return SessionEnvelope(
        authenticated=True,
        candidate_id=account["candidate_id"],
        email=account["email"],
        account_id=account["account_id"],
    )


@router.post("/logout")
def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"logged_out": True}


@router.post("/bootstrap")
def bootstrap(request: Request, response: Response) -> dict[str, str]:
    candidate_id = ensure_session(request, response)
    return {"candidate_id": candidate_id}
