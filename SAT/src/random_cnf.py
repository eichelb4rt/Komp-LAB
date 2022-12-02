import os
import sys
import random
import argparse
import numpy as np

from cnf import Variable, Clause, CNF


def gen_cnf(n: int, c: int, k: int) -> CNF:
    """
    Generate a random CNF.

    Parameters
    ----------
    n : int
        Number of variables.
    c : int
        Number of clauses.
    k : int
        Clause width.

    Returns
    -------
    CNF
        Returns a CNF with c unique (n,k) clauses.
    """

    clauses: list[Clause] = []
    for _ in range(c):
        # add unique clause
        new_clause = gen_clause(n, k)
        while duplicate_clause_exists(clauses, new_clause):
            new_clause = gen_clause(n, k)
        clauses.append(new_clause)
    return CNF(n, c, clauses)


def duplicate_clause_exists(clauses: list[Clause], new_clause: Clause) -> bool:
    """
    Check if a duplicate there is already a clause similar to the new clause added.

    Parameters
    ----------
    clauses : list[Clause]
        Array with all the clauses.
    new_clause : Clause
        Clause to be checked.

    Returns
    -------
    bool
        True if duplicate clause found, False otherwise.
    """

    for old_clause in clauses:
        if np.all(new_clause == old_clause):    # true if all the values inside the np array are equal
            return True
    return False


def gen_clause(n: int, k: int) -> Clause:
    """
    Generate a random clause.

    Parameters
    ----------
    n : int
        Number of variables.
    k : int
        Clause width.

    Returns
    -------
    Clause
        Returns a random (n,k) clause.
    """

    variables: list[Variable] = random.sample(range(1, n + 1), k)  # choose k from n possible variables
    variables = np.sort(variables)  # sort them (turns into np array)
    # negate the var with a chance of 50% (random.randrange(-1, 2, 2) = 1 in 50%, -1 in 50%)
    literals = [random.randrange(-1, 2, 2) * variable for variable in variables]
    return literals


def main():
    parser = argparse.ArgumentParser(description="Generates random CNFs.")
    parser.add_argument(
        "t",
        type=int,
        help="Number of CNFs"
    )
    parser.add_argument(
        "n",
        type=int,
        help="Number of variables"
    )
    parser.add_argument(
        "c",
        type=int,
        help="Number of clauses"
    )
    parser.add_argument(
        "k",
        type=int,
        help="Clause width"
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="output_dir",
        dest="output",
        default="out",
        help="Directory that the CNFs are written to"
    )
    args = parser.parse_args()

    # check if arguments are viable
    if args.k > args.n:
        sys.stderr.write("Clauses cannot be wider than the number of variables\n")    # assuming there aren"t any tautologies
        sys.exit(1)
    if args.c > 2**args.n:
        sys.stderr.write("CNF cannot have more than 2^n clauses\n")
        sys.exit(1)

    # make the output directory if not existent
    try:
        os.mkdir(args.output)
    except FileExistsError:
        pass
    except Exception:
        print(f"Unable to make directory: {args.output}")

    # write t random CNFs
    for i in range(args.t):
        cnf = gen_cnf(args.n, args.c, args.k)   # generate cnf
        # e.g.: out/random_cnf_0.txts
        cnf.write(f"{args.output}/random_cnf_{i}.txt", comment="random cnf")


if __name__ == "__main__":
    main()
