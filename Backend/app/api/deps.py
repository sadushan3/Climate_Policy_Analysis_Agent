"""Request dependencies: authentication and rate limiting."""
from __future__ import annotations

import logging
import time
from collections import defaultdict, deque

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings
from app.core.security import AuthError, decode_access_token
from app.store import users as user_store

log = logging.getLogger(__name__)

# `auto_error=False` so a missing header raises our own typed AuthError with a
# consistent JSON envelope, rather than FastAPI's bare 403.
_bearer = HTTPBearer(auto_error=False, description="Bearer access token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    """Resolve the caller from a bearer token.

    The user row is loaded on every request rather than trusted from the token
    claims. It costs one indexed primary-key lookup and means a deactivated
    account stops working immediately instead of at token expiry.
    """
    if credentials is None or not credentials.credentials:
        raise AuthError("Authentication required.")

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise AuthError("Access token is missing a subject.")

    try:
        user = user_store.get_user(user_id)
    except Exception as exc:
        # The token is validly signed but its user is gone.
        raise AuthError("Account no longer exists.") from exc

    if not user["is_active"]:
        raise AuthError("This account is disabled.")
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict | None:
    """For endpoints that vary by caller but do not require one."""
    if credentials is None or not credentials.credentials:
        return None
    try:
        return await get_current_user(credentials)
    except AuthError:
        return None


class RateLimiter:
    """Fixed-window-per-key limiter over an in-memory deque of timestamps.

    Scope, stated honestly: per-process, so with multiple workers the effective
    limit is `workers x limit`, and it resets on restart. Adequate for slowing
    credential stuffing on a single node; a real deployment puts this in Redis or
    at the edge. It is here because shipping a login endpoint with no throttle at
    all is worse than shipping an imperfect one.
    """

    def __init__(self, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        bucket = self._hits[key]
        while bucket and now - bucket[0] > self.window:
            bucket.popleft()

        if len(bucket) >= self.max_attempts:
            retry_after = int(self.window - (now - bucket[0])) + 1
            raise _TooManyRequests(
                f"Too many attempts. Try again in {retry_after} seconds.",
                details={"retry_after_seconds": retry_after},
            )
        bucket.append(now)

    def reset(self, key: str) -> None:
        """Clear a key after a success, so one bad password does not count
        against a user who then signs in correctly."""
        self._hits.pop(key, None)


from app.core.errors import AppError  # noqa: E402  (avoids a circular import at module load)


class _TooManyRequests(AppError):
    status_code = 429
    code = "rate_limited"


_settings = get_settings()
login_limiter = RateLimiter(_settings.login_max_attempts, _settings.login_window_seconds)


def client_key(request: Request) -> str:
    """Identify a caller for rate limiting.

    `X-Forwarded-For` is only consulted when a trusted proxy sets it; behind no
    proxy a client could otherwise spoof the header and evade the limiter
    entirely. Here we take the left-most entry and accept that this is only
    correct when the app sits behind a proxy that overwrites the header.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
