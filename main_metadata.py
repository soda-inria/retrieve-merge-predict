"""
Combined script to prepare retrieval methods or create metadata for data lakes.

This script provides two main operations:
1. prepare-retrieval: Prepare retrieval method indices according to a config file
2. create-metadata: Build metadata index for a data lake folder
"""

import argparse
from pathlib import Path


def prepare_retrieval_command(args):
    """Execute the prepare retrieval methods functionality."""
    import toml
    
    config_file_path = args.config_file
    if Path(config_file_path).exists():
        config = toml.load(config_file_path)
        print(f"Reading configuration from file {config_file_path}")
        from src.utils.indexing import prepare_retrieval_methods

        if args.repeats > 1:
            for _ in range(args.repeats):
                prepare_retrieval_methods(config)
        else:
            prepare_retrieval_methods(config)
    else:
        raise FileNotFoundError(f"Configuration file not found: {config_file_path}")


def create_metadata_command(args):
    """Execute the metadata creation functionality."""
    import os
    from pathlib import Path
    from joblib import Parallel, delayed
    from tqdm import tqdm
    
    data_folder = Path(args.path_data_folder)
    flat = args.flat
    case = data_folder.stem
    if flat:
        case += "_flat"
    
    if data_folder.exists() and data_folder.is_dir():
        print(f"Building metadata for folder {data_folder}")
        # Importing here to save time, so that if the folder is missing we find out immediately.
        from src.data_structures.metadata import MetadataIndex
        from src.utils.indexing import save_single_table

        # Creating the dirtree
        os.makedirs(f"data/metadata/{case}", exist_ok=True)
        os.makedirs("data/metadata/_mdi", exist_ok=True)

        match_pattern = "**/*.parquet" if not flat else "*.parquet"
        total_files = sum(1 for f in data_folder.glob(match_pattern))

        if total_files == 0:
            raise RuntimeError("No parquet files found. Is the path correct? ")

        metadata_dest = f"data/metadata/{case}"

        # Prepare the metadata by running on all available cores
        Parallel(n_jobs=-1, verbose=0)(
            delayed(save_single_table)(dataset_path, "yadl", metadata_dest)
            for dataset_path in tqdm(data_folder.glob(match_pattern), total=total_files)
        )
        metadata_index = MetadataIndex(
            data_lake_variant=case, metadata_dir=f"data/metadata/{case}"
        )
        metadata_index.save_index(f"data/metadata/_mdi/md_index_{case}.pickle")
    else:
        raise FileNotFoundError(f"Invalid data folder path '{data_folder}'")


def parse_args():
    """Parse command line arguments with subcommands."""
    parser = argparse.ArgumentParser(
        description="Prepare retrieval methods or create metadata for data lakes."
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        required=True
    )
    
    # Subparser for prepare-retrieval command
    prepare_parser = subparsers.add_parser(
        "prepare-retrieval",
        help="Prepare retrieval method indices according to a config file"
    )
    prepare_parser.add_argument(
        "config_file",
        action="store",
        help="Path to the configuration file to be used."
    )
    prepare_parser.add_argument(
        "--repeats",
        action="store",
        type=int,
        default=1,
        help="Utility parameter that repeats the index creation for the given config to measure avg. time."
    )
    prepare_parser.set_defaults(func=prepare_retrieval_command)
    
    # Subparser for create-metadata command
    metadata_parser = subparsers.add_parser(
        "create-metadata",
        help="Build metadata index for a data lake folder"
    )
    metadata_parser.add_argument(
        "path_data_folder",
        action="store",
        help="Path to the folder to use to prepare metadata."
    )
    metadata_parser.add_argument(
        "--flat",
        action="store_true",
        help="If provided, do not proceed recursively and only consider parquet files found in the main folder."
    )
    metadata_parser.set_defaults(func=create_metadata_command)
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    args.func(args)
