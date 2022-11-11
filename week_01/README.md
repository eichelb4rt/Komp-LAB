# Usage

```text
python tm-multiband.py -h
usage: tm-multiband.py [-h] [-i] [-a] [-l] [-t] filename input

Runs a Turing Machine on an input text.

positional arguments:
  filename           File with the encoded Turing Machine.
  input              Input to the Turing Machine (or file with the input if -i was set).

options:
  -h, --help         show this help message and exit
  -i, --fileinput    Read input from filename instead of positional argument.
  -a, --animate      Animate the Turing Machine.
  -l, --logging      Logs the snapshots of the Turing Machine.
  -t, --transitions  Shows the transition table with the animation or log.
```

## Example

```text
python tm-multiband.py tm5.txt -i input.txt --animate -t
```
