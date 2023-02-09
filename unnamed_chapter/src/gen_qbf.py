import random
import numpy as np
from qbf import QBF, Clause, Variable, Literal, Quantor, QuantifiedVariables


def gen_qbf_chen_interian(n_clauses: int, clause_widths: tuple[int], prefix_widths: tuple[int]) -> QBF:
    """Generates a QBF with the Chen-Interian model.

    Parameters
    ----------
    n_clauses : int
        Number of clauses generated.
    clause_widths : tuple[int]
        Tuple classifying how many literals from each quantifier block each clause holds.
    prefix_widths : tuple[int]
        Tuple classifying how many variables each quantifier block binds.

    Returns
    -------
    QBF
        Random QBF.
    """

    for clause_width, prefix_width in zip(clause_widths, prefix_widths):
        assert clause_width <= prefix_width, "Can't have more variables from a quantor block than there are variables in a quantor block."
    # prefix_width = (2, 3) -> there are 5 variables in total
    n_vars = sum(prefix_widths)
    # build the prefix
    prefix: list[QuantifiedVariables] = [None] * len(prefix_widths)
    already_added = 0
    for i, prefix_width in enumerate(prefix_widths):
        # quantor on the very right is E w.l.o.g. (?)
        quantor = Quantor.E if (n_vars - i) % 2 == 0 else Quantor.A
        quantified_vars = list(range(already_added + 1, already_added + prefix_width + 1))
        prefix[i] = (quantor, quantified_vars)
        already_added += prefix_width
    # build the matrix
    clauses: list[np.ndarray] = []
    for _ in range(n_clauses):
        # add unique clause
        new_clause = gen_clause(prefix, clause_widths)
        while duplicate_clause_exists(clauses, new_clause):
            new_clause = gen_clause(prefix, clause_widths)
        clauses.append(new_clause)
    # turn the numpy arrays into lists again
    clauses = [clause.tolist() for clause in clauses]
    return QBF(n_vars, n_clauses, prefix, clauses)


def duplicate_clause_exists(clauses: list[np.ndarray], new_clause: np.ndarray) -> bool:
    """
    Check if a duplicate there is already a clause similar to the new clause added.

    Parameters
    ----------
    clauses : list[np.ndarray]
        Array with all the clauses (as numpy arrays - literals are sorted).
    new_clause : np.ndarray
        Clause to be checked (as a numpy array - literals are sorted).

    Returns
    -------
    bool
        True if duplicate clause found, False otherwise.
    """

    for old_clause in clauses:
        # true if all the values inside the np array are equal (this is only possible because the literals are sorted)
        if np.all(new_clause == old_clause):
            return True
    return False


def gen_clause(prefix: list[QuantifiedVariables], clause_widths: tuple[int]) -> np.ndarray:
    """Generate a random clause."""

    # choose k_i variables from block i
    variables: list[Variable] = []
    # add variables for every block
    for (quantor, potential_variables), clause_width in zip(prefix, clause_widths):
        block_vars = random.sample(potential_variables, clause_width)
        variables += block_vars
    # sort them (turns into np array)
    variables = np.sort(variables)
    # negate the var with a chance of 50%
    signs = np.random.choice([-1, 1], size=len(variables))
    return signs * variables


def main():
    qbf = gen_qbf_chen_interian(10, (2, 3), (4, 5))
    print(qbf)


if __name__ == "__main__":
    main()
