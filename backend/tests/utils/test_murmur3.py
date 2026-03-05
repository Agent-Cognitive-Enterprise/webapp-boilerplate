# /backend/tests/utils/test_murmur3.py

from utils.murmur3 import murmurhash3_32


# noinspection PyTypeChecker
def test_murmur3():

    assert murmurhash3_32("") == "00000000"
    assert murmurhash3_32("hello") == "248bfa47"
    assert murmurhash3_32("The quick brown fox jumps over the lazy dog") == "2e4ff723"
    assert murmurhash3_32("こんにちは") == "2d2241dc"
    assert murmurhash3_32("😀😃😄😁😆😅😂🤣☺️😊") == "7982c47b"
    assert murmurhash3_32("special chars !@#$%^&*()") == "f0b5f3b3"
    assert murmurhash3_32(str("a" * 1000)) == "a1e5b608"
    assert murmurhash3_32("different seed", seed=42) == "f1d3d5f5"
    assert murmurhash3_32("different seed", seed=12345) == "6ee50f30"
