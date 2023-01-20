import argparse
import random

from bit_util import to_bits
from exact_cover import write_instance


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


def main():
    parser = argparse.ArgumentParser(description="Generates random instaces of Exact Cover.")
    parser.add_argument(
        "n_instances",
        type=int,
        help="Number of generated instances."
    )
    parser.add_argument(
        "n_vars",
        type=int,
        help="Number of variables."
    )
    parser.add_argument(
        "s_size",
        type=int,
        help="Size of generated S."
    )
    args = parser.parse_args()

    for i in range(args.n_instances):
        sets = gen_instance(args.n_vars, args.s_size)
        out_file = f"inputs/exact_cover_{i}.random.txt"
        write_instance(out_file, args.n_vars, sets)


if __name__ == "__main__":
    main()
