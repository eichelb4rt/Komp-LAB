import argparse
from typing import Self
from io import TextIOWrapper


# variables are positive integers
Variable = int
# literals are variables with a sign
Literal = int
Clause = list[Literal]


def skip_comments(f: TextIOWrapper):
    while line := f.readline():
        if line[0] != 'c':
            return line


class CNF:
    def __init__(self, n: int, c: int, clauses: list[Clause]):
        self.n = n
        self.c = c
        self.clauses = clauses

    def __repr__(self) -> str:
        return repr(self.clauses)

    def write(self, filename: str, comment: str = None):
        """Writes the CNF to a file with DIMACS encoding.

        Parameters
        ----------
        filename : str
            File that the DIMACS encoded CNF is written to.
        comment : str, optional
            A comment that is written into the first line of the file.
        """

        dimacs_str = ""
        # maybe write a comment in the first line
        if comment is not None:
            dimacs_str += f"c {comment}\n"
        # specify n and c in first line
        dimacs_str += f"p cnf {self.n} {self.c}\n"
        for clause in self.clauses:
            # all the literals separated by space
            dimacs_str += " ".join([str(literal) for literal in clause]) + " 0\n"

        with open(filename, 'w') as f:
            f.write(dimacs_str)

    @classmethod
    def from_file(cls, filename: str) -> Self:
        """Reads a DIMACS encoded CNF from a file.

        Parameters
        ----------
        filename : str
            File with DIMACS encoded CNF.
        """

        with open(filename, 'r') as f:
            # skip comments to find first line and remove the line break on the right
            firstline = skip_comments(f).rstrip()
            # p cnf <n> <c>
            firstline_args = firstline.split(" ")
            assert len(firstline_args) == 4, f"First line not valid DIMACS: {firstline} (should be 'p cnf <n> <c>')."
            n = int(firstline_args[2])
            c = int(firstline_args[3])

            # read cnf
            clauses: list[Clause] = []
            # read next encoded clause as long as we can
            while encoded_clause := skip_comments(f):
                # remove line break
                encoded_clause = encoded_clause.rstrip()
                # get the literals seperated by space
                literals = [int(literal) for literal in encoded_clause.split(" ")]
                assert literals[-1] == 0, f"Non-0-terminated clause: {encoded_clause}"
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

        return CNF(n, c, clauses)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input",
        type=str,
        help="Input file where DIMACS notation of a formular is stored."
    )
    args = parser.parse_args()
    cnf = CNF.from_file(args.input)
    print(cnf)


if __name__ == "__main__":
    main()
