"""User accounts and refresh-token sessions."""
from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta

from app.config import get_settings
from app.core.errors import AppError, NotFound
from app.core.security import (
    generate_refresh_token,
    hash_refresh_token,
)
from app.store.repository import connect

log = logging.getLogger(__name__)

USER_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    email         TEXT NOT NULL,
    email_lower   TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name  TEXT NOT NULL DEFAULT '',
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL,
    last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    token_hash TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    issued_at  TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    user_agent TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_refresh_user ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_expiry ON refresh_tokens(expires_at);
"""


class EmailAlreadyRegistered(AppError):
    status_code = 409
    code = "email_already_registered"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def init_user_tables() -> None:
    with connect() as conn:
        conn.executescript(USER_SCHEMA)


# --------------------------------------------------------------------------
# users
# --------------------------------------------------------------------------

def create_user(*, email: str, password_hash: str, display_name: str = "") -> dict:
    user_id = uuid.uuid4().hex[:16]
    with connect() as conn:
        existing = conn.execute(
            "SELECT 1 FROM users WHERE email_lower = ?", (email.lower(),)
        ).fetchone()
        if existing:
            raise EmailAlreadyRegistered("That email address is already registered.")
        conn.execute(
            """INSERT INTO users (id, email, email_lower, password_hash, display_name, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, email, email.lower(), password_hash, display_name or email.split("@")[0], _now()),
        )
    return get_user(user_id)


def get_user(user_id: str) -> dict:
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise NotFound("User does not exist.")
    return dict(row)


def find_by_email(email: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email_lower = ?", (email.lower(),)).fetchone()
    return dict(row) if row else None


def update_password_hash(user_id: str, password_hash: str) -> None:
    with connect() as conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))


def record_login(user_id: str) -> None:
    with connect() as conn:
        conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (_now(), user_id))


# --------------------------------------------------------------------------
# refresh tokens
# --------------------------------------------------------------------------

def issue_refresh_token(user_id: str, user_agent: str = "") -> tuple[str, datetime]:
    """Mint a refresh token. Only its hash is persisted."""
    settings = get_settings()
    token = generate_refresh_token()
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_days)

    with connect() as conn:
        conn.execute(
            """INSERT INTO refresh_tokens (token_hash, user_id, issued_at, expires_at, user_agent)
               VALUES (?, ?, ?, ?, ?)""",
            (hash_refresh_token(token), user_id, _now(), expires_at.isoformat(), user_agent[:200]),
        )
    return token, expires_at


def consume_refresh_token(token: str, user_agent: str = "") -> tuple[dict, str, datetime]:
    """Validate a refresh token and rotate it.

    Rotation on every use is what makes a stolen refresh token a bounded problem:
    the thief's first use invalidates the legitimate holder's copy, so the theft
    surfaces as an unexpected logout instead of silent indefinite access.
    """
    from app.core.security import AuthError

    token_hash = hash_refresh_token(token)

    # Read and decide inside one transaction, but do not raise inside it: the
    # `connect()` context manager rolls back on exception, so a revocation
    # written just before an `AuthError` would be silently undone. The
    # breach-response write therefore happens in its own committed transaction
    # after this block, and only then is the error raised.
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM refresh_tokens WHERE token_hash = ?", (token_hash,)
        ).fetchone()

        if row is None:
            problem = "unknown"
            user_id = None
        elif row["revoked_at"]:
            problem = "reused"
            user_id = row["user_id"]
        elif datetime.fromisoformat(row["expires_at"]) < datetime.now(UTC):
            problem = "expired"
            user_id = row["user_id"]
        else:
            problem = None
            user_id = row["user_id"]
            conn.execute(
                "UPDATE refresh_tokens SET revoked_at = ? WHERE token_hash = ?", (_now(), token_hash)
            )

    if problem == "unknown":
        raise AuthError("Refresh token is not recognised.")
    if problem == "reused":
        # Presenting an already-rotated token means it leaked: the legitimate
        # holder has moved past it, so someone else is holding a copy. Revoke
        # every live session for the account and force a fresh sign-in.
        log.warning("Reuse of revoked refresh token for user %s; revoking all sessions", user_id)
        revoke_all_for_user(user_id)
        raise AuthError("Refresh token has been revoked. Please sign in again.")
    if problem == "expired":
        raise AuthError("Refresh token has expired. Please sign in again.")

    user = get_user(user_id)
    if not user["is_active"]:
        raise AuthError("This account is disabled.")

    new_token, expires_at = issue_refresh_token(user_id, user_agent)
    return user, new_token, expires_at


def revoke_refresh_token(token: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE refresh_tokens SET revoked_at = ? WHERE token_hash = ? AND revoked_at IS NULL",
            (_now(), hash_refresh_token(token)),
        )


def revoke_all_for_user(user_id: str) -> int:
    with connect() as conn:
        cursor = conn.execute(
            "UPDATE refresh_tokens SET revoked_at = ? WHERE user_id = ? AND revoked_at IS NULL",
            (_now(), user_id),
        )
        return cursor.rowcount


def purge_expired_tokens() -> int:
    """Housekeeping: expired rows are dead weight and a needless liability."""
    with connect() as conn:
        cursor = conn.execute("DELETE FROM refresh_tokens WHERE expires_at < ?", (_now(),))
        return cursor.rowcount
