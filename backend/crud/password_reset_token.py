# /backend/crud/password_reset_token.py

import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, and_

from models.password_reset_token import PasswordResetToken


async def create(
    session: AsyncSession,
    user_id: uuid.UUID,
    token_hash: str,
    expires_at: datetime.datetime,
    ip: str = None,
) -> PasswordResetToken:
    """Create a new password reset token."""
    reset_token = PasswordResetToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        ip=ip,
    )
    session.add(reset_token)
    await session.commit()
    await session.refresh(reset_token)
    return reset_token


async def get_by_token_hash(
    session: AsyncSession,
    token_hash: str,
) -> PasswordResetToken | None:
    """Get a password reset token by its hash."""
    result = await session.execute(
        select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.deleted_at == None,
            )
        )
    )
    return result.scalar_one_or_none()


async def mark_as_used(
    session: AsyncSession,
    reset_token: PasswordResetToken,
) -> PasswordResetToken:
    """Mark a password reset token as used."""
    reset_token.used = True
    reset_token.used_at = datetime.datetime.now(datetime.UTC)
    session.add(reset_token)
    await session.commit()
    await session.refresh(reset_token)
    return reset_token


async def invalidate_user_tokens(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> int:
    """Soft delete all unused password reset tokens for a user."""
    result = await session.execute(
        select(PasswordResetToken).where(
            and_(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used == False,
                PasswordResetToken.deleted_at == None,
            )
        )
    )
    tokens = result.scalars().all()

    count = 0
    now = datetime.datetime.now(datetime.UTC)
    for token in tokens:
        token.deleted_at = now
        session.add(token)
        count += 1

    if count > 0:
        await session.commit()

    return count
