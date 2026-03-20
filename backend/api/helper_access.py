from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from i18n.messages import msg
from utils.db import AsyncSessionLocal


async def validate_user_opus_access(
    session: AsyncSession,
    opus_id: UUID,
    user_id: UUID,
) -> None:
    from crud.opus_contributor import is_contributor

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
) -> None:
    from models.chapter import Chapter

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


async def validate_user_path_access(
    user_id: UUID,
    path: str,
) -> None:
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
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=msg(
                    request=None,
                    key="helper.invalid_path_item_id",
                    default="Invalid item ID in path",
                ),
            ) from exc

        if parts[2] == "user" and item_id == user_id:
            return

        async with AsyncSessionLocal() as session:
            if parts[2] == "opus":
                await validate_user_opus_access(
                    session=session,
                    opus_id=item_id,
                    user_id=user_id,
                )
                return

    raise HTTPException(
        status_code=403,
        detail=msg(
            request=None,
            key="helper.path_unauthorized",
            default="User is not authorized to access this path",
        ),
    )
