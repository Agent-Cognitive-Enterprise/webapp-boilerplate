from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from api import ui_label_read_handlers
from api import ui_label_write_handlers


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/ui-label",
            "headers": [],
        }
    )


@pytest.mark.asyncio
async def test_handle_get_action_returns_no_changes_when_hash_matches(monkeypatch):
    async def _get_or_create(**_kwargs):
        return SimpleNamespace(values_hash="hash-1"), None

    async def _get_list_by_locale(**_kwargs):
        raise AssertionError("labels should not be loaded when hashes match")

    monkeypatch.setattr(
        ui_label_read_handlers,
        "get_or_create_locale_metadata",
        _get_or_create,
    )
    monkeypatch.setattr(
        ui_label_read_handlers,
        "get_list_by_locale",
        _get_list_by_locale,
    )

    result = await ui_label_read_handlers.handle_get_action(
        request=_request(),
        session=object(),
        locale="en",
        values_hash="hash-1",
    )

    assert result.success is True
    assert result.message == "no changes"
    assert result.data == {"values_hash": "hash-1"}


@pytest.mark.asyncio
async def test_handle_add_action_schedules_translation_for_missing_label(monkeypatch):
    scheduled = []

    async def _get_by_key_locale(**_kwargs):
        return None

    async def _schedule_translation(**kwargs):
        scheduled.append(kwargs)

    monkeypatch.setattr(
        ui_label_write_handlers,
        "get_by_key_locale",
        _get_by_key_locale,
    )

    result = await ui_label_write_handlers.handle_add_action(
        request=_request(),
        session=object(),
        locale="fr",
        key="greeting.hello",
        schedule_translation=_schedule_translation,
    )

    assert result.success is True
    assert result.message == "scheduled for translation"
    assert scheduled == [{"key": "greeting.hello", "target_locale": "fr"}]


@pytest.mark.asyncio
async def test_handle_suggest_action_raises_unauthorized_when_user_missing():
    async def _get_current_user(**_kwargs):
        return None

    with pytest.raises(HTTPException) as exc_info:
        await ui_label_write_handlers.handle_suggest_action(
            request=_request(),
            session=object(),
            action_input=ui_label_write_handlers.SuggestActionInput(
                token="bad",
                locale="en",
                key="login.button",
                value="Sign In",
            ),
            dependencies=ui_label_write_handlers.SuggestActionDependencies(
                get_current_user=_get_current_user,
                schedule_suggestion_evaluation=lambda **_kwargs: None,
            ),
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Unauthorized"


@pytest.mark.asyncio
async def test_handle_suggest_action_schedules_evaluation_for_changed_value(monkeypatch):
    scheduled = []

    async def _get_current_user(**_kwargs):
        return SimpleNamespace(id=99)

    async def _get_by_key_locale(**_kwargs):
        return SimpleNamespace(id=10, value="Log in")

    async def _create_suggestion(**_kwargs):
        return SimpleNamespace(value="Sign In")

    async def _schedule_suggestion_evaluation(**kwargs):
        scheduled.append(kwargs["ui_label"].id)

    monkeypatch.setattr(
        ui_label_write_handlers,
        "get_by_key_locale",
        _get_by_key_locale,
    )
    monkeypatch.setattr(
        ui_label_write_handlers,
        "create_suggestion",
        _create_suggestion,
    )

    result = await ui_label_write_handlers.handle_suggest_action(
        request=_request(),
        session=object(),
        action_input=ui_label_write_handlers.SuggestActionInput(
            token="good",
            locale="en",
            key="login.button",
            value="Sign In",
        ),
        dependencies=ui_label_write_handlers.SuggestActionDependencies(
            get_current_user=_get_current_user,
            schedule_suggestion_evaluation=_schedule_suggestion_evaluation,
        ),
    )

    assert result.success is True
    assert result.message == "suggestion submitted"
    assert scheduled == [10]
