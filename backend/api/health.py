# /backend/api/health.py

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from crud.helper import is_connected
from settings import APP_NAME
from services.system_settings import get_system_settings_row
from utils.db import get_session

logger = logging.getLogger(__name__)

router = APIRouter()


class AppVersion:
    version: str = "0.1.6"


@router.get("/health")
async def health_check(
    *,
    session: AsyncSession = Depends(get_session),
):
    """
    Health check endpoint to verify the service is running.
    Returns a simple JSON response with the service status.
    """

    try:
        driver_name = session.bind.dialect.name
    except (Exception,):
        driver_name = "unknown"

    if await is_connected(session=session):
        logger.info(f"✅ Database ({driver_name}) session is active")
    else:
        logger.error("❌ Database session is not active")
        raise HTTPException(
            500,
            "Database session is not active",
        )

    settings = await get_system_settings_row(session=session, create_if_missing=False)
    app_name = APP_NAME
    if settings and settings.site_name and settings.site_name.strip():
        app_name = settings.site_name.strip()

    return {
        "status": "Running",
        "version": AppVersion.version,
        "app_name": app_name,
        "site_logo": settings.site_logo if settings else None,
        "background_image": settings.background_image if settings else None,
        "database_driver": driver_name,
    }
