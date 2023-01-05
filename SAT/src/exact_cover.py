import random

from bit_util import to_bits
from cnf import CNF, Variable, Clause


def exact_cover(n: int, S: list[list[int]]) -> bool:
    """Does an exact cover S' subset S exist, such that every i in [n] is in exactly 1 set in S'?"""


def gen_subset(subset_id: int) -> list[int]:
    return [i for i, bit in enumerate(to_bits(subset_id), start=1) if bit]


def gen_instance(n: int, s_size: int) -> list[list[int]]:
    """Generates a random instance of the Exact Cover problem.

    Parameters
    ----------
    n : int
        Number of elements to choose from.
    s_size : int
        Size of S.

    Returns
    -------
    list[list[int]]
        S, a subset of 2^[n].
    """

    assert s_size <= 2**n, "Subset size can't be greater than 2^n."

    possible_subset_ids = list(range(1, 2**n))
    subset_ids = random.sample(possible_subset_ids, s_size)
    return [gen_subset(subset_id) for subset_id in subset_ids]


def subset_to_bits(subset: list[int]) -> int:
    """Turns a subset into a bitset ([1, 3, 7] -> 1000101)."""

    bit_str = 0
    for m in subset:
        # least significant bit describes if 1 is in set
        bit_str |= 1 << (m - 1)
    return bit_str


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
    bit_subsets: list[int] = [subset_to_bits(subset) for subset in S]
    for subset1, s_var1 in zip(bit_subsets, S_variables):
        for subset2, s_var2 in zip(bit_subsets, S_variables):
            # if they share an element, they can't both be active
            if subset1 & subset2 != 0:
                clauses.append([-s_var1, -s_var2])

    # build cnf
    n_variables = n + len(S)
    n_clauses = len(clauses)
    return CNF(n_variables, n_clauses, clauses)


def main():
    n = 7
    s_size = 5
    n_instances = 10
    for i in range(n_instances):
        sets = gen_instance(n, s_size)
        print(f"Instance {i}:\t{sets}")
        cnf = exact_cover_cnf(n, sets)
        out_file = f"cnfs/ex_cov_{i}.txt"
        cnf.write(out_file, comment=f"Exact Cover generated CNF. n={n} S={sets}")


if __name__ == "__main__":
    main()
