import argparse
import curses
import os
import re
from enum import Enum
from typing import TYPE_CHECKING, Literal, Self

from tabulate import tabulate

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
    UP = 'KEY_UP'
    DOWN = 'KEY_DOWN'


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


SPECIAL_CHARS = ['S', '_']


# just to not confuse elements of the alphabet with actual strings
Char = str
# input to transition function: state and character
TransitionIn = tuple[int, list[Char]]
# output of transtion function: state (+ end states), character (only writeable ones), direction
TransitionOut = tuple[int | EndStates, list[tuple[Char, Directions]]]


def str_to_chars(string: str) -> list[Char]:
    return [c for c in string]


def chars_to_str(chars: list[Char]):
    return "".join(chars)


def is_endstate(state: int | EndStates):
    return type(state) == EndStates


def to_key(trans_in: TransitionIn):
    state = trans_in[0]
    chars = tuple(trans_in[1])
    return (state, chars)


def sanitize(line: str):
    return re.sub(r"\s+", "", line)


def skip_comments(f):
    while line := f.readline():
        if line[0] != '#':
            return line


class TransitionFunction:
    def __init__(self, n_states: int, n_tapes: int, alphabet: list[Char]):
        self.n_states = n_states
        self.n_tapes = n_tapes
        self.alphabet = alphabet
        self.__transitions: dict[TransitionIn, TransitionOut] = {}

    def get(self, state: int, chars: list[Char]) -> TransitionOut:
        # if we didn't specify this combination, we reject
        trans_in: TransitionIn = (state, chars)
        key = to_key(trans_in)
        if key not in self.__transitions:
            return (EndStates.REJECT, zip(chars, [Directions.N] * self.n_tapes))
        # otherwise just return the matching transition
        return self.__transitions[key]

    def __repr__(self) -> str:
        return tabulate([[
            # state in
            trans_in[0],
            # chars in
            ",".join(trans_in[1]),
            # state out
            trans_out[0],
            # chars out
            ",".join(char_out for char_out, _ in trans_out[1]),
            # directions out
            ",".join(direction_out.value for _, direction_out in trans_out[1])
        ] for trans_in, trans_out in self.__transitions.items()],
            headers=["state in", "chars in", "state out", "chars out", "directions"],
            colalign=["center"] * 5,
            tablefmt='simple_grid')

    def _add(self, input: TransitionIn, output: TransitionOut):
        self.__transitions[to_key(input)] = output

    @classmethod
    def from_file(cls, filename: str) -> Self:
        with open(filename, 'r') as f:
            # read how the transition function is supposed to look
            # ignore comments
            firstline = skip_comments(f)
            n_states, n_tapes, alphabet_size, n_lines = [int(c) for c in firstline.split(" ")]
            # ignore comments
            secondline = sanitize(skip_comments(f))
            alphabet = secondline.split(",")
            assert alphabet_size == len(alphabet), "Alphabet does not have promised size."
            # read the transition function
            fun = TransitionFunction(n_states, n_tapes, alphabet)
            observed_lines = 0
            observed_states: set[Char] = set()
            while line := sanitize(f.readline()):
                # skip comments
                if line[0] == '#':
                    continue
                # add transition
                trans_in, trans_out = TransitionFunction.parse_line(line, n_tapes)
                fun._add(trans_in, trans_out)
                # collect observed states, chars, ...
                state_in, chars_in = trans_in
                state_out, chars_dirs_out = trans_out
                if not is_endstate(state_in):
                    observed_states.add(state_in)
                if not is_endstate(state_out):
                    observed_states.add(state_out)
                observed_lines += 1
                # chars need to be in alphabet
                for char in chars_in:
                    assert char in alphabet or char in SPECIAL_CHARS, f"Observed char ({char}) not in alphabet ({alphabet})."
                for char, _ in chars_dirs_out:
                    assert char in alphabet or char in SPECIAL_CHARS, f"Observed char ({char}) not in alphabet ({alphabet})."
            # assert that the transition function actually looks like it's supposed to look
            assert n_lines == observed_lines, f"Observed line count ({observed_lines}) does not equal promised line count ({n_lines})."
            assert n_states == len(observed_states), f"Observed state count ({observed_states}, {len(observed_states)} states) does not equal promised state count ({n_states})."
        return fun

    @classmethod
    def parse_line(cls, line: str, n_tapes: int) -> tuple[TransitionIn, TransitionOut]:
        # remove all whitespace and line breaks
        line = re.sub(r"\s+", "", line)
        # read entries and make sure it's the right amount
        entries = line.split(",")
        # 1 state_in, 1 state_out, n chars_in, n chars_out, n directions
        n_entries_expected = 2 + 3 * n_tapes
        assert len(entries) == n_entries_expected, f"Error in processing line: {line} - not {n_entries_expected} entries."
        # 1 state_in
        state_in = int(entries[0])
        # n chars_in
        chars_in = entries[1:n_tapes + 1]
        # 1 state_out
        state_out = entries[n_tapes + 1]
        state_out = int(state_out) if state_out not in END_STATE_CHARS else EndStates(state_out)
        # n times char and directions
        rest = entries[n_tapes + 2:]
        chars_and_dirs_out = [(rest[2 * i], Directions(rest[2 * i + 1])) for i in range(n_tapes)]
        # build transition entry
        trans_in: TransitionIn = (state_in, chars_in)
        trans_out: TransitionOut = (state_out, chars_and_dirs_out)
        return trans_in, trans_out


class Tape:
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


class ScrollableDisplay:
    def __init__(self, window: Window) -> None:
        self.window = window
        self.display_str = ""
        self.pos = 0

    def add(self, string: str):
        self.display_str += string

    def clear(self):
        self.display_str = ""

    def scroll(self, n_lines: int):
        self.pos += n_lines
        self.pos = max(self.pos, 0)
        self.pos = min(self.pos, self.display_str.count(os.linesep))
        self.update()

    def update(self):
        max_rows, _ = self.window.getmaxyx()
        lines = self.display_str.splitlines()
        display_end = min(self.pos + max_rows, len(lines))
        displayed_lines = lines[self.pos:display_end]
        window_str = "\n".join(displayed_lines)
        print(lines)
        print(max_rows)
        print(display_end)
        self.window.clear()
        self.window.addstr(window_str)


class TuringMachine:
    def __init__(self, n_states: int, n_tapes: int, transition_function: TransitionFunction, logging=False, show_transitions=False) -> None:
        # TODO: do sth with this? (i'm not using n_states anywhere)
        self.n_states = n_states
        self.n_tapes = n_tapes
        self.transition_function = transition_function
        self.logging = logging
        self.show_transitions = show_transitions
        self.tapes: list[Tape] = [Tape()] * n_tapes
        self.state: int | EndStates = 0
        self.time: int = 0

    def __read(self) -> list[Char]:
        return [tape.read() for tape in self.tapes]

    def __write(self, chars: list[Char]):
        for tape, char in zip(self.tapes, chars):
            tape.write(char)

    def __move(self, directions: list[Directions]):
        for tape, direction in zip(self.tapes, directions):
            tape.move(direction)

    def step(self):
        """Does one (1) step for the TM."""

        self.time += 1
        # find out what needs to happen
        chars = self.__read()
        next_state, chars_and_directions = self.transition_function.get(self.state, chars)
        written_chars = [char for char, _ in chars_and_directions]
        directions = [direction for _, direction in chars_and_directions]
        # make it happen
        self.__write(written_chars)
        self.__move(directions)
        self.state = next_state

    def run(self, input: str | list[Char]) -> EndStates:
        """Runs the TM until it is in an end state."""

        # if logging is enabled and we show transitions, show them now (at the start)
        if self.logging and self.show_transitions:
            print(f"{self.transition_function}\n")
        self.state = 0
        self.time = 0
        # init tapes
        self.tapes = [Tape() for _ in range(self.n_tapes)]
        # first tape is input tape
        self.tapes[0] = Tape(input)
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
        result = chars_to_str(self.tapes[-1].chars)
        # remove trailing blanks: convert '_' to whitespace, remove whitespace on the right, convert whitespace back to '_'
        result = result.replace("_", " ").rstrip().replace(" ", "_")
        # return everything but the start symbol
        return result[1:]

    ################################################################
    # all of these four (4) functions run the turing machine
    ################################################################

    def accepts(self, input: str | list[Char]) -> bool:
        """Runs the TM on the input and returns True if the input is accepted by the TM."""

        return self.run(input) == EndStates.ACCEPT

    def rejects(self, input: str | list[Char]) -> bool:
        """Runs the TM on the input and returns True if the input is rejected by the TM."""

        return self.run(input) == EndStates.REJECT

    def result(self, input: str | list[Char]) -> str:
        """Runs the TM on the input and returns the output if TM halts. Otherwise returns an empty string."""

        # if we didn't halt, but instead accepted or rejected, the result is supposed to be a function output
        if self.run(input) != EndStates.HALT:
            return ""
        return self.output()

    def runtime(self, input: str | list[Char]) -> str:
        """Runs the TM on the input and returns the number of steps needed to reach the final state."""
        self.run(input)
        return self.time

    ################################################################
    # animation stuff
    ################################################################

    def __run_animation(self, input: str | list[Char], window: Window) -> EndStates:
        """Runs and animates the TM in a curses window."""

        self.state = 0
        self.time = 0
        # init tapes
        self.tapes = [Tape() for _ in range(self.n_tapes)]
        # first tape is input tape
        self.tapes[0] = Tape(input)

        # animation stuff
        # snapshots of the TM at any given time (just string representations)
        snapshots: list[str] = []
        current_snapshot = 0
        snapshots.append(str(self))
        # cached result of the run of the TM
        result = None
        # display first snapshot
        display = ScrollableDisplay(window)
        display.add("To leave animation, press Enter.\n")
        display.add(snapshots[current_snapshot] + "\n")
        # if we show transitions, show them below everything else
        if self.show_transitions:
            display.add(str(self.transition_function))
        display.update()

        # animate
        # we can leave by pressing Enter
        while (key := window.getkey()) not in [os.linesep, 'q']:
            # now if the key is not a direction, just wait for the next direction
            if key not in ANIMATION_DIRECTION_STRINGS:
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
            elif direction == AnimationDirections.UP:
                display.scroll(-1)
                continue
            elif direction == AnimationDirections.DOWN:
                display.scroll(1)
                continue

            # display the current snapshot
            display.clear()
            display.add("To leave animation, press Enter.\n")
            display.add(snapshots[current_snapshot] + "\n")
            # on the last snapshot, also print the result
            if current_snapshot == len(snapshots) - 1 and is_endstate(self.state):
                # cache it like it's hot
                if not result:
                    result = self.output()
                display.add(f"Result: {result}\n")
            # if we show transitions, show them below everything else
            if self.show_transitions:
                display.add(str(self.transition_function))
            display.update()

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
        tape_strings = "\n".join([str(tape) for tape in self.tapes])
        return f"time: {self.time},\tstate: {self.state}\ntapes:\n{tape_strings}"

    @classmethod
    def from_file(cls, filename: str, logging=False, show_transitions=False) -> Self:
        fun: TransitionFunction = TransitionFunction.from_file(filename)
        return TuringMachine(fun.n_states, fun.n_tapes, fun, logging, show_transitions)


def test():
    """Tests my implementation."""

    assert EndStates.ACCEPT != 'y'
    assert EndStates.ACCEPT == EndStates('y')
    assert EndStates.ACCEPT in EndStates

    state: int | EndStates = 0
    assert type(state) == int
    state = EndStates.ACCEPT
    assert type(state) == EndStates

    fun: TransitionFunction = TransitionFunction.from_file("tm4.txt")
    assert fun.get(0, ['0']) == (0, [('1', Directions.R)])

    tm5: TuringMachine = TuringMachine.from_file("tm5.txt")
    assert tm5.result("0100$1101") == "1001"

    # test Turing Machines that were part of the task
    # tm_task1 should accept 0^n 1^n 0^n
    tm_task1: TuringMachine = TuringMachine.from_file("task1.txt")
    for n in range(20):
        # 010
        word = "0" * n + "1" * n + "0" * n
        assert tm_task1.accepts(word), f"Task 1 failed: {word} not accepted."
        # 0100, 0110, 0010
        word = "0" * n + "1" * n + "0" * (n + 1)
        assert tm_task1.rejects(word), f"Task 1 failed: {word} not rejected."
        word = "0" * n + "1" * (n + 1) + "0" * n
        assert tm_task1.rejects(word), f"Task 1 failed: {word} not rejected."
        word = "0" * (n + 1) + "1" * n + "0" * n
        assert tm_task1.rejects(word), f"Task 1 failed: {word} not rejected."
        # 01100, 00100, 00110
        word = "0" * n + "1" * (n + 1) + "0" * (n + 1)
        assert tm_task1.rejects(word), f"Task 1 failed: {word} not rejected."
        word = "0" * (n + 1) + "1" * (n + 1) + "0" * n
        assert tm_task1.rejects(word), f"Task 1 failed: {word} not rejected."
        word = "0" * (n + 1) + "1" * (n + 1) + "0" * n
        assert tm_task1.rejects(word), f"Task 1 failed: {word} not rejected."
    # tm_task2 should add 2 binary numbers
    tm_task2a: TuringMachine = TuringMachine.from_file("task2a.txt")
    tm_task2b: TuringMachine = TuringMachine.from_file("task2b.txt")
    n_numbers_tested = 20
    for x in range(n_numbers_tested):
        for y in range(n_numbers_tested):
            word = f"{bin(x)[2:]}${bin(y)[2:]}"
            expected_result = bin(x + y)[2:]
            result_2a = tm_task2a.result(word)
            assert result_2a == expected_result, f"Task 2a failed: input = {word}, result = {result_2a}, expected = {expected_result}"
            result_2b = tm_task2b.result(word)
            assert result_2b == expected_result, f"Task 2b failed: input = {word}, result = {result_2b}, expected = {expected_result}"

    print("all tests passed.")


class test_action(argparse.Action):
    """This class is for the test flag."""

    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, nargs=0, default=argparse.SUPPRESS, **kwargs)

    def __call__(self, parser, namespace, values, option_string, **kwargs):
        # if testing flag was set, ignore everything else and just test
        test()
        parser.exit()


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
    parser.add_argument("-l", "--logging",
                        action='store_true',
                        help="Logs the snapshots of the Turing Machine.")
    parser.add_argument("-s", "--showtransitions",
                        action='store_true',
                        help="Shows the transition table with the animation or log.")
    parser.add_argument("-t", "--test",
                        action=test_action,
                        help="Tests the implementation and the Turing Machines that were part of the task.")
    args = parser.parse_args()

    # read turing machine
    tm: TuringMachine = TuringMachine.from_file(args.filename, args.logging, args.showtransitions)
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
