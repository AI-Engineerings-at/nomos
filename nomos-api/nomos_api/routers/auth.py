"""Auth endpoints: login, logout, 2FA setup/verify, recovery."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.auth.jwt import TokenPayload, create_token, decode_token
from nomos_api.auth.password import hash_password, verify_password
from nomos_api.auth.rate_limiter import RateLimiter
from nomos_api.auth.recovery import verify_recovery_key
from nomos_api.auth.totp import generate_totp_secret, get_provisioning_uri, verify_totp
from nomos_api.config import settings
from nomos_api.database import get_db
from nomos_api.models import User
from nomos_api.schemas import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RecoveryRequest,
    RecoveryResponse,
    TotpSetupResponse,
    TotpVerifyRequest,
    TotpVerifyResponse,
)

logger = logging.getLogger("nomos-api.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])

# In-memory rate limiter: 5 attempts, 15 min (900s) lockout
_login_limiter = RateLimiter(max_attempts=5, window_seconds=900, lockout_seconds=900)


async def _get_current_user(
    nomos_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency: extract current user from JWT cookie."""
    if not nomos_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(nomos_token, settings.jwt_secret)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    result = await db.execute(select(User).where(User.id == payload.user_id, User.is_active == True))  # noqa: E712
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found or deactivated")
    return user


@router.get("/me")
async def get_current_user_info(
    user: User = Depends(_get_current_user),
) -> dict:
    """Return current user info from JWT cookie."""
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "name": getattr(user, "name", user.email.split("@")[0]),
    }


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    # Rate limiting by email
    if not _login_limiter.is_allowed(body.email):
        logger.warning("Rate limit exceeded for %s", body.email)
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    result = await db.execute(select(User).where(User.email == body.email, User.is_active == True))  # noqa: E712
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        _login_limiter.record_attempt(body.email)
        logger.info("Failed login attempt for %s", body.email)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Successful login — reset rate limiter
    _login_limiter.reset(body.email)

    payload = TokenPayload(user_id=user.id, email=user.email, role=user.role)
    token = create_token(payload, settings.jwt_secret, expires_hours=user.session_timeout_hours)

    response.set_cookie(
        key="nomos_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # set True in production behind TLS
        max_age=user.session_timeout_hours * 3600,
    )

    logger.info("Successful login for %s (role=%s)", user.email, user.role)
    return LoginResponse(message="Login successful", role=user.role, email=user.email)


@router.post("/logout", response_model=LogoutResponse)
async def logout(response: Response) -> LogoutResponse:
    response.delete_cookie("nomos_token")
    return LogoutResponse(message="Logged out")


@router.post("/2fa/setup", response_model=TotpSetupResponse)
async def setup_2fa(
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TotpSetupResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can set up 2FA")

    secret = generate_totp_secret()
    uri = get_provisioning_uri(secret, current_user.email)

    current_user.totp_secret = secret
    await db.commit()

    logger.info("2FA setup initiated for %s", current_user.email)
    return TotpSetupResponse(secret=secret, provisioning_uri=uri)


@router.post("/2fa/verify", response_model=TotpVerifyResponse)
async def verify_2fa(
    body: TotpVerifyRequest,
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TotpVerifyResponse:
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA not set up. Call /2fa/setup first.")

    if not verify_totp(current_user.totp_secret, body.code):
        logger.warning("Failed 2FA verification for %s", current_user.email)
        raise HTTPException(status_code=401, detail="Invalid TOTP code")

    current_user.totp_enabled = True
    await db.commit()

    logger.info("2FA enabled for %s", current_user.email)
    return TotpVerifyResponse(verified=True)


@router.post("/recovery", response_model=RecoveryResponse)
async def recovery(
    body: RecoveryRequest,
    db: AsyncSession = Depends(get_db),
) -> RecoveryResponse:
    result = await db.execute(select(User).where(User.email == body.email, User.is_active == True))  # noqa: E712
    user = result.scalar_one_or_none()

    if user is None or not user.recovery_key_hash:
        raise HTTPException(status_code=401, detail="Recovery failed")

    if not verify_recovery_key(body.recovery_phrase, user.recovery_key_hash):
        logger.warning("Failed recovery attempt for %s", body.email)
        raise HTTPException(status_code=401, detail="Recovery failed")

    user.password_hash = hash_password(body.new_password)
    await db.commit()

    logger.info("Password reset via recovery for %s", body.email)
    return RecoveryResponse(message="Password reset successful")
