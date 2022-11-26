import argparse
from collections.abc import Callable

import tm
import compress
import transitions


def test_action(test_function: Callable[[], None]):
    """Returns test action that can be used as an actual argparse action. Basically returns partial function."""

    return lambda option_strings, dest, **kwargs: test_action_class(option_strings, dest, test_function, **kwargs)


class test_action_class(argparse.Action):
    """This class is for the test flag."""

    def __init__(self, option_strings, dest, test_function: Callable[[], None], **kwargs):
        self._test_function = test_function
        super().__init__(option_strings, dest, nargs=0, default=argparse.SUPPRESS, **kwargs)

    def __call__(self, parser, namespace, values, option_string, **kwargs):
        # if testing flag was set, ignore everything else and just test
        self._test_function()
        parser.exit()


def test_turing_machines():
    """Tests my implemented Turing Machines."""

    assert transitions.EndStates.ACCEPT != 'y'
    assert transitions.EndStates.ACCEPT == transitions.EndStates('y')
    assert transitions.EndStates.ACCEPT in transitions.EndStates

    state: int | transitions.EndStates = 0
    assert type(state) == int
    state = transitions.EndStates.ACCEPT
    assert type(state) == transitions.EndStates

    fun: transitions.TransitionFunction = transitions.TransitionFunction.from_file("machines/tm4.txt")
    assert fun.get(0, ['0']) == (0, [('1', transitions.Directions.R)])

    tm5: tm.TuringMachine = tm.TuringMachine.from_file("machines/tm5.txt")
    assert tm5.result("0100$1101") == "1001"

    # test Turing Machines that were part of the task
    # tm_task1 should accept 0^n 1^n 0^n
    tm_task1: tm.TuringMachine = tm.TuringMachine.from_file("machines/task1.txt")
    for n in range(20):
        # 010
        word = "0" * n + "1" * n + "0" * n
        assert tm_task1.accepts(word), f"Task 1 failed: {word} not accepted."
        # 0100, 0110, 0010
        word = "0" * n + "1" * n + "0" * (n + 1)
        assert tm_task1.rejects(word), f"Task 1 failed: {word} not rejected."
        word = "0" * n + "1" * (n + 1) + "0" * n
        assert tm_task1.rejects(word), f"Task 1 failed: {word} not rejected."
        word = "0" * (n + 1) + "1" * n + "0" * n
        assert tm_task1.rejects(word), f"Task 1 failed: {word} not rejected."
        # 01100, 00100, 00110
        word = "0" * n + "1" * (n + 1) + "0" * (n + 1)
        assert tm_task1.rejects(word), f"Task 1 failed: {word} not rejected."
        word = "0" * (n + 1) + "1" * n + "0" * (n + 1)
        assert tm_task1.rejects(word), f"Task 1 failed: {word} not rejected."
        word = "0" * (n + 1) + "1" * (n + 1) + "0" * n
        assert tm_task1.rejects(word), f"Task 1 failed: {word} not rejected."
    # tm_task2 should add 2 binary numbers
    tm_task2a: tm.TuringMachine = tm.TuringMachine.from_file("machines/task2a.txt")
    tm_task2b: tm.TuringMachine = tm.TuringMachine.from_file("machines/task2b.txt")
    n_numbers_tested = 20
    for x in range(n_numbers_tested):
        for y in range(n_numbers_tested):
            word = f"{bin(x)[2:]}${bin(y)[2:]}"
            expected_result = bin(x + y)[2:]
            result_2a = tm_task2a.result(word)
            assert result_2a == expected_result, f"Task 2a failed: input = {word}, result = {result_2a}, expected = {expected_result}"
            result_2b = tm_task2b.result(word)
            assert result_2b == expected_result, f"Task 2b failed: input = {word}, result = {result_2b}, expected = {expected_result}"

    print("Turing Machines test: all tests passed.")


def test_compression():
    """Tests the Turing Machine compression."""

    # test compression of the copy machine
    tm_copy = tm.TuringMachine.from_file("machines/copy.txt")
    tm_copy_compressed = tm.TuringMachine(compress.compress(tm_copy.transition_function))
    n_numbers_tested = 10
    for x in range(n_numbers_tested):
        word = bin(x)[2:]
        tm_copy.run(word)
        tm_copy_compressed.run(word)
        assert tm_copy.output() == tm_copy_compressed.output(), f"Copy compression failed: input = {word}, normal result = {tm_copy.output()}, compressed_result = {tm_copy_compressed.output()}"

    # test compression of task 1
    tm_task1 = tm.TuringMachine.from_file("machines/task1.txt")
    tm_task1_compressed = tm.TuringMachine(compress.compress(tm_task1.transition_function))
    for n in range(20):
        words = [
            # 010
            "0" * n + "1" * n + "0" * n,
            # 0100, 0110, 0010
            "0" * n + "1" * n + "0" * (n + 1),
            "0" * n + "1" * (n + 1) + "0" * n,
            "0" * (n + 1) + "1" * n + "0" * n,
            # 01100, 00100, 00110
            "0" * n + "1" * (n + 1) + "0" * (n + 1),
            "0" * (n + 1) + "1" * n + "0" * (n + 1),
            "0" * (n + 1) + "1" * (n + 1) + "0" * n
        ]
        for word in words:
            tm_task1.run(word)
            tm_task1_compressed.run(word)
            assert tm_task1.output() == tm_task1_compressed.output(), f"Task 1 compression failed: input = {word}, normal result = {tm_task1.output()}, compressed_result = {tm_task1_compressed.output()}"

    # test compression of task 2a
    tm_task2a = tm.TuringMachine.from_file("machines/task2a.txt")
    tm_task2a_compressed = tm.TuringMachine(compress.compress(tm_task2a.transition_function))
    n_numbers_tested = 10
    for x in range(n_numbers_tested):
        for y in range(n_numbers_tested):
            word = f"{bin(x)[2:]}${bin(y)[2:]}"
            tm_task2a.run(word)
            tm_task2a_compressed.run(word)
            assert tm_task2a.output() == tm_task2a_compressed.output(), f"Task 2a compression failed: input = {word}, normal result = {tm_task2a.output()}, compressed_result = {tm_task2a_compressed.output()}"


if __name__ == "__main__":
    test_turing_machines()
