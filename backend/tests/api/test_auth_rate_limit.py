from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from api.auth_shared import check_rate_limit
from models.auth_rate_limit_event import AuthRateLimitEvent
import api.auth_shared as auth_shared


@pytest.mark.asyncio
async def test_check_rate_limit_records_attempts_and_blocks_at_limit(
    session: AsyncSession,
    monkeypatch,
) -> None:
    monkeypatch.setattr(auth_shared, "AUTH_RATE_LIMIT_ENABLED", True)
    monkeypatch.setitem(auth_shared._RATE_LIMITS, "token", (2, 3600))

    await check_rate_limit(session=session, action="token", ip="203.0.113.10")
    await check_rate_limit(session=session, action="token", ip="203.0.113.10")

    with pytest.raises(HTTPException) as exc_info:
        await check_rate_limit(session=session, action="token", ip="203.0.113.10")

    assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    events = (
        await session.execute(
            select(AuthRateLimitEvent).where(
                AuthRateLimitEvent.action == "token",
                AuthRateLimitEvent.bucket_key == "token:203.0.113.10",
            )
        )
    ).scalars().all()

    assert len(events) == 2


@pytest.mark.asyncio
async def test_check_rate_limit_scopes_buckets_by_action_and_ip(
    session: AsyncSession,
    monkeypatch,
) -> None:
    monkeypatch.setattr(auth_shared, "AUTH_RATE_LIMIT_ENABLED", True)
    monkeypatch.setitem(auth_shared._RATE_LIMITS, "token", (1, 3600))
    monkeypatch.setitem(auth_shared._RATE_LIMITS, "refresh", (1, 3600))

    await check_rate_limit(session=session, action="token", ip="203.0.113.11")
    await check_rate_limit(session=session, action="token", ip="203.0.113.12")
    await check_rate_limit(session=session, action="refresh", ip="203.0.113.11")

    with pytest.raises(HTTPException):
        await check_rate_limit(session=session, action="token", ip="203.0.113.11")


@pytest.mark.asyncio
async def test_check_rate_limit_discards_expired_events(
    session: AsyncSession,
    monkeypatch,
) -> None:
    monkeypatch.setattr(auth_shared, "AUTH_RATE_LIMIT_ENABLED", True)
    monkeypatch.setitem(auth_shared._RATE_LIMITS, "token", (1, 60))

    old_event = AuthRateLimitEvent(
        action="token",
        bucket_key="token:203.0.113.13",
        created_at=(datetime.now(timezone.utc) - timedelta(minutes=5)).replace(
            tzinfo=None
        ),
        updated_at=(datetime.now(timezone.utc) - timedelta(minutes=5)).replace(
            tzinfo=None
        ),
    )
    session.add(old_event)
    await session.commit()

    await check_rate_limit(session=session, action="token", ip="203.0.113.13")

    events = (
        await session.execute(
            select(AuthRateLimitEvent).where(
                AuthRateLimitEvent.action == "token",
                AuthRateLimitEvent.bucket_key == "token:203.0.113.13",
            )
        )
    ).scalars().all()

    assert len(events) == 1
    assert events[0].id != old_event.id
