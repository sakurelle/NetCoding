"""Detailed terminal demo for the Shannon-Fano compression part of the assignment."""

from __future__ import annotations

import argparse
from pathlib import Path

from compression_app.demo_support import ensure_sample_file, run_single_algorithm_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Detailed Shannon-Fano compression demo")
    parser.add_argument(
        "file",
        nargs="?",
        help="File to compress. If omitted, data/sample.txt is used.",
    )
    args = parser.parse_args()

    source_path = Path(args.file) if args.file else ensure_sample_file()
    run_single_algorithm_demo(source_path, "shannon_fano")


if __name__ == "__main__":
    main()
