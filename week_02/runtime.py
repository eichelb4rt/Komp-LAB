import argparse
import numpy as np
from typing import Self
import matplotlib.pyplot as plt

from tm import TuringMachine


IRRELEVANT_PARAM_MARGIN = 0.005


def poly(x, degree):
    return np.vander(x, degree + 1, True).T


class PolyReg:
    """Polynomial regression with degree d and regularization constant c."""

    def __init__(self, d, c=0):
        self.d = d
        self.c = c

    def fit(self, x: np.ndarray, y: np.ndarray) -> Self:
        dm = poly(x, self.d)
        xxt = dm @ dm.T
        self.theta = np.linalg.solve(xxt + self.c * np.eye(xxt.shape[0]), dm @ y)
        return self

    def predict(self, x: np.ndarray):
        # X shape: (n features, n samples)
        return self.theta.T @ poly(x, self.d)

    def str_parameters(self, varname="x") -> str:
        exponent = lambda power: f"^{power}" if power > 1 else ""
        descriptor = lambda power: f"{np.abs(self.theta[power]):.2f} * {varname}{exponent(power)}" if power != 0 else f"{np.abs(self.theta[power]):.2f}"
        # string builder
        sb = ""
        first_done = False
        for power in reversed(range(len(self.theta))):
            if np.abs(self.theta[power]) <= IRRELEVANT_PARAM_MARGIN:
                continue
            sign = np.sign(self.theta[power])
            # no sign before first term
            if first_done:
                sb += " + " if sign > 0 else " - "
            # except for a minus, then directly before the term
            elif sign < 0:
                sb += f"-"
            sb += descriptor(power)
            first_done = True
        return sb


def measure(tm: TuringMachine, inputs: list[str]) -> list[int]:
    return [tm.runtime(x) for x in inputs]


def worst_times(inputs: list[str], worsts: list[int]) -> tuple[np.ndarray, np.ndarray]:
    """Finds the worst case time for given input of length n."""

    assert len(inputs) == len(worsts), "Inputs and times must be same size."
    worst_time: dict[int, int] = {}
    for x, time in zip(inputs, worsts):
        n = len(x)
        if x not in worst_time:
            worst_time[n] = time
            continue
        worst_time[n] = max(worst_time[n], time)
    ns, worsts = zip(*worst_time.items())
    return np.array(ns), np.array(worsts)


def plot_regression_line(x, regression: PolyReg, step=0.1):
    domain = np.arange(np.min(x), np.max(x), step)
    prediction = regression.predict(domain)
    plt.plot(domain, prediction, color='red')


def approximate_time(tm: TuringMachine, inputs: list[str], max_degree=4, regularization_constant=0):
    times = measure(tm, inputs)
    n, t = worst_times(inputs, times)
    reg = PolyReg(max_degree, regularization_constant).fit(n, t)
    complexity = reg.str_parameters(varname="n")
    print(complexity)
    plt.scatter(n, t)
    plot_regression_line(n, reg)
    plt.title(complexity)
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Tries finding out the runtime complexity of a TM if it's a polynomial (degree <= 4).")
    parser.add_argument("tm",
                        help="File with the encoded Turing Machine.")
    parser.add_argument("inputs",
                        help="File with the measured inputs to the Turing Machine.")
    parser.add_argument("-d", "--degree",
                        type=int,
                        default=4,
                        help="Max degree of the polynomial.")
    parser.add_argument("-c", "--constant",
                        type=float,
                        default=0,
                        help="Regularization constant for the polynomial regression.")
    args = parser.parse_args()
    tm = TuringMachine.from_file(args.tm)
    with open(args.inputs, 'r') as f:
        inputs = f.readlines()
    approximate_time(tm, inputs, args.degree, args.constant)


if __name__ == "__main__":
    main()
