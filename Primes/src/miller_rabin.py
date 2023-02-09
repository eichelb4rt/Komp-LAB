import math
import random
import argparse
import pandas as pd
from tqdm import tqdm
from test import TestAction


def fast_pow(a: int, b: int, n: int) -> int:
    """Calculate x = a**b mod n relatively quickly."""

    # r = number of bits that b is stored in
    r = math.floor(math.log2(b)) + 1
    x = 1
    # for i=0 to r
    for i in range(r + 1):
        # if i-th bit of b = 1
        if (b >> i) & 1 == 1:
            x = x * a % n
        a = a * a % n
    return x


def miller_rabin_once(n: int) -> bool:
    """True everytime if n is prime, False if n is prime with some constant probability."""

    # we need to know n-1 = 2^k * m
    m = n - 1
    k = 0
    while m % 2 == 0:
        k += 1
        m //= 2
    # get a random a in Z_n
    a = random.randrange(1, n)
    # now start the actual algorithm
    b = fast_pow(a, m, n)
    if b == 1 % n:
        return True
    for _ in range(k):
        if b == -1 % n:
            return True
        else:
            b = b**2 % n
    return False


def miller_rabin(n: int) -> bool:
    """Apply miller_rabin 100 times to make sure it's actually prime."""

    for _ in range(100):
        if not miller_rabin_once(n):
            return False
    return True


def test_miller_rabin():
    PRIMES_TESTED = 10000
    prime_dataset = pd.read_csv("primes.csv")
    primes = prime_dataset["Num"].to_numpy()
    # make this a set to check if a number is in there quickly
    prime_set = set(primes)
    # test all numbers between the first and last prime
    tested_numbers = range(primes[0], primes[PRIMES_TESTED - 1] + 1)
    for n in tqdm(tested_numbers):
        assert miller_rabin(n) == (n in prime_set)

    print("Miller-Rabin Test: all tests passed.")


def main():
    parser = argparse.ArgumentParser(description="Checks if a given number is prime.")
    parser.add_argument("n",
                        type=int,
                        help="Number to be tested.")
    parser.add_argument("--test",
                        action=TestAction.build(test_miller_rabin),
                        help="Tests the implementation (no other arguments needed).")
    args = parser.parse_args()

    is_prime = miller_rabin(args.n)
    if is_prime:
        print(f"{args.n} is prime.")
    else:
        print(f"{args.n} is not prime.")


if __name__ == "__main__":
    main()
