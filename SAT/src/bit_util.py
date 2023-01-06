def to_bits(n: int) -> list[bool]:
    return list(map(lambda bit_str: bool(int(bit_str)), reversed(bin(n)[2:])))


def to_number(sum_bits: list[bool]) -> int:
    # lowest bit is at sum_bits[0]
    return int("".join([str(int(bit)) for bit in reversed(sum_bits)]), 2)


def pad_right_bits(x: list[int], to_size: int) -> list[int]:
    left_space = to_size - len(x)
    return x + [False] * left_space


def pad_left_bits(x: list[int], to_size: int) -> list[int]:
    left_space = to_size - len(x)
    return [False] * left_space + x
