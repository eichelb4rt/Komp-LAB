import numpy as np
import matplotlib.pyplot as plt

from turing_machines import runtime
from turing_machines.tape import MultiCharTape
from turing_machines.tm import TuringMachine

import matplotlib
matplotlib.rcParams["figure.dpi"] = 300


def main():
    print("generating inputs...")
    machine_name = "task2a_compressed"
    inputs = ["1" * i for i in range(1, 200)]
    input_sizes = [len(x) for x in inputs]

    with open(f"machines/{machine_name}.txt") as f:
        n_lines = len(f.readlines())
    if n_lines < 1000:
        print("loading turing machine...")
    else:
        print(f"loading turing machine... ({n_lines} lines, might be slow)")
    tm = TuringMachine.from_file(f"machines/{machine_name}.txt")

    print("computing outputs...")
    times = runtime.measure(tm, inputs, show_progress=True)

    print("saving runtimes...")
    np.save(f"runtimes/runtime_{machine_name}.npy", (np.array(input_sizes, dtype=np.int32), np.array(times, dtype=np.int32)))

    print("plotting...")
    plt.scatter(input_sizes, times, s=0.3)
    plt.savefig(f"plots/runtime_{machine_name}.png")


if __name__ == "__main__":
    main()
