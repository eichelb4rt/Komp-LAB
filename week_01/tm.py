import re
from enum import Enum
from tabulate import tabulate
from typing import Literal, Self


class EndStates(Enum):
    ACCEPT = 'y'
    REJECT = 'n'
    HALT = 'h'


END_STATE_CHARS = [state.value for state in EndStates]


class Directions(Enum):
    L = 'L'
    N = 'N'
    R = 'R'


Char = Literal['S', '_', '0', '1']
# input to transition function: state and character
TransitionIn = tuple[int, Char]
# output of transtion function: state (+ end states), character (only writeable ones), direction
TransitionOut = tuple[int | EndStates, Char, Directions]


class TransitionFunction:
    def __init__(self):
        self.transitions: dict[TransitionIn, TransitionOut] = {}

    def add(self, input: TransitionIn, output: TransitionOut):
        self.transitions[input] = output

    def __repr__(self) -> str:
        return tabulate([[state_in, char_in, state_out if type(state_out) == int else state_out.value, char_out, dir_out.value] for (state_in, char_in), (state_out, char_out, dir_out) in self.transitions.items()],
                        headers=["state in", "char in", "state out", "char out", "direction"],
                        colalign=["center"] * 5,
                        tablefmt='simple_grid')

    @staticmethod
    def from_file(filename: str) -> Self:
        fun = TransitionFunction()
        with open(filename, 'r') as f:
            firstline = f.readline()
            n_states, n_lines = [int(c) for c in firstline.split(" ")]
            for _ in range(n_lines):
                fun.add(*TransitionFunction.parse_line(f.readline()))
        # TODO: make sure that only the said states are actually included?
        return fun

    @staticmethod
    def parse_line(line: str) -> tuple[TransitionIn, TransitionOut]:
        # remove all whitespace and line breaks
        line = re.sub(r"\s+", "", line)
        # read entries and make sure it's the right amount
        entries = line.split(",")
        assert len(entries) == 5, f"Error in processing line: {line} - not 5 entries."
        state_in, char_in, state_out, char_out, dir_out = entries
        state_in = int(state_in)
        state_out = int(state_out) if state_out not in END_STATE_CHARS else EndStates(state_out)
        dir_out = Directions(dir_out)
        # build transition entry
        trans_in: TransitionIn = (state_in, char_in)
        trans_out: TransitionOut = (state_out, char_out, dir_out)
        return trans_in, trans_out


class TuringMachine:
    def __init__(self, n_states: int, transition_function) -> None:
        pass


def main():
    assert EndStates.ACCEPT != 'y'
    assert EndStates.ACCEPT == EndStates('y')
    abc = TransitionFunction.from_file("tm1.txt")
    print(abc)


if __name__ == "__main__":
    main()
