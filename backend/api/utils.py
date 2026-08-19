import secrets
import string


def generate_short_link():
    characters = string.ascii_letters + string.digits

    return ''.join(
        secrets.choice(characters)
        for _ in range(3)
    )
