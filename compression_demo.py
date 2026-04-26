"""One-command demo for task 2: Shannon-Fano and Huffman compression.

Run:
    python compression_demo.py
    python compression_demo.py path/to/file.txt
"""

from __future__ import annotations

import argparse
from pathlib import Path

from compression_app.algorithms import (
    compress_bytes,
    decompress_bytes,
    describe_symbol,
    frequencies,
)


DEFAULT_SAMPLE = """Computer networks and coding systems demo.\n""" \
    """This file intentionally contains repeated words: demo demo demo, code code code, network network.\n""" \
    """Алгоритмы Шеннона-Фано и Хаффмана хорошо сжимают повторяющиеся символы.\n""" \
    """0000000000111111111122222222223333333333\n"""


def ensure_sample_file() -> Path:
    path = Path("data/sample.txt")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(DEFAULT_SAMPLE, encoding="utf-8")
    return path


def print_codebook_preview(data: bytes, codebook: dict[int, str], limit: int = 12) -> None:
    freq = frequencies(data)
    items = sorted(codebook.items(), key=lambda item: (-freq[item[0]], item[0]))[:limit]
    print("  first codes by frequency:")
    print("  symbol | freq | code")
    print("  -------+------+------")
    for symbol, code in items:
        print(f"  {describe_symbol(symbol)!r:>6} | {freq[symbol]:>4} | {code}")


def run_for_algorithm(source_path: Path, data: bytes, algorithm: str) -> None:
    result = compress_bytes(data, algorithm)  # type: ignore[arg-type]

    suffix = ".sfano.ksc" if algorithm == "shannon_fano" else ".huff.ksc"
    compressed_path = source_path.with_name(source_path.name + suffix)
    restored_path = source_path.with_name(source_path.name + suffix + ".restored")

    compressed_path.write_bytes(result.compressed)
    restored = decompress_bytes(result.compressed)
    restored_path.write_bytes(restored)

    payload_ratio = (result.encoded_payload_size / result.original_size) if result.original_size else 0
    final_ratio = (result.container_size / result.original_size) if result.original_size else 0

    print(f"\n[{algorithm.upper()}]")
    print(f"  original size:        {result.original_size} bytes")
    print(f"  encoded bits:         {result.encoded_bit_length} bits")
    print(f"  encoded payload size: {result.encoded_payload_size} bytes, ratio {payload_ratio:.3f}")
    print(f"  final .ksc size:      {result.container_size} bytes, ratio {final_ratio:.3f}")
    print(f"  compressed file:      {compressed_path}")
    print(f"  restored file:        {restored_path}")
    print(f"  restored == original: {restored == data}")
    print_codebook_preview(data, result.codebook)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare Shannon-Fano and Huffman compression")
    parser.add_argument(
        "file",
        nargs="?",
        help="File to compress. If omitted, data/sample.txt is created and used.",
    )
    args = parser.parse_args()

    source_path = Path(args.file) if args.file else ensure_sample_file()
    data = source_path.read_bytes()

    print("[DEMO] Compression comparison")
    print(f"[DEMO] source file: {source_path}")

    run_for_algorithm(source_path, data, "shannon_fano")
    run_for_algorithm(source_path, data, "huffman")

    print("\n[DEMO] Note: for very small files the final .ksc can be larger than the original")
    print("       because the demo stores the code table in the file header.")


if __name__ == "__main__":
    main()
