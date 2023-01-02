from enum import Enum
from cnf import CNF, Clause, Variable


ZERO_BIT = 1


class LogicalOperator(Enum):
    AND = "^"
    OR = "v"
    NEGATE = "-"


# operator, out, in1, in2
Gate = tuple[LogicalOperator, Variable, Variable, Variable]


def to_clauses(gate: Gate) -> list[Clause]:
    operator, out, in1, in2 = gate
    if operator == LogicalOperator.AND:
        return [[-out, in1], [-out, in2], [out, -in1, -in2]]
    if operator == LogicalOperator.OR:
        return [[-out, in1, in2], [out, -in1], [out, -in2]]
    if operator == LogicalOperator.NEGATE:
        assert in1 == in2, f"Negate inputs should be the same (it has only 1 input): {gate}"
        return [[out, in1], [-out, -in1]]


class Circuit:
    def __init__(self, inputs: list[Variable], gates: list[Gate]) -> None:
        self.inputs = inputs
        self.gates = gates

    def sat_equivalent_cnf(self) -> CNF:
        # first len(inputs) variables are reserved for the input variables
        for gate in self.gates:
            operator, out, in1, in2 = gate
            assert out not in self.inputs, f"Can't reassign input variables."
        # we need 1 variable for every gate and 1 for every input variable
        n_variables = len(self.inputs) + len(self.gates)
        # combine all the clauses of the gates
        clauses = [clause for gate in self.gates for clause in to_clauses(gate)]
        n_clauses = len(clauses)
        return CNF(n_variables, n_clauses, clauses)


class HalfAdder(Circuit):
    size = 6

    def __init__(self, a: Variable, b: Variable, start_at: int) -> None:
        gates: list[Gate] = [
            # carry bit
            (LogicalOperator.AND, start_at, a, b),
            # -a
            (LogicalOperator.NEGATE, start_at + 1, a, a),
            # -b
            (LogicalOperator.NEGATE, start_at + 2, b, b),
            # -a ^ b
            (LogicalOperator.NEGATE, start_at + 3, start_at + 1, b),
            # a ^ -b
            (LogicalOperator.NEGATE, start_at + 4, a, start_at + 2),
            # a xor b (sum bit)
            (LogicalOperator.OR, start_at + 5, start_at + 3, start_at + 4),
        ]
        # remember the output bits
        self.sum_bit = start_at + 5
        self.carry_bit = start_at
        super().__init__([a, b], gates)


class FullAdder(Circuit):
    size = 2 * HalfAdder.size + 1

    def __init__(self, a: Variable, b: Variable, c_in: Variable, start_at: int) -> None:
        half_adder_1 = HalfAdder(a, b, start_at)
        half_adder_2 = HalfAdder(half_adder_1.sum_bit, c_in, start_at + HalfAdder.size)
        # full adder is made out of: 2 half adders and 1 disjunction
        gates: list[Gate] = half_adder_1.gates + half_adder_2.gates + [(LogicalOperator.OR, start_at + 2 * HalfAdder.size, half_adder_1.carry_bit, half_adder_2.carry_bit)]
        # remember output bits
        self.sum_bit = half_adder_2.sum_bit
        self.c_out = start_at + 2 * HalfAdder.size
        super().__init__([a, b, c_in], gates)


class RCA(Circuit):
    """Ripple-Carry Adder"""

    def __init__(self, a: list[Variable], b: list[Variable], n_bits: int, start_at: int) -> None:
        assert n_bits >= 1, "RCA has to be at least 1 bit wide."
        assert len(a) == n_bits and len(b) == n_bits, "Number of input bits has to be the same as the passed number of bits."

        # first adder is a half adder
        half_adder = HalfAdder(a[0], b[0], start_at)
        # remaining adders are full adders
        full_adders: list[FullAdder] = [None] * (n_bits - 1)
        for i in range(n_bits - 1):
            # figure out where to start
            full_adder_start = start_at + HalfAdder.size + i * FullAdder.size
            # connect the carry bits
            c_in = full_adders[i - 1].c_out if i > 0 else half_adder.carry_bit
            # where to read the bit
            input_bit = i + 1
            # build full adders
            full_adders[i] = FullAdder(a[input_bit], b[input_bit], c_in, full_adder_start)

        # assemble gates
        gates = half_adder.gates + [gate for adder in full_adders for gate in adder.gates]

        # remember output bits
        self.sum_bits: list[Variable] = [half_adder.sum_bit] + [adder.sum_bit for adder in full_adders]
        self.carry_bit = full_adders[-1].c_out

        super().__init__(a + b, gates)

    @classmethod
    def size(cls, n_bits: int) -> int:
        return HalfAdder.size + (n_bits - 1) * FullAdder.size


class CountBitsCircuit(Circuit):
    """Sums up the input bits and saves the result in an `n_bits`-size number."""

    def __init__(self, inputs: list[Variable], n_bits: int, start_at: int) -> None:
        # convert all the input bits to n-bit numbers (pad left with zeros)
        input_numbers: list[list[Variable]] = [[ZERO_BIT] * (n_bits - 1) + [bit] for bit in inputs]

        # add up the input bits with n-bit RCAs
        adders: list[RCA] = [None] * (len(inputs) - 1)
        for i in range(len(inputs) - 1):
            rca_start = start_at + i * RCA.size(n_bits)
            # first argument: last adder's sum or first number
            a = adders[i - 1].sum_bits if i > 0 else input_numbers[0]
            # second argument: next number
            b = input_numbers[i + 1]
            adders[i] = RCA(a, b, n_bits, rca_start)

        # assemble gates
        gates = [gate for adder in adders for gate in adder.gates]

        # output is the last sum
        self.sum_bits = adders[-1].sum_bits

        # careful! ZERO_BIT was used for padding and is also an input to the circuit
        super().__init__(inputs + [ZERO_BIT], gates)


def main():
    print(FullAdder.size)


if __name__ == "__main__":
    main()
