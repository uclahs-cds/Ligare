from random import choices
from string import ascii_letters


def get_random_str(k: int | None = None, characters: str = ascii_letters):
    if k is None:
        k = len(characters)
    return "".join(choices(characters, k=k))
