# A bunch of programs doing stuff with Turing Machines

## Simulate Turing Machine

`tm.py` simulates a Turing Machine on an input.

### Usage

```text
usage: tm.py [-h] [-i] [-a] [-l] [-s] [-t] [-m] [--test] filename input

Runs a Turing Machine on an input text.

positional arguments:
  filename              File with the encoded Turing Machine.
  input                 Input to the Turing Machine (or file with the input if -i was set).

options:
  -h, --help            show this help message and exit
  -i, --fileinput       Read input from filename instead of positional argument.
  -a, --animate         Animate the Turing Machine.
  -l, --logging         Logs the snapshots of the Turing Machine.
  -s, --showtransitions
                        Shows the transition table with the animation or log (logging must be enabled for the latter).
  -t, --time            Shows runtime of the Turing Machine.
  -m, --multichars      Enable ability to have multiple chars in one tape cell.
  --test                Tests the implementation and the Turing Machines that were part of the task (no other
                        arguments needed).
```

### Examples

```text
python src/tm.py machines/tm5.txt -i inputs/input.txt -t
python src/tm.py machines/task1.txt "000111000" --animate
python src/tm.py machines/task2a.txt "1101\$1011" -s -l
python src/tm.py machines/multichars.txt "11|0|11|0|0" -m --animate
```

## Approximate Runtime

`runtime.py` approximates the runtime of a Turing Machine with a polynomial.
You can either view a plot of it or save it.

### Usage

```text
usage: runtime.py [-h] [-d DEGREE] [-c CONSTANT] [-s] tm inputs

Tries finding out the runtime complexity of a TM if it's a polynomial (degree <= 4).

positional arguments:
  tm                    File with the encoded Turing Machine.
  inputs                File with the measured inputs to the Turing Machine.

options:
  -h, --help            show this help message and exit
  -d DEGREE, --degree DEGREE
                        Max degree of the polynomial.
  -c CONSTANT, --constant CONSTANT
                        Regularization constant for the polynomial regression.
  -s, --save            Save plot instead of showing it.
```

### Examples

```text
python src/runtime.py machines/task1.txt inputs/inputs_task1.txt
python src/runtime.py machines/task2a.txt inputs/inputs_task2.txt -d 3 --save
```

## Test

`test.py` test my implementation.

### Usage

```text
python src/test.py
```

## Generate Inputs

`gen_inputs.py` generates tailored inputs for some Turing Machines to later test the runtime on them.

### Usage

```text
python src/gen_inputs.py
```
