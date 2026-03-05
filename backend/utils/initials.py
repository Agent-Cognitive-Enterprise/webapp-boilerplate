# /backend/utils/initials.py


def get_initials(full_name: str) -> str:
    """
    Extracts the initials from a full name. Get the first letter of the first word and last word
    """

    return (full_name.split()[0][0] + full_name.split()[-1][0]).upper()
