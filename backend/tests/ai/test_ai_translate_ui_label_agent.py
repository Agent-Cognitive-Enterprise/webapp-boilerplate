import pytest

from ai import ai_translate_ui_label_agent as agent


@pytest.mark.asyncio
async def test_translate_returns_english_without_provider_calls(monkeypatch):
    openai_called = {"value": False}
    deepseek_called = {"value": False}

    async def _openai(*args, **kwargs):
        openai_called["value"] = True
        return "unused"

    async def _deepseek(*args, **kwargs):
        deepseek_called["value"] = True
        return "unused"

    async def _key(provider: str):
        return None

    monkeypatch.setattr(agent, "get_openai_response", _openai)
    monkeypatch.setattr(agent, "get_deepseek_response", _deepseek)
    monkeypatch.setattr(agent, "get_provider_api_key_from_db", _key)

    result = await agent.translate_english_to_locale(
        key="setup.field.site_name",
        value_en="Site name",
        locale="en",
    )

    assert result == "Site name"
    assert openai_called["value"] is False
    assert deepseek_called["value"] is False


@pytest.mark.asyncio
async def test_translate_uses_openai_when_available(monkeypatch):
    async def _openai(*args, **kwargs):
        return "Nom du site"

    async def _deepseek(*args, **kwargs):
        raise AssertionError("DeepSeek fallback should not run when OpenAI succeeds")

    async def _key(provider: str):
        if provider == "openai":
            return "openai-key"
        return None

    monkeypatch.setattr(agent, "get_openai_response", _openai)
    monkeypatch.setattr(agent, "get_deepseek_response", _deepseek)
    monkeypatch.setattr(agent, "get_provider_api_key_from_db", _key)

    result = await agent.translate_english_to_locale(
        key="setup.field.site_name",
        value_en="Site name",
        locale="fr",
    )

    assert result == "Nom du site"


@pytest.mark.asyncio
async def test_translate_falls_back_to_deepseek_when_openai_fails(monkeypatch):
    async def _openai(*args, **kwargs):
        raise RuntimeError("OpenAI unavailable")

    async def _deepseek(*args, **kwargs):
        return "Nom du site (DS)"

    async def _key(provider: str):
        return "provider-key"

    monkeypatch.setattr(agent, "get_openai_response", _openai)
    monkeypatch.setattr(agent, "get_deepseek_response", _deepseek)
    monkeypatch.setattr(agent, "get_provider_api_key_from_db", _key)

    result = await agent.translate_english_to_locale(
        key="setup.field.site_name",
        value_en="Site name",
        locale="fr",
    )

    assert result == "Nom du site (DS)"


@pytest.mark.asyncio
async def test_translate_returns_empty_when_no_provider_keys_configured(monkeypatch):
    openai_called = {"value": False}
    deepseek_called = {"value": False}

    async def _openai(*args, **kwargs):
        openai_called["value"] = True
        return "unused"

    async def _deepseek(*args, **kwargs):
        deepseek_called["value"] = True
        return "unused"

    async def _key(provider: str):
        return None

    monkeypatch.setattr(agent, "get_openai_response", _openai)
    monkeypatch.setattr(agent, "get_deepseek_response", _deepseek)
    monkeypatch.setattr(agent, "get_provider_api_key_from_db", _key)

    result = await agent.translate_english_to_locale(
        key="setup.field.site_name",
        value_en="Site name",
        locale="fr",
    )

    assert result == ""
    assert openai_called["value"] is False
    assert deepseek_called["value"] is False
