from transitions import Char, chars_to_str, str_to_chars, Directions


class Tape:
    """Represents 1 tape of a Turing Machine."""

    def __init__(self, machine_input: str | list[Char] = None) -> None:
        if machine_input is None:
            # write standard stuff on tape
            self.chars: list[Char] = ['S', '_']
        else:
            # convert char list to str
            if type(machine_input) == list[Char]:
                machine_input = chars_to_str(machine_input)
            # put input on tape in between and initialize head and state
            self.chars = str_to_chars(f"S{machine_input}_")
        self.head = 1

    def read(self) -> Char:
        return self.chars[self.head]

    def write(self, char: Char):
        # that should not happen, but it will if your turing machine is weird
        if self.read() == 'S' and char != 'S':
            raise RuntimeError("Start symbol can't be overwritten.")
        self.chars[self.head] = char

    def move(self, direction: Directions):
        if direction == Directions.L:
            self.head -= 1
        elif direction == Directions.R:
            self.head += 1
        # expand tape if necessary (we don't actually have infinite memory)
        if self.head >= len(self.chars):
            self.chars.append('_')
        # that should not happen, but it will if your turing machine is weird
        if self.head < 0:
            raise IndexError("Head can't go to the left of the start of the tape.")

    def __repr__(self) -> str:
        # S11101_
        #   ^
        return f"{chars_to_str(self.chars)}\n{' ' * self.head}^"
