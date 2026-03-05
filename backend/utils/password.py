# /backend/utils/password.py

import hashlib
import bcrypt


_BCRYPT_ROUNDS = 12


def _sha256_hexdigest_bytes(password: str) -> bytes:
    return hashlib.sha256(password.encode()).hexdigest().encode()


def get_password_hash(password: str) -> str:
    """Hash password using bcrypt of SHA256-hexdigest(password).

    Returns a standard bcrypt hash string (e.g., "$2b$12$...").
    """
    prehashed = _sha256_hexdigest_bytes(password)
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(prehashed, salt)

    return hashed.decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored hash.

    Tries legacy prehashed mode first (sha256-hexdigest -> bcrypt). If that fails, it
    falls back to checking plain bcrypt (no pre-hash). Any ValueError from bcrypt
    (e.g., due to >72 byte inputs in plain mode) is treated as a failed check.
    """
    hp_bytes = hashed_password.encode()

    # 1) Preferred / legacy-compatible path: sha256-hexdigest -> bcrypt
    prehashed = _sha256_hexdigest_bytes(plain_password)
    if bcrypt.checkpw(prehashed, hp_bytes):
        return True

    # 2) Fallback: plain -> bcrypt (only if some old records used plain bcrypt)
    try:

        return bcrypt.checkpw(plain_password.encode(), hp_bytes)

    except ValueError:
        # bcrypt v5 raises if input >72 bytes (instead of silently truncating)

        return False
