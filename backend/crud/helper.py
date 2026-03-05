# /backend/crud/helper.py
import re
import unicodedata

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


async def is_connected(session: AsyncSession) -> bool:
    """
    Check if the database session is connected.
    """
    try:
        await session.execute(text("SELECT 1"))
        await session.rollback()

        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")

        return False


# noinspection SpellCheckingInspection
def normalize_ui_label_value(value: str) -> str:
    """
    Normalise suggestion value for deduplication:
    - Unicode NFKC normalization
    - Trim leading/trailing whitespace
    - Collapse multiple internal whitespace to single spaces
    """
    if value is None:
        return ""
    normalized_value = unicodedata.normalize("NFKC", value).strip()
    # Collapse any run of whitespace (spaces, tabs, newlines) to a single space
    return re.sub(r"\s+", " ", normalized_value)
