# /backend/api/users.py

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from auth.auth_handler import get_current_admin_user, get_current_user
from crud.user import create as create_user, get_all as get_all_users, get_by_email
from models.user import User, UserPublic
from utils.db import get_session
from utils.password import get_password_hash
from utils.password_validator import validate_password_strength
from i18n.messages import msg

router = APIRouter()


class AdminUserResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    is_active: bool
    is_admin: bool
    email_verified: bool
    created_at: str | None


class AdminUserCreateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    is_admin: bool = False
    is_active: bool = True


class AdminUserUpdateRequest(BaseModel):
    is_active: bool | None = None


def _to_admin_user_response(user: User) -> AdminUserResponse:
    return AdminUserResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        is_active=user.is_active,
        is_admin=bool(user.is_superuser),
        email_verified=user.email_verified,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.get("/users/me/", response_model=UserPublic)
async def get_me(
    *,
    current_user=Depends(get_current_user),
):
    return UserPublic(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        is_active=current_user.is_active,
        is_admin=bool(getattr(current_user, "is_superuser", False)),
        email_verified=current_user.email_verified,
    )


@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(
    *,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin_user),
):
    users = await get_all_users(session=session)
    return [_to_admin_user_response(user) for user in users]


@router.post("/users", response_model=AdminUserResponse, status_code=201)
async def create_user_by_admin(
    *,
    request: Request,
    payload: AdminUserCreateRequest,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin_user),
):
    existing_user = await get_by_email(session=session, email=payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg(
                request=request,
                key="users.email_already_registered",
                default="Email already registered.",
            ),
        )

    is_valid, errors = validate_password_strength(payload.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password does not meet security requirements", "errors": errors},
        )

    created_user = await create_user(
        session=session,
        full_name=payload.full_name.strip(),
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        is_active=payload.is_active,
        is_superuser=payload.is_admin,
        email_verified=True,
    )

    return _to_admin_user_response(created_user)


@router.put("/users/{user_id}", response_model=AdminUserResponse)
async def update_user_by_admin(
    *,
    request: Request,
    user_id: UUID,
    payload: AdminUserUpdateRequest,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin_user),
):
    user = await session.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg(
                request=request,
                key="users.user_not_found",
                default="User not found",
            ),
        )

    if payload.is_active is not None:
        user.is_active = payload.is_active

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return _to_admin_user_response(user)


@router.delete("/users/{user_id}", status_code=204)
async def delete_user_by_admin(
    *,
    request: Request,
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_admin: User = Depends(get_current_admin_user),
):
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg(
                request=request,
                key="users.cannot_delete_self",
                default="You cannot delete your own account",
            ),
        )

    user = await session.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg(
                request=request,
                key="users.user_not_found",
                default="User not found",
            ),
        )

    user.deleted_at = datetime.now(timezone.utc)
    session.add(user)
    await session.commit()

    return None
