# /backend/api/health.py

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from crud.helper import is_connected
from settings import APP_NAME
from services.system_settings import get_system_settings_row
from utils.db import get_session

logger = logging.getLogger(__name__)

router = APIRouter()
SCHEMA_UNAVAILABLE_HINT = (
    "Database schema is unavailable or out of date. "
    "Run `alembic upgrade head` before serving requests."
)
SCHEMA_ERROR_PATTERNS = (
    "no such table",
    "no such column",
    "has no column named",
    "undefinedtable",
    "undefinedcolumn",
)


class AppVersion:
    version: str = "0.1.6"


def _is_schema_unavailable_error(exc: SQLAlchemyError) -> bool:
    message = str(exc).lower()
    if any(pattern in message for pattern in SCHEMA_ERROR_PATTERNS):
        return True
    if "relation " in message and "does not exist" in message:
        return True
    return "column " in message and "does not exist" in message


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

    try:
        settings = await get_system_settings_row(session=session, create_if_missing=False)
    except SQLAlchemyError as exc:
        if not _is_schema_unavailable_error(exc):
            raise

        logger.warning("Health check failed because the database schema is unavailable: %s", exc)
        return JSONResponse(
            status_code=503,
            content={
                "status": "Unavailable",
                "detail": SCHEMA_UNAVAILABLE_HINT,
                "database_driver": driver_name,
            },
        )

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
