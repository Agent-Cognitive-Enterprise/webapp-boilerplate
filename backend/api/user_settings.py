# /backend/api/user_settings.py

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from auth.auth_handler import get_current_user
from schemas.user_settings import UserSettingsIn, UserSettingsOut
from crud.user_settings import upsert_user_settings, get_user_settings
from utils.db import get_session
from i18n.messages import msg


router = APIRouter()


@router.post("/user-settings", response_model=UserSettingsOut | None)
async def post_or_get_user_settings(
    data: UserSettingsIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """
    - If `data.settings` is provided -> upsert (insert/update/reactivate)
    - If `data.settings` is None -> retrieve settings for the route
    """
    if not current_user or not hasattr(current_user, "id"):
        raise HTTPException(
            status_code=401,
            detail=msg(
                request=request,
                key="user_settings.unauthorized",
                default="Unauthorized",
            ),
        )

    user_id: UUID = current_user.id

    # Upsert if settings are provided
    if data.settings is not None:

        return await upsert_user_settings(session=session, user_id=user_id, data=data)

    # Otherwise get
    settings = await get_user_settings(
        session=session, user_id=user_id, route=data.route
    )

    return settings or None
