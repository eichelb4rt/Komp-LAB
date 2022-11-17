# Usage

```text
usage: tm.py [-h] [-i] [-a] [-l] [-s] [--time] [-t] filename input

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
                        Shows the transition table with the animation or log.
  --time                Shows runtime of the Turing Machine.
  -t, --test            Tests the implementation and the Turing Machines that were part of the task.
```

## Example

```text
python src/tm.py machines/tm5.txt -i inputs/input.txt --animate -t
```
