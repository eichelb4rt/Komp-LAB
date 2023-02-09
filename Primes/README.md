# Primes

We're doing stuff with primes here to show how fast it is to use randomized algorithms.

- [Prime Number Tests](#prime-number-tests)
- [Generate Primes](#generate-primes)

## Prime Number Tests

`miller_rabin.py` tests if a given number is prime. `--test` compares the output of miller-rabin to a prime dataset with the first $10^6$ primes (Checks all primes and all non-primes).

### Usage

```text
usage: miller_rabin.py [-h] [--test] n

Checks if a given number is prime.

positional arguments:
  n           Number to be tested.

options:
  -h, --help  show this help message and exit
  --test      Tests the implementation (no other arguments needed).
```

### Examples

```text
python src/miller_rabin.py 3
python src/miller_rabin.py --test
```

## Generate Primes

Generate some primes! They're cool. I'll give you as many as i want, don't care if they repeat.

### Usage

```text
usage: gen_primes.py [-h] [-p BASE] [-d DIGITS]

Generates primes with a constant length in some base.

options:
  -h, --help            show this help message and exit
  -p BASE, --base BASE  Base in which the number of digits is constant.
  -d DIGITS, --digits DIGITS
                        Number of digits in the given base.
```