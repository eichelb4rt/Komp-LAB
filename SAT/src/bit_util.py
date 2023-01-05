def to_bits(n: int) -> list[bool]:
    return list(map(lambda bit_str: bool(int(bit_str)), reversed(bin(n)[2:])))