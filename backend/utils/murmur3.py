# /backend/utils/murmur3.py

import unicodedata


def murmurhash3_32(key: str, seed: int = 0) -> str:
    key = unicodedata.normalize("NFKC", key or "")
    data = key.encode("utf-8")
    length = len(data)
    h1 = seed & 0xFFFFFFFF

    c1 = 0xCC9E2D51
    c2 = 0x1B873593

    i = 0
    while i + 4 <= length:
        k1 = int.from_bytes(data[i : i + 4], "little")
        i += 4
        k1 = (k1 * c1) & 0xFFFFFFFF
        k1 = ((k1 << 15) | (k1 >> 17)) & 0xFFFFFFFF
        k1 = (k1 * c2) & 0xFFFFFFFF

        h1 ^= k1
        h1 = ((h1 << 13) | (h1 >> 19)) & 0xFFFFFFFF
        h1 = (h1 * 5 + 0xE6546B64) & 0xFFFFFFFF

    k1 = 0
    rem = length & 3
    if rem:
        tail = data[-rem:]
        for shift, b in enumerate(tail):
            k1 |= b << (shift * 8)
        k1 = (k1 * c1) & 0xFFFFFFFF
        k1 = ((k1 << 15) | (k1 >> 17)) & 0xFFFFFFFF
        k1 = (k1 * c2) & 0xFFFFFFFF
        h1 ^= k1

    h1 ^= length
    h1 ^= h1 >> 16
    h1 = (h1 * 0x85EBCA6B) & 0xFFFFFFFF
    h1 ^= h1 >> 13
    h1 = (h1 * 0xC2B2AE35) & 0xFFFFFFFF
    h1 ^= h1 >> 16

    return f"{h1:08x}"
