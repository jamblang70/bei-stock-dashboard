"""
Unit tests for app.services.auth_service.

Tests cover:
- User registration (success + duplicate email)
- Login (valid credentials, invalid password, invalid email, non-specific error message)
- Token refresh (valid token, revoked token)
- Logout (token revocation)
- Password hashing (bcrypt, not plaintext)

Database: SQLite in-memory (via conftest.py fixtures)
"""

import hashlib
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.models.user import RefreshToken, User
from app.services.auth_service import (
    login_user,
    logout_user,
    refresh_access_token,
    register_user,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(db, email="test@example.com", password="SecurePass123!", name="Test User"):
    """Register a user and return the User object."""
    with patch("app.services.auth_service._send_verification_email"):
        return register_user(db, email=email, password=password, name=name)


# ---------------------------------------------------------------------------
# Registration tests
# ---------------------------------------------------------------------------


def test_register_user_success(db):
    """Req 1.1 — Register a new user; user should be persisted in the database."""
    with patch("app.services.auth_service._send_verification_email"):
        user = register_user(db, email="new@example.com", password="Pass1234!", name="New User")

    assert user.id is not None
    assert user.email == "new@example.com"
    assert user.name == "New User"

    # Verify the user is actually in the DB
    stored = db.query(User).filter(User.email == "new@example.com").first()
    assert stored is not None
    assert stored.id == user.id


def test_register_user_duplicate_email(db):
    """Req 1.2 — Registering with an already-used email raises HTTP 400."""
    _make_user(db, email="dup@example.com")

    with pytest.raises(HTTPException) as exc_info:
        with patch("app.services.auth_service._send_verification_email"):
            register_user(db, email="dup@example.com", password="AnotherPass!", name="Dup User")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Email sudah digunakan"


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------


def test_login_user_valid_credentials(db):
    """Req 1.4 — Login with valid credentials returns access_token and refresh_token."""
    _make_user(db, email="login@example.com", password="ValidPass99!")

    result = login_user(db, email="login@example.com", password="ValidPass99!")

    assert "access_token" in result
    assert "refresh_token" in result
    assert result["access_token"]
    assert result["refresh_token"]


def test_login_user_invalid_password(db):
    """Req 1.5 — Login with wrong password raises HTTP 401."""
    _make_user(db, email="wrongpw@example.com", password="CorrectPass!")

    with pytest.raises(HTTPException) as exc_info:
        login_user(db, email="wrongpw@example.com", password="WrongPass!")

    assert exc_info.value.status_code == 401


def test_login_user_invalid_email(db):
    """Req 1.5 — Login with unregistered email raises HTTP 401."""
    with pytest.raises(HTTPException) as exc_info:
        login_user(db, email="nobody@example.com", password="AnyPass!")

    assert exc_info.value.status_code == 401


def test_login_error_message_not_specific(db):
    """
    Req 1.5 — The 401 error message must not reveal whether the email or
    password specifically was wrong (prevents user enumeration).
    Both failure cases must return the same generic error message.
    """
    _make_user(db, email="enumtest@example.com", password="RealPass!")

    # Wrong password
    with pytest.raises(HTTPException) as exc_wrong_pw:
        login_user(db, email="enumtest@example.com", password="BadPass!")

    # Non-existent email
    with pytest.raises(HTTPException) as exc_no_email:
        login_user(db, email="ghost@example.com", password="AnyPass!")

    # Both errors must return the exact same message (no enumeration)
    assert exc_wrong_pw.value.detail == exc_no_email.value.detail

    # The message must not say ONLY "email" or ONLY "password" is wrong
    # (a generic message like "Email atau password tidak valid" is acceptable)
    detail = exc_wrong_pw.value.detail.lower()
    assert "email saja" not in detail, "Message reveals email is the issue"
    assert "password saja" not in detail, "Message reveals password is the issue"
    # Must not say "email tidak ditemukan" or "password salah" specifically
    assert "tidak ditemukan" not in detail
    assert "password salah" not in detail


# ---------------------------------------------------------------------------
# Token refresh tests
# ---------------------------------------------------------------------------


def test_refresh_access_token_valid(db):
    """Req 1.6 — Refreshing with a valid token returns a new access_token."""
    _make_user(db, email="refresh@example.com", password="RefreshPass!")
    tokens = login_user(db, email="refresh@example.com", password="RefreshPass!")

    result = refresh_access_token(db, refresh_token=tokens["refresh_token"])

    assert "access_token" in result
    assert result["access_token"]


def test_refresh_access_token_revoked(db):
    """Req 1.6 — Refreshing with a revoked token raises HTTP 401."""
    _make_user(db, email="revoked@example.com", password="RevokedPass!")
    tokens = login_user(db, email="revoked@example.com", password="RevokedPass!")

    # Revoke the token via logout
    logout_user(db, refresh_token=tokens["refresh_token"])

    with pytest.raises(HTTPException) as exc_info:
        refresh_access_token(db, refresh_token=tokens["refresh_token"])

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Logout tests
# ---------------------------------------------------------------------------


def test_logout_user_revokes_token(db):
    """Req 1.7 — Logout sets revoked=True on the refresh token record."""
    _make_user(db, email="logout@example.com", password="LogoutPass!")
    tokens = login_user(db, email="logout@example.com", password="LogoutPass!")

    logout_user(db, refresh_token=tokens["refresh_token"])

    token_hash = hashlib.sha256(tokens["refresh_token"].encode()).hexdigest()
    record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    assert record is not None
    assert record.revoked is True


# ---------------------------------------------------------------------------
# Password hashing tests
# ---------------------------------------------------------------------------


def test_password_hashed_with_bcrypt(db):
    """Req 1.8 — Passwords must be stored as bcrypt hashes, never plaintext."""
    plain_password = "PlainTextPass123!"
    _make_user(db, email="bcrypt@example.com", password=plain_password)

    user = db.query(User).filter(User.email == "bcrypt@example.com").first()

    assert user is not None
    # Must not store plaintext
    assert user.password_hash != plain_password
    # Must be a bcrypt hash (starts with $2b$ or $2a$)
    assert user.password_hash.startswith(("$2b$", "$2a$")), (
        f"Expected bcrypt hash, got: {user.password_hash[:10]}..."
    )
