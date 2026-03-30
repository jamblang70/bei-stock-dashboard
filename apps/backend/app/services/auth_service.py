"""Auth service — register, login, refresh, logout, verify email."""

import hashlib
import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import RefreshToken, User

logger = logging.getLogger(__name__)

import bcrypt as _bcrypt_lib

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hash_password(password: str) -> str:
    return _bcrypt_lib.hashpw(password.encode(), _bcrypt_lib.gensalt(rounds=12)).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt_lib.checkpw(plain.encode(), hashed.encode())


def _create_access_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(UTC) + timedelta(hours=1)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _create_refresh_token_value() -> str:
    """Return a cryptographically random opaque token string."""
    return secrets.token_urlsafe(64)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _send_verification_email(email: str, token: str) -> None:
    """Send verification email. Falls back to console log when SMTP is not configured."""
    verify_url = f"http://localhost:8000/api/v1/auth/verify-email?token={token}"
    try:
        smtp_host = getattr(settings, "SMTP_HOST", None)
        if not smtp_host:
            raise ValueError("SMTP not configured")

        import emails  # type: ignore[import-untyped]

        message = emails.Message(
            subject="Verifikasi Email BEI Stock Dashboard",
            html=f"<p>Klik link berikut untuk verifikasi email Anda: <a href='{verify_url}'>{verify_url}</a></p>",
            mail_from=("BEI Stock Dashboard", "noreply@bei-dashboard.com"),
        )
        message.send(to=email, smtp={"host": smtp_host, "port": 587})
        logger.info("Verification email sent to %s", email)
    except Exception:
        logger.info(
            "[EMAIL VERIFICATION] To: %s | URL: %s",
            email,
            verify_url,
        )


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


def register_user(db: Session, email: str, password: str, name: str) -> User:
    """Register a new user. Raises HTTP 400 if email already exists."""
    existing = db.query(User).filter(User.email == email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email sudah digunakan",
        )

    user = User(
        email=email.lower(),
        name=name,
        password_hash=_hash_password(password),
        email_verified=False,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate a short-lived verification token (24 h) stored as a signed JWT
    expire = datetime.now(UTC) + timedelta(hours=24)
    verify_payload = {
        "sub": str(user.id),
        "exp": expire,
        "type": "email_verify",
    }
    verify_token = jwt.encode(
        verify_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    _send_verification_email(user.email, verify_token)

    return user


def login_user(
    db: Session,
    email: str,
    password: str,
) -> dict:
    """
    Verify credentials and return access + refresh tokens.
    Raises HTTP 401 (without specific detail) on invalid credentials.
    """
    user = db.query(User).filter(User.email == email.lower()).first()

    if not user or not _verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password tidak valid",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password tidak valid",
        )

    access_token = _create_access_token(user.id)

    raw_refresh = _create_refresh_token_value()
    expires_at = datetime.now(UTC) + timedelta(days=7)
    refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(raw_refresh),
        expires_at=expires_at,
        revoked=False,
    )
    db.add(refresh_record)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "token_type": "bearer",
        "expires_in": 3600,
    }


def refresh_access_token(db: Session, refresh_token: str) -> dict:
    """
    Validate refresh token and issue a new access token.
    Raises HTTP 401 if token is invalid, expired, or revoked.
    """
    token_hash = _hash_token(refresh_token)
    record = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,  # noqa: E712
        )
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token tidak valid atau sudah dicabut",
        )

    now = datetime.now(UTC)
    expires_at = record.expires_at
    # SQLite stores naive datetimes — make timezone-aware for comparison
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token sudah kadaluarsa",
        )

    access_token = _create_access_token(record.user_id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600,
    }


def logout_user(db: Session, refresh_token: str) -> None:
    """Revoke the given refresh token."""
    token_hash = _hash_token(refresh_token)
    record = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )
    if record:
        record.revoked = True
        db.commit()


def verify_email(db: Session, token: str) -> None:
    """
    Validate email verification token and mark user as verified.
    Raises HTTP 400 on invalid/expired token.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "email_verify":
            raise JWTError("wrong token type")
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token verifikasi tidak valid atau sudah kadaluarsa",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token verifikasi tidak valid atau sudah kadaluarsa",
        )

    user.email_verified = True
    db.commit()


def get_current_user_from_token(db: Session, token: str) -> User:
    """Decode access token and return the corresponding User. Used by auth middleware."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise JWTError("wrong token type")
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()  # noqa: E712
    if not user:
        raise credentials_exception
    return user
