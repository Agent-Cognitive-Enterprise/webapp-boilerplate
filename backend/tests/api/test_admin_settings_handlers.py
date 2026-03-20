from api.admin_settings_handlers import normalize_optional_text


def test_normalize_optional_text_strips_and_drops_empty_values() -> None:
    assert normalize_optional_text(None) is None
    assert normalize_optional_text("   ") is None
    assert normalize_optional_text("  value  ") == "value"
