# /backend/utils/password_validator.py

import re
from typing import List, Tuple


def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password meets security requirements.

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Length check
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    # Uppercase check
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")

    # Lowercase check
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")

    # Digit check
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")

    # Special character check
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;\'`~]', password):
        errors.append("Password must contain at least one special character")

    # Common password check (basic list)
    common_passwords = {
        'password', 'password123', '12345678', 'qwerty', 'abc123',
        'monkey', '1234567890', 'letmein', 'trustno1', 'dragon',
        'baseball', 'iloveyou', 'master', 'sunshine', 'ashley',
        'bailey', 'passw0rd', 'shadow', '123123', '654321'
    }

    if password.lower() in common_passwords:
        errors.append("Password is too common. Please choose a stronger password")

    is_valid = len(errors) == 0
    return is_valid, errors
