# /backend/api/helper.py

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from api.helper_access import validate_user_chapter_access as _validate_user_chapter_access
from api.helper_access import validate_user_opus_access as _validate_user_opus_access
from api.helper_access import validate_user_path_access as _validate_user_path_access
from api.helper_text import compute_sha256 as _compute_sha256
from api.helper_text import normalize_text as _normalize_text
from api.helper_text import utf16_to_py_indices as _utf16_to_py_indices
from api.helper_text import utf16_units_for_char as _utf16_units_for_char


async def validate_user_opus_access(
    session: AsyncSession,
    opus_id: UUID,
    user_id: UUID,
):
    return await _validate_user_opus_access(session=session, opus_id=opus_id, user_id=user_id)


async def validate_user_chapter_access(
    session: AsyncSession,
    chapter_id: UUID,
    user_id: UUID,
):
    return await _validate_user_chapter_access(
        session=session,
        chapter_id=chapter_id,
        user_id=user_id,
    )


async def validate_user_path_access(
    user_id: UUID,
    path: str,
):
    return await _validate_user_path_access(user_id=user_id, path=path)


def normalize_text(text: str | None) -> str:
    return _normalize_text(text)


def compute_sha256(text: str) -> str:
    return _compute_sha256(text)


def utf16_units_for_char(ch: str) -> int:
    return _utf16_units_for_char(ch)


def utf16_to_py_indices(
    text: str,
    start_u16: int,
    end_u16: int,
) -> tuple[int, int]:
    return _utf16_to_py_indices(text, start_u16, end_u16)
