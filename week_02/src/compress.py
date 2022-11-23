import argparse
from enum import Enum
import itertools
from pathlib import Path
from bidict import bidict

from chars import Char
from transitions import SPECIAL_CHARS, Directions, EndStates, TransitionFunction, TransitionIn, TransitionOut, is_endstate

################################################################
# PLAN
# ==============================================================
# loop:

# stage 1 (reading):
# from left to right, collect what chars we see

# stage 1 -> stage 2:
# when on the right, figure out what stuff to write

# stage 2 (writing):
# go back (left), write it

# stage 3 (moving right):
# go right, move some heads to the right

# stage 4 (moving left):
# go left, move some heads to the left
################################################################

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


def extract_states(trans_fun: TransitionFunction) -> set[int | EndStates]:
    """Extracts all states from a transition function."""

    states: set[int | EndStates] = set()
    for t_in, t_out in trans_fun._transitions.items():
        state_in, chars_in = t_in
        state_out, chars_and_dirs_out = t_out
        states.add(state_in)
        states.add(state_out)
    return states


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


################################################################
# COMPRESS DIRECTIONS
################################################################


def directions_apply_found(directions: tuple[Directions], found_vector: tuple[bool]) -> tuple[Directions]:
    """Replaces the directions where we found the headers with `Directions.N`."""

    # make it mutable
    new_directions = list(directions)
    for tape_index, found_header in enumerate(found_vector):
        if found_header:
            new_directions[tape_index] = Directions.N
    # make it immutable again
    return tuple(new_directions)


def possible_found_vectors(directions: tuple[Directions], going: Directions) -> list[tuple[bool]]:
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
    possibilities_right: set[MoveInfo] = set()
    for state_out, directions in original_moves:
        # add possibilities for if we found them or not
        # this only needs to be done for headers we want to move to the right, we don't care about left here (we just set them to False)
        found_vectors = possible_found_vectors(directions, going=Directions.R)
        for found_vector in found_vectors:
            new_directions = directions_apply_found(directions, found_vector)
            possibilities_right.add((state_out, new_directions))

    # now computer all ways the headers can be found going left
    # note that we already found all the headers that have to be moved right
    possibilities_left: set[tuple[Directions]] = set()
    for state_out, directions in original_moves:
        # we found every Directions.R
        new_directions = directions_apply_found(directions, [direction == Directions.R for direction in directions])
        found_vectors = possible_found_vectors(new_directions, going=Directions.L)
        for found_vector in found_vectors:
            new_directions = directions_apply_found(new_directions, found_vector)
            possibilities_left.add((state_out, new_directions))

    return possibilities_right, possibilities_left


################################################################
# COMPRESS ALPHABET AND GENERATE CHAR SAVES
################################################################


def compress_alphabet(original_input_alphabet: list[Char], n_tapes: int) -> list[Char]:
    """Compresses all possible combinations of headers and chars into one compressed char each."""

    # first add all the possible combinations of chars without the start symbol ('S')
    compressed_alphabet = ["".join(chars) for chars in itertools.product(HEAD_ALPHABET, original_input_alphabet + ['_'], repeat=n_tapes)]
    # start symbol can only be in one position
    compressed_alphabet += ["".join(chars) for chars in itertools.product(HEAD_ALPHABET, ['S'], repeat=n_tapes)]
    return compressed_alphabet


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


def compress_states_reading(incomplete_saves: set[tuple[int, str]], start_at: int) -> bidict[ReadingStageInfo, int]:
    """Builds a bidirectional dictionary that maps from every occuring combination of original state and saved chars to one compressed state each.
    (original state, saved chars) -> compressed state

    Returns that dict and the next unassigned state."""

    # map from current original state and saved chars to respective compressed state
    compressed_states_map: bidict[ReadingStageInfo, int] = bidict()

    # add states for reading
    # for all combinations of states and k (k = number of tapes) chars, make a new compressed state for reading
    next_state = start_at
    for incomplete_save in incomplete_saves:
        compressed_states_map[incomplete_save] = next_state
        next_state += 1

    # add states for moving headers in any direction (this is only need when moving headers to the right)
    return compressed_states_map, next_state


def compress_states_writing(original_trans_outs: set[TransitionOut], start_at: int) -> bidict[WritingStageInfo, int]:
    """Builds a bidirectional dictionary that maps from every combination of original state and finished saved chars to one compressed state each.
    (original state, write vector) -> compressed state

    Returns that dict and the maximum state assigned"""

    # map from current original state and saved chars to respective compressed state
    compressed_states_map: bidict[WritingStageInfo, int] = bidict()

    # add states for writing
    next_state = start_at
    for trans_out in original_trans_outs:
        compressed_states_map[trans_out] = next_state
        next_state += 1

    # add states for moving headers in any direction (this is only need when moving headers to the right)
    return compressed_states_map, next_state


def compress_states_moving(possible_moves: set[MoveInfo], going: Directions, start_at: int) -> bidict[MovingStageInfo, int]:
    """Builds a bidirectional dictionary that maps from every combination of original state and list of directions to one compressed state each.
    (original state, directions, header found) -> compressed state

    Returns that dict and the maximum state assigned"""

    # map from current original state and saved chars to respective compressed state
    compressed_states_map: bidict[MovingStageInfo, int] = bidict()

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


################################################################
# BUILD TRANSITIONS
################################################################


def header_clashes(char_in: Char, saved_chars: str, n_tapes: int) -> bool:
    """Returns `True` if we already saved a char on some tape, but then found another header."""

    for i in range(n_tapes):
        # every 2nd char in `char_in` indicates if the header is there
        header_found = char_in[2 * i] == '*'
        # if the char read at position `i` isn't empty, we already found a char for that tape
        char_found = saved_chars[i] != ' '
        if header_found and char_found:
            return True
    return False


def save_new_chars(char_in: Char, old_saved_chars: str, n_tapes: int) -> str:
    """Saves chars on tapes where a header is."""

    new_saved_chars = old_saved_chars
    for i in range(n_tapes):
        # if we find a header on tape i
        if char_in[2 * i] == '*':
            # save the respective char on tape i
            new_saved_chars[i] = char_in[2 * i + 1]
    return new_saved_chars


def build_transition(state_in: int, char_in: Char, state_out: int | EndStates, char_out: Char, direction: Directions) -> tuple[TransitionIn, TransitionOut]:
    t_in = (state_in, [char_in])
    t_out = (state_out, [(char_out, direction)])
    return t_in, t_out


################################################################
# PRETTY MUCH MAIN
################################################################


def compress(original_function: TransitionFunction) -> TransitionFunction:
    """Compresses a k-tape transition function into a 1-tape transition function."""

    n_tapes = original_function.n_tapes
    # alphabets
    original_input_alphabet = original_function.alphabet
    original_working_alphabet = original_function.alphabet + SPECIAL_CHARS
    # extract info from the original function
    original_states = extract_states(original_function)
    original_trans_ins = extract_trans_ins(original_function)
    original_trans_outs = extract_trans_outs(original_function)
    # all of the possible directions we can go (where the headers are moved)
    original_moves = extract_moves(original_function)

    # NOTE: in the reading stage, ' ' is used for tapes where the char hasn't been encountered yet.
    # NOTE: in the writing stage, ' ' isn't needed because we don't care if a char has already been written or not.

    # start compressing
    compressed_alphabet = compress_alphabet(original_input_alphabet, n_tapes)

    # compressed states start at 1 (state 0 is instantly converted to a compressed state)
    possible_incomplete_char_saves = generate_incomplete_saves(original_trans_ins, n_tapes)
    compressed_states_map_reading, next_state = compress_states_reading(possible_incomplete_char_saves, start_at=1)
    compressed_states_map_writing, next_state = compress_states_writing(original_trans_outs, start_at=next_state)

    # now consider all orders in which headers can be found
    compressed_going_right, compressed_moves_going_left = generate_possible_moves(original_moves)
    # and compress them all into states
    compressed_states_map_moving_right, next_state = compress_states_moving(compressed_going_right, going=Directions.R, start_at=next_state)
    compressed_states_map_moving_left, next_state = compress_states_moving(compressed_moves_going_left, going=Directions.L, start_at=next_state)

    print("STATES READING")
    print(compressed_states_map_reading)
    print("STATES WRITING")
    print(compressed_states_map_writing)
    print("STATES MOVING RIGHT")
    print(compressed_states_map_moving_right)
    print("STATES MOVING LEFT")
    print(compressed_states_map_moving_left)

    # TODO: add states for what we can write on the tapes
    # TODO: need to add the direction we're going

    # # start building the transitions
    # compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []

    # # add transitions for step 1:
    # # we're in "compressed" state 0:
    # # we haven't read anything yet. no matter what is on the tapes, go into the state where nothing is read yet.
    # for char_in in compressed_alphabet:
    #     state_in = 0
    #     # go into compressed state:
    #     # original state is 0 and we haven't saved anything
    #     state_out = compressed_states_map[0, ' ' * original_function.n_tapes]
    #     # don't write anything
    #     char_out = char_in
    #     # don't move anything
    #     direction = Directions.N
    #     # add it to the list
    #     compressed_transitions.append(build_transition(state_in, char_in, state_out, char_out, direction))

    # # now add transitions for reading chars if there's the header there
    # possible_saves = compressed_states_map.keys()
    # # we observe some chars
    # for char_in in compressed_alphabet:
    #     # and we already saved these chars
    #     for old_saved_chars in possible_saves:
    #         # the header can only be at one position at the same time, so the following situation can't occur:
    #         # we observe a header and there's already a char read at that position
    #         # so we can just skip these cases
    #         if header_clashes(char_in, old_saved_chars, original_function.n_tapes):
    #             continue
    #         # figure out which chars to save
    #         new_saved_chars = save_new_chars(char_in, old_saved_chars, original_function.n_tapes)
    #         # construct transition
    #         # we're in some state
    #         for original_state in original_states:
    #             # no matter what original state we're in, just keep it.
    #             state_in = compressed_states_map[original_state, old_saved_chars]
    #             state_out = compressed_states_map[original_state, new_saved_chars]
    #             # don't write anything, go to the next char
    #             char_out = char_in
    #             direction = Directions.R
    #             compressed_transitions.append(build_transition(state_in, char_in, state_out, char_out, direction))

    # step 2: if we found the end of the tape, convert the current state and the saved chars to the desired output
    # this is where the actual work of the original Turing Machine is done

    # we read all tapes so every tape must have a saved char

    # TODO: if original goes into q_h, clean up all the stuff and write down the output
    # TODO: ask if we also need to do this


def main():
    parser = argparse.ArgumentParser(description="Compresses a k-tape Turing Machine into a 1-tape Turing Machine.")
    parser.add_argument("tm",
                        help="File with the encoded Turing Machine.")
    args = parser.parse_args()

    # load tm
    original = TransitionFunction.from_file(args.tm)
    out_file = f"machines/{Path(args.tm).stem}_compressed.txt"
    print("Compressing.")
    compressed = compress(original)
    print("Saving transtition function.")
    original.save(out_file)
    print("Transition function saved.")
    # try to load the transition function to check if it is a working encoding
    TransitionFunction.from_file(out_file)
    print("Saved encoding checked.")


if __name__ == "__main__":
    main()
