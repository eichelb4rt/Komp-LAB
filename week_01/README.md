# Usage

```text
python tm.py -h
usage: tm.py [-h] [-i] [-a] filename input

Runs a Turing Machine on an input text.

positional arguments:
  filename         File with the encoded Turing Machine.
  input            Input to the Turing Machine (or file with the input if -i was set).

options:
  -h, --help       show this help message and exit
  -i, --fileinput  Read input from filename instead of positional argument.
  -a, --animate    Animate the Turing Machine.
```

## Example

```text
python tm.py Verdopplung1.txt 11111 --animate
```
