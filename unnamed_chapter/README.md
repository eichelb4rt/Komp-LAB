# Unnamed Chapter

Idk what exactly we're doing now.

- [Primes](#primes)
  - [Prime Number Tests](#prime-number-tests)
  - [Generate Primes](#generate-primes)

## Primes

### Prime Number Tests

`miller_rabin.py` tests if a given number is prime. `--test` compares the output of miller-rabin to a prime dataset with the first $10^6$ primes (Checks all primes and all non-primes).

#### Usage

```text
usage: miller_rabin.py [-h] [--test] n

Checks if a given number is prime.

positional arguments:
  n           Number to be tested.

options:
  -h, --help  show this help message and exit
  --test      Tests the implementation (no other arguments needed).
```

#### Examples

```text
python src/miller_rabin.py 3
python src/miller_rabin.py --test
```

### Generate Primes

bruh
