import argparse
import itertools
from typing import Any
from pathlib import Path
from tabulate import tabulate
from collections.abc import Iterable

from chars import Char
from transitions import SPECIAL_CHARS, Directions, EndStates, TransitionFunction, TransitionIn, TransitionOut, is_endstate
import test

################################################################
# PLAN
# ==============================================================
# loop:

# stage 0: (convert input)
# from left to right, convert every char to a compressed char
# don't forget to add artificial compressed start points
# example: S1010_ -> S|1_|0_|1_|0_|_
# this stage uses state 0 and 1

# stage 1 (reading):
# from left to right, collect what chars we see

# stage 1 -> stage 2:
# when on the right, figure out what stuff to write

# stage 2 (writing):
# go back (left), write it

# stage 2 -> stage 3:
# forget about what we wrote, remember the directions

# stage 3 (moving right):
# go right, move some heads to the right

# stage 4 (moving left):
# go left, move some heads to the left

# state 4 -> stage 1:
# if we're not in an original end state, start reading again

# stage 4 -> stage 5:
# if the original state is an endstate:
# - accept / decline -> accept / decline
# - halt -> stage 5

# stage 5 (clean up):
# go right to blank '_'
# go left and copy contents of last compressed tape (and shift left again, because we need to remove the artificial start symbol)
################################################################

# used states:
# 0: start state
STATE_START = 0
# 1: go left (after converting input)
STATE_INIT_GO_LEFT = 1
# 2: ready for simulation
STATE_READY = 2
# 3: entering cleanup stage
STATE_CLEANUP = 3
# 4: observed blank input, just write it down and start
STATE_BLANK_INPUT = 4
MAX_RESERVED_STATE = 4

# '*' if the head is there, '-' if it's not there.
HEAD_ALPHABET = ['-', '*']

# info about the directions heads can move in specific states
MoveInfo = tuple[int | EndStates, tuple[Directions]]

# original state (not including endstates), incomplete char saves
ReadingStageInfo = tuple[int, str]
# original state (including endstates), saved chars, directions
WritingStageInfo = TransitionOut
# original state (including endstates), list of directions, whether we found a header or not
MovingStageInfo = tuple[int | EndStates, tuple[Directions], tuple[bool]]


################################################################
# EXTRACT INFORMATION
################################################################


def extract_moves(trans_fun: TransitionFunction) -> set[MoveInfo]:
    """Extracts all possible (state, directions)-vectors from the transition function."""

    moves: set[MoveInfo] = set()
    for t_in, t_out in trans_fun._transitions.items():
        state_in, chars_in = t_in
        state_out, chars_and_dirs_out = t_out
        chars_out, dirs_out = zip(*chars_and_dirs_out)
        moves.add((state_out, tuple(dirs_out)))
    return moves


def extract_trans_ins(trans_fun: TransitionFunction) -> list[TransitionIn]:
    return list(trans_fun._transitions.keys())


def extract_trans_outs(trans_fun: TransitionFunction) -> set[TransitionOut]:
    return set([(state_out, tuple(chars_and_dirs_out)) for state_out, chars_and_dirs_out in trans_fun._transitions.values()])


def extract_non_end_states(transitions: list[tuple[TransitionIn, TransitionOut]]) -> set[int | EndStates]:
    states: set[int | EndStates] = set()
    for t_in, t_out in transitions:
        state_in, chars_in = t_in
        state_out, chars_and_dirs_out = t_out
        chars_out, dirs_out = zip(*chars_and_dirs_out)
        if not is_endstate(state_in):
            states.add(state_in)
        if not is_endstate(state_out):
            states.add(state_out)
    return states


################################################################
# COMPRESS DIRECTIONS
################################################################


def possible_found_vectors(directions: tuple[Directions], going: Directions) -> Iterable[tuple[bool]]:
    """Returns the possibilities in which the headers in the direction we're going can be found.

    Example: LRLNR, Directions.R -> [00000,01000,00001,01001]"""

    found_possibilities = [[True, False] if direction == going else [False] for direction in directions]
    return itertools.product(*found_possibilities)


def generate_possible_moves(original_moves: set[MoveInfo]) -> tuple[set[MoveInfo], set[MoveInfo]]:
    """Generates all the possible ways, in which order the headers in the tapes can be found. Output format: (right, left)

    Takes the set of original directions vectors and computes for that:
    - ways in which headers can be found going right
    - ways in which headers can be found going left

    Example: [0, LRLNR] -> [(0, LRLNR), (0, LRLNN), (0, LNNLNR), (0, LNLNN)], [(0, LNLNN), (0, LNNNN), (0, NNLNN), (0, NNNNN)]"""

    # first compute all the possible ways the headers can be found going right
    possibilities_right: set[MoveInfo] = original_moves

    # now computer all ways the headers can be found going left
    # note that we already found all the headers that have to be moved right
    possibilities_left: set[tuple[Directions]] = set()
    for state_out, directions in original_moves:
        # we found every Directions.R
        new_directions = tuple([Directions.N if direction == Directions.R else direction for direction in directions])
        possibilities_left.add((state_out, new_directions))

    return possibilities_right, possibilities_left


################################################################
# COMPRESS ALPHABET AND GENERATE CHAR SAVES
################################################################


def compress_alphabet(original_input_alphabet: list[Char], n_tapes: int) -> tuple[list[Char], list[Char]]:
    """Compresses all possible combinations of headers and chars into one compressed char each.

    Returns a list of compressed start chars and a list of compressed non-start chars."""

    # first add all the possible combinations of chars without the start symbol ('S')
    compressed_non_start = ["".join(chars) for chars in itertools.product(HEAD_ALPHABET, original_input_alphabet + ['_'], repeat=n_tapes)]
    # start symbol can only be in one position
    compressed_start = ["".join(chars) for chars in itertools.product(HEAD_ALPHABET, ['S'], repeat=n_tapes)]
    return compressed_start, compressed_non_start


def chars_apply_found(chars: tuple[Char], found_vector: list[bool]) -> str:
    # make it mutable
    new_chars = list(chars)
    for tape_index, found_header in enumerate(found_vector):
        if not found_header:
            # insert missing char (' ') if the header wasn't found yet
            new_chars[tape_index] = ' '
    # make it immutable
    return "".join(new_chars)


def generate_incomplete_saves(original_trans_in: list[TransitionIn], n_tapes: int) -> set[tuple[int, str]]:
    """Chars can be read in an arbitrary order. So missing chars have to be considered.

    Example: ['01'] -> [' ', ' 1', '0 ', '01']"""

    saves: set[tuple[int, str]] = set()
    possible_found_vectors = itertools.product([True, False], repeat=n_tapes)
    for found_vector in possible_found_vectors:
        for trans_in in original_trans_in:
            state_in, chars_in = trans_in
            # add every possibility of found / not found chars
            incomplete_save = chars_apply_found(chars_in, found_vector)
            saves.add((state_in, incomplete_save))
    return saves


################################################################
# COMPRESS STATES
################################################################


def compress_states_copying(original_alphabet: list[Char], start_at: int) -> tuple[dict[tuple[Char, bool], int], int]:
    """Builds states for stage 0. In stage 0, we have to remember the last char on the tape. We also have to remember if we already wrote the first char or not (to place the heads). That's two states for every char."""

    compressed_states_map: dict[tuple[Char, bool], int] = {}
    next_state = start_at
    for char in original_alphabet:
        for placed_first in [True, False]:
            compressed_states_map[char, placed_first] = next_state
            next_state += 1
    return compressed_states_map, next_state


def compress_states_reading(incomplete_saves: set[tuple[int, str]], start_at: int) -> tuple[dict[ReadingStageInfo, int], int]:
    """Builds a bidirectional dictionary that maps from every occuring combination of original state and saved chars to one compressed state each.
    (original state, saved chars) -> compressed state

    Returns that dict and the next unassigned state."""

    # map from current original state and saved chars to respective compressed state
    compressed_states_map: dict[ReadingStageInfo, int] = {}

    # add states for reading
    # for all combinations of states and k (k = number of tapes) chars, make a new compressed state for reading
    next_state = start_at
    for incomplete_save in incomplete_saves:
        compressed_states_map[incomplete_save] = next_state
        next_state += 1

    # add states for moving headers in any direction (this is only need when moving headers to the right)
    return compressed_states_map, next_state


def compress_states_writing(original_trans_outs: set[TransitionOut], start_at: int) -> tuple[dict[WritingStageInfo, int], int]:
    """Builds a bidirectional dictionary that maps from every combination of original state and finished saved chars to one compressed state each.
    (original state, write vector) -> compressed state

    Returns that dict and the maximum state assigned"""

    # map from current original state and saved chars to respective compressed state
    compressed_states_map: dict[WritingStageInfo, int] = {}

    # add states for writing
    next_state = start_at
    for trans_out in original_trans_outs:
        compressed_states_map[trans_out] = next_state
        next_state += 1

    # add states for moving headers in any direction (this is only need when moving headers to the right)
    return compressed_states_map, next_state


def compress_states_moving(possible_moves: set[MoveInfo], going: Directions, start_at: int) -> tuple[dict[MovingStageInfo, int], int]:
    """Builds a bidirectional dictionary that maps from every combination of original state and list of directions to one compressed state each.
    (original state, directions, header found) -> compressed state

    Returns that dict and the maximum state assigned"""

    # map from current original state and saved chars to respective compressed state
    compressed_states_map: dict[MovingStageInfo, int] = {}

    # add states for writing
    next_state = start_at
    for state_out, directions in possible_moves:
        # for all the directions: pick out the directions in which we're actually going
        # we can find all the headers on the respective tape in any arbitrary order, so let's encode that
        found_vectors = possible_found_vectors(directions, going)
        for found_headers in found_vectors:
            compressed_states_map[state_out, directions, found_headers] = next_state
            next_state += 1

    # add states for moving headers in any direction (this is only need when moving headers to the right)
    return compressed_states_map, next_state


def compress_states_cleanup(original_alphabet: list[Char], start_at: int) -> tuple[dict[tuple[Char, bool], int], int]:
    """Builds states for stage 0. In stage 0, we have to remember the last char on the tape. We also have to remember if we already wrote the first char or not (to place the heads). That's two states for every char."""

    compressed_states_map: dict[tuple[Char, bool], int] = {}
    next_state = start_at
    # we also want to copy the blank symbol ('_')
    for char in original_alphabet + ['_']:
        compressed_states_map[char] = next_state
        next_state += 1
    return compressed_states_map, next_state


################################################################
# BUILD TRANSITIONS
################################################################

def build_transition(state_in: int, char_in: Char, state_out: int | EndStates, char_out: Char, direction: Directions) -> tuple[TransitionIn, TransitionOut]:
    t_in = (state_in, [char_in])
    t_out = (state_out, [(char_out, direction)])
    return t_in, t_out


################################################################
# STATE 0
################################################################


def build_transitions_stage_zero(original_alphabet: list[Char], compressed_states_map_copying: dict[Char, int], n_tapes: int) -> list[tuple[TransitionIn, TransitionOut]]:
    compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []

    # add an artificial start symbol (-S-S-S)
    compressed_start_char = "-S" * n_tapes
    # first cell needs to have heads everywhere
    init_multichar_with_heads = lambda original_char: '*' + original_char + '*_' * (n_tapes - 1)
    # no heads here, just copy original char and fill rest with blank
    init_multichar_without_heads = lambda original_char: '-' + original_char + '-_' * (n_tapes - 1)

    # cover empty inputs
    compressed_transitions.append(build_transition(
        state_in=STATE_START,
        char_in='_',
        state_out=STATE_BLANK_INPUT,
        char_out=compressed_start_char,
        direction=Directions.R
    ))
    compressed_transitions.append(build_transition(
        state_in=STATE_BLANK_INPUT,
        char_in='_',
        state_out=STATE_READY,
        char_out=init_multichar_with_heads('_'),
        direction=Directions.N
    ))

    # whatever char there is on the first cell, remember it and put the artificial start symbol there
    for replaced_char in original_alphabet:
        # remember the replaced char in a state, remember that we haven't placed the first char yet
        state_out = compressed_states_map_copying[replaced_char, False]
        # replace it with the atificial start symbol and go right
        compressed_transitions.append(build_transition(
            state_in=STATE_START,
            char_in=replaced_char,
            state_out=state_out,
            char_out=compressed_start_char,
            direction=Directions.R
        ))

    # now shift the first char 1 to the right
    for second_char in original_alphabet:
        for first_char in original_alphabet:
            # we remembered the 1st char, but didn't place it yet
            state_in = compressed_states_map_copying[first_char, False]
            # remember the replaced char in a state (we placed the 1st char by then)
            state_out = compressed_states_map_copying[second_char, True]
            # we can just write the compressed char immediately
            compressed_char = init_multichar_with_heads(first_char)
            # replace it with the last remembered char and go next
            compressed_transitions.append(build_transition(
                state_in=state_in,
                char_in=second_char,
                state_out=state_out,
                char_out=compressed_char,
                direction=Directions.R
            ))

    # now shift all the rest 1 to the right
    for replaced_char in original_alphabet:
        for prev_char in original_alphabet:
            # we remembered the previous char
            state_in = compressed_states_map_copying[prev_char, True]
            # remember the replaced char in a state
            state_out = compressed_states_map_copying[replaced_char, True]
            # we can just write the compressed char immediately
            compressed_char = init_multichar_without_heads(prev_char)
            # replace it with the last remembered char and go next
            compressed_transitions.append(build_transition(
                state_in=state_in,
                char_in=replaced_char,
                state_out=state_out,
                char_out=compressed_char,
                direction=Directions.R
            ))

    # if we find the end / blank ('_'), write down the last char and go back
    for last_char in original_alphabet:
        # doesn't matter if we placed the first char already or not
        for placed_first in [True, False]:
            # we remembered the previous char
            state_in = compressed_states_map_copying[last_char, placed_first]
            # we can just write the compressed char immediately
            compressed_char = init_multichar_without_heads(last_char) if placed_first else init_multichar_with_heads(last_char)
            compressed_transitions.append(build_transition(
                state_in=state_in,
                char_in='_',
                state_out=STATE_INIT_GO_LEFT,
                char_out=compressed_char,
                direction=Directions.L
            ))

    # now go back, doesn't matter what's on the tape
    for original_char in original_alphabet:
        for placed_first in [True, False]:
            compressed_char = init_multichar_without_heads(original_char) if placed_first else init_multichar_with_heads(original_char)
            compressed_transitions.append(build_transition(
                state_in=STATE_INIT_GO_LEFT,
                char_in=compressed_char,
                state_out=STATE_INIT_GO_LEFT,
                char_out=compressed_char,
                direction=Directions.L
            ))

    # if we find the artificial start symbol again, go into the ready state and place header on the first real cell
    compressed_transitions.append(build_transition(
        state_in=1,
        char_in=compressed_start_char,
        state_out=STATE_READY,
        char_out=compressed_start_char,
        direction=Directions.R
    ))

    return compressed_transitions


################################################################
# STATE 0 -> STAGE 1
################################################################


def build_transitions_stage_zero_to_one(compressed_alphabet: list[Char], compressed_states_map_reading: dict[ReadingStageInfo, int], n_tapes: int) -> list[tuple[TransitionIn, TransitionOut]]:
    compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []
    # we're in "compressed" state 0:
    # we haven't read anything yet. no matter what is on the tapes, go into the state where nothing is read yet.
    for char_in in compressed_alphabet:
        # go into compressed state:
        # original state is 0 and we haven't saved anything
        state_out = compressed_states_map_reading[0, ' ' * n_tapes]
        # add it to the list
        # don't write anything, don't move anything
        compressed_transitions.append(build_transition(
            state_in=STATE_READY,
            char_in=char_in,
            state_out=state_out,
            char_out=char_in,
            direction=Directions.N
        ))
    return compressed_transitions


################################################################
# STAGE 1
################################################################


def head_clash_reading(char_in: Char, saved_chars: str, n_tapes: int) -> bool:
    """Returns `True` if we already saved a char on some tape, but then found another header."""

    for i in range(n_tapes):
        # every 2nd char in `char_in` indicates if the head is there
        head_found = char_in[2 * i] == '*'
        # if the char read at position `i` isn't empty, we already found a char for that tape
        char_found = saved_chars[i] != ' '
        if head_found and char_found:
            return True
    return False


def save_new_chars(char_in: Char, old_saved_chars: str, n_tapes: int) -> str:
    """Saves chars on tapes where a header is."""

    # make a mutable representation
    new_saved_chars = list(old_saved_chars)
    for i in range(n_tapes):
        # if we find a header on tape i
        if char_in[2 * i] == '*':
            # save the respective char on tape i
            new_saved_chars[i] = char_in[2 * i + 1]
    # make it immutable again
    return "".join(new_saved_chars)


def build_transitions_stage_one(compressed_alphabet: list[Char], compressed_states_map_reading: dict[ReadingStageInfo, int], n_tapes: int) -> list[tuple[TransitionIn, TransitionOut]]:
    compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []
    # now add transitions for reading chars if there's the header there
    incomplete_saves: Iterable[ReadingStageInfo] = compressed_states_map_reading.keys()
    # we observe some chars
    for char_in in compressed_alphabet:
        # and we already saved these chars
        for original_state_in, old_save in incomplete_saves:
            # the header can only be at one position at the same time, so the following situation can't occur:
            # we observe a header and there's already a char read at that position
            # so we can just skip these cases
            if head_clash_reading(char_in, old_save, n_tapes):
                continue
            # figure out which chars to save
            new_save = save_new_chars(char_in, old_save, n_tapes)
            # if the original TM doesn't want to read the input, don't read an incomplete version of it either
            if (original_state_in, old_save) not in compressed_states_map_reading:
                continue
            if (original_state_in, new_save) not in compressed_states_map_reading:
                continue
            compressed_state_in = compressed_states_map_reading[original_state_in, old_save]
            compressed_state_out = compressed_states_map_reading[original_state_in, new_save]
            # construct transition
            # no matter what state we're in, just keep it. we're just reading.
            # connect old save to new save
            # don't write anything, go right
            compressed_transitions.append(build_transition(
                state_in=compressed_state_in,
                char_in=char_in,
                state_out=compressed_state_out,
                char_out=char_in,
                direction=Directions.R
            ))
    return compressed_transitions


################################################################
# STAGE 1 -> STAGE 2
################################################################


def build_transitions_stage_one_to_two(original_function: TransitionFunction, compressed_states_map_reading: dict[ReadingStageInfo, int], compressed_states_map_writing: dict[WritingStageInfo, int]) -> list[tuple[TransitionIn, TransitionOut]]:
    compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []
    incomplete_saves: Iterable[ReadingStageInfo] = compressed_states_map_reading.keys()
    # we saved some state and chars
    for original_state_in, complete_save in incomplete_saves:
        # we only want complete saves now
        if ' ' in complete_save:
            continue
        # construct the input for the original Turing Machine
        original_chars_in: list[Char] = list(complete_save)
        # this is where the actual work is done: construct what the original function would do
        original_trans_out = original_function.get(original_state_in, original_chars_in)
        # construct compressed version of the original transition output
        original_state_out, original_chars_and_dirs_out = original_trans_out
        compressed_trans_out = (original_state_out, tuple(original_chars_and_dirs_out))
        compressed_state_in = compressed_states_map_reading[original_state_in, complete_save]
        compressed_state_out = compressed_states_map_writing[compressed_trans_out]
        # construct the transition
        # we found the end of the tape
        # don't write anything, just change states and go left again
        compressed_transitions.append(build_transition(
            state_in=compressed_state_in,
            char_in='_',
            state_out=compressed_state_out,
            char_out='_',
            direction=Directions.L
        ))
    return compressed_transitions


################################################################
# STAGE 2
################################################################


def write_compressed(char_in: Char, chars_and_dirs_out: list[tuple[Char, Directions]], n_tapes: int) -> Char:
    """Reads a compressed char and writes the respective single chars where the headers are."""

    # make mutable representation of the compressed input char
    char_out = list(char_in)
    # iterate over all the tapes
    for i in range(n_tapes):
        # if we found a head
        if char_in[2 * i] == '*':
            # write the respective char
            # reminder: char_out is built like this: *a-b-c*d-e*f...
            # chars_and_dirs_out is built like this: [(p, N), (q, R), (r, L), ...]
            char_out[2 * i + 1] = chars_and_dirs_out[i][0]
    # make char immutable again
    return "".join(char_out)


def illegal_start_write(char_in: Char, char_out: Char) -> bool:
    """Returns if a start symbol was written somewhere it's not supposed to be written."""

    # we don't want to write the start symbol anywhere in the middle of the tape
    return 'S' not in char_in and 'S' in char_out


def illegal_start_overwrite(char_in: Char, char_out: Char, n_tapes: int) -> bool:
    """Returns if a non-start symbol was written on start."""

    # if we're not overwriting the start symbol, we're fine
    if 'S' not in char_in:
        return False
    # we're writing on the start symbol, let's hope that we're only writing start symbols
    for i in range(n_tapes):
        if char_out[2 * i + 1] != 'S':
            return True
    return False


def build_transitions_stage_two(compressed_alphabet: list[Char], compressed_states_map_writing: dict[WritingStageInfo, int], n_tapes: int) -> list[tuple[TransitionIn, TransitionOut]]:
    compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []
    trans_outs: Iterable[TransitionOut] = compressed_states_map_writing.keys()
    # we observe some chars, not the start chars tho. we don't write start chars.
    for char_in in compressed_alphabet:
        # we want to write some chars
        for original_state, chars_and_dirs_out in trans_outs:
            # if we find headers, write on them
            char_out = write_compressed(char_in, chars_and_dirs_out, n_tapes)
            # if we'd be writing start illegaly here, just don't include the transition
            # this can occur here because we don't know when the saved chars are written down
            if illegal_start_write(char_in, char_out):
                continue
            # what if the original function wants to write on start? nah man.
            if illegal_start_overwrite(char_in, char_out, n_tapes):
                continue
            # DEBUG
            # if char_out == "-0-0*S-0":
            #     print("HEY")
            #     print(char_in)
            #     print(chars_and_dirs_out)
            compressed_state = compressed_states_map_writing[original_state, chars_and_dirs_out]
            # construct transition
            # don't change the state
            # write the compressed char
            # go left
            compressed_transitions.append(build_transition(
                state_in=compressed_state,
                char_in=char_in,
                state_out=compressed_state,
                char_out=char_out,
                direction=Directions.L
            ))
    return compressed_transitions


################################################################
# STAGE 2 -> STAGE 3
################################################################


def build_transitions_stage_two_to_three(compressed_start_alphabet: list[Char], compressed_states_map_writing: dict[WritingStageInfo, int], compressed_states_map_moving_right: dict[MovingStageInfo, int], n_tapes: int) -> list[tuple[TransitionIn, TransitionOut]]:
    compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []
    trans_outs: Iterable[TransitionOut] = compressed_states_map_writing.keys()
    # we observe only start chars
    for compressed_start_char in compressed_start_alphabet:
        # we wrote some chars and we're in some state and stuff
        for original_state, chars_and_dirs_out in trans_outs:
            # separate written chars and directions, to forget about the chars we wrote
            wrote_chars, dirs_out = zip(*chars_and_dirs_out)
            # start stage 3 with no headers found
            headers_found = tuple([False] * n_tapes)
            # transition between stages
            compressed_state_in = compressed_states_map_writing[original_state, chars_and_dirs_out]
            compressed_state_out = compressed_states_map_moving_right[original_state, tuple(dirs_out), headers_found]
            # construct transition
            # don't write anything, don't move anywhere, just change states
            compressed_transitions.append(build_transition(
                state_in=compressed_state_in,
                char_in=compressed_start_char,
                state_out=compressed_state_out,
                char_out=compressed_start_char,
                direction=Directions.N
            ))
    return compressed_transitions


################################################################
# STAGE 3
################################################################


def head_clash_moving(char_in: Char, found_directions: tuple[bool], n_tapes: int) -> bool:
    """Returns `True` if we just found a char on some tape, but then found another header."""

    for i in range(n_tapes):
        # every 2nd char in `char_in` indicates if the head is there
        head_found = char_in[2 * i] == '*'
        if head_found and found_directions[i]:
            return True
    return False


def pick_up_heads(compressed_char: Char, directions: tuple[Directions], n_tapes: int, desired_direction: Directions) -> tuple[Char, tuple[bool]]:
    """Picks up the heads on each tape if we're moving into the desired direction on that tape.

    Returns new compressed char without the picked up heads, also returns positions where the heads where picked up."""

    heads_found = [compressed_char[2 * i] == '*' for i in range(n_tapes)]
    # pickup heads that we found, but only if we're going into the desired direction
    picked_up_heads = [heads_found[i] and directions[i] == desired_direction for i in range(n_tapes)]
    # create a mutable representation
    new_char = list(compressed_char)
    for i in range(n_tapes):
        # if the head on the i-th tape was picked up, remove it
        if picked_up_heads[i]:
            new_char[2 * i] = '-'
    # make immutable again
    return "".join(new_char), tuple(picked_up_heads)


def drop_heads(compressed_char: Char, dropped_heads: tuple[bool], n_tapes: int) -> Char:
    """Writes the heads we found in the previous cell to the current cell (because we want to move them)."""

    # create mutable representation
    new_char = list(compressed_char)
    for i in range(n_tapes):
        if dropped_heads[i]:
            new_char[2 * i] = '*'
    # make char immutable again
    return "".join(new_char)


def build_transitions_stage_three(compressed_alphabet: list[Char], compressed_states_map_moving_right: dict[MovingStageInfo, int], n_tapes: int) -> list[tuple[TransitionIn, TransitionOut]]:
    compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []
    moving_stage_infos: Iterable[MovingStageInfo] = compressed_states_map_moving_right.keys()
    # scenario: we found another compressed char and want to move the picked up heads
    for compressed_char_in in compressed_alphabet:
        for original_state, directions, dropped_heads in moving_stage_infos:
            # we can't find a head immediately after we just found it
            if head_clash_moving(compressed_char_in, dropped_heads, n_tapes):
                continue
            # save what heads we're finding on the tapes
            picked_up_char, picked_up_heads = pick_up_heads(compressed_char_in, directions, n_tapes, desired_direction=Directions.R)
            # write down the heads we just found in the previous cell
            compressed_char_out = drop_heads(picked_up_char, dropped_heads, n_tapes)
            # figure out states
            compressed_state_in = compressed_states_map_moving_right[original_state, directions, dropped_heads]
            compressed_state_out = compressed_states_map_moving_right[original_state, directions, picked_up_heads]
            # build transition
            # remember the heads we just picked up in the state
            # change heads and go right
            compressed_transitions.append(build_transition(
                state_in=compressed_state_in,
                char_in=compressed_char_in,
                state_out=compressed_state_out,
                char_out=compressed_char_out,
                direction=Directions.R
            ))
    # scenario: we found a blank ('_') but still haven't moved all the heads -> expand tapes
    no_heads = tuple([False] * n_tapes)
    new_blanks = "-_" * n_tapes
    for original_state, directions, dropped_heads in moving_stage_infos:
        # we just consider cases where we actually have to move something (otherwise we don't need new blanks)
        if dropped_heads == no_heads:
            continue
        # make a new blank symbol on every tape but with some heads
        compressed_char_out = drop_heads(new_blanks, dropped_heads, n_tapes)
        # figure out states
        compressed_state_in = compressed_states_map_moving_right[original_state, directions, dropped_heads]
        # we can't pick up any heads on a new blank
        compressed_state_out = compressed_states_map_moving_right[original_state, directions, no_heads]
        # build transition
        # don't change the state
        compressed_transitions.append(build_transition(
            state_in=compressed_state_in,
            char_in='_',
            state_out=compressed_state_out,
            char_out=compressed_char_out,
            direction=Directions.R
        ))
    return compressed_transitions


################################################################
# STAGE 2 -> STAGE 3
################################################################


def build_transitions_stage_three_to_four(compressed_moves_going_right: set[MoveInfo], compressed_states_map_moving_right: dict[MovingStageInfo, int], compressed_states_map_moving_left: dict[MovingStageInfo, int], n_tapes: int) -> list[tuple[TransitionIn, TransitionOut]]:
    compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []
    no_heads = tuple([False] * n_tapes)
    # we see a blank ('_') and we're done moving all the heads to the right. Let's forget about them and start moving heads to the left.
    for original_state, old_directions in compressed_moves_going_right:
        # replace all the Directions.R with Directions.N
        new_directions = tuple([Directions.N if direction == Directions.R else direction for direction in old_directions])
        # we already moved all the heads to the right
        compressed_state_in = compressed_states_map_moving_right[original_state, old_directions, no_heads]
        # and we didn't find any head to move to the left yet
        compressed_state_out = compressed_states_map_moving_left[original_state, new_directions, no_heads]
        # build transition
        # don't write anything, just change states and go left
        compressed_transitions.append(build_transition(
            state_in=compressed_state_in,
            char_in='_',
            state_out=compressed_state_out,
            char_out='_',
            direction=Directions.L
        ))
    return compressed_transitions


################################################################
# STAGE 4
################################################################


def build_transitions_stage_four(compressed_alphabet: list[Char], compressed_states_map_moving_left: dict[MovingStageInfo, int], n_tapes: int) -> list[tuple[TransitionIn, TransitionOut]]:
    compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []
    moving_stage_infos: Iterable[MovingStageInfo] = compressed_states_map_moving_left.keys()
    for compressed_char_in in compressed_alphabet:
        for original_state, directions, dropped_heads in moving_stage_infos:
            # we can't find a head immediately after we just found it
            if head_clash_moving(compressed_char_in, dropped_heads, n_tapes):
                continue
            # save what heads we're finding on the tapes
            picked_up_char, picked_up_heads = pick_up_heads(compressed_char_in, directions, n_tapes, desired_direction=Directions.L)
            # write down the heads we just found in the previous cell
            compressed_char_out = drop_heads(picked_up_char, dropped_heads, n_tapes)
            # figure out states
            compressed_state_in = compressed_states_map_moving_left[original_state, directions, dropped_heads]
            compressed_state_out = compressed_states_map_moving_left[original_state, directions, picked_up_heads]
            # build transition
            compressed_transitions.append(build_transition(
                state_in=compressed_state_in,
                char_in=compressed_char_in,
                state_out=compressed_state_out,
                char_out=compressed_char_out,
                direction=Directions.L
            ))
    return compressed_transitions


################################################################
# STAGE 4 -> STAGE 1
################################################################


def build_transitions_stage_four_to_one(compressed_moves_going_left: set[MoveInfo], compressed_states_map_moving_left: dict[MovingStageInfo, int], compressed_states_map_reading: dict[ReadingStageInfo, int], n_tapes) -> list[tuple[TransitionIn, TransitionOut]]:
    # if we find the actual start ('S'), just go back to ready state and
    compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []
    no_heads = tuple([False] * n_tapes)
    # we pretty much only care about the original state
    for original_state, directions in compressed_moves_going_left:
        # just go on with the whole simulation if we're not in an endstate
        if is_endstate(original_state):
            continue
        compressed_state_in = compressed_states_map_moving_left[original_state, directions, no_heads]
        # no matter what directions we wrote, what heads we dropped, whatever. just forget about it.
        # remember the state we're in however
        saved_chars = ' ' * n_tapes
        compressed_state_out = compressed_states_map_reading[original_state, saved_chars]
        # just go into ready state and move right
        compressed_transitions.append(build_transition(
            state_in=compressed_state_in,
            char_in='S',
            state_out=compressed_state_out,
            char_out='S',
            direction=Directions.R
        ))
    return compressed_transitions


################################################################
# STAGE 4 -> STAGE 5 / END STATE
################################################################


def build_transitions_stage_four_to_five(compressed_moves_going_left: set[MoveInfo], compressed_states_map_moving_left: dict[MovingStageInfo, int], n_tapes) -> list[tuple[TransitionIn, TransitionOut]]:
    # if we find the actual start ('S'), just go back to ready state and
    compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []
    no_heads = tuple([False] * n_tapes)
    # we pretty much only care about the original state
    for original_state, directions in compressed_moves_going_left:
        # just go on with the whole simulation if we're not in an endstate
        if not is_endstate(original_state):
            continue
        compressed_state_in = compressed_states_map_moving_left[original_state, directions, no_heads]
        # no matter what directions we wrote, what heads we dropped, whatever. just forget about it.
        # either accept or reject
        if original_state in [EndStates.ACCEPT, EndStates.REJECT]:
            compressed_transitions.append(build_transition(
                state_in=compressed_state_in,
                char_in='S',
                state_out=original_state,
                char_out='S',
                direction=Directions.N
            ))
        # halt state -> cleanup
        else:
            compressed_transitions.append(build_transition(
                state_in=compressed_state_in,
                char_in='S',
                state_out=STATE_CLEANUP,
                char_out='S',
                direction=Directions.R
            ))
    return compressed_transitions


################################################################
# STAGE 5
################################################################


def build_transitions_stage_five(original_alphabet: list[Char], compressed_start_alphabet: list[Char], compressed_non_start_alphabet: list[Char], compressed_states_map_cleanup: dict[Char, int]) -> list[tuple[TransitionIn, TransitionOut]]:
    compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []
    compressed_alphabet = compressed_start_alphabet + compressed_non_start_alphabet

    # first go right no matter what compressed char we see
    for observed_compressed_char in compressed_alphabet:
        compressed_transitions.append(build_transition(
            state_in=STATE_CLEANUP,
            char_in=observed_compressed_char,
            state_out=STATE_CLEANUP,
            char_out=observed_compressed_char,
            direction=Directions.R
        ))

    # then if we find blank ('_'), go left and start copying the last tape (and shifting)
    remembered_blank = compressed_states_map_cleanup['_']
    compressed_transitions.append(build_transition(
        state_in=STATE_CLEANUP,
        char_in='_',
        state_out=remembered_blank,
        char_out='_',
        direction=Directions.L
    ))

    # remember the current char in a state. also write down the previous remembered char
    for remembered_char in original_alphabet + ['_']:
        for observed_compressed_char in compressed_non_start_alphabet:
            # doesn't matter what compressed char we observe, we only care for the char on the last tape.
            char_on_last_tape = observed_compressed_char[-1]
            # we remembered the char
            compressed_state_in = compressed_states_map_cleanup[remembered_char]
            # now we want to remember the char on the last tape
            compressed_state_out = compressed_states_map_cleanup[char_on_last_tape]
            # build transition
            compressed_transitions.append(build_transition(
                state_in=compressed_state_in,
                char_in=observed_compressed_char,
                state_out=compressed_state_out,
                char_out=remembered_char,
                direction=Directions.L
            ))

    # if we find the artificial start symbol, write down the last remembered char and halt.
    for remembered_char in original_alphabet + ['_']:
        for compressed_start_char in compressed_start_alphabet:
            compressed_state_in = compressed_states_map_cleanup[remembered_char]
            compressed_transitions.append(build_transition(
                state_in=compressed_state_in,
                char_in=compressed_start_char,
                state_out=EndStates.HALT,
                char_out=remembered_char,
                direction=Directions.N
            ))
    return compressed_transitions

################################################################
# PRETTY MUCH MAIN
################################################################


def state_map_to_array(state_map: dict[int, Any], used_states: set[int]) -> list[tuple[int, str, str]]:
    return [(state, "->", mapped_to) for mapped_to, state in state_map.items() if state in used_states]


def state_map_array_to_str(state_map: list[tuple[int, str, str]]) -> str:
    return tabulate(state_map,
                    colalign=['left'] * 3,
                    tablefmt='plain')


def state_map_to_str(state_map: dict[int, Any], used_states: set[int]) -> str:
    return state_map_array_to_str(state_map_to_array(state_map, used_states))


def compress(original_function: TransitionFunction, save_states_map=False, states_map_file: str = None) -> TransitionFunction:
    """Compresses a k-tape transition function into a 1-tape transition function."""

    n_tapes = original_function.n_tapes
    original_input_alphabet = original_function.alphabet
    # extract info from the original function
    original_trans_ins = extract_trans_ins(original_function)
    original_trans_outs = extract_trans_outs(original_function)
    # all of the possible directions we can go (where the headers are moved)
    original_moves = extract_moves(original_function)

    # start compressing
    compressed_start_alphabet, compressed_non_start_alphabet = compress_alphabet(original_input_alphabet, n_tapes)
    # the whole alphabet consists of the start chars and the non-start chars
    compressed_alphabet = compressed_start_alphabet + compressed_non_start_alphabet

    # start counting states at 1 above the max reserved states
    next_state = MAX_RESERVED_STATE + 1
    compressed_states_map_copying, next_state = compress_states_copying(original_input_alphabet, start_at=next_state)

    # compressed states start at 1 (state 0 is instantly converted to a compressed state)
    possible_incomplete_char_saves = generate_incomplete_saves(original_trans_ins, n_tapes)
    compressed_states_map_reading, next_state = compress_states_reading(possible_incomplete_char_saves, start_at=next_state)
    compressed_states_map_writing, next_state = compress_states_writing(original_trans_outs, start_at=next_state)

    # now consider all orders in which headers can be found
    compressed_moves_going_right, compressed_moves_going_left = generate_possible_moves(original_moves)
    # and compress them all into states
    compressed_states_map_moving_right, next_state = compress_states_moving(compressed_moves_going_right, going=Directions.R, start_at=next_state)
    compressed_states_map_moving_left, next_state = compress_states_moving(compressed_moves_going_left, going=Directions.L, start_at=next_state)

    # and maybe we need to clean up (we're essentially just copying chars here again)
    compressed_states_map_cleanup, next_state = compress_states_cleanup(original_input_alphabet, start_at=next_state)

    # start building the transitions
    compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []
    compressed_transitions += build_transitions_stage_zero(original_input_alphabet, compressed_states_map_copying, n_tapes)
    compressed_transitions += build_transitions_stage_zero_to_one(compressed_alphabet, compressed_states_map_reading, n_tapes)
    compressed_transitions += build_transitions_stage_one(compressed_alphabet, compressed_states_map_reading, n_tapes)
    compressed_transitions += build_transitions_stage_one_to_two(original_function, compressed_states_map_reading, compressed_states_map_writing)
    compressed_transitions += build_transitions_stage_two(compressed_alphabet, compressed_states_map_writing, n_tapes)
    compressed_transitions += build_transitions_stage_two_to_three(compressed_start_alphabet, compressed_states_map_writing, compressed_states_map_moving_right, n_tapes)
    compressed_transitions += build_transitions_stage_three(compressed_alphabet, compressed_states_map_moving_right, n_tapes)
    compressed_transitions += build_transitions_stage_three_to_four(compressed_moves_going_right, compressed_states_map_moving_right, compressed_states_map_moving_left, n_tapes)
    compressed_transitions += build_transitions_stage_four(compressed_alphabet, compressed_states_map_moving_left, n_tapes)
    compressed_transitions += build_transitions_stage_four_to_one(compressed_moves_going_left, compressed_states_map_moving_left, compressed_states_map_reading, n_tapes)
    compressed_transitions += build_transitions_stage_four_to_five(compressed_moves_going_left, compressed_states_map_moving_left, n_tapes)
    compressed_transitions += build_transitions_stage_five(original_input_alphabet, compressed_start_alphabet, compressed_non_start_alphabet, compressed_states_map_cleanup)

    # build transition function
    # we might not use all the states we created
    used_states = extract_non_end_states(compressed_transitions)
    n_states = len(used_states)
    compressed_function = TransitionFunction(n_states, 1, original_input_alphabet + compressed_alphabet)
    for trans_in, trans_out in compressed_transitions:
        compressed_function._add(trans_in, trans_out)

    if save_states_map:
        print("Saving state map.")
        save_states_str = "=== RESERVED ===\n"
        reserved_array = [
            (STATE_START, "->", "start state"),
            (STATE_INIT_GO_LEFT, "->", "state after copying, now go left"),
            (STATE_READY, "->", "simulation starts now"),
            (STATE_CLEANUP, "->", "simulation halted, let's clean up"),
            (STATE_BLANK_INPUT, "->", "observed blank input")
        ]
        save_states_str += state_map_array_to_str(reserved_array)
        save_states_str += "\n=== COPYING ===\n"
        save_states_str += state_map_to_str(compressed_states_map_copying, used_states)
        save_states_str += "\n=== READING ===\n"
        save_states_str += state_map_to_str(compressed_states_map_reading, used_states)
        save_states_str += "\n=== WRITING ===\n"
        save_states_str += state_map_to_str(compressed_states_map_writing, used_states)
        save_states_str += "\n=== MOVING RIGHT ===\n"
        save_states_str += state_map_to_str(compressed_states_map_moving_right, used_states)
        save_states_str += "\n=== MOVING LEFT ===\n"
        save_states_str += state_map_to_str(compressed_states_map_moving_left, used_states)
        save_states_str += "\n=== CLEANUP ===\n"
        save_states_str += state_map_to_str(compressed_states_map_cleanup, used_states)
        with open(states_map_file, 'w') as f:
            f.write(save_states_str)

    return compressed_function


def main():
    parser = argparse.ArgumentParser(description="Compresses a k-tape Turing Machine into a 1-tape Turing Machine.")
    parser.add_argument("tm",
                        help="File with the encoded Turing Machine.")
    parser.add_argument("-m", "--savemap",
                        action='store_true',
                        help="Also saves a map with explanations of the states.")
    parser.add_argument("--test",
                        action=test.test_action(test.test_compression),
                        help="Tests the compression of some selected Turing Machines (no other arguments needed).")
    args = parser.parse_args()

    # load tm
    original = TransitionFunction.from_file(args.tm)
    out_file = f"machines/{Path(args.tm).stem}_compressed.txt"
    map_file = f"maps/{Path(args.tm).stem}_compressed_map.txt"
    print("Compressing.")
    compressed = compress(original, save_states_map=args.savemap, states_map_file=map_file)
    print("Saving transtition function.")
    compressed.save(out_file)
    print("Transition function saved.")
    # try to load the transition function to check if it is a working encoding
    print("Checking saved encoding.")
    TransitionFunction.from_file(out_file)
    print("Saved encoding checked.")


if __name__ == "__main__":
    main()
