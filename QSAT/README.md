# Stuff with QBFs

Here we play around with generating and solving QBFs.

## Generate Random QBFs

`gen_qbf.py` generates a number of random QBFs with the [Chen-Interian Model](https://www.ijcai.org/Proceedings/05/Papers/0633.pdf) and saves them to `qdimacs/qbf_*.random.txt` in the QDIMACS encoding.

### Usage

```text
usage: gen_qbf.py [-h] [-p PREFIX [PREFIX ...]] [-w WIDTH [WIDTH ...]] n_qbfs n_clauses

Generates random QBFs.

positional arguments:
  n_qbfs                Number of QBFs.
  n_clauses             Number of clauses.

options:
  -h, --help            show this help message and exit
  -p PREFIX [PREFIX ...], --prefix PREFIX [PREFIX ...]
                        Number of variables in each prefix.
  -w WIDTH [WIDTH ...], --width WIDTH [WIDTH ...]
                        Number of variables contained from each quantor block in each clause.
```

### Examples

```text
python src/gen_qbf.py 10 11 -p 2 3 2 -w 1 1 1
```

## Solve QSAT

`qdpll.py` solves QSAT for a formula given in QDIMACS.
<!-- TODO: update when testing is available -->

### Usage

```text
usage: qdpll.py [-h] input

Checks if a QBF is true (satisfiable).

positional arguments:
  input       Input file where QDIMACS encoding of a formula is stored.

options:
  -h, --help  show this help message and exit
```

### Examples

```text
python src/qdpll.py qdimacs/qbf_0.random.txt
```
