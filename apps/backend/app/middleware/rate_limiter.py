"""Rate limiting middleware and account lockout helpers.

Task 3.2 — Account lockout:
  - check_login_lockout(db, ip_address): raise HTTP 429 if IP blocked
  - record_login_attempt(db, ip_address, success): persist to login_attempts

Task 3.3 — Rate limiting middleware:
  - RateLimitMiddleware: FastAPI ASGI middleware using Redis counters
    * Authenticated users: 100 req/min  (key: rate:user:{user_id})
    * Public endpoints per IP: 20 req/min (key: rate:ip:{ip_address})
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.core.redis_client import get_redis
from app.models.user import LoginAttempt

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LOCKOUT_WINDOW_MINUTES = 15
LOCKOUT_THRESHOLD = 5  # failed attempts within the window

RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_AUTHENTICATED = 100  # req/min per user
RATE_LIMIT_PUBLIC = 20  # req/min per IP

# ---------------------------------------------------------------------------
# Account lockout (Task 3.2)
# ---------------------------------------------------------------------------


def check_login_lockout(db: Session, ip_address: str) -> None:
    """
    Raise HTTP 429 if the IP has ≥ LOCKOUT_THRESHOLD failed login attempts
    within the last LOCKOUT_WINDOW_MINUTES minutes.
    """
    window_start = datetime.now(UTC) - timedelta(minutes=LOCKOUT_WINDOW_MINUTES)
    failed_count = (
        db.query(LoginAttempt)
        .filter(
            LoginAttempt.ip_address == ip_address,
            LoginAttempt.success == False,  # noqa: E712
            LoginAttempt.attempted_at >= window_start,
        )
        .count()
    )

    if failed_count >= LOCKOUT_THRESHOLD:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Terlalu banyak percobaan login gagal. "
                f"Coba lagi setelah {LOCKOUT_WINDOW_MINUTES} menit."
            ),
        )


def record_login_attempt(db: Session, ip_address: str, success: bool) -> None:
    """Persist a login attempt record to the database."""
    attempt = LoginAttempt(ip_address=ip_address, success=success)
    db.add(attempt)
    db.commit()


# ---------------------------------------------------------------------------
# Rate limiting middleware (Task 3.3)
# ---------------------------------------------------------------------------


def _get_client_ip(request: Request) -> str:
    """Extract the real client IP, respecting X-Forwarded-For."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _extract_user_id_from_request(request: Request) -> str | None:
    """Try to decode the Bearer token and return the user_id string, or None."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[len("Bearer "):]
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") == "access":
            return payload.get("sub")
    except JWTError:
        pass
    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that enforces per-user and per-IP rate limits using Redis.

    - Authenticated (Bearer token present & valid): 100 req/min
      Redis key: rate:user:{user_id}
    - Public (no valid token): 20 req/min per IP
      Redis key: rate:ip:{ip_address}
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            redis_client = get_redis()
        except Exception:
            # If Redis is unavailable, fail open (don't block requests)
            logger.warning("Redis unavailable — skipping rate limit check")
            return await call_next(request)

        user_id = _extract_user_id_from_request(request)
        ip_address = _get_client_ip(request)

        if user_id:
            key = f"rate:user:{user_id}"
            limit = RATE_LIMIT_AUTHENTICATED
        else:
            key = f"rate:ip:{ip_address}"
            limit = RATE_LIMIT_PUBLIC

        try:
            pipe = redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, RATE_LIMIT_WINDOW_SECONDS)
            results = pipe.execute()
            current_count = results[0]
        except Exception as exc:
            logger.warning("Redis rate limit check failed: %s — failing open", exc)
            return await call_next(request)

        if current_count > limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": (
                        f"Rate limit terlampaui. Maksimal {limit} request per menit."
                    )
                },
                headers={"Retry-After": str(RATE_LIMIT_WINDOW_SECONDS)},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - current_count))
        return response
