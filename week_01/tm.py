import os
import re
import curses
import argparse
from enum import Enum
from tabulate import tabulate
from typing import Literal, Self, TYPE_CHECKING

# this stuff is kinda weird (but it's needed)
if TYPE_CHECKING:
    from _curses import _CursesWindow
    Window = _CursesWindow
else:
    from typing import Any
    Window = Any


class AnimationDirections(Enum):
    LEFT = 'KEY_LEFT'
    RIGHT = 'KEY_RIGHT'


ANIMATION_DIRECTION_STRINGS = [state.value for state in AnimationDirections]


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
        # if we didn't specify this combination, we reject
        if (state, char) not in self.__transitions:
            return (EndStates.REJECT, char, Directions.N)
        # otherwise just return the matching transition
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
    def __init__(self, n_states: int, transition_function: TransitionFunction, logging=False) -> None:
        # TODO: do sth with this? (i'm not using n_states anywhere)
        self.n_states = n_states
        self.transition_function = transition_function
        self.logging = logging
        self.tape: list[Char] = ['S', '_']
        self.head: int = 1
        self.state: int | EndStates = 0
        self.time: int = 0

    def __read(self) -> Char:
        return self.tape[self.head]

    def __write(self, char: Char):
        self.tape[self.head] = char

    def step(self):
        """Does one (1) step for the TM."""

        self.time += 1
        # find out what needs to happen
        char = self.__read()
        next_state, write_char, step_dir = self.transition_function.get(self.state, char)
        # that should not happen, but it will if your turing machine is weird
        if char == 'S' and write_char != 'S':
            raise RuntimeError("Start symbol can't be overwritten.")
        # make it happen
        self.state = next_state
        self.__write(write_char)
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

    def run(self, input: str | list[Char]) -> EndStates:
        """Runs the TM until it is in an end state."""

        # convert char list to str
        if type(input) == list[Char]:
            input = chars_to_str(input)
        # put input on tape in between and initialize head and state
        self.tape = str_to_chars(f"S{input}_")
        self.head = 1
        self.state = 0
        self.time = 0
        # log starting state
        if self.logging:
            print(self)
        # run until in end state
        while not is_endstate(self.state):
            self.step()
            # log current state
            if self.logging:
                print(self)
        return self.state

    def output(self) -> EndStates | str:
        """Returns the output if the TM halts. Otherwise returns end state (accept/reject)."""

        if self.state != EndStates.HALT:
            return self.state
        result = chars_to_str(self.tape)
        # remove trailing blanks: convert '_' to whitespace, remove whitespace on the right, convert whitespace back to '_'
        result = result.replace("_", " ").rstrip().replace(" ", "_")
        # return everything but the start symbol
        return result[1:]

    ################################################################
    # all of these three (3) functions run the turing machine
    ################################################################

    def accepts(self, input: str | list[Char]) -> bool:
        """Runs the TM on the input and finds returns True if the input is accepted by the TM."""

        return self.run(input) == EndStates.ACCEPT

    def rejects(self, input: str | list[Char]) -> bool:
        """Runs the TM on the input and finds returns True if the input is rejected by the TM."""

        return self.run(input) == EndStates.REJECT

    def result(self, input: str | list[Char]) -> str:
        """Runs the TM on the input and finds returns the output if TM halts. Otherwise returns an empty string."""

        # if we didn't halt, but instead accepted or rejected, the result is supposed to be a function output
        if self.run(input) != EndStates.HALT:
            return ""
        return self.output()

    ################################################################
    # animation stuff
    ################################################################

    def __run_animation(self, input: str | list[Char], window: Window) -> EndStates:
        """Runs and animates the TM in a curses window."""

        # convert char list to str
        if type(input) == list[Char]:
            input = chars_to_str(input)
        # put input on tape in between and initialize head and state
        self.tape = str_to_chars(f"S{input}_")
        self.head = 1
        self.state = 0
        self.time = 0

        # animation stuff
        # snapshots of the TM at any given time (just string representations)
        snapshots: list[str] = []
        current_snapshot = 0
        snapshots.append(str(self))
        # cached result of the run of the TM
        result = None
        # display first snapshot
        window.clear()
        window.addstr("To leave animation, press Enter.\n")
        window.addstr(snapshots[current_snapshot] + "\n")

        # animate
        key = window.getkey()
        # we can leave by pressing Enter
        while key != os.linesep and key != 'q':
            # now if the key is not a direction, just wait for the next direction
            if key not in ANIMATION_DIRECTION_STRINGS:
                key = window.getkey()
                continue

            # navigate with direction keys
            direction = AnimationDirections(key)
            if direction == AnimationDirections.LEFT:
                current_snapshot -= 1
                # don't go before the first snapshot
                current_snapshot = max(current_snapshot, 0)
            elif direction == AnimationDirections.RIGHT:
                current_snapshot += 1
                # don't go any further if we reached the end
                if is_endstate(self.state):
                    current_snapshot = min(current_snapshot, len(snapshots) - 1)
                # if we haven't calculated this snapshot yet, calculate it now
                if current_snapshot == len(snapshots):
                    self.step()
                    snapshots.append(str(self))

            # display the current snapshot
            window.clear()
            window.addstr("To leave animation, press Enter.\n")
            window.addstr(snapshots[current_snapshot] + "\n")
            # on the last snapshot, also print the result
            if current_snapshot == len(snapshots) - 1 and is_endstate(self.state):
                # cache it like it's hot
                if not result:
                    result = self.output()
                window.addstr(f"Result: {result}")
            # get the next key
            key = window.getkey()

        # if an endstate wasn't reached, just keep running until the end
        while not is_endstate(self.state):
            self.step()
        return self.state

    def animate(self, input: str | list[Char]) -> EndStates:
        """Builds a curses window and animates the TM in it."""

        animation = lambda window: self.__run_animation(input, window)
        curses.wrapper(animation)
        return self.state

    ################################################################
    # utility
    ################################################################

    def __repr__(self) -> str:
        # time: 2,  state: 0
        # tape: S11101_
        #          ^
        return f"time: {self.time},\tstate: {self.state}\ntape: {chars_to_str(self.tape)}\n{' ' * (self.head + len('tape: '))}^"

    @staticmethod
    def from_file(filename: str, logging=False) -> Self:
        with open(filename, 'r') as f:
            firstline = f.readline()
            n_states, _ = [int(c) for c in firstline.split(" ")]
        fun = TransitionFunction.from_file(filename)
        return TuringMachine(n_states, fun, logging)


def test():
    """Tests my implementation."""

    assert EndStates.ACCEPT != 'y'
    assert EndStates.ACCEPT == EndStates('y')
    assert EndStates.ACCEPT in EndStates

    state: int | EndStates = 0
    assert type(state) == int
    state = EndStates.ACCEPT
    assert type(state) == EndStates

    fun: TransitionFunction = TransitionFunction.from_file("tm1.txt")
    assert fun.get(0, '0') == (0, '1', Directions.R)

    # tm1 counts the number of characters in the input
    tm1: TuringMachine = TuringMachine.from_file("tm1.txt")
    assert tm1.result("") == ""
    assert tm1.result("010010") == "111111"

    # tm2 only accepts words that only 1s
    tm2: TuringMachine = TuringMachine.from_file("tm2.txt")
    assert tm2.rejects("11101")
    assert tm2.accepts("11111")

    # tm3 does other stuff
    tm3: TuringMachine = TuringMachine.from_file("Verdopplung1.txt")
    assert tm3.result("") == ""
    assert tm3.result("1111") == "1111_1111"


def main():
    parser = argparse.ArgumentParser(description="Runs a Turing Machine on an input text.")
    parser.add_argument("filename",
                        help="File with the encoded Turing Machine.")
    parser.add_argument("-i", "--fileinput",
                        action='store_true',
                        help="Read input from filename instead of positional argument.")
    parser.add_argument("input",
                        help="Input to the Turing Machine (or file with the input if -i was set).")
    parser.add_argument("-a", "--animate",
                        action='store_true',
                        help="Animate the Turing Machine.")
    args = parser.parse_args()
    
    # read turing machine
    tm: TuringMachine = TuringMachine.from_file(args.filename)
    # read machine input
    if args.fileinput:
        with open(args.input, 'r') as f:
            tm_input = f.read().strip()
    else:
        tm_input = args.input
    # run tm
    if args.animate:
        tm.animate(tm_input)
    else:
        tm.run(tm_input)
        print(tm.output())


if __name__ == "__main__":
    main()
