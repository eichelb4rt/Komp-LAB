import argparse
from pathlib import Path
from transitions import TransitionFunction


def compress(original: TransitionFunction) -> TransitionFunction:
    """Compresses a k-tape transition function into a 1-tape transition function."""
    
    # states that i need: 
    # - originial states
    # - 1 state for every combination of chars
    # - 
    
    
    pass


def main():
    parser = argparse.ArgumentParser(description="Compresses a k-tape Turing Machine into a 1-tape Turing Machine.")
    parser.add_argument("tm",
                        help="File with the encoded Turing Machine.")
    args = parser.parse_args()

    # load tm
    trans_fun = TransitionFunction.from_file(args.tm)
    out_file = f"{Path(args.tm).stem}_compressed.txt"
    print("Saving transtition function.")
    trans_fun.save(out_file)
    print("Transition function saved.")
    # try to load the transition function to check if it is a working encoding
    TransitionFunction.from_file(out_file)
    print("Saved encoding checked.")


if __name__ == "__main__":
    main()
