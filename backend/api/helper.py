# /backend/api/helper.py

import hashlib
import unicodedata
from typing import Optional, Tuple
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from crud.opus_contributor import is_contributor
from i18n.messages import msg
from models.chapter import Chapter
from utils.db import AsyncSessionLocal


async def validate_user_opus_access(
    session: AsyncSession,
    opus_id: UUID,
    user_id: UUID,
):
    """
    Validate if a user has access to a specified opus by checking whether the user
    is a contributor. If the user is not a contributor, an HTTP 403 Forbidden
    exception is raised.

    :param session: Async database session is used to perform the access validation
        queries.
    :type session: AsyncSession

    :param opus_id: The unique identifier of the opus to validate against the user's
        access.
    :type opus_id: UUID

    :param user_id: The unique identifier of the user whose access is being validated.
    :type user_id: UUID

    :return: None if the validation passes without raising an exception.
    :rtype: None

    :raises HTTPException: Rose with a status code of 403 if the user is not among
        the contributors of the specified opus.
    """
    # Check whether the current user is among the contributors of the opus
    allowed = await is_contributor(
        session=session,
        opus_id=opus_id,
        user_id=user_id,
    )

    if not allowed:
        raise HTTPException(
            status_code=403,
            detail=msg(
                request=None,
                key="helper.not_contributor",
                default="User is not a contributor to this opus",
            ),
        )


async def validate_user_chapter_access(
    session: AsyncSession,
    chapter_id: UUID,
    user_id: UUID,
):
    """
    Validates whether a user has access to a specific chapter by checking the chapter's
    existence and ensuring the user has access permissions to the related opus.

    This function retrieves the chapter using its `chapter_id` and, if found, validates
    that the user identified by `user_id` has the necessary access to the opus with which
    the chapter is associated. If the chapter does not exist, an HTTP 404 error will be
    raised.

    :param session: Database session used to retrieve chapter and validate permissions
    :type session: AsyncSession
    :param chapter_id: Unique identifier of the chapter to validate
    :type chapter_id: UUID
    :param user_id: Unique identifier of the user whose access is being validated
    :type user_id: UUID
    :return: None. Raises HTTPException with appropriate status if access cannot be validated
    :rtype: None
    """
    db_chapter = await session.get(
        Chapter,
        chapter_id,
    )

    if not db_chapter:
        raise HTTPException(
            status_code=404,
            detail=msg(
                request=None,
                key="helper.chapter_not_found",
                default="Chapter not found",
            ),
        )

    await validate_user_opus_access(
        session=session,
        opus_id=db_chapter.opus_id,
        user_id=user_id,
    )


# noinspection GrazieInspection
def normalize_text(text: Optional[str]) -> str:
    """
    Normalize a given text by standardizing newlines and applying Unicode NFC
    normalization. If the input is None, an empty string is returned.

    :param text: Input string to normalize, or None.
    :type text: Optional[str]
    :return: Normalized string with standardized newlines and NFC normalization.
    :rtype: str
    """
    if text is None:

        return ""
    # Normalize newlines to \n and Unicode to NFC
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    return unicodedata.normalize("NFC", text)


# noinspection GrazieInspection
def compute_sha256(text: str) -> str:
    """
    Computes the SHA-256 hash of the provided input text.

    This function takes a string, encodes it into UTF-8, computes its SHA-256
    hash, and returns the resulting hexadecimal hash as a string.

    :param text: The input string to compute the SHA-256 hash for.
    :type text: str

    :return: The hexadecimal SHA-256 hash of the input text.
    :rtype: str
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# noinspection GrazieInspection
def utf16_units_for_char(ch: str) -> int:
    """
    Determines the number of UTF-16 code units required to represent a single Unicode
    character.

    UTF-16 encoding represents each Unicode character using one or two 16-bit code
    units. Characters falling within the Basic Multilingual Plane (BMP) require a single
    16-bit code unit. Characters outside the BMP, represented as surrogate pairs, require
    two 16-bit code units.

    :param ch: A single Unicode character to evaluate.
    :type ch: str
    :return: The number of UTF-16 code units (1 or 2) needed to represent the given
        Unicode character.
    :rtype: int
    """
    return 2 if ord(ch) >= 0x10000 else 1


# noinspection GrazieInspection
def utf16_to_py_indices(
    text: str,
    start_u16: int,
    end_u16: int,
) -> Tuple[int, int]:
    """
    Converts UTF-16 indices to Python string indices by accounting for surrogate
    pairs and differences between characters' code points and UTF-16 encoding units.

    This function ensures correct indexing in Python strings with respect to UTF-16
    character encoding, handling the cases where surrogate pairs are used
    (e.g., for astral characters) or when the indices may fall outside valid
    ranges of the string.

    :param text: The input string containing text to be indexed.
    :type text: str
    :param start_u16: The starting index in the UTF-16 encoding units.
    :type start_u16: int
    :param end_u16: The ending index in the UTF-16 encoding units.
    :type end_u16: int
    :return: A tuple of two integers, (start_index, end_index), representing
        the computed Python string indices corresponding to the given UTF-16 indices.
    :rtype: Tuple[int, int]
    """
    from bisect import bisect_left, bisect_right

    if start_u16 < 0:
        start_u16 = 0
    if end_u16 < start_u16:
        end_u16 = start_u16

    # Fast path: if no astral characters (no surrogate pairs), units match code points
    has_astral = any(ord(c) >= 0x10000 for c in text)
    if not has_astral:
        n = len(text)
        return min(start_u16, n), min(end_u16, n)

    # Build prefix sums of UTF-16 units: u[i] = total units up to code point i
    u = [0]
    units_seen = 0
    for ch in text:
        units_seen += utf16_units_for_char(ch)
        u.append(units_seen)

    n = len(text)

    # Map start: if inside a character (between u[i] and u[i+1]), choose i
    cp_index_start = bisect_right(u, start_u16) - 1
    if cp_index_start < 0:
        cp_index_start = 0
    elif cp_index_start > n:
        cp_index_start = n

    # Map end: if inside a character, choose i+1 (round up)
    cp_index_end = bisect_left(u, end_u16)
    if cp_index_end < 0:
        cp_index_end = 0
    elif cp_index_end > n:
        cp_index_end = n

    # Ensure non-decreasing indices
    if cp_index_end < cp_index_start:
        cp_index_end = cp_index_start

    return cp_index_start, cp_index_end


# noinspection PyTypeChecker
async def validate_user_path_access(
    user_id: UUID,
    path: str,
):
    if path.startswith("/ludus/opus/") or path.startswith("/ludus/user/"):
        parts = path.split("/")
        if len(parts) < 4:
            raise HTTPException(
                status_code=400,
                detail=msg(
                    request=None,
                    key="helper.invalid_path_format",
                    default="Invalid path format",
                ),
            )
        item_id_str = parts[3]
        try:
            item_id = UUID(item_id_str)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=msg(
                    request=None,
                    key="helper.invalid_path_item_id",
                    default="Invalid item ID in path",
                ),
            )

        if parts[2] == "user" and item_id == user_id:

            return None

        async with AsyncSessionLocal() as session:
            if parts[2] == "opus":
                await validate_user_opus_access(
                    session=session,
                    opus_id=item_id,
                    user_id=user_id,
                )

                return None

    raise HTTPException(
        status_code=403,
        detail=msg(
            request=None,
            key="helper.path_unauthorized",
            default="User is not authorized to access this path",
        ),
    )
