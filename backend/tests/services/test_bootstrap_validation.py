import pytest

from services.bootstrap_validation import SetupValidationError
from services.bootstrap_validation import merged_supported_locales
from services.bootstrap_validation import normalize_supported_locales


def test_normalize_supported_locales_deduplicates_and_validates_default() -> None:
    default_locale, supported = normalize_supported_locales(
        default_locale="en",
        supported_locales=["en", "fr", "en"],
    )

    assert default_locale == "en"
    assert supported == ["en", "fr"]


def test_normalize_supported_locales_requires_default_in_supported() -> None:
    with pytest.raises(SetupValidationError):
        normalize_supported_locales(
            default_locale="sk",
            supported_locales=["en", "fr"],
        )


def test_merged_supported_locales_appends_seed_locales_without_duplicates() -> None:
    merged = merged_supported_locales(["en", "fr"])

    assert "en" in merged
    assert "fr" in merged
    assert len(merged) == len(set(merged))
