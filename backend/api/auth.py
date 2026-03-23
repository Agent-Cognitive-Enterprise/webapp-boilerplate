# /backend/api/auth.py

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth_account_recovery import router as auth_account_recovery_router
from api.auth_registration import register_user_handler
from api.auth_sessions import login_for_access_token_handler
from api.auth_sessions import logout_handler
from api.auth_sessions import rotate_refresh_token_handler
from api.auth_shared import (
    check_rate_limit,
    email_verification_expiry,
    generate_email_verification_token,
    resolve_auth_backend_base_url,
)
from auth.auth_handler import create_access_token
from models.token import Token
from models.user import UserCreate, UserPublic
from services.email_service import send_email
from utils.db import get_session

router = APIRouter()


@router.post("/auth/register", response_model=UserPublic)
async def register_user(
    *,
    session: AsyncSession = Depends(get_session),
    request: Request,
    user: UserCreate,
):
    return await register_user_handler(
        session=session,
        request=request,
        user=user,
        check_rate_limit=check_rate_limit,
        resolve_auth_backend_base_url=resolve_auth_backend_base_url,
        generate_email_verification_token=generate_email_verification_token,
        email_verification_expiry=email_verification_expiry,
        send_email=send_email,
    )


@router.post("/auth/token", response_model=Token)
async def login_for_access_token(
    *,
    session: AsyncSession = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request,
    response: Response,
) -> Token:
    return await login_for_access_token_handler(
        session=session,
        form_data=form_data,
        request=request,
        response=response,
        check_rate_limit=check_rate_limit,
        create_access_token=create_access_token,
    )


@router.post("/auth/refresh", response_model=Token)
async def rotate_refresh_token(
    *,
    session: AsyncSession = Depends(get_session),
    request: Request,
    response: Response,
) -> Token:
    return await rotate_refresh_token_handler(
        session=session,
        request=request,
        response=response,
        check_rate_limit=check_rate_limit,
        create_access_token=create_access_token,
    )


@router.post("/auth/logout", status_code=204)
async def logout(
    *,
    session: AsyncSession = Depends(get_session),
    request: Request,
    response: Response,
):
    return await logout_handler(
        session=session,
        request=request,
        response=response,
    )
router.include_router(auth_account_recovery_router)
