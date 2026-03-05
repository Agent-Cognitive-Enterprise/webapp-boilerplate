from fastapi import Request

from i18n.messages import get_message, resolve_locale


def _request_with_accept_language(value: str) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"accept-language", value.encode("utf-8"))],
    }
    return Request(scope)


def test_resolve_locale_prefers_full_locale_then_language_prefix() -> None:
    assert resolve_locale(_request_with_accept_language("pt-BR,pt;q=0.9")) == "pt-BR"
    assert resolve_locale(_request_with_accept_language("de-DE,de;q=0.8")) == "de"


def test_get_message_falls_back_to_english_when_key_missing() -> None:
    value = get_message(
        key="non.existent.key",
        locale="fr",
        default="fallback",
    )
    assert value == "fallback"


def test_get_message_returns_localized_value() -> None:
    value = get_message(
        key="auth.incorrect_credentials",
        locale="es",
        default="Incorrect email or password",
    )
    assert value != ""
