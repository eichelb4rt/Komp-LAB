import os
import re
from enum import Enum
from typing import Self
from io import TextIOWrapper
from tabulate import tabulate
from chars import Char


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


# input to transition function: state and character
TransitionIn = tuple[int, list[Char]]
# output of transtion function: state (+ end states), character (only writeable ones), direction
TransitionOut = tuple[int | EndStates, list[tuple[Char, Directions]]]


def is_endstate(state: int | EndStates):
    return type(state) == EndStates


def to_key(trans_in: TransitionIn):
    state = trans_in[0]
    chars = tuple(trans_in[1])
    return (state, chars)


def sanitize(line: str):
    return re.sub(r"\s+", "", line)


def skip_comments(f: TextIOWrapper):
    while line := f.readline():
        if line[0] != '#':
            return line


def transition_to_str(t_in: TransitionIn, t_out: TransitionOut) -> str:
    state_in, chars_in = t_in
    state_out, chars_and_dirs_out = t_out
    chars_in_str = ",".join(chars_in)
    chars_and_dirs_out_str = ",".join([f"{char},{direction.value}" for char, direction in chars_and_dirs_out])
    return f"{state_in},{chars_in_str},{state_out if not is_endstate(state_out) else state_out.value},{chars_and_dirs_out_str}"


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

    def save(self, filename: str):
        """Saves the encoded transition function to a file."""

        comment = "# This Turing Machine was saved automatically from a Transition Function."
        firstline = f"{self.n_states} {self.n_tapes} {len(self.alphabet)} {len(self.__transitions)}"
        secondline = ",".join(self.alphabet)
        transitions_lines = [transition_to_str(t_in, t_out) for t_in, t_out in self.__transitions.items()]
        encoded = os.linesep.join([comment, firstline, secondline] + transitions_lines)
        with open(filename, 'w') as f:
            f.write(encoded)

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
