import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.setup_handlers import check_setup_email_settings_handler
from api.setup_handlers import get_setup_status_handler
from api.setup_handlers import run_initial_setup_handler
from api.setup_handlers import setup_page_state_handler
from schemas.admin_settings import EmailSettingsCheckRequest, EmailSettingsCheckResponse
from schemas.bootstrap import (
    SetupInitializeRequest,
    SetupInitializeResponse,
    SetupStatusResponse,
)
from services.email_service import (
    send_email,
    test_smtp_connection,
)
from utils.db import get_session

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/setup/status", response_model=SetupStatusResponse)
async def get_setup_status(
    session: AsyncSession = Depends(get_session),
) -> SetupStatusResponse:
    return await get_setup_status_handler(
        session=session,
    )


@router.get("/setup")
async def setup_page_state(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    return await setup_page_state_handler(
        request=request,
        session=session,
    )


@router.post("/setup", response_model=SetupInitializeResponse)
async def run_initial_setup(
    payload: SetupInitializeRequest,
    session: AsyncSession = Depends(get_session),
) -> SetupInitializeResponse:
    return await run_initial_setup_handler(
        payload=payload,
        session=session,
        send_email=send_email,
    )


@router.post("/setup/email/check", response_model=EmailSettingsCheckResponse)
async def check_setup_email_settings(
    request: Request,
    payload: EmailSettingsCheckRequest,
) -> EmailSettingsCheckResponse:
    return await check_setup_email_settings_handler(
        request=request,
        payload=payload,
        test_smtp_connection=test_smtp_connection,
    )
