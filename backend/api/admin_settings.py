from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.admin_settings_handlers import check_admin_email_settings_handler
from api.admin_settings_handlers import get_admin_settings_handler
from api.admin_settings_handlers import update_admin_settings_handler
from auth.auth_handler import get_current_admin_user
from models.user import User
from schemas.admin_settings import (
    AdminSettingsResponse,
    AdminSettingsUpdateRequest,
    EmailSettingsCheckRequest,
    EmailSettingsCheckResponse,
)
from services.email_service import test_smtp_connection
from utils.db import get_session


router = APIRouter()


@router.get("/admin/settings", response_model=AdminSettingsResponse)
async def get_admin_settings(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: User = Depends(get_current_admin_user),
) -> AdminSettingsResponse:
    return await get_admin_settings_handler(
        request=request,
        session=session,
        current_admin=current_admin,
    )


@router.put("/admin/settings", response_model=AdminSettingsResponse)
async def update_admin_settings(
    payload: AdminSettingsUpdateRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: User = Depends(get_current_admin_user),
) -> AdminSettingsResponse:
    return await update_admin_settings_handler(
        payload=payload,
        request=request,
        session=session,
        current_admin=current_admin,
    )


@router.post("/admin/settings/email/check", response_model=EmailSettingsCheckResponse)
async def check_admin_email_settings(
    payload: EmailSettingsCheckRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> EmailSettingsCheckResponse:
    return await check_admin_email_settings_handler(
        payload=payload,
        request=request,
        session=session,
        test_smtp_connection=test_smtp_connection,
    )
