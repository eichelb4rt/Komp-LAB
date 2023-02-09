import numpy as np
from PIL import Image

from gen_primes import find_prime


def digits(n: int, base: int, length: int) -> np.ndarray:
    return np.array([(n // (base**i)) % base for i in range(length)])


def main():
    BASE = 16
    N_DIGITS = 100
    GENERATED_LINES = 500
    # generate primes
    MIN = BASE**N_DIGITS
    MAX = BASE**(N_DIGITS + 1) - 1
    generated_primes = [find_prime(MIN, MAX) for _ in range(GENERATED_LINES)]
    # read the digits of the primes
    prime_digits = np.array([digits(prime, BASE, N_DIGITS) for prime in generated_primes])
    color_values = 255 * prime_digits / (BASE - 1)
    # sliding window over the color values
    images_arrays = [color_values[i - N_DIGITS:i] for i in range(N_DIGITS, GENERATED_LINES)]
    images = [Image.fromarray(img) for img in images_arrays]
    # # duration is the number of milliseconds between frames; this is 40 frames per second
    images[0].save("prime_noise.gif", save_all=True, append_images=images[1:], duration=50, loop=0)


if __name__ == "__main__":
    main()
