# A bunch of programs doing stuff with Turing Machines

## Turing Machine Encoding

- first line: `n_states n_tapes alphabet_size n_transitions`
- second line: all chars in the alphabet, separated by comma
- all lines after: transitions
- lines that start with \# are ignored

### Transitions

Transitions are formed like this:

```q_in,ci_1,ci_2,ci_3,...,q_out,co_1,d_1,co_2,d_2,co_3,d_3,...```

| Symbol          | Explanation                               | Allowed values           |
| --------------- | ----------------------------------------- | ------------------------ |
| `q_in`          | input state                               | integers                 |
| `ci_1` - `ci_k` | chars read on the k tapes                 | chars/strings            |
| `q_out`         | output state                              | integers + `y`, `n`, `h` |
| `co_1` - `co_k` | output chars to be written on the k tapes | chars/strings            |
| `d_1` - `d_k`   | directions the heads should move          | `L`, `N`, `R`            |

### Example

This example just copies a binary number from the first tape to the second tape:

```text
1 2 2 3
0,1
0,0,_,0,0,R,0,R
0,1,_,0,1,R,1,R
0,_,_,h,_,N,_,N
```

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
python src/tm.py machines/task2a_compressed.txt "101\$101" -ma
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
python src/runtime.py machines/task2a.txt inputs/inputs_task2_worst.txt -s
```

## Compress k-tape Turing Machines

`compress.py` compresses a k-tape Turing Machine into a 1-tape Turing Machine with the same outputs. The compressed machine is saved in the `machines` directory (e.g. `machines/tm1.txt` -> `machines/tm1_compressed.txt`).

### Usage

```text
usage: compress.py [-h] tm

Compresses a k-tape Turing Machine into a 1-tape Turing Machine.

positional arguments:
  tm          File with the encoded Turing Machine.

options:
  -h, --help  show this help message and exit
```

### Examples

```text
python src/compress.py machines/copy.txt
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
