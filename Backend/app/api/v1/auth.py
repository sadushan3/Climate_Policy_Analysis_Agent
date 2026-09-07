"""Registration, login, token refresh and session management."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, EmailStr, Field

from app.api.deps import client_key, get_current_user, login_limiter
from app.config import get_settings
from app.core.errors import ValidationError
from app.core.security import (
    AuthError,
    create_access_token,
    hash_password,
    needs_rehash,
    password_problems,
    verify_password,
)
from app.store import users as user_store

log = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "refresh_token"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    display_name: str = Field(default="", max_length=80)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    created_at: str
    last_login_at: str | None = None
    document_count: int = 0


def _public(user: dict) -> dict:
    """Never let `password_hash` reach a response body."""
    return {
        "id": user["id"],
        "email": user["email"],
        "display_name": user["display_name"],
        "created_at": user["created_at"],
        "last_login_at": user.get("last_login_at"),
    }


def _set_refresh_cookie(response: Response, token: str) -> None:
    """Deliver the refresh token as an HttpOnly cookie.

    Deliberately not returned in the JSON body: a token readable by JavaScript is
    a token an XSS bug can exfiltrate. The short-lived access token lives in
    memory; the long-lived refresh token stays out of reach of page scripts.
    """
    settings = get_settings()
    response.set_cookie(
        REFRESH_COOKIE,
        token,
        max_age=settings.refresh_token_days * 24 * 3600,
        httponly=True,
        secure=settings.environment == "prod",  # over plain HTTP in dev
        samesite="lax",
        path="/api/v1/auth",  # sent only to the auth endpoints that need it
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: RegisterRequest, request: Request, response: Response):
    settings = get_settings()
    if not settings.allow_registration:
        raise ValidationError("Registration is closed on this deployment.")

    problems = password_problems(payload.password)
    if problems:
        raise ValidationError(
            "Password " + "; ".join(problems) + ".", details={"problems": problems}
        )

    user = user_store.create_user(
        email=payload.email,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
    )
    log.info("Registered user %s", user["id"])

    token, expires_in = create_access_token(user["id"], user["email"])
    refresh, _ = user_store.issue_refresh_token(user["id"], request.headers.get("user-agent", ""))
    _set_refresh_cookie(response, refresh)

    return TokenResponse(access_token=token, expires_in=expires_in, user=_public(user))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, response: Response):
    # Throttle on IP *and* on the account, so an attacker cannot spread attempts
    # against one account across many source addresses.
    ip_key = f"ip:{client_key(request)}"
    account_key = f"account:{payload.email.lower()}"
    login_limiter.check(ip_key)
    login_limiter.check(account_key)

    user = user_store.find_by_email(payload.email)

    # Verify against a dummy hash when the account is unknown, so the response
    # time does not reveal whether the address is registered.
    stored = user["password_hash"] if user else _DUMMY_HASH
    password_ok = verify_password(payload.password, stored)

    if not user or not password_ok or not user["is_active"]:
        log.info("Failed login for %s", payload.email)
        raise AuthError("Email or password is incorrect.")

    # Transparently upgrade a hash stored under weaker parameters.
    if needs_rehash(user["password_hash"]):
        user_store.update_password_hash(user["id"], hash_password(payload.password))

    login_limiter.reset(ip_key)
    login_limiter.reset(account_key)
    user_store.record_login(user["id"])

    token, expires_in = create_access_token(user["id"], user["email"])
    refresh, _ = user_store.issue_refresh_token(user["id"], request.headers.get("user-agent", ""))
    _set_refresh_cookie(response, refresh)

    return TokenResponse(access_token=token, expires_in=expires_in, user=_public(user))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(request: Request, response: Response):
    """Exchange a refresh token for a new access token, rotating the refresh token."""
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise AuthError("No refresh token supplied.")

    user, new_refresh, _ = user_store.consume_refresh_token(
        token, request.headers.get("user-agent", "")
    )
    _set_refresh_cookie(response, new_refresh)

    access, expires_in = create_access_token(user["id"], user["email"])
    return TokenResponse(access_token=access, expires_in=expires_in, user=_public(user))


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response):
    token = request.cookies.get(REFRESH_COOKIE)
    if token:
        user_store.revoke_refresh_token(token)
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")


@router.post("/logout-all", status_code=200)
async def logout_everywhere(response: Response, user: dict = Depends(get_current_user)):
    """Revoke every session for the caller.

    This is the capability a pure-JWT design cannot offer, and the reason refresh
    tokens are stored server-side rather than being self-contained.
    """
    revoked = user_store.revoke_all_for_user(user["id"])
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")
    return {"revoked_sessions": revoked}


@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(get_current_user)):
    from app.store import repository as repo

    return UserResponse(**_public(user), document_count=repo.count_documents(user["id"]))


# Computed once at import: a real Argon2 hash of a random string, used to keep
# the failed-login path the same cost as the successful one.
_DUMMY_HASH = hash_password("not-a-real-password-used-only-for-timing")
