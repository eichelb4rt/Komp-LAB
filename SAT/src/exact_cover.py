import ast
import glob
import argparse
from io import TextIOWrapper
from pathlib import Path
from bit_util import to_bits
from cnf import CNF, Variable, Clause
from dpll import DPLLSolver

from test import TestAction


################################################################
# FUNCTIONALITY
################################################################


def exact_cover(n: int, S: list[list[int]]) -> tuple[bool, list[list[int]]]:
    """Returns True and an exact cover if it exists, False and None otherwise."""

    # convert subsets to bitstrings
    S_bitstrings = [subset_to_bitstring(subset) for subset in S]
    # at the start, every element is remaining
    done_elements = 0
    # compute a solution with bitstrings and convert it back to a normal solution.
    possible, solution = exact_cover_bin(n, done_elements, S_bitstrings)
    if possible:
        solution = [bitstring_to_subset(bitstring) for bitstring in solution]
    return possible, solution


def exact_cover_bin(n: int, done_elements: int, S: list[int]) -> tuple[bool, list[int]]:
    """Same as exact cover, but represents subsets and elements as bitstrings (int)."""

    # check if we already have a solution
    # if all elements are done, we got a solution
    if done_elements == 2**n - 1:
        return True, []
    # if elements are remaining and there are no remaining subsets, there is no solution with these selected elements
    elif len(S) == 0:
        return False, None

    # if there are elements remaining and there are subsets remaining, try to find a solution
    # compute a solution recursively
    for selected_subset in S:
        # compute all the disjoint sets
        # a subset and another set are disjunct precisely when the conjunction is 0.
        disjoint_sets = [disjoint_set for disjoint_set in S if not (selected_subset & disjoint_set)]
        # the new done elements are all the elements that are already done and the ones in the selected subsets
        new_done_elements = done_elements | selected_subset
        # compute if there is an exact cover of the remaining elements in the disjoint sets
        possible, solution = exact_cover_bin(n, new_done_elements, disjoint_sets)
        # if there is one, just append the selected subset and it is a solution
        if possible:
            return True, solution + [selected_subset]
    # it's not possible for any of the selected sets until now
    return False, None


def subset_to_bitstring(subset: list[int]) -> int:
    """Turns a subset into a bitset ([1, 3, 7] -> 1000101)."""

    bit_str = 0
    for element in subset:
        # least significant bit describes if 1 is in set
        bit_str |= 1 << (element - 1)
    return bit_str


def bitstring_to_subset(subset_bitstr: int) -> list[int]:
    """Turns a given bitset into a set of integer elements (1000101 -> [1, 3, 7])."""

    return [element for element, bit in enumerate(to_bits(subset_bitstr), start=1) if bit]


def exact_cover_cnf(n: int, S: list[list[int]]) -> CNF:
    # make variable for every m in [n]
    m_variables: list[Variable] = list(range(1, n + 1))
    # make variable for every set in S
    S_variables: list[Variable] = list(range(n + 1, len(S) + n + 1))
    # encode that all m variables have to be found
    clauses: list[Clause] = [[m] for m in m_variables]
    # encode where we can find those variables
    # "if we take this set, this variables are gonna be in them"
    for subset, s_var in zip(S, S_variables):
        for m in subset:
            # we can find element m in subset s_var
            clauses.append([-s_var, m])
    # "if we find this variable, it has to have been one of these sets"
    for m in m_variables:
        found_in: list[Variable] = [s_var for subset, s_var in zip(S, S_variables) if m in subset]
        # 2 can be found in set 8, 9, and 12:
        # 2 => 8 v 9 v 12
        clauses.append([-m] + found_in)
    # encode that we can't pick 2 subsets that share elements
    bit_subsets: list[int] = [subset_to_bitstring(subset) for subset in S]
    for subset1, s_var1 in zip(bit_subsets, S_variables):
        for subset2, s_var2 in zip(bit_subsets, S_variables):
            # if they share an element, they can't both be active
            if subset1 != subset2 and subset1 & subset2 != 0:
                clauses.append([-s_var1, -s_var2])

    # build cnf
    n_variables = n + len(S)
    n_clauses = len(clauses)
    return CNF(n_variables, n_clauses, clauses)


def skip_comments(f: TextIOWrapper) -> str:
    while line := f.readline():
        if line[0] != '#':
            return line
    return ""


def from_file(filename: str) -> tuple[int, list[list[int]]]:
    with open(filename, 'r') as f:
        # get n and the size of s
        firstline = skip_comments(f)
        n, s_size = [int(c) for c in firstline.split(" ")]
        # read S
        s: list[list[int]] = []
        while line := skip_comments(f):
            subset = ast.literal_eval(line)
            # assert the subsets contain valid numbers
            assert all([element >= 1 and element <= n for element in subset]), f"Invalid element found in {subset}, n={n}."
            # this doesn't really prevent different permutations, but it's not that important anyway
            assert subset not in s, f"Elements in S should be unique (found duplicate: {subset})."
            s.append(subset)
        assert len(s) == s_size, f"Promised size of S ({s_size}) does not match observed size ({len(s)})."
    return n, s


def write_instance(filename: str, n: int, S: list[list[int]]):
    with open(filename, 'w') as f:
        s_size = len(S)
        out_str = f"{n} {s_size}\n"
        out_str += "\n".join(map(str, S))
        f.write(out_str)


################################################################
# TESTS
################################################################


def test_exact_cover():
    solver = DPLLSolver()
    for filename in glob.glob("inputs/EC_*.txt"):
        n, sets = from_file(filename)
        recursive_result, _ = exact_cover(n, sets)
        cnf = exact_cover_cnf(n, sets)
        cnf_result = solver.solve(cnf)
        assert recursive_result == cnf_result
    print("Exact cover test: all tests passed.")


################################################################
# MAIN
################################################################


def main():
    parser = argparse.ArgumentParser(description="Computes the exact cover for an Exact Cover instance from a file.")
    parser.add_argument("filename",
                        help="File with the Exact Cover instance.")
    parser.add_argument("--cnf",
                        action='store_true',
                        help="Builds and saves a cnf for the problem instead of solving it recursively.")
    parser.add_argument("--test",
                        action=TestAction.build(test_exact_cover),
                        help="Tests the implementation (no other arguments needed).")
    args = parser.parse_args()

    n, sets = from_file(args.filename)
    # if there is the empty set in the sets, then remove it (the empty set is very annoying here)
    if [] in sets:
        sets = [subset for subset in sets if subset != []]
    # write the cnf for the instance
    if args.cnf:
        cnf = exact_cover_cnf(n, sets)
        out_file = f"inputs/cnf_{Path(args.filename).stem}.txt"
        cnf.write(out_file, comment=f"Exact Cover generated CNF. n={n} S={sets}")
        print(f"CNF written to: {out_file}")
    # or just solve it
    else:
        # TODO: make naming of S/sets consistent
        possible, solution = exact_cover(n, sets)
        if possible:
            print(f"Partition does exist: {solution}")
        else:
            print(f"Partition does not exist.")


if __name__ == "__main__":
    main()
