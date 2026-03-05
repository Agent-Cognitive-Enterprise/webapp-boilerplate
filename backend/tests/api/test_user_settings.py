import pytest
# /backend/tests/api/test_user_settings.py

from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from crud.user_settings import (
    get_user_settings,
    soft_delete_user_settings,
    count_user_settings,
)
from tests.helper import create_test_token_and_user


async def create_test_user_settings_and_token(client, session):
    access_token, db_user = await create_test_token_and_user(session, client)
    route = "/test-route"
    settings_data = {"theme": "dark", "notifications": True}
    # Upsert (insert)
    response = await client.post(
        "/user-settings",
        json={"route": route, "settings": settings_data},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return access_token, db_user, route, settings_data, response


@pytest.mark.asyncio
async def test_post_user_settings_upsert(client: AsyncClient, session: AsyncSession):
    access_token, db_user, route, settings_data, response = (
        await create_test_user_settings_and_token(client, session)
    )

    assert response.status_code == 200

    resp_json = response.json()

    assert resp_json["user_id"] == str(db_user.id)
    assert resp_json["route"] == route
    assert resp_json["settings"] == settings_data

    # Upsert (update)
    new_settings_data = {"theme": "light", "notifications": False}
    response = await client.post(
        "/user-settings",
        json={"route": route, "settings": new_settings_data},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200

    resp_json = response.json()

    assert resp_json["settings"] == new_settings_data


@pytest.mark.asyncio
async def test_post_user_settings_get(client: AsyncClient, session: AsyncSession):
    access_token, db_user, route, settings_data, response = (
        await create_test_user_settings_and_token(client, session)
    )

    # Get
    response = await client.post(
        "/user-settings",
        json={"route": route, "settings": None},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200

    resp_json = response.json()

    assert resp_json["user_id"] == str(db_user.id)
    assert resp_json["route"] == route
    assert resp_json["settings"] == settings_data


@pytest.mark.asyncio
async def test_post_user_settings_unauthorized(client):
    # No user
    response = await client.post(
        "/user-settings",
        json={"route": "/any-route", "settings": {"key": "value"}},
    )
    assert response.status_code == 401
    resp_json = response.json()
    assert resp_json["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_post_user_settings_reactivate(
    client: AsyncClient, session: AsyncSession
):
    access_token, db_user, route, settings_data, response = (
        await create_test_user_settings_and_token(client, session)
    )

    db_user_settings = await get_user_settings(
        session=session, user_id=db_user.id, route=route
    )

    assert db_user_settings is not None
    assert db_user_settings.deleted_at is None

    # Soft-delete
    await soft_delete_user_settings(session=session, user_id=db_user.id, route=route)

    assert db_user_settings.deleted_at is not None

    # Reactivate by posting new settings
    new_settings_data = {"theme": "reactivated", "notifications": True}
    response = await client.post(
        "/user-settings",
        json={"route": route, "settings": new_settings_data},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200

    resp_json = response.json()

    assert resp_json["settings"] == new_settings_data

    db_user_settings = await get_user_settings(
        session=session, user_id=db_user.id, route=route
    )

    assert db_user_settings.deleted_at is None
    assert db_user_settings.settings == new_settings_data

    assert (
        await count_user_settings(session=session, user_id=db_user.id, route=route) == 1
    )


@pytest.mark.asyncio
async def test_post_user_settings_updated_at_changes(
    client: AsyncClient, session: AsyncSession
):
    access_token, db_user, route, settings_data, response = (
        await create_test_user_settings_and_token(client, session)
    )

    db_user_settings = await get_user_settings(
        session=session, user_id=db_user.id, route=route
    )

    first_updated_at = db_user_settings.updated_at

    # Update with new settings
    new_settings_data = {"theme": "light", "notifications": False}
    response = await client.post(
        "/user-settings",
        json={"route": route, "settings": new_settings_data},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    second_resp = response.json()

    db_user_settings = await get_user_settings(
        session=session, user_id=db_user.id, route=route
    )

    second_updated_at = db_user_settings.updated_at

    assert second_updated_at != first_updated_at
    assert second_resp["settings"] == new_settings_data

    assert (
        await count_user_settings(session=session, user_id=db_user.id, route=route) == 1
    )


@pytest.mark.asyncio
async def test_post_user_settings_conflict_insert(
    client: AsyncClient, session: AsyncSession
):
    access_token, db_user, route, settings_data, _ = (
        await create_test_user_settings_and_token(client, session)
    )

    # Insert the same settings again
    response = await client.post(
        "/user-settings",
        json={"route": route, "settings": settings_data},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200

    # Ensure still only one record exists
    assert await count_user_settings(session, db_user.id, route) == 1
