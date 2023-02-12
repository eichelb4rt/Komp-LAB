from tqdm import tqdm
import numpy as np
from PIL import Image

from gen_primes import find_prime


def digits(n: int, base: int, length: int) -> np.ndarray:
    return np.array([(n // (base**i)) % base for i in range(length)])


def main():
    BASE = 2
    N_DIGITS = 90
    N_GENERATED_PRIMES = 1200
    IMAGE_HEIGHT = 30
    # generate primes
    MIN = BASE**N_DIGITS
    MAX = BASE**(N_DIGITS + 1) - 1
    # colors
    MIN_COLOR = np.array([25, 27, 34])
    MAX_COLOR = np.array([128, 144, 167])
    generated_primes = np.empty(N_GENERATED_PRIMES, dtype=object)

    print("Generating primes...")
    for i in tqdm(range(N_GENERATED_PRIMES)):
        generated_primes[i] = find_prime(MIN, MAX)

    # read the digits of the primes
    print("Converting primes to pixels...")
    prime_digits = np.array([digits(prime, BASE, N_DIGITS) for prime in generated_primes])
    color_values = np.einsum("ij,k->ijk", prime_digits / (BASE - 1), MAX_COLOR - MIN_COLOR) + np.einsum("ij,k->ijk", np.ones(prime_digits.shape), MIN_COLOR)

    # sliding window over the color values
    print("Sliding the window...")
    # [[0 1 2 3 4]
    #  [1 2 3 4 5]
    #  [2 3 4 5 6]
    #  [3 4 5 6 7]
    #  [4 5 6 7 8]
    #  [5 6 7 8 9]
    #  [6 7 8 9 0]
    #  [7 8 9 0 1]
    #  [8 9 0 1 2]
    #  [9 0 1 2 3]]
    sliding_window = (np.arange(IMAGE_HEIGHT)[None, :] + np.arange(N_GENERATED_PRIMES)[:, None]) % N_GENERATED_PRIMES
    images_arrays = color_values[sliding_window].astype(np.uint8)

    print("Making the gif...")
    images = [Image.fromarray(img, 'RGB') for img in images_arrays]
    # # duration is the number of milliseconds between frames; this is 40 frames per second
    images[0].save("prime_noise.gif", save_all=True, append_images=images[1:], duration=50, loop=0)


if __name__ == "__main__":
    main()
