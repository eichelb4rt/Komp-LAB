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


def str_to_chars(string: str) -> list[Char]:
    return [c for c in string]


def chars_to_str(chars: list[Char]):
    return "".join(chars)


def is_endstate(state: int | EndStates):
    return type(state) == EndStates


class TransitionFunction:
    def __init__(self):
        self.__transitions: dict[TransitionIn, TransitionOut] = {}

    def get(self, state: int, char: Char) -> TransitionOut:
        return self.__transitions[(state, char)]

    def __repr__(self) -> str:
        return tabulate([[state_in, char_in, state_out if type(state_out) == int else state_out.value, char_out, dir_out.value] for (state_in, char_in), (state_out, char_out, dir_out) in self.__transitions.items()],
                        headers=["state in", "char in", "state out", "char out", "direction"],
                        colalign=["center"] * 5,
                        tablefmt='simple_grid')

    def __add(self, input: TransitionIn, output: TransitionOut):
        self.__transitions[input] = output

    @staticmethod
    def from_file(filename: str) -> Self:
        fun = TransitionFunction()
        with open(filename, 'r') as f:
            firstline = f.readline()
            n_states, n_lines = [int(c) for c in firstline.split(" ")]
            for _ in range(n_lines):
                fun.__add(*TransitionFunction.parse_line(f.readline()))
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
    def __init__(self, n_states: int, transition_function: TransitionFunction) -> None:
        # TODO: do sth with this?
        self.n_states = n_states
        self.transition_function = transition_function
        self.tape: list[Char] = ['S', '_']
        self.head: int = 1
        self.state: int | EndStates = 0

    def read(self) -> Char:
        return self.tape[self.head]
    
    def write(self, char: Char):
        self.tape[self.head] = char

    def run(self, input: str | list[Char]) -> EndStates:
        # convert char list to str
        if type(input) == list[Char]:
            input = chars_to_str(input)
        # put input on tape in between and initialize head and state
        self.tape = str_to_chars(f"S{input}_")
        self.head = 1
        self.state = 0
        # run until in end state
        while not is_endstate(self.state):
            # find out what needs to happen
            char = self.read()
            next_state, write_char, step_dir = self.transition_function.get(self.state, char)
            # make it happen
            self.state = next_state
            self.write(write_char)
            # move head
            if step_dir == Directions.L:
                self.head -= 1
            elif step_dir == Directions.R:
                self.head += 1
            # expand tape if necessary (we don't actually have infinite memory)
            if self.head >= len(self.tape):
                self.tape.append('_')
            # that should not happen, but it will if your turing machine is weird
            if self.head < 0:
                raise IndexError("Head can't go to the left of the start of the tape.")
        return self.state
    
    def accepts(self, input: str | list[Char]) -> bool:
        return self.run(input) == EndStates.ACCEPT
    
    def rejects(self, input: str | list[Char]) -> bool:
        return self.run(input) == EndStates.REJECT
    
    def result(self, input: str | list[Char]) -> str:
        end_state = self.run(input)
        if end_state != EndStates.HALT:
            return ""
        result = chars_to_str(self.tape)
        # remove trailing blanks: convert '_' to whitespace, remove whitespace on the right, convert whitespace back to '_'
        result = result.replace("_", " ").rstrip().replace(" ", "_")
        # return everything but the start symbol
        return result[1:]

    @staticmethod
    def from_file(filename: str) -> Self:
        with open(filename, 'r') as f:
            firstline = f.readline()
            n_states, _ = [int(c) for c in firstline.split(" ")]
        fun = TransitionFunction.from_file(filename)
        return TuringMachine(n_states, fun)


def main():
    assert EndStates.ACCEPT != 'y'
    assert EndStates.ACCEPT == EndStates('y')
    assert EndStates.ACCEPT in EndStates
    state: int | EndStates = 0
    assert type(state) == int
    state = EndStates.ACCEPT
    assert type(state) == EndStates
    fun: TransitionFunction = TransitionFunction.from_file("tm1.txt")
    print(fun)
    assert fun.get(0, '0') == (0, '1', Directions.R)
    tm: TuringMachine = TuringMachine.from_file("tm1.txt")
    assert tm.result("") == ""
    assert tm.result("010010") == "111111"


if __name__ == "__main__":
    main()
