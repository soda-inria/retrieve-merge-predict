"""
Script to load and inspect retrieval method indices saved as pickle files.

These indices are created by the prepare_retrieval_methods function and saved
using joblib.dump in data/metadata/_indices/<data_lake_variant>/
"""

import argparse
from pathlib import Path

from joblib import load


def load_index_from_path(index_path):
    """Load an index object from a pickle file saved with joblib.dump.

    Args:
        index_path (str | Path): Path to the pickle file containing the index.

    Returns:
        dict: The loaded index object (typically a dictionary).

    Raises:
        FileNotFoundError: If the specified path does not exist.
    """
    index_path = Path(index_path)

    if not index_path.exists():
        raise FileNotFoundError(f"Index file not found: {index_path}")

    print(f"Loading index from: {index_path}")

    with open(index_path, "rb") as fp:
        index_obj = load(fp)

    print(f"Successfully loaded index: {type(index_obj)}")

    return index_obj


def print_index_info(index_obj):
    """Print information about the loaded index.

    Args:
        index_obj: The loaded index object.
        verbose (bool): If True, print detailed information.
    """
    if isinstance(index_obj, dict):
        print("\nIndex type: Dictionary")
    else:
        print(f"\nIndex is a {type(index_obj).__name__} object")
        if hasattr(index_obj, "__dict__"):
            print(f"Attributes: {list(index_obj.__dict__.keys())}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Load and inspect retrieval method indices from pickle files."
    )

    parser.add_argument(
        "index_path",
        type=str,
        help="Path to the pickle file containing the index (e.g., data/metadata/_indices/binary_update/minhash_index.pickle)",
    )
    parser.add_argument(
        "--export-json",
        type=str,
        help="Export basic index metadata to a JSON file (path to output file)",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # Load the index
    index_obj = load_index_from_path(args.index_path)

    # Print information
    print_index_info(index_obj)

    return index_obj


if __name__ == "__main__":
    index = main()
    print("\nIndex loaded successfully and available in the 'index' variable.")
