# Stuff about satisfiability

## Generate random CNFs

`random_cnf.py` generates random cnfs.

### Usage

```text
usage: random_cnf.py [-h] [-o output_dir] t n c k

Generates random CNFs.

positional arguments:
  t                     Number of CNFs
  n                     Number of variables
  c                     Number of clauses
  k                     Clause width

options:
  -h, --help            show this help message and exit
  -o output_dir, --output output_dir
                        Directory that the CNFs are written to
```

### Examples

```text
# generate 10 random 2-cnfs with 5 variables and 4 clauses each
python src/random_cnf.py 10 5 4 2 -o "random_cnfs"
# use a preset
bash presets/small_2cnf.sh
```

## DPLL

`dpll.py` checks if a CNF encoded with DIMACS is satisfiable.

### Usage

```text
usage: dpll.py [-h] input

Checks if a CNF is satisfiable.

positional arguments:
  input       Input file where DIMACS encoding of a formula is stored.

options:
  -h, --help  show this help message and exit
```

### Examples

```text
python src/dpll.py random_cnfs/random_cnf_0.txt
python src/dpll.py cnfs/unsatisfiable_cnf.txt
```
