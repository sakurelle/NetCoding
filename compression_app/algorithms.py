"""Shannon-Fano and Huffman compression for byte files.

Both algorithms build a variable-length prefix code from byte frequencies.
This module stores compressed data in a simple educational container format.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import heapq
import itertools
import json
import struct
from typing import Literal

AlgorithmName = Literal["shannon_fano", "huffman"]
MAGIC = b"KSC1"


@dataclass(frozen=True)
class CompressionResult:
    algorithm: AlgorithmName
    original_size: int
    encoded_bit_length: int
    encoded_payload_size: int
    container_size: int
    codebook: dict[int, str]
    compressed: bytes


def frequencies(data: bytes) -> Counter[int]:
    return Counter(data)


def build_shannon_fano_codebook(data: bytes) -> dict[int, str]:
    """Build Shannon-Fano prefix codes for bytes.

    The symbols are sorted by frequency. Each recursive step splits symbols into
    two groups with total frequencies as close as possible, then appends 0/1.
    """
    freq = frequencies(data)
    if not freq:
        return {}
    items = sorted(freq.items(), key=lambda item: (-item[1], item[0]))
    if len(items) == 1:
        return {items[0][0]: "0"}

    codes: dict[int, str] = {symbol: "" for symbol, _ in items}

    def split(symbols: list[tuple[int, int]]) -> None:
        if len(symbols) <= 1:
            return

        total = sum(count for _, count in symbols)
        best_index = 1
        best_diff = total
        left_sum = 0
        for index in range(1, len(symbols)):
            left_sum += symbols[index - 1][1]
            right_sum = total - left_sum
            diff = abs(left_sum - right_sum)
            if diff < best_diff:
                best_diff = diff
                best_index = index

        left = symbols[:best_index]
        right = symbols[best_index:]
        for symbol, _ in left:
            codes[symbol] += "0"
        for symbol, _ in right:
            codes[symbol] += "1"

        split(left)
        split(right)

    split(items)
    return codes


@dataclass
class _Node:
    symbol: int | None
    freq: int
    left: "_Node | None" = None
    right: "_Node | None" = None


def build_huffman_codebook(data: bytes) -> dict[int, str]:
    """Build Huffman prefix codes for bytes using a priority queue."""
    freq = frequencies(data)
    if not freq:
        return {}
    if len(freq) == 1:
        symbol = next(iter(freq))
        return {symbol: "0"}

    counter = itertools.count()
    heap: list[tuple[int, int, _Node]] = []
    for symbol, count in freq.items():
        heapq.heappush(heap, (count, next(counter), _Node(symbol=symbol, freq=count)))

    while len(heap) > 1:
        freq1, _, left = heapq.heappop(heap)
        freq2, _, right = heapq.heappop(heap)
        parent = _Node(symbol=None, freq=freq1 + freq2, left=left, right=right)
        heapq.heappush(heap, (parent.freq, next(counter), parent))

    root = heap[0][2]
    codes: dict[int, str] = {}

    def walk(node: _Node, prefix: str) -> None:
        if node.symbol is not None:
            codes[node.symbol] = prefix or "0"
            return
        if node.left is not None:
            walk(node.left, prefix + "0")
        if node.right is not None:
            walk(node.right, prefix + "1")

    walk(root, "")
    return codes


def encode_bits(data: bytes, codebook: dict[int, str]) -> str:
    return "".join(codebook[byte] for byte in data)


def pack_bits(bits: str) -> tuple[bytes, int]:
    """Pack a 0/1 string into bytes. Returns (packed_bytes, padding_bit_count)."""
    if not bits:
        return b"", 0
    padding = (8 - len(bits) % 8) % 8
    padded = bits + "0" * padding
    return bytes(int(padded[i : i + 8], 2) for i in range(0, len(padded), 8)), padding


def unpack_bits(packed: bytes, padding: int) -> str:
    bits = "".join(f"{byte:08b}" for byte in packed)
    if padding:
        bits = bits[:-padding]
    return bits


def _make_container(
    algorithm: AlgorithmName,
    original_size: int,
    codebook: dict[int, str],
    packed_payload: bytes,
    padding: int,
) -> bytes:
    header = {
        "algorithm": algorithm,
        "original_size": original_size,
        "padding": padding,
        "codebook": {str(symbol): code for symbol, code in sorted(codebook.items())},
    }
    header_bytes = json.dumps(header, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return MAGIC + struct.pack(">I", len(header_bytes)) + header_bytes + packed_payload


def _read_container(container: bytes) -> tuple[dict, bytes]:
    if len(container) < 8 or container[:4] != MAGIC:
        raise ValueError("Not a KSC1 compressed file")
    header_length = struct.unpack(">I", container[4:8])[0]
    header_start = 8
    header_end = header_start + header_length
    if header_end > len(container):
        raise ValueError("Container header length is invalid")
    header = json.loads(container[header_start:header_end].decode("utf-8"))
    payload = container[header_end:]
    return header, payload


def compress_bytes(data: bytes, algorithm: AlgorithmName) -> CompressionResult:
    if algorithm == "shannon_fano":
        codebook = build_shannon_fano_codebook(data)
    elif algorithm == "huffman":
        codebook = build_huffman_codebook(data)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    bit_string = encode_bits(data, codebook) if data else ""
    packed_payload, padding = pack_bits(bit_string)
    container = _make_container(algorithm, len(data), codebook, packed_payload, padding)
    return CompressionResult(
        algorithm=algorithm,
        original_size=len(data),
        encoded_bit_length=len(bit_string),
        encoded_payload_size=len(packed_payload),
        container_size=len(container),
        codebook=codebook,
        compressed=container,
    )


def decompress_bytes(container: bytes) -> bytes:
    header, packed_payload = _read_container(container)
    algorithm = header.get("algorithm")
    if algorithm not in {"shannon_fano", "huffman"}:
        raise ValueError(f"Unsupported algorithm in container: {algorithm!r}")

    raw_codebook = header.get("codebook")
    if not isinstance(raw_codebook, dict):
        raise ValueError("Container codebook is missing or invalid")

    codebook = {int(symbol): code for symbol, code in raw_codebook.items()}
    if any(
        not isinstance(code, str) or not code or any(bit not in "01" for bit in code)
        for code in codebook.values()
    ):
        raise ValueError("Container codebook contains invalid codes")

    reverse = {code: symbol for symbol, code in codebook.items()}
    if len(reverse) != len(codebook):
        raise ValueError("Container codebook contains duplicate codes")
    bits = unpack_bits(packed_payload, int(header["padding"]))

    output = bytearray()
    current = ""
    for bit in bits:
        current += bit
        if current in reverse:
            output.append(reverse[current])
            current = ""

    if current:
        raise ValueError("Compressed bit stream ended in the middle of a code")

    original_size = int(header["original_size"])
    if len(output) != original_size:
        raise ValueError(
            f"Decompressed size mismatch: expected {original_size}, got {len(output)}"
        )
    return bytes(output)


def describe_symbol(symbol: int) -> str:
    """Human-readable byte symbol for console output."""
    if symbol == 10:
        return "\\n"
    if symbol == 13:
        return "\\r"
    if symbol == 9:
        return "\\t"
    if 32 <= symbol <= 126:
        return chr(symbol)
    return f"0x{symbol:02X}"
