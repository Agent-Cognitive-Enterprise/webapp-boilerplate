# /backend/utils/helper.py

from pydantic import EmailStr, TypeAdapter

_email_adapter = TypeAdapter(EmailStr)


def to_email_str(value: str) -> EmailStr:
    """Validates the string and returns it typed as EmailStr."""
    return _email_adapter.validate_python(value)
