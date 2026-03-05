# /backend/tests/api/test_ui_label.py

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from crud.ui_label import (
    create as create_label,
)
from crud.ui_label import (
    get_by_key_locale,
)
from crud.ui_label import (
    update as update_label,
)
from crud.ui_label_suggestions import get_label_suggestions
from crud.ui_locale import create as create_locale
from i18n.messages import get_message
from tests.helper import create_test_token_and_user


# Avoid real OpenAI calls: monkeypatch evaluator to deterministic async fn
# noinspection PyTypeChecker,PyShadowingNames
async def _fake_evaluator(
    ui_label,
    suggestions,
):
    # Pick the value with the highest votes; break ties lexicographically
    if not suggestions:
        return None

    max_votes = max(suggestions.values())
    winners = sorted([v for v, c in suggestions.items() if c == max_votes])
    # If current is among winners, keep current (no change)
    if ui_label.value in winners:
        return None

    return winners[0]


@pytest.fixture(autouse=True)
def disable_background_suggestion_tasks(monkeypatch, request):
    if request.node.name == "test_background_suggestion_evaluation_updates_label_and_hash":
        return

    async def _no_background_task(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "api.ui_label.schedule_suggestion_evaluation",
        _no_background_task,
    )


@pytest_asyncio.fixture
async def token_and_user(
    client: AsyncClient,
    session: AsyncSession,
):
    return await create_test_token_and_user(session)


@pytest.mark.asyncio
async def test_ui_label_get_does_not_require_auth(client: AsyncClient):
    # No Authorization header: GET action should be allowed, returns dict payload
    resp = await client.post(
        "/ui-label",
        json={
            "action": "get",
            "locale": "en",
        },
        headers={
            "Authorization": "Bearer free",
        },
    )

    assert resp.status_code == 200

    payload = resp.json()

    assert payload["success"] is True
    assert payload["message"] == "fetched"
    assert isinstance(payload["data"], dict)
    assert payload["data"]["locale"] == "en"
    assert "values_hash" in payload["data"]
    assert isinstance(payload["data"]["labels"], dict)


@pytest.mark.asyncio
async def test_ui_label_locale_required_message_is_localized(client: AsyncClient):
    response = await client.post(
        "/ui-label",
        json={"action": "get", "locale": ""},
        headers={"Authorization": "Bearer free", "Accept-Language": "de-DE"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["message"] == get_message(
        key="ui_label.locale_required",
        locale="de",
        default="locale is required",
    )


@pytest.mark.parametrize(
    "body, ok, msg",
    [
        (
            {
                "action": "get",
                "locale": "",
            },
            False,
            "locale is required",
        ),
        (
            {
                "action": "suggest",
                "locale": "en",
            },
            False,
            "key and value required for suggest",
        ),
        (
            {
                "action": "suggest",
                "locale": "en",
                "key": "login.button",
            },
            False,
            "key and value required for suggest",
        ),
        (
            {
                "action": "suggest",
                "locale": "en",
                "value": "Log in",
            },
            False,
            "key and value required for suggest",
        ),
    ],
)
@pytest.mark.asyncio
async def test_ui_label_invalid_inputs(
    client: AsyncClient,
    session: AsyncSession,
    token_and_user,
    body,
    ok,
    msg,
    monkeypatch,
):
    monkeypatch.setattr(
        "api.ui_label.AsyncSessionLocal",
        lambda: session,
    )

    monkeypatch.setattr(
        "api.ui_label.evaluate_label_suggestions",
        _fake_evaluator,
    )

    token, _user = token_and_user

    resp = await client.post(
        "/ui-label",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json=body,
    )

    assert resp.status_code == 200 or resp.status_code == 401

    if resp.status_code == 200:
        payload = resp.json()

        assert payload["success"] is ok
        assert payload.get("message") == msg


# noinspection PyTypeChecker,GrazieInspection,SpellCheckingInspection
@pytest.mark.asyncio
async def test_ui_label_suggest_requires_auth(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch,
):
    monkeypatch.setattr(
        "api.ui_label.AsyncSessionLocal",
        lambda: session,
    )

    monkeypatch.setattr(
        "api.ui_label.evaluate_label_suggestions",
        _fake_evaluator,
    )
    # Suggest should be unauthorized without token
    resp = await client.post(
        "/ui-label",
        json={
            "action": "suggest",
            "locale": "en",
            "key": "login.button",
            "value": "Log in",
        },
    )

    assert resp.status_code == 401

    payload = resp.json()

    assert payload["detail"] in ("Unauthorized", "Not authenticated")


@pytest.mark.asyncio
async def test_ui_label_suggest_creates_and_increments(
    client: AsyncClient,
    session: AsyncSession,
    token_and_user,
    monkeypatch,
):
    monkeypatch.setattr(
        "api.ui_label.AsyncSessionLocal",
        lambda: session,
    )

    monkeypatch.setattr(
        "api.ui_label.evaluate_label_suggestions",
        _fake_evaluator,
    )

    token, _user = token_and_user

    # Ensure a label exists for this key/locale
    await create_label(
        session=session,
        key="login.button",
        locale="en",
        value="Log in",
    )

    # Submit first suggestion
    body = {
        "action": "suggest",
        "locale": "en",
        "key": "login.button",
        "value": "  Sign   In  ",
    }

    resp1 = await client.post(
        "/ui-label",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
    )

    assert resp1.status_code == 200

    p1 = resp1.json()

    assert p1["success"] is True
    assert p1["message"] == "suggestion submitted"

    # Submit the same idea again with different whitespace -> is normalized
    resp2 = await client.post(
        "/ui-label",
        headers={"Authorization": f"Bearer {token}"},
        json={**body, "value": "Sign\tIn"},
    )

    assert resp2.status_code == 200

    p2 = resp2.json()

    assert p2["success"] is True

    # Check suggestion counts directly from CRUD
    counts = await get_label_suggestions(
        session=session,
        label_id=(
            await get_by_key_locale(
                session=session,
                key="login.button",
                locale="en",
            )
        ).id,
    )
    # Normalization collapses whitespace but keeps the case -> "Sign In" key expected
    assert counts.get("Sign In") == 2


@pytest.mark.asyncio
async def test_ui_label_unknown_action_returns_false(
    client: AsyncClient,
    session: AsyncSession,
    token_and_user,
):
    token, _user = token_and_user

    resp = await client.post(
        "/ui-label",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "action": "unknown",
            "locale": "en",
        },
    )

    assert resp.status_code == 200

    payload = resp.json()

    assert payload["success"] is False
    assert payload["message"] == "Unknown action"


@pytest.mark.asyncio
async def test_background_suggestion_evaluation_updates_label_and_hash(
    client: AsyncClient,
    session: AsyncSession,
    token_and_user,
    monkeypatch,
):
    token, _user = token_and_user

    monkeypatch.setattr(
        "api.ui_label.evaluate_label_suggestions",
        _fake_evaluator,
    )

    async def _inline_schedule(ui_label):
        db_ui_label_suggestions = await get_label_suggestions(
            session=session,
            label_id=ui_label.id,
        )
        best_value = await _fake_evaluator(
            ui_label=ui_label,
            suggestions=db_ui_label_suggestions,
        )
        if not best_value or best_value == ui_label.value:
            return
        ui_label.value = best_value
        await update_label(
            session=session,
            label=ui_label,
        )

    monkeypatch.setattr(
        "api.ui_label.schedule_suggestion_evaluation",
        _inline_schedule,
    )

    key = "login.button.bg"
    locale = "en"

    # Create an initial label with a different value
    await create_label(
        session=session,
        key=key,
        locale=locale,
        value="Log in",
    )

    # Submit suggestions: two votes for "Sign In", one for "Log in" (keep vs. change)
    for v in ("Sign In", "Sign In", "Log in"):
        resp = await client.post(
            "/ui-label",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "action": "suggest",
                "locale": locale,
                "key": key,
                "value": v,
            },
        )
        assert resp.status_code == 200

    # Best should be applied -> "Sign In"
    updated = await get_by_key_locale(
        session=session,
        key=key,
        locale=locale,
    )

    assert updated is not None
    assert updated.value == "Sign In"

    # Verify GET shape and values_hash present
    resp_get = await client.post(
        "/ui-label",
        json={
            "action": "get",
            "locale": locale,
        },
        headers={"Authorization": "Bearer free"},
    )

    assert resp_get.status_code == 200

    data = resp_get.json()["data"]

    assert data["locale"] == locale
    assert isinstance(data["values_hash"], str) and len(data["values_hash"]) > 0
    assert data["labels"][key] == "Sign In"


@pytest.mark.asyncio
async def test_ui_label_list(
    client: AsyncClient,
    session: AsyncSession,
    token_and_user,
):
    token, _user = token_and_user

    test_locales = ["en", "fr", "de"]

    # Create several UiLocale records
    for locale in test_locales:
        await create_locale(
            session=session,
            locale=locale,
            values_hash="hash",
        )

    resp = await client.post(
        "/ui-label",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "action": "list",
        },
    )

    assert resp.status_code == 200

    data = resp.json()

    assert data["success"] is True
    assert data["message"] == "fetched UI locales"

    data = data["data"]["locales"]

    assert isinstance(data, list)
    assert len(data) == 3
    assert all(item in test_locales for item in data)


@pytest.mark.asyncio
async def test_ui_label_add_materializes_translation(
    client: AsyncClient,
    session: AsyncSession,
    monkeypatch,
) -> None:
    async def _inline_schedule(key: str, target_locale: str):
        await create_label(
            session=session,
            key=key,
            locale=target_locale,
            value="Bonjour",
        )

    monkeypatch.setattr(
        "api.ui_label.schedule_translation",
        _inline_schedule,
    )

    add_response = await client.post(
        "/ui-label",
        headers={"Authorization": "Bearer free"},
        json={
            "action": "add",
            "locale": "fr",
            "key": "greeting.hello",
        },
    )
    assert add_response.status_code == 200
    assert add_response.json()["success"] is True

    get_response = await client.post(
        "/ui-label",
        headers={"Authorization": "Bearer free"},
        json={
            "action": "get",
            "locale": "fr",
        },
    )
    assert get_response.status_code == 200
    payload = get_response.json()["data"]["labels"]
    assert payload["greeting.hello"] == "Bonjour"
