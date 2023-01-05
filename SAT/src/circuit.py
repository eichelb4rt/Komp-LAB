from enum import Enum
import itertools
from cnf import CNF, Clause, Variable


ZERO_BIT = 1
MAX_RESERVED_VARIABLE = ZERO_BIT


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
        self.size = len(gates)

    def tseitin(self) -> CNF:
        """Transforms the Circuit into a CNF with new variables for every gate and the relations between them. Does not include the clause that sets the output gate to 1."""

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

    def evaluate(self, input_assignments: list[bool], output_vars: list[Variable]) -> list[bool]:
        assignments: dict[Variable, bool] = {variable: assignment for variable, assignment in zip(self.inputs, input_assignments)}
        self.gates.sort(key=lambda gate: gate[1])
        for gate in self.gates:
            operator, out, in1, in2 = gate
            assert out > in1 and out > in2, f"Gate output should always be greater than inputs. ({gate})"
            if operator == LogicalOperator.AND:
                assignments[out] = assignments[in1] and assignments[in2]
            elif operator == LogicalOperator.OR:
                assignments[out] = assignments[in1] or assignments[in2]
            elif operator == LogicalOperator.NEGATE:
                assert in1 == in2, f"Negate inputs should be the same (it has only 1 input): {gate}"
                assignments[out] = not assignments[in1]
        return [assignments[output_var] for output_var in output_vars]


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
            (LogicalOperator.AND, start_at + 3, start_at + 1, b),
            # a ^ -b
            (LogicalOperator.AND, start_at + 4, a, start_at + 2),
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
        # build first half adder
        half_adder_1 = HalfAdder(a, b, start_at)
        start_at += HalfAdder.size
        # build second half adder, connected to first sum bit
        half_adder_2 = HalfAdder(half_adder_1.sum_bit, c_in, start_at)
        start_at += HalfAdder.size
        # full adder is made out of: 2 half adders and 1 disjunction
        gates: list[Gate] = half_adder_1.gates + half_adder_2.gates + [(LogicalOperator.OR, start_at, half_adder_1.carry_bit, half_adder_2.carry_bit)]
        # remember output bits
        self.sum_bit = half_adder_2.sum_bit
        # c_out is the result of the last gate (disjunction)
        self.c_out = start_at
        super().__init__([a, b, c_in], gates)


class RCA(Circuit):
    """Ripple-Carry Adder"""

    def __init__(self, a: list[Variable], b: list[Variable], n_bits: int, start_at: int) -> None:
        assert n_bits >= 1, "RCA has to be at least 1 bit wide."
        assert len(a) == n_bits and len(b) == n_bits, "Number of input bits has to be the same as the passed number of bits."

        # first adder is a half adder
        half_adder = HalfAdder(a[0], b[0], start_at)
        # 2nd adder starts after half adder
        start_at += half_adder.size
        # remaining adders are full adders
        full_adders: list[FullAdder] = [None] * (n_bits - 1)
        for i in range(n_bits - 1):
            # connect the carry bits
            c_in = full_adders[i - 1].c_out if i > 0 else half_adder.carry_bit
            # where to read the bit
            input_bit = i + 1
            # build full adders
            full_adders[i] = FullAdder(a[input_bit], b[input_bit], c_in, start_at)
            # next adder starts after this adder
            start_at += full_adders[i].size

        # assemble gates
        gates = half_adder.gates + [gate for adder in full_adders for gate in adder.gates]

        # remember output bits
        self.sum_bits: list[Variable] = [half_adder.sum_bit] + [adder.sum_bit for adder in full_adders]
        self.carry_bit = full_adders[-1].c_out if n_bits > 1 else half_adder.carry_bit

        super().__init__(a + b, gates)


class CountBitsCircuit(Circuit):
    """Sums up the input bits and saves the result in an `n_bits`-size number."""

    def __init__(self, inputs: list[Variable], n_bits: int, start_at: int) -> None:
        # convert all the input bits to n-bit numbers (pad left with zeros)
        input_numbers: list[list[Variable]] = [pad_right_vars([bit], n_bits) for bit in inputs]

        # add up the input bits with n-bit RCAs
        adders: list[RCA] = [None] * (len(inputs) - 1)
        for i in range(len(inputs) - 1):
            # first argument: last adder's sum or first number
            if i == 0:
                arg_1 = input_numbers[0]
            else:
                arg_1 = adders[i - 1].sum_bits
            # second argument: next number
            arg_2 = input_numbers[i + 1]
            adders[i] = RCA(arg_1, arg_2, n_bits, start_at)
            # next adder starts after this adder
            start_at += adders[i].size

        # assemble gates
        gates = [gate for adder in adders for gate in adder.gates]

        # output is the last sum
        self.sum_bits = adders[-1].sum_bits

        # careful! ZERO_BIT was used for padding and is also an input to the circuit
        super().__init__(inputs + [ZERO_BIT], gates)


def pad_right_vars(x: list[Variable], to_size: int) -> list[Variable]:
    left_space = to_size - len(x)
    return x + [ZERO_BIT] * left_space


def pad_right_bits(x: list[int], to_size: int) -> list[int]:
    left_space = to_size - len(x)
    return x + [False] * left_space


def pad_left_bits(x: list[int], to_size: int) -> list[int]:
    left_space = to_size - len(x)
    return [False] * left_space + x


def make_bits_and_vars(x: int, n_bits: int, start_at: int) -> tuple[list[int], list[Variable]]:
    x_bits = [bool(int(bit)) for bit in reversed(bin(x)[2:])]
    x_vars = pad_right_vars(list(range(start_at, start_at + len(x_bits))), n_bits)
    return x_bits, x_vars


def to_number(sum_bits: list[bool]) -> int:
    # lowest bit is at sum_bits[0]
    return int("".join([str(int(bit)) for bit in reversed(sum_bits)]), 2)


def main():
    # test full adder
    for a in [True, False]:
        for b in [True, False]:
            for c_in in [True, False]:
                expected_carry, expected_sum = pad_left_bits([int(bit) for bit in bin(a + b + c_in)[2:]], 2)
                adder = FullAdder(1, 2, 3, start_at=4)
                sum_bit, c_out = adder.evaluate([a, b, c_in], [adder.sum_bit, adder.c_out])
                assert bool(expected_sum) == sum_bit
                assert bool(expected_carry) == c_out

    # test RCA
    n_bits = 5
    for a in range(9):
        for b in range(9):
            # bit representation of a
            a_bits, a_vars = make_bits_and_vars(a, n_bits, start_at=2)
            b_bits, b_vars = make_bits_and_vars(b, n_bits, start_at=2 + len(a_bits))
            # make the adder
            adder = RCA(a_vars, b_vars, n_bits, start_at=2 + len(a_bits) + len(b_bits))
            sum_bits = adder.evaluate(pad_right_bits(a_bits, n_bits) + pad_right_bits(b_bits, n_bits), adder.sum_bits)
            result = to_number(sum_bits)
            assert result == a + b, f"{a} + {b} = {result}?"

    # test bit counter
    n_nodes = 5
    n_bits = 3
    node_vars = list(range(MAX_RESERVED_VARIABLE + 1, MAX_RESERVED_VARIABLE + n_nodes + 1))
    counter = CountBitsCircuit(node_vars, n_bits, start_at=MAX_RESERVED_VARIABLE + n_nodes + 1)
    for bits in itertools.product([True, False], repeat=n_nodes):
        expected_count = sum(bits)
        # don't forget to assign the ZERO_BIT
        sum_bits = counter.evaluate(list(bits) + [False], counter.sum_bits)
        result = to_number(sum_bits)
        assert result == expected_count, f"{bits} has {result} active bits?"

    print(f"Circuit tests: all tests passed.")


if __name__ == "__main__":
    main()
