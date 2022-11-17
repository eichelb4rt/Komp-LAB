import argparse
from pathlib import Path
from tm import TransitionFunction


def main():
    parser = argparse.ArgumentParser(description="Compresses a k-tape Turing Machine into a 1-tape Turing Machine.")
    parser.add_argument("tm",
                        help="File with the encoded Turing Machine.")
    args = parser.parse_args()

    out_file = f"{Path(args.tm).stem}_compressed.txt"


if __name__ == "__main__":
    main()
