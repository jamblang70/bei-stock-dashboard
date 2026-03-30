"""Auth API router — /api/v1/auth/*"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.rate_limiter import check_login_lockout, record_login_attempt
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import (
    login_user,
    logout_user,
    refresh_access_token,
    register_user,
    verify_email,
)

router = APIRouter()


def _get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=MessageResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    register_user(db, email=body.email, password=body.password, name=body.name)
    return MessageResponse(
        message="Registrasi berhasil. Silakan cek email Anda untuk verifikasi."
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate user and return JWT access + refresh tokens."""
    ip = _get_client_ip(request)

    # Check lockout before attempting login
    check_login_lockout(db, ip)

    try:
        tokens = login_user(db, email=body.email, password=body.password)
        record_login_attempt(db, ip, success=True)
        return TokenResponse(**tokens)
    except Exception:
        record_login_attempt(db, ip, success=False)
        raise


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    """Issue a new access token using a valid refresh token."""
    result = refresh_access_token(db, refresh_token=body.refresh_token)
    return AccessTokenResponse(**result)


@router.post("/logout", response_model=MessageResponse)
def logout(body: LogoutRequest, db: Session = Depends(get_db)):
    """Revoke the provided refresh token."""
    logout_user(db, refresh_token=body.refresh_token)
    return MessageResponse(message="Logout berhasil.")


@router.get("/verify-email", response_model=MessageResponse)
def verify_email_endpoint(
    token: str = Query(..., description="Email verification token"),
    db: Session = Depends(get_db),
):
    """Verify user email address via token sent during registration."""
    verify_email(db, token=token)
    return MessageResponse(message="Email berhasil diverifikasi.")
