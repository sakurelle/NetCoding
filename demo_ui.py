"""Console helpers for more readable algorithm demos."""

from __future__ import annotations

import sys


def configure_console_utf8() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def print_banner(title: str, char: str = "=") -> None:
    line = char * 88
    print(f"\n{line}")
    print(title)
    print(line)


def print_step(number: int, title: str) -> None:
    print(f"\n[{number}] {title}")
    print("-" * 88)


def print_kv(label: str, value: object) -> None:
    print(f"{label:<28} {value}")


def group_bits(bits: str, group_size: int = 8) -> str:
    return " ".join(bits[index : index + group_size] for index in range(0, len(bits), group_size))


def preview_text(text: str, limit: int = 120) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def preview_bits(bits: str, limit: int = 128, group_size: int = 8) -> str:
    if len(bits) <= limit:
        return group_bits(bits, group_size)
    return group_bits(bits[:limit], group_size) + f" ... ({len(bits)} bits)"


def highlight_bit(bits: str, zero_based_index: int, radius: int = 24) -> str:
    if zero_based_index < 0 or zero_based_index >= len(bits):
        raise ValueError(f"Bit index {zero_based_index} is outside 0..{len(bits) - 1}")
    start = max(0, zero_based_index - radius)
    end = min(len(bits), zero_based_index + radius + 1)
    fragment = bits[start:end]
    local_index = zero_based_index - start
    return (
        fragment[:local_index]
        + "["
        + fragment[local_index]
        + "]"
        + fragment[local_index + 1 :]
        + f"  (global index {zero_based_index})"
    )


def render_positions(positions: list[int]) -> str:
    width = max(2, max((len(str(position)) for position in positions), default=2))
    return " ".join(f"{position:>{width}}" for position in positions)


def render_values(values: list[str]) -> str:
    width = max(2, max((len(value) for value in values), default=2))
    return " ".join(f"{value:>{width}}" for value in values)
