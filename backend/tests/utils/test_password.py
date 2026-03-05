# /backend/tests/utils/test_password.py

from utils.password import get_password_hash, verify_password

# noinspection SpellCheckingInspection
test_password = "securepassword"
# noinspection SpellCheckingInspection
test_wrong_password = "wrongpassword"


def test_verify_password():
    hashed_password = get_password_hash(test_password)

    assert (
        verify_password(
            test_password,
            hashed_password,
        )
        is True
    )
    # noinspection SpellCheckingInspection
    assert (
        verify_password(
            test_wrong_password,
            hashed_password,
        )
        is False
    )


def test_get_password_hash():
    hashed_password = get_password_hash(test_password)

    assert (
        hashed_password != test_password
    )  # Ensure the hash is different from the plain password
    assert (
        verify_password(
            test_password,
            hashed_password,
        )
        is True
    )  # Verify the hash matches the original password
