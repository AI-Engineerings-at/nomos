"""User management endpoints (admin only)."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nomos_api.auth.jwt import decode_token, TokenPayload
from nomos_api.auth.password import hash_password, validate_password_strength
from nomos_api.auth.recovery import generate_recovery_key, hash_recovery_key
from nomos_api.config import settings
from nomos_api.database import get_db
from nomos_api.models import User
from nomos_api.schemas import (
    UserCreateRequest,
    UserCreateResponse,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
)

logger = logging.getLogger("nomos-api.users")

router = APIRouter(prefix="/api/users", tags=["users"])


async def _require_admin(
    nomos_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency: require admin role."""
    if not nomos_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(nomos_token, settings.jwt_secret)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    result = await db.execute(select(User).where(User.id == payload.user_id, User.is_active == True))  # noqa: E712
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found or deactivated")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.post("/bootstrap", response_model=UserCreateResponse, status_code=201)
async def bootstrap_admin(
    body: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> UserCreateResponse:
    """Create the first admin user. Only works when no users exist."""
    existing = await db.execute(select(User))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=403, detail="Bootstrap already completed. Users exist.")

    errors = validate_password_strength(body.password)
    if errors:
        raise HTTPException(status_code=422, detail="; ".join(errors))

    recovery_words = generate_recovery_key()
    recovery_phrase = " ".join(recovery_words)

    user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        password_hash=hash_password(body.password),
        role="admin",
        recovery_key_hash=hash_recovery_key(recovery_phrase),
        session_timeout_hours=8,
    )
    db.add(user)
    await db.commit()
    logger.info("Bootstrap admin created: %s", body.email)

    return UserCreateResponse(
        id=user.id, email=user.email, role="admin",
        recovery_key=recovery_words,
        totp_enabled=False, session_timeout_hours=8, is_active=True,
    )


@router.get("", response_model=UserListResponse)
async def list_users(
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserListResponse:
    result = await db.execute(select(User).order_by(User.email))
    users = result.scalars().all()
    return UserListResponse(
        users=[
            UserResponse(
                id=u.id,
                email=u.email,
                role=u.role,
                totp_enabled=u.totp_enabled,
                session_timeout_hours=u.session_timeout_hours,
                is_active=u.is_active,
            )
            for u in users
        ],
        total=len(users),
    )


@router.post("", response_model=UserCreateResponse, status_code=201)
async def create_user(
    body: UserCreateRequest,
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserCreateResponse:
    # Validate password strength
    errors = validate_password_strength(body.password)
    if errors:
        raise HTTPException(status_code=422, detail="; ".join(errors))

    # Check for duplicate email
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email already in use")

    # Generate recovery key
    recovery_words = generate_recovery_key()
    recovery_phrase = " ".join(recovery_words)

    # Set session timeout based on role
    timeout = 8 if body.role == "admin" else 24

    user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
        recovery_key_hash=hash_recovery_key(recovery_phrase),
        session_timeout_hours=timeout,
        is_active=True,
    )
    db.add(user)
    await db.commit()

    logger.info("User created: %s (role=%s) by admin %s", body.email, body.role, admin.email)

    # Recovery key is shown ONCE
    return UserCreateResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        recovery_key=recovery_phrase,
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    body: UserUpdateRequest,
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if body.role is not None:
        user.role = body.role
        # Update timeout when role changes
        user.session_timeout_hours = 8 if body.role == "admin" else 24
    if body.session_timeout_hours is not None:
        user.session_timeout_hours = body.session_timeout_hours
    if body.is_active is not None:
        user.is_active = body.is_active

    await db.commit()
    await db.refresh(user)

    logger.info("User %s updated by admin %s", user.email, admin.email)
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        totp_enabled=user.totp_enabled,
        session_timeout_hours=user.session_timeout_hours,
        is_active=user.is_active,
    )


@router.delete("/{user_id}", response_model=UserResponse)
async def deactivate_user(
    user_id: str,
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    await db.commit()

    logger.info("User %s deactivated by admin %s", user.email, admin.email)
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        totp_enabled=user.totp_enabled,
        session_timeout_hours=user.session_timeout_hours,
        is_active=user.is_active,
    )
