import random

from miller_rabin import miller_rabin


def find_prime(min: int, max: int) -> int:
    """Find a prime between min and max."""

    # start with a number of the form 30z, z \in \N
    # for that, we can just start with the biggest number n <= min, that is divisible by 30
    # x = random number between (min - min%30, max) with steps of 30
    x = random.randrange(min - min % 30, max, 30)
    # then we try a sequence of numbers until we find a prime number (p+1, p+7, p+11, p+13, p+17, p+19, p+23, p+29, p+30+1, ...)
    sequence = [1, 7, 11, 13, 17, 19, 23, 29]
    while True:
        for offset in sequence:
            p = x + offset
            # is p a prime within our set bounds?
            if p >= min and p <= max:
                if miller_rabin(p):
                    return p
        # x += 30
        x += 30
        # now if we reach max without finding a prime, we probably just guessed a number too near to max. Let's just guess again then.
        if x > max:
            x = random.randrange(min - min % 30, max, 30)


def main():
    power = 100
    MIN = 10**power
    MAX = 10**(power + 1) - 1
    while True:
        print(find_prime(MIN, MAX))


if __name__ == "__main__":
    main()
