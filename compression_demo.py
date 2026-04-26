"""One-command demo for task 2: Shannon-Fano and Huffman compression.

Run:
    python compression_demo.py
    python compression_demo.py path/to/file.txt
"""

from __future__ import annotations

import argparse
from pathlib import Path

from compression_app.demo_support import ensure_sample_file, run_single_algorithm_demo
from demo_ui import configure_console_utf8, print_banner


def main() -> None:
    configure_console_utf8()
    parser = argparse.ArgumentParser(description="Compare Shannon-Fano and Huffman compression")
    parser.add_argument(
        "file",
        nargs="?",
        help="File to compress. If omitted, data/sample.txt is created and used.",
    )
    args = parser.parse_args()

    source_path = Path(args.file) if args.file else ensure_sample_file()
    print_banner("СРАВНЕНИЕ: ШЕННОН-ФАНО И ХАФФМАН")
    run_single_algorithm_demo(source_path, "shannon_fano")
    run_single_algorithm_demo(source_path, "huffman")


if __name__ == "__main__":
    main()
