import argparse
from types import NoneType
from cnf import Variable, Clause, CNF, literal_true, literal_false


class DPLLSolver:
    def __init__(self) -> None:
        # [(var, bool)] - order of assignment
        self.assignments_view: list[tuple[Variable, bool]]
        # fast access variable assignment - variable (x) stored at index (x-1)
        self.assignments: list[bool | NoneType]
        # original cnf
        self.original_formula: CNF

    def solve(self, cnf: CNF) -> bool:
        """Checks if a CNF is satisfiable."""

        self.assignments_view = []
        self.assignments = [None] * cnf.n
        self.original_formula = cnf
        return self.is_satisfiable()

    def is_satisfiable(self) -> bool:
        """Checks if the formula is satisfiable with the current assignments."""

        # check for TERMINATION - Arnold Schwarzenegger style
        if self.cnf_empty():
            return True
        if self.cnf_contains_contradiction():
            return False

        # this should never actually return None, because if all variables are assigned, the cnf is trivially either true or not
        variable = self.get_next_variable()
        # try to set the variable to False and see what happens
        self.assign(variable, False)
        if self.is_satisfiable():
            return True
        self.unassign_last()
        # try to set the variable to True and see what happens
        self.assign(variable, True)
        if self.is_satisfiable():
            return True
        self.unassign_last()

        # current formula is not satisfiable, regardless how we set the variable
        return False

    def cnf_empty(self) -> bool:
        """Checks if the current cnf is empty."""

        for clause in self.original_formula.clauses:
            if not self.clause_satisfied(clause):
                return False
        return True

    def cnf_contains_contradiction(self) -> bool:
        """Checks if the contradiction (empty clause) is contained in the current CNF."""

        for clause in self.original_formula.clauses:
            if self.is_contradiction(clause):
                return True
        return False

    def is_contradiction(self, clause: Clause) -> bool:
        """Checks if the clause is the contraction with the current assignment."""

        for literal in clause:
            variable = abs(literal)
            var_assignment = self.assignments[variable - 1]
            # all literals have to be either unassigned or true
            # if all literals are falsified, the clause is a contradiction
            if not literal_false(literal, var_assignment):
                return False
        return True

    def clause_satisfied(self, clause: Clause) -> bool:
        """Checks if the clause is already satisfied by the current assignment."""

        for literal in clause:
            variable = abs(literal)
            var_assignment = self.assignments[variable - 1]
            if literal_true(literal, var_assignment):
                return True
        return False

    def get_next_variable(self) -> Variable | NoneType:
        """Gets the next unassigned variable.

        Returns
        -------
        Variable | NoneType
            The next unassigned variable if one exists, None otherwise.
        """

        # start enumerating at 1, this way we immediately get the respective variable
        for variable, assignment in enumerate(self.assignments, 1):
            if assignment is None:
                return variable
        return None

    def assign(self, variable: Variable, assignment: bool):
        self.assignments_view.append((variable, assignment))
        self.assignments[variable - 1] = assignment

    def unassign_last(self):
        # this function is effectively used for backtracking
        last_assigned_var, assignment = self.assignments_view[-1]
        self.assignments[last_assigned_var - 1] = None
        del self.assignments_view[-1]


def main():
    parser = argparse.ArgumentParser(description="Checks if a CNF is satisfiable.")
    parser.add_argument(
        "input",
        type=str,
        help="Input file where DIMACS notation of a formula is stored."
    )
    args = parser.parse_args()
    cnf = CNF.from_file(args.input)
    solver = DPLLSolver()
    satisfiable = solver.solve(cnf)
    if satisfiable:
        print(f"satisfiable, assignments: {solver.assignments_view}")
    else:
        print("unsatisfiable")


if __name__ == "__main__":
    main()
