import argparse
from types import NoneType
from typing import Optional
from qbf import Quantor, Variable, Clause, QBF, Literal


def literal_true(literal: Literal, assignment: bool | NoneType) -> bool:
    if assignment is None:
        return False
    # literal > 0 -> variable has to be True, literal < 0 -> variable has to be False
    return (literal > 0) == assignment


def literal_false(literal: Literal, assignment: bool | NoneType) -> bool:
    if assignment is None:
        return False
    # literal > 0 -> variable has to be False, literal < 0 -> variable has to be True
    return (literal < 0) == assignment


class QDPLLSolver:
    def __init__(self) -> None:
        # [(var, bool)] - order of assignment
        self.assignments_view: list[tuple[Variable, bool]]
        # fast access variable assignment - variable (x) stored at index (x-1)
        self.assignments: list[bool | NoneType]
        # original cnf
        self.qbf: QBF
        # the indices of the clauses that the literals are contained in
        self.occurences: dict[Literal, int]

    def solve(self, qbf: QBF) -> bool:
        """Checks if a CNF is satisfiable."""

        self.assignments_view = []
        self.assignments = [None] * qbf.n_vars
        self.qbf = qbf
        self.occurences = {sign * var: [] for var in range(1, qbf.n_vars + 1) for sign in [-1, 1]}
        for i, clause in enumerate(qbf.clauses):
            for literal in clause:
                self.occurences[literal].append(i)
        return self.is_satisfiable()

    def is_satisfiable(self) -> bool:
        """Checks if the formula is satisfiable with the current assignments."""

        # check for TERMINATION - Arnold Schwarzenegger style
        if self.cnf_empty():
            return True
        if self.cnf_contains_contradiction():
            return False

        # see if we have to set some literal
        unit_literal = self.get_unit_literal()
        if unit_literal is not None:
            assignment = True if unit_literal > 0 else False
            self.assign(abs(unit_literal), assignment)
            return self.is_satisfiable()
        # maybe not a unit literal, but a pure one?
        unit_literal = self.get_pure_literal()
        if unit_literal is not None:
            assignment = True if unit_literal > 0 else False
            self.assign(abs(unit_literal), assignment)
            return self.is_satisfiable()

        # this should never actually return None, because if all variables are assigned, the qbf is trivially either true or not
        variable = self.get_next_variable()
        # remember the entry point for backtracking
        entry_point = self.n_assigned_vars()
        # remember if it's a universal or existential variable
        quantor = self.qbf.get_quantor(variable)

        if quantor == Quantor.E:
            # if it's an existential variable, try to satisfy the formula
            # try to set the variable to False and see what happens
            self.assign(variable, False)
            if self.is_satisfiable():
                return True
            self.backtrack(entry_point)
            # try to set the variable to True and see what happens
            self.assign(variable, True)
            if self.is_satisfiable():
                return True
            self.backtrack(entry_point)
            # current formula is not satisfiable, regardless how we set the variable
            return False

        # quantor == Quantor.A
        else:
            # if it's a universal quantor, try to get a contradiction
            # try to set the variable to False and see what happens
            self.assign(variable, False)
            if not self.is_satisfiable():
                return False
            self.backtrack(entry_point)
            # try to set the variable to True and see what happens
            self.assign(variable, True)
            if not self.is_satisfiable():
                return False
            self.backtrack(entry_point)
            # current formula can't get a contradiction, regardless how we set the variable
            return True

    def cnf_empty(self) -> bool:
        """Checks if the current cnf is empty."""

        for clause in self.qbf.clauses:
            if not self.clause_satisfied(clause):
                return False
        return True

    def cnf_contains_contradiction(self) -> bool:
        """Checks if the contradiction (empty clause) is contained in the current CNF."""

        for clause in self.qbf.clauses:
            if self.is_contradiction(clause):
                return True
        return False

    def is_contradiction(self, clause: Clause) -> bool:
        """Checks if the clause is the contraction with the current assignment."""

        for literal in clause:
            variable = abs(literal)
            var_assignment = self.get_assignment(variable)
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

    def get_next_variable(self) -> Optional[Variable]:
        """Gets the next unassigned variable if some are left, None otherwise."""

        # start enumerating at 1, this way we immediately get the respective variable
        for quantor, variables in self.qbf.prefix:
            for variable in variables:
                if not self.is_assigned(variable):
                    return variable
        return None

    def assign(self, variable: Variable, assignment: bool):
        self.assignments_view.append((variable, assignment))
        self.assignments[variable - 1] = assignment

    def get_assignment(self, variable: Variable) -> Optional[bool]:
        """Gets the assignment of a variable, None if it wasn't assigned yet."""

        return self.assignments[variable - 1]

    def is_assigned(self, variable: Variable) -> bool:
        return self.get_assignment(variable) is not None

    def backtrack(self, step: int):
        """Backtracks to the given step. Unassigns every assignment after the first `step` assignments."""

        # erase all assignments after step `step`
        for assigned_var, assignment in self.assignments_view[step:]:
            self.assignments[assigned_var - 1] = None
        del self.assignments_view[step:]

    def n_assigned_vars(self) -> int:
        return len(self.assignments_view)

    def get_unit_literal(self) -> Optional[Variable]:
        """Returns a unit literal if one exists, None otherwise."""

        for clause in self.qbf.clauses:
            unit_literal = self.get_unit_literal_in_clause(clause)
            if unit_literal is not None:
                return unit_literal
        return None

    def get_unit_literal_in_clause(self, clause: Clause) -> Optional[Literal]:
        """Gets a unit literal from the clause if it exists, None otherwise."""

        # get all unassigned literals in that clause
        unassigned_literals = [literal for literal in clause if not self.is_assigned(abs(literal))]
        existential_unassigned_literals = [literal for literal in unassigned_literals if self.qbf.get_quantor(abs(literal)) == Quantor.E]
        # a literal can't be unit in a clause if there is more than one unassigned existential literal in that clause
        if len(existential_unassigned_literals) != 1:
            return None
        # a literal can't be unit in a clause if that clause is already satisfied
        if self.clause_satisfied(clause):
            return None
        potential_unit_literal = existential_unassigned_literals[0]
        # see if all unassigned literals in the clause besides the potential unit literal are universal that are quantified after the variable of the unit literal
        for literal in unassigned_literals:
            # we allow the unit literal itself
            if literal == potential_unit_literal:
                continue
            # we can now assume that all of the literals are universal (because the potential unit literal is the only existential one in the clause)
            # if there's any unassigned universal literal in the clause that is unassigned and comes before the potential unit literal, then the literal is not unit
            if not self.qbf.is_bound_after(abs(literal), abs(potential_unit_literal)):
                return None
        return potential_unit_literal

    def get_pure_literal(self) -> Optional[Literal]:
        """Gets a pure literal if it exists, None otherwise"""

        unassigned_variables: list[Variable] = [variable for variable in range(1, self.qbf.n_vars + 1) if not self.is_assigned(variable)]
        # indices of the unsatisfied clauses
        satisfied_clauses: set[int] = {i for i, clause in enumerate(self.qbf.clauses) if self.clause_satisfied(clause)}
        for variable in unassigned_variables:
            # see how many times the variable occurs as a positive literal
            positive_occurences = len([clause_index for clause_index in self.occurences[variable] if clause_index not in satisfied_clauses])
            # and as a negative literal
            negative_occurences = len([clause_index for clause_index in self.occurences[-variable] if clause_index not in satisfied_clauses])
            # if one of them is 0 and the other  isn't, we got a pure literal on our hands
            quantor = self.qbf.get_quantor(variable)
            if positive_occurences > 0 and negative_occurences == 0:
                # what pure literal we got changes with the quantor that the variable is bound to
                if quantor == Quantor.E:
                    return variable
                else:
                    return -variable
            elif positive_occurences == 0 and negative_occurences > 0:
                if quantor == Quantor.E:
                    return -variable
                else:
                    return variable
        return None


def main():
    parser = argparse.ArgumentParser(description="Checks if a QBF is true (satisfiable).")
    parser.add_argument(
        "input",
        type=str,
        help="Input file where QDIMACS encoding of a formula is stored."
    )
    args = parser.parse_args()
    qbf = QBF.from_file(args.input)
    solver = QDPLLSolver()
    satisfiable = solver.solve(qbf)
    if satisfiable:
        print(f"true (satisfiable), assignments: {solver.assignments_view}")
    else:
        print("false (unsatisfiable)")


if __name__ == "__main__":
    main()
