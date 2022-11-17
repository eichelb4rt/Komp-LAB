import tm
import transitions


def test_implementation():
    """Tests my implementation."""

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

    print("all tests passed.")


if __name__ == "__main__":
    test_implementation()
