# /backend/crud/refresh_token.py

from datetime import datetime, timezone
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import and_, col, select

from models.refresh_token import RefreshToken


async def create_refresh_token(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    token_hash: str,
    expires_at,
    rotated_from_id: uuid.UUID | None = None,
    client_binding_hash: str | None = None,
    ip: str | None = None,
    ua: str | None = None,
) -> RefreshToken:
    rt = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        rotated_from_id=rotated_from_id,
        client_binding_hash=client_binding_hash,
        ip=ip,
        user_agent=ua,
    )
    session.add(rt)
    await session.flush()

    return rt


async def get_by_token_hash(
    session: AsyncSession, token_hash: str
) -> RefreshToken | None:
    q = await session.execute(
        select(RefreshToken).where(
            and_(
                RefreshToken.token_hash == token_hash,
                col(RefreshToken.deleted_at).is_(None),
            )
        )
    )

    return q.scalar_one_or_none()


async def mark_used_and_revoke(session: AsyncSession, rt: RefreshToken) -> None:
    rt.used_at = datetime.now(timezone.utc)
    rt.revoked = True
    await session.flush()


async def revoke_token_and_descendants(session: AsyncSession, rt: RefreshToken) -> None:
    # Revoke the token chain starting from the provided token.
    now = datetime.now(timezone.utc)
    queue: list[RefreshToken] = [rt]
    visited: set[uuid.UUID] = set()

    while queue:
        current = queue.pop(0)
        if current.id in visited:
            continue
        visited.add(current.id)

        current.revoked = True
        if current.used_at is None:
            current.used_at = now

        children_result = await session.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.rotated_from_id == current.id,
                    col(RefreshToken.deleted_at).is_(None),
                )
            )
        )
        queue.extend(children_result.scalars().all())

    await session.flush()


async def revoke_all_for_user(session: AsyncSession, user_id: uuid.UUID) -> int:
    """
    Revoke all non-revoked refresh tokens for a user.
    Returns number of tokens revoked.
    """
    result = await session.execute(
        select(RefreshToken).where(
            and_(
                RefreshToken.user_id == user_id,
                col(RefreshToken.revoked).is_(False),
                col(RefreshToken.deleted_at).is_(None),
            )
        )
    )
    tokens = result.scalars().all()
    if not tokens:
        return 0

    now = datetime.now(timezone.utc)
    for token in tokens:
        token.revoked = True
        if token.used_at is None:
            token.used_at = now

    await session.flush()
    return len(tokens)
