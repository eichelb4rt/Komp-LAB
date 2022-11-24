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
################################################################

# used states:
# 0: start state
# 1: go left (after converting input)
# 2: ready for simulation
READY_STATE = 2

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


def extract_states(transitions: list[tuple[TransitionIn, TransitionOut]]) -> set[int | EndStates]:
    states: set[int | EndStates] = set()
    for t_in, t_out in transitions:
        state_in, chars_in = t_in
        state_out, chars_and_dirs_out = t_out
        chars_out, dirs_out = zip(*chars_and_dirs_out)
        states.add(state_in)
        states.add(state_out)
    return states


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


def compress_states_copying(original_alphabet: list[Char], start_at=2) -> bidict[Char, int]:
    """Builds states for stage 0. In stage 0, we have to remember the last char on the tape. That's one state for every char."""
    
    compressed_states_map: bidict[Char, int] = bidict()
    next_state = start_at
    for char in original_alphabet:
        compressed_states_map[char] = next_state
        next_state += 1
    return compressed_states_map, next_state


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

def build_transition(state_in: int, char_in: Char, state_out: int | EndStates, char_out: Char, direction: Directions) -> tuple[TransitionIn, TransitionOut]:
    t_in = (state_in, [char_in])
    t_out = (state_out, [(char_out, direction)])
    return t_in, t_out


################################################################
# STATE 0
################################################################


def build_transitions_stage_zero(original_alphabet: list[Char], compressed_states_map_copying: bidict[Char, int], n_tapes: int) -> list[tuple[TransitionIn, TransitionOut]]:
    compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []
    
    # add an artificial start symbol (*S*S*S)
    compressed_start_char = "*S" * n_tapes
    # whatever char there is on the first cell, remember it and put the artificial start symbol there
    for replaced_char in original_alphabet:
        # remember the replaced char in a state
        state_out = compressed_states_map_copying[replaced_char]
        # replace it with the atificial start symbol and go right
        compressed_transitions.append(build_transition(
            state_in=0,
            char_in=replaced_char,
            state_out=state_out,
            char_out=compressed_start_char,
            direction=Directions.R
        ))
        
    # now shift all the chars 1 to the right
    for replaced_char in original_alphabet:
        for prev_char in original_alphabet:
            # we remembered the previous char
            state_in = compressed_states_map_copying[prev_char]
            # remember the replaced char in a state
            state_out = compressed_states_map_copying[replaced_char]
            # we can just write the compressed char immediately
            compressed_char = prev_char + '_' * (n_tapes - 1)
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
        # we remembered the previous char
        state_in = compressed_states_map_copying[prev_char]
        # we can just write the compressed char immediately
        compressed_char = last_char + '_' * (n_tapes - 1)
        compressed_transitions.append(build_transition(
            state_in=state_in,
            char_in=original_char,
            state_out=1,
            char_out=compressed_char,
            direction=Directions.L
        ))
        
    # now go back, doesn't matter what's on the tape
    for original_char in original_alphabet:
        compressed_char = original_char + '_' * (n_tapes - 1)
        compressed_transitions.append(build_transition(
            state_in=1,
            char_in=compressed_char,
            state_out=1,
            char_out=compressed_char,
            direction=Directions.L
        ))
    
    # if we find the artificial start symbol again, go into the ready state
    compressed_transitions.append(build_transition(
        state_in=1,
        char_in=compressed_start_char,
        state_out=READY_STATE,
        char_out=compressed_start_char,
        direction=Directions.N
    ))
    
    return compressed_transitions


################################################################
# STATE 0 -> STAGE 1
################################################################


def build_transitions_stage_zero_to_one(compressed_alphabet: list[Char], compressed_states_map_reading: bidict[ReadingStageInfo, int], n_tapes: int) -> list[tuple[TransitionIn, TransitionOut]]:
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
            state_in=READY_STATE,
            char_in=char_in,
            state_out=state_out,
            char_out=char_in,
            direction=Directions.N
        ))
    return compressed_transitions


################################################################
# STAGE 1
################################################################


def header_clash(char_in: Char, saved_chars: str, n_tapes: int) -> bool:
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

    # make a mutable representation
    new_saved_chars = list(old_saved_chars)
    for i in range(n_tapes):
        # if we find a header on tape i
        if char_in[2 * i] == '*':
            # save the respective char on tape i
            new_saved_chars[i] = char_in[2 * i + 1]
    # make it immutable again
    return "".join(new_saved_chars)


def build_transitions_stage_one(compressed_alphabet: list[Char], compressed_states_map_reading: bidict[ReadingStageInfo, int], n_tapes: int) -> list[tuple[TransitionIn, TransitionOut]]:
    compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []
    # now add transitions for reading chars if there's the header there
    incomplete_saves = compressed_states_map_reading.keys()
    # we observe some chars
    for char_in in compressed_alphabet:
        # and we already saved these chars
        for original_state_in, old_save in incomplete_saves:
            # the header can only be at one position at the same time, so the following situation can't occur:
            # we observe a header and there's already a char read at that position
            # so we can just skip these cases
            if header_clash(char_in, old_save, n_tapes):
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


def build_transitions_stage_one_to_two(original_function: TransitionFunction, compressed_states_map_reading: bidict[ReadingStageInfo, int], compressed_states_map_writing: bidict[WritingStageInfo, int], n_tapes: int) -> list[tuple[TransitionIn, TransitionOut]]:
    compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []
    incomplete_saves = compressed_states_map_reading.keys()
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


def build_transitions_stage_two(compressed_non_start_alphabet: list[Char], compressed_states_map_writing: bidict[WritingStageInfo, int], n_tapes: int) -> list[tuple[TransitionIn, TransitionOut]]:
    compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []
    trans_outs: list[TransitionOut] = compressed_states_map_writing.keys()
    # we observe some chars, not the start chars tho. we don't write start chars.
    for char_in in compressed_non_start_alphabet:
        # we want to write some chars
        for original_state, chars_and_dirs_out in trans_outs:
            # if we find headers, write on them
            char_out = write_compressed(char_in, chars_and_dirs_out, n_tapes)
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


def build_transitions_stage_two_to_three(compressed_start_alphabet: list[Char], compressed_states_map_writing: bidict[WritingStageInfo, int], compressed_states_map_moving_right: bidict[MovingStageInfo, int], n_tapes: int) -> list[tuple[TransitionIn, TransitionOut]]:
    compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []
    trans_outs: list[TransitionOut] = compressed_states_map_writing.keys()
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
        

def build_transitions_stage_three(compressed_alphabet: list[Char], compressed_states_map_moving_right: bidict[MovingStageInfo, int], n_tapes: int) -> list[tuple[TransitionIn, TransitionOut]]:
    pass

################################################################
# PRETTY MUCH MAIN
################################################################


def compress(original_function: TransitionFunction) -> TransitionFunction:
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
    
    # used states:
    # 0: start state
    # 1: go left (after converting input)
    # 2: ready for simulation
    next_state = READY_STATE + 1
    compressed_states_map_copying, next_state = compress_states_copying(original_input_alphabet, start_at=next_state)

    # compressed states start at 1 (state 0 is instantly converted to a compressed state)
    possible_incomplete_char_saves = generate_incomplete_saves(original_trans_ins, n_tapes)
    compressed_states_map_reading, next_state = compress_states_reading(possible_incomplete_char_saves, start_at=next_state)
    compressed_states_map_writing, next_state = compress_states_writing(original_trans_outs, start_at=next_state)

    # now consider all orders in which headers can be found
    compressed_going_right, compressed_moves_going_left = generate_possible_moves(original_moves)
    # and compress them all into states
    compressed_states_map_moving_right, next_state = compress_states_moving(compressed_going_right, going=Directions.R, start_at=next_state)
    compressed_states_map_moving_left, next_state = compress_states_moving(compressed_moves_going_left, going=Directions.L, start_at=next_state)

    # print("STATES READING")
    # print(compressed_states_map_reading)
    # print("STATES WRITING")
    # print(compressed_states_map_writing)
    # print("STATES MOVING RIGHT")
    # print(compressed_states_map_moving_right)
    # print("STATES MOVING LEFT")
    # print(compressed_states_map_moving_left)

    # start building the transitions
    compressed_transitions: list[tuple[TransitionIn, TransitionOut]] = []
    compressed_transitions += build_transitions_stage_zero(compressed_alphabet, compressed_states_map_copying, n_tapes)
    compressed_transitions += build_transitions_stage_zero_to_one(compressed_alphabet, compressed_states_map_reading, n_tapes)
    compressed_transitions += build_transitions_stage_one(compressed_alphabet, compressed_states_map_reading, n_tapes)
    compressed_transitions += build_transitions_stage_one_to_two(original_function, compressed_states_map_reading, compressed_states_map_writing, n_tapes)
    compressed_transitions += build_transitions_stage_two(compressed_non_start_alphabet, compressed_states_map_writing, n_tapes)
    compressed_transitions += build_transitions_stage_two_to_three(compressed_start_alphabet, compressed_states_map_writing, compressed_states_map_moving_right, n_tapes)

    # add transitions for step 1:

    # step 2: if we found the end of the tape, convert the current state and the saved chars to the desired output
    # this is where the actual work of the original Turing Machine is done

    # we read all tapes so every tape must have a saved char

    # TODO: if original goes into q_h, clean up all the stuff and write down the output
    # TODO: ask if we also need to do this
    # build transition function
    # we might not use all the states we created
    n_states = len(extract_states(compressed_transitions))
    compressed_function = TransitionFunction(n_states, 1, compressed_alphabet)
    for trans_in, trans_out in compressed_transitions:
        compressed_function._add(trans_in, trans_out)
    return compressed_function


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
    compressed.save(out_file)
    print("Transition function saved.")
    # try to load the transition function to check if it is a working encoding
    TransitionFunction.from_file(out_file)
    print("Saved encoding checked.")


if __name__ == "__main__":
    main()
