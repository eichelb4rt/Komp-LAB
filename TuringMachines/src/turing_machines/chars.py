# just to not confuse elements of the alphabet with actual strings
Char = str


def str_to_chars(string: str) -> list[Char]:
    return [c for c in string]


def chars_to_str(chars: list[Char]) -> str:
    return "".join(chars)


# multichars are separated by "|"

def str_to_multistr(string: str) -> str:
    """Converts a string to a multistr (chars separated by '|')."""

    if "|" in string:
        return string
    return "|".join([c for c in string])


def str_to_multichars(string: str) -> list[Char]:
    return string.split("|")


def multichars_to_str(chars: list[Char]) -> str:
    return "|".join(chars)
