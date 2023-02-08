from qbf import QBF, Variable, Literal, Quantor, QuantifiedVariables


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
    for i in range(prefix_widths):
        # quantor on the very right is E w.l.o.g. (?)
        quantor = Quantor.E if (n_vars - i) % 2 == 0 else Quantor.A
        quantified_vars = list(range(already_added + 1, already_added + prefix_widths[i] + 1))
        prefix[i] = (quantor, quantified_vars)
    


def main():
    gen_qbf_chen_interian(10, (2, 3), (4, 5))


if __name__ == "__main__":
    main()
