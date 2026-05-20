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
    LoginUserInfo,
    LogoutResponse,
    RecoveryRequest,
    RecoveryResponse,
    TotpSetupResponse,
    TotpVerifyRequest,
    TotpVerifyResponse,
)

logger = logging.getLogger("nomos-api.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])

_login_limiter: RateLimiter | None = None


def _get_limiter() -> RateLimiter:
    global _login_limiter
    if _login_limiter is None:
        from nomos_api.config import settings

        _login_limiter = RateLimiter(
            max_attempts=5,
            window_seconds=900,
            lockout_seconds=900,
            valkey_url=settings.valkey_url,
        )
    return _login_limiter


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


# Public alias for use by other routers (e.g. agents.py)
get_current_user = _get_current_user


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


# router-coverage-skip: /login is unauthenticated by design — issues the JWT cookie.
@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    # Rate limiting by email
    if not await _get_limiter().is_allowed(body.email):
        logger.warning("Rate limit exceeded for %s", body.email)
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    result = await db.execute(select(User).where(User.email == body.email, User.is_active == True))  # noqa: E712
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        await _get_limiter().record_attempt(body.email)
        logger.info("Failed login attempt for %s", body.email)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Successful login — reset rate limiter
    await _get_limiter().reset(body.email)

    payload = TokenPayload(user_id=user.id, email=user.email, role=user.role)
    token = create_token(payload, settings.jwt_secret, expires_hours=user.session_timeout_hours)

    # M1 (CSRF): SameSite=strict UNCONDITIONALLY. Previously this dropped to
    # 'lax' when cookie_secure was false, which allows top-level cross-site
    # navigations to send the auth cookie. The console is same-origin, so
    # strict does not break the golden path.
    # v0.4.0 P6 (audit A-#14): path="/api" — the cookie is only ever sent
    # to /api/* endpoints, not to /docs, /openapi.json, or any future
    # subpath. Defense-in-depth: a future XSS-able non-API path no longer
    # automatically receives the session cookie.
    response.set_cookie(
        key="nomos_token",
        value=token,
        path="/api",
        httponly=True,
        samesite="strict",
        secure=settings.cookie_secure,
        max_age=user.session_timeout_hours * 3600,
    )

    logger.info("Successful login for %s (role=%s)", user.email, user.role)
    has_2fa = getattr(user, "totp_enabled", False)
    return LoginResponse(
        requires_2fa=has_2fa,
        user=LoginUserInfo(
            id=str(user.id),
            email=user.email,
            name=user.email.split("@")[0],
            role=user.role,
        )
        if not has_2fa
        else None,
        message="Login successful",
    )


# router-coverage-skip: /logout only clears the JWT cookie. AuthMiddleware enforces principal presence.
@router.post("/logout", response_model=LogoutResponse)
async def logout(response: Response) -> LogoutResponse:
    # v0.4.0 P6 (A-#14): match the path used by /login so the browser
    # actually deletes the cookie. Without `path="/api"` a cookie set at
    # /api wouldn't be cleared by a delete at /.
    response.delete_cookie(
        "nomos_token",
        path="/api",
        samesite="strict",
        secure=settings.cookie_secure,
    )
    return LogoutResponse(message="Logged out")


# router-coverage-skip: /2fa/setup is in PUBLIC_PREFIXES (/api/auth/2fa). Authenticated-cookie users only; role-check N/A.
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


# router-coverage-skip: /2fa/verify is in PUBLIC_PREFIXES (/api/auth/2fa) — must run before the post-login cookie is upgraded.
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
    return TotpVerifyResponse(
        verified=True,
        user=LoginUserInfo(
            id=str(current_user.id),
            email=current_user.email,
            name=current_user.email.split("@")[0],
            role=current_user.role,
        ),
    )


# router-coverage-skip: /recovery is unauthenticated — second-factor / cookie loss recovery.
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
