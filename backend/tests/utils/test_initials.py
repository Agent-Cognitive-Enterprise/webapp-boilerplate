# /backend/tests/utils/test_initials.py

from faker import Faker

from utils.initials import get_initials


def test_initials():
    faker = Faker()
    for _ in range(1000):
        full_name = faker.name()
        parts = [word for word in full_name.split() if word]

        assert get_initials(full_name) == parts[0][0].upper() + parts[-1][0].upper()
