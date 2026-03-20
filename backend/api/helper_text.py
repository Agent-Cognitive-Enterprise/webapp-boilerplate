import hashlib
import unicodedata
from typing import Optional


def normalize_text(text: Optional[str]) -> str:
    if text is None:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return unicodedata.normalize("NFC", text)


def compute_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def utf16_units_for_char(ch: str) -> int:
    return 2 if ord(ch) >= 0x10000 else 1


def utf16_to_py_indices(
    text: str,
    start_u16: int,
    end_u16: int,
) -> tuple[int, int]:
    from bisect import bisect_left, bisect_right

    if start_u16 < 0:
        start_u16 = 0
    if end_u16 < start_u16:
        end_u16 = start_u16

    has_astral = any(ord(c) >= 0x10000 for c in text)
    if not has_astral:
        n = len(text)
        return min(start_u16, n), min(end_u16, n)

    units_prefix = [0]
    units_seen = 0
    for ch in text:
        units_seen += utf16_units_for_char(ch)
        units_prefix.append(units_seen)

    n = len(text)
    cp_index_start = bisect_right(units_prefix, start_u16) - 1
    if cp_index_start < 0:
        cp_index_start = 0
    elif cp_index_start > n:
        cp_index_start = n

    cp_index_end = bisect_left(units_prefix, end_u16)
    if cp_index_end < 0:
        cp_index_end = 0
    elif cp_index_end > n:
        cp_index_end = n

    if cp_index_end < cp_index_start:
        cp_index_end = cp_index_start

    return cp_index_start, cp_index_end
