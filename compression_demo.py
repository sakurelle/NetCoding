"""One-command demo for task 2: Shannon-Fano and Huffman compression.

Run:
    python compression_demo.py
    python compression_demo.py path/to/file.txt
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from compression_app.algorithms import (
    compress_bytes,
    decompress_bytes,
    describe_symbol,
    frequencies,
)


def _configure_console_utf8() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


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


def _ratio(part: int, whole: int) -> float:
    return (part / whole) if whole else 0.0


def run_for_algorithm(source_path: Path, data: bytes, algorithm: str) -> dict[str, float | str | bool]:
    result = compress_bytes(data, algorithm)  # type: ignore[arg-type]

    suffix = ".sfano.ksc" if algorithm == "shannon_fano" else ".huff.ksc"
    compressed_path = source_path.with_name(source_path.name + suffix)
    restored_path = source_path.with_name(source_path.name + suffix + ".restored")

    compressed_path.write_bytes(result.compressed)
    restored = decompress_bytes(result.compressed)
    restored_path.write_bytes(restored)

    payload_ratio = _ratio(result.encoded_payload_size, result.original_size)
    final_ratio = _ratio(result.container_size, result.original_size)
    restored_ok = restored == data

    print(f"\n[{algorithm.upper()}]")
    print(f"  original size:        {result.original_size} bytes")
    print(f"  encoded bits:         {result.encoded_bit_length} bits")
    print(f"  encoded payload size: {result.encoded_payload_size} bytes, ratio {payload_ratio:.3f}")
    print(f"  final .ksc size:      {result.container_size} bytes, ratio {final_ratio:.3f}")
    print(f"  compressed file:      {compressed_path}")
    print(f"  restored file:        {restored_path}")
    print(f"  restored == original: {restored_ok}")
    print_codebook_preview(data, result.codebook)

    return {
        "algorithm": algorithm,
        "payload_ratio": payload_ratio,
        "final_ratio": final_ratio,
        "restored_ok": restored_ok,
    }


def print_summary(results: list[dict[str, float | str | bool]]) -> None:
    by_payload = min(results, key=lambda item: float(item["payload_ratio"]))
    by_container = min(results, key=lambda item: float(item["final_ratio"]))

    print("\n[SUMMARY]")
    print(
        "  better encoded payload: "
        f"{by_payload['algorithm']} (ratio {float(by_payload['payload_ratio']):.3f})"
    )
    print(
        "  smaller final container: "
        f"{by_container['algorithm']} (ratio {float(by_container['final_ratio']):.3f})"
    )
    if all(bool(item["restored_ok"]) for item in results):
        print("  round-trip check: both algorithms restored the original file correctly")


def main() -> None:
    _configure_console_utf8()
    parser = argparse.ArgumentParser(description="Compare Shannon-Fano and Huffman compression")
    parser.add_argument(
        "file",
        nargs="?",
        help="File to compress. If omitted, data/sample.txt is created and used.",
    )
    args = parser.parse_args()

    source_path = Path(args.file) if args.file else ensure_sample_file()
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")
    data = source_path.read_bytes()

    print("[DEMO] Compression comparison")
    print(f"[DEMO] source file: {source_path}")

    results = [
        run_for_algorithm(source_path, data, "shannon_fano"),
        run_for_algorithm(source_path, data, "huffman"),
    ]
    print_summary(results)

    print("\n[DEMO] Note: for very small files the final .ksc can be larger than the original")
    print("       because the demo stores the code table in the file header.")


if __name__ == "__main__":
    main()
