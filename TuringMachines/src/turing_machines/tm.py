import os
import curses
import argparse
from enum import Enum
from typing import Generic, Self, Type, TypeVar

import turing_machines.test as test
from turing_machines.tape import MultiCharTape, SingleCharTape, Tape
from turing_machines.display import ScrollableDisplay, Window
from turing_machines.transitions import TransitionFunction, EndStates, Char, Directions, is_endstate


class AnimationDirections(Enum):
    LEFT = 'KEY_LEFT'
    RIGHT = 'KEY_RIGHT'
    UP = 'KEY_UP'
    DOWN = 'KEY_DOWN'


ANIMATION_DIRECTION_STRINGS = [state.value for state in AnimationDirections]


class TuringMachine:
    def __init__(self, transition_function: TransitionFunction, logging=False, show_transitions=False, tape_cls: Type[Tape] = SingleCharTape) -> None:
        # TODO: do sth with this? (i'm not using n_states anywhere)
        self.n_states = transition_function.n_states
        self.n_tapes = transition_function.n_tapes
        self.transition_function = transition_function
        self.logging = logging
        self.show_transitions = show_transitions
        # tape can be of different sub classes
        self.tape_cls = tape_cls
        # initialized when TM is run
        self.tapes: list[Tape]
        self.state: int | EndStates
        self.time: int

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
        self.tapes = [self.tape_cls() for _ in range(self.n_tapes)]
        # first tape is input tape
        self.tapes[0] = self.tape_cls(input)
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
        return self.tapes[-1].output()

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

    def runtime(self, input: str | list[Char]) -> int:
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
        self.tapes = [self.tape_cls() for _ in range(self.n_tapes)]
        # first tape is input tape
        self.tapes[0] = self.tape_cls(input)

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
    def from_file(cls, filename: str, **kwargs) -> Self:
        fun: TransitionFunction = TransitionFunction.from_file(filename)
        return TuringMachine(fun, **kwargs)


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
                        help="Shows the transition table with the animation or log (logging must be enabled for the latter).")
    parser.add_argument("-t", "--time",
                        action='store_true',
                        help="Shows runtime of the Turing Machine.")
    parser.add_argument("-m", "--multichars",
                        action='store_true',
                        help="Enable ability to have multiple chars in one tape cell.")
    parser.add_argument("--test",
                        action=test.test_action(test.test_turing_machines),
                        help="Tests the implementation and the Turing Machines that were part of the task (no other arguments needed).")
    args = parser.parse_args()

    # find out which kind of tape we are using
    if args.multichars:
        tape_cls = MultiCharTape
    else:
        tape_cls = SingleCharTape
    # read turing machine
    tm: TuringMachine = TuringMachine.from_file(args.filename, logging=args.logging, show_transitions=args.showtransitions, tape_cls=tape_cls)
    # read machine input
    if args.fileinput:
        with open(args.input, 'r') as f:
            tm_input = f.read().strip()
    else:
        tm_input = args.input
    # run tm
    if args.animate:
        # animation does not need to print output
        tm.animate(tm_input)
    else:
        tm.run(tm_input)
        print(f"Result: {tm.output()}")
        # maybe print time as well
        if args.time:
            print(f"Time: {tm.time}")


if __name__ == "__main__":
    main()
