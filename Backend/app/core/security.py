"""Password hashing and token issuance.

Two token types, deliberately different in kind:

  * **Access token** — a short-lived signed JWT. Stateless, so every request
    validates it with no database round trip. It cannot be revoked, which is
    exactly why it is short-lived.
  * **Refresh token** — a long-lived opaque random string, stored server-side as
    a hash. Because it *is* a database row, it can be revoked: logout, password
    change and "sign out everywhere" all work, which a pure-JWT design cannot do.

That pairing is the whole point. A design that hands out a 30-day JWT and calls
it a session has no way to end that session early.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.config import get_settings
from app.core.errors import AppError

log = logging.getLogger(__name__)

# Argon2id is the current password-hashing recommendation (PHC winner, memory-hard
# so GPU/ASIC attacks gain far less than against bcrypt or PBKDF2). Defaults here
# are the argon2-cffi defaults, which target roughly 50 ms per hash.
_hasher = PasswordHasher()

ACCESS_TOKEN_TYPE = "access"


class AuthError(AppError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"


# --------------------------------------------------------------------------
# passwords
# --------------------------------------------------------------------------

def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        _hasher.verify(password_hash, password)
        return True
    except (VerifyMismatchError, InvalidHashError):
        return False
    except Exception:
        # Any other argon2 failure is a corrupt hash, not a valid login.
        log.warning("Password verification failed unexpectedly", exc_info=True)
        return False


def needs_rehash(password_hash: str) -> bool:
    """True when the stored hash used weaker parameters than the current policy.

    Lets cost parameters be raised over time and applied transparently on the
    user's next successful login.
    """
    try:
        return _hasher.check_needs_rehash(password_hash)
    except Exception:
        return False


def password_problems(password: str) -> list[str]:
    """Validate password strength. Length first: it dominates actual entropy."""
    problems = []
    if len(password) < 12:
        problems.append("must be at least 12 characters")
    if len(password) > 128:
        problems.append("must be at most 128 characters")
    if password.lower() in _COMMON_PASSWORDS:
        problems.append("is among the most commonly used passwords")
    return problems


# A token list only. Real deployments should check against a breach corpus
# (e.g. Have I Been Pwned's k-anonymity range API) rather than a literal.
_COMMON_PASSWORDS = frozenset(
    ["password", "password123", "123456789012", "qwertyuiopas", "letmeinplease", "welcome12345", "administrator", "changeme1234", "iloveyou1234", "passw0rd1234", "monkey123456"]
)


# --------------------------------------------------------------------------
# access tokens (stateless JWT)
# --------------------------------------------------------------------------

def create_access_token(user_id: str, email: str) -> tuple[str, int]:
    """Return (token, expires_in_seconds)."""
    settings = get_settings()
    now = datetime.now(UTC)
    expires_in = settings.access_token_minutes * 60

    payload = {
        "sub": user_id,
        "email": email,
        "type": ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        "iss": settings.jwt_issuer,
        # A unique id per token, so individual tokens can be denylisted later
        # without changing the token format.
        "jti": secrets.token_urlsafe(12),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_in


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            # Pinning the algorithm matters: accepting the token's own `alg`
            # header is the classic "alg: none" / HS-vs-RS confusion vulnerability.
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iat", "sub", "iss"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Access token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("Access token is invalid.") from exc

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        # Stops a refresh token being replayed as an access token.
        raise AuthError("Wrong token type.")
    return payload


# --------------------------------------------------------------------------
# refresh tokens (opaque, revocable)
# --------------------------------------------------------------------------

def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """Store only a hash.

    A database leak then yields no usable sessions. SHA-256 rather than Argon2 is
    correct here: the token is 48 random bytes, so it has no guessable structure
    for a slow hash to protect, and refresh happens on a hot path.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def refresh_tokens_match(candidate: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_refresh_token(candidate), stored_hash)
