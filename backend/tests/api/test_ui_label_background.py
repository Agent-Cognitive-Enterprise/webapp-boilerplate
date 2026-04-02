from types import SimpleNamespace

import pytest

from api import ui_label_background


@pytest.mark.asyncio
async def test_schedule_translation_task_skips_worker_when_background_tasks_disabled(
    monkeypatch,
) -> None:
    scheduled: list[object] = []

    def _create_task(task):
        scheduled.append(task)
        return SimpleNamespace()

    monkeypatch.setattr(
        ui_label_background,
        "UI_LABEL_BACKGROUND_TASKS_ENABLED",
        False,
    )
    monkeypatch.setattr(ui_label_background.asyncio, "create_task", _create_task)

    await ui_label_background.schedule_translation_task(
        key="profile.title.user_profile",
        target_locale="fr",
        session_factory=lambda: (_ for _ in ()).throw(
            AssertionError("session factory should not run when disabled")
        ),
        get_label_by_key_locale=lambda **_kwargs: None,
        create_label=lambda **_kwargs: None,
        get_labels_by_locale=lambda **_kwargs: [],
        update_values_hash=lambda **_kwargs: None,
        snake_key_to_english_value=lambda **_kwargs: "Profile",
        translate_english_to_locale=lambda **_kwargs: "Profil",
    )

    assert scheduled == []


@pytest.mark.asyncio
async def test_schedule_suggestion_evaluation_skips_worker_when_background_tasks_disabled(
    monkeypatch,
) -> None:
    scheduled: list[object] = []

    def _create_task(task):
        scheduled.append(task)
        return SimpleNamespace()

    monkeypatch.setattr(
        ui_label_background,
        "UI_LABEL_BACKGROUND_TASKS_ENABLED",
        False,
    )
    monkeypatch.setattr(ui_label_background.asyncio, "create_task", _create_task)

    await ui_label_background.schedule_suggestion_evaluation_task(
        ui_label=SimpleNamespace(
            id=10,
            key="profile.title.user_profile",
            locale="en",
            value="User profile",
        ),
        session_factory=lambda: (_ for _ in ()).throw(
            AssertionError("session factory should not run when disabled")
        ),
        get_labels_by_locale=lambda **_kwargs: [],
        get_label_suggestions=lambda **_kwargs: {},
        evaluate_label_suggestions=lambda **_kwargs: None,
        update_label=lambda **_kwargs: None,
        update_values_hash=lambda **_kwargs: None,
    )

    assert scheduled == []
