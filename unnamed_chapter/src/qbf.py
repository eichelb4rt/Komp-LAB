import argparse
from enum import Enum
from typing import Optional, Self
from io import TextIOWrapper


class Quantor(Enum):
    E = 'E'
    A = 'A'


QUANTOR_CHARS = [quantor.value for quantor in Quantor]


Variable = int
Literal = int
Clause = list[Literal]
QuantifiedVariables = tuple[Quantor, list[Variable]]


def skip_comments(f: TextIOWrapper) -> str:
    while line := f.readline():
        if line[0] != 'c':
            return line
    return ""


class QBF:
    def __init__(self, n: int, c: int, prefix: list[QuantifiedVariables], clauses: list[Clause]) -> None:
        self.n = n
        self.c = c
        self.prefix = prefix
        self.clauses = clauses
        # the quantifiers have to alternate
        for i in range(1, len(prefix)):
            current_quantor, current_vars = prefix[i]
            previous_quantor, previous_vars = prefix[i - 1]
            assert current_quantor != previous_quantor, f"Quantors have to alternate! Quantor {i} and {i - 1} are the same ({current_quantor})."

    def write(self, filename: str, comment: Optional[str] = None):
        """Writes the QBF to a file with QDIMACS encoding.

        Parameters
        ----------
        filename : str
            File that the QDIMACS encoded QBF is written to.
        comment : str, optional
            A comment that is written into the first line of the file.
        """

        dimacs_str = ""
        # maybe write a comment in the first line
        if comment is not None:
            dimacs_str += f"c {comment}\n"
        # specify n and c in first line
        dimacs_str += f"p cnf {self.n} {self.c}\n"
        # add prefix
        for quantor, variables in self.prefix:
            dimacs_str += f"{str(quantor.value).lower()} {' '.join([str(variable) for variable in variables])} 0\n"
        # add clauses
        for clause in self.clauses:
            # all the literals separated by space
            dimacs_str += " ".join([str(literal) for literal in clause]) + " 0\n"

        with open(filename, 'w') as f:
            f.write(dimacs_str)

    @classmethod
    def from_file(cls, filename: str) -> Self:
        """Reads a QDIMACS encoded QBF from a file.

        Parameters
        ----------
        filename : str
            File with QDIMACS encoded QBF.
        """

        with open(filename, 'r') as f:
            # skip comments to find first line and remove the line break on the right
            firstline = skip_comments(f).rstrip()
            # p cnf <n> <c>
            firstline_args = firstline.split(" ")
            assert len(firstline_args) == 4, f"First line not valid QDIMACS: {firstline} (should be 'p cnf <n> <c>')."
            n = int(firstline_args[2])
            c = int(firstline_args[3])
            # read prefix and then matrix
            prefix: list[QuantifiedVariables] = []
            clauses: list[Clause] = []
            # read next encoded clause as long as we can
            first_clause_found = False
            while line := skip_comments(f):
                # remove line break
                line = line.rstrip()
                # check if the first char is a quantor (quantor chars are uppercase here)
                if line[0].upper() in QUANTOR_CHARS:
                    # if we already found a clause, we can't have any more quantors
                    assert not first_clause_found, f"Found quantor after first clause: {line}"
                    # process quantor
                    quantor = Quantor(line[0].upper())
                    variables = [int(variables) for variables in line.split(" ")[1:]]
                    assert variables[-1] == 0, f"Non-0-terminated prefix: {line}"
                    # quantors have to alternate
                    if len(prefix) > 0:
                        prev_quantor, prev_vars = prefix[-1]
                        assert quantor != prev_quantor, f"Contiguous quantor: {line}"
                    prefix.append((quantor, variables[:-1]))
                else:
                    first_clause_found = True
                    # get the literals seperated by space
                    literals = [int(literal) for literal in line.split(" ")]
                    assert literals[-1] == 0, f"Non-0-terminated clause: {line}"
                    # the clause is all the literals except for the terminating 0
                    clauses.append(literals[:-1])

        # check if c is correct
        assert len(clauses) == c, f"Clause amount ({len(clauses)}) is not the same as promised ({c})."
        # check if n is correct
        used_variables = set([abs(literal) for clause in clauses for literal in clause])
        assert len(used_variables) == n, f"Variable amount ({len(used_variables)}) is not the same as promised ({n})."
        # check if variables are all the numbers from 1..n
        for used_variable in used_variables:
            assert used_variable >= 1 and used_variable <= n, f"Used variable is out of bounds: {used_variable} (bounds: [1, {n}])."
        # check if all variables are bound exactly once
        already_bound: set[Variable] = set()
        for quantor, variables in prefix:
            for variable in variables:
                assert used_variable >= 1 and used_variable <= n, f"Used variable is out of bounds: {used_variable} (bounds: [1, {n}])."
                assert variable not in already_bound, f"Variable was bound twice: {variable}."
                already_bound.add(variable)
        assert len(already_bound) == n, f"Not all variables bound (all: {n}, bound: {len(already_bound)})."

        return cls(n, c, prefix, clauses)

    def __repr__(self) -> str:
        quantified_str = "".join(f"{quantor.value}{str(vars)}" for quantor, vars in self.prefix)
        return f"{quantified_str}: {str(self.clauses)}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input",
        type=str,
        help="Input file where QDIMACS notation of a formula is stored."
    )
    args = parser.parse_args()
    qbf = QBF.from_file(args.input)
    print(qbf)


if __name__ == "__main__":
    main()
