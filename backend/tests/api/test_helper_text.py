from api.helper_text import compute_sha256
from api.helper_text import normalize_text
from api.helper_text import utf16_to_py_indices
from api.helper_text import utf16_units_for_char


def test_normalize_text_standardizes_newlines_and_none() -> None:
    assert normalize_text(None) == ""
    assert normalize_text("a\r\nb\rc") == "a\nb\nc"


def test_compute_sha256_is_stable() -> None:
    assert compute_sha256("abc") == (
        "ba7816bf8f01cfea414140de5dae2223"
        "b00361a396177a9cb410ff61f20015ad"
    )


def test_utf16_helpers_handle_astral_characters() -> None:
    text = "A😀B"
    assert utf16_units_for_char("A") == 1
    assert utf16_units_for_char("😀") == 2
    assert utf16_to_py_indices(text, 1, 3) == (1, 2)
