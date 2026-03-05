import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_, select

from models.email_verification_token import EmailVerificationToken


async def create(
    session: AsyncSession,
    user_id: uuid.UUID,
    token_hash: str,
    expires_at: datetime.datetime,
    ip: str | None = None,
    *,
    commit: bool = True,
) -> EmailVerificationToken:
    token = EmailVerificationToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        ip=ip,
    )
    session.add(token)
    if commit:
        await session.commit()
        await session.refresh(token)
    return token


async def get_by_token_hash(
    session: AsyncSession,
    token_hash: str,
) -> EmailVerificationToken | None:
    result = await session.execute(
        select(EmailVerificationToken).where(
            and_(
                EmailVerificationToken.token_hash == token_hash,
                EmailVerificationToken.deleted_at == None,
            )
        )
    )
    return result.scalar_one_or_none()


async def mark_as_used(
    session: AsyncSession,
    token: EmailVerificationToken,
    *,
    commit: bool = True,
) -> EmailVerificationToken:
    token.used = True
    token.used_at = datetime.datetime.now(datetime.UTC)
    session.add(token)
    if commit:
        await session.commit()
        await session.refresh(token)
    return token


async def invalidate_user_tokens(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    commit: bool = True,
) -> int:
    result = await session.execute(
        select(EmailVerificationToken).where(
            and_(
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.used == False,
                EmailVerificationToken.deleted_at == None,
            )
        )
    )
    tokens = result.scalars().all()

    now = datetime.datetime.now(datetime.UTC)
    count = 0
    for token in tokens:
        token.deleted_at = now
        session.add(token)
        count += 1

    if commit and count > 0:
        await session.commit()

    return count
