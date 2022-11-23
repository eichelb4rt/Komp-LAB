from abc import ABC, abstractmethod
from transitions import Directions
from chars import Char, str_to_chars, str_to_multichars, chars_to_str, multichars_to_str, str_to_multistr


class Tape(ABC):
    def __init__(self, machine_input: str | list[Char] = None):
        if machine_input is None:
            # write standard stuff on tape
            self.chars: list[Char] = ['S', '_']
        else:
            self.write_input(machine_input)
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

    @abstractmethod
    def write_input(self, machine_input: str | list[Char]) -> None:
        pass

    @abstractmethod
    def output(self) -> str:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass


class SingleCharTape(Tape):
    """Represents 1 tape of a Turing Machine."""

    def write_input(self, machine_input: str | list[Char]):
        # convert char list to str
        if type(machine_input) == list[Char]:
            machine_input = chars_to_str(machine_input)
        # put input on tape in between and initialize head and state
        self.chars = str_to_chars(f"S{machine_input}_")

    def output(self) -> str:
        result = chars_to_str(self.chars)
        result = result.replace("_", " ").rstrip().replace(" ", "_")
        return result[1:]

    def __repr__(self) -> str:
        # S11101_
        #   ^
        return f"{chars_to_str(self.chars)}\n{' ' * self.head}^"


class MultiCharTape(Tape):
    def write_input(self, machine_input: str | list[Char]):
        # convert char list to str
        if type(machine_input) == list[Char]:
            machine_input = multichars_to_str(machine_input)
        else:
            machine_input = str_to_multistr(machine_input)
        # put input on tape in between and initialize head and state
        self.chars = str_to_multichars(f"S|{machine_input}|_")

    def output(self) -> str:
        result = multichars_to_str(self.chars)
        result = result.replace("|_", " ").rstrip().replace(" ", "|_")
        return result[2:]

    def __repr__(self) -> str:
        # S11|11|0|11_
        #     ^
        print(self.head)
        print(self.read())
        head_char_pos = len(multichars_to_str(self.chars[:self.head])) + 1
        return f"{multichars_to_str(self.chars)}\n{' ' * head_char_pos}^"
