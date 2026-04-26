"""Algorithms for the client-server coding demo.

CRC-32 is used for error detection only.
Hamming code uses parity bits at positions 1, 2, 4, 8, ... and can correct one bit.
"""

from __future__ import annotations

from dataclasses import dataclass
import binascii


@dataclass(frozen=True)
class HammingDecodeResult:
    received_bits: str
    corrected_bits: str
    data_bits: str
    syndrome: int
    corrected: bool


def bytes_to_bits(data: bytes) -> str:
    """Convert bytes to a string of 0/1 characters."""
    return "".join(f"{byte:08b}" for byte in data)


def bits_to_bytes(bits: str) -> bytes:
    """Convert a 0/1 bit string to bytes. Length must be divisible by 8."""
    if len(bits) % 8 != 0:
        raise ValueError("Bit string length must be divisible by 8")
    if any(ch not in "01" for ch in bits):
        raise ValueError("Bit string may contain only 0 and 1")
    return bytes(int(bits[i : i + 8], 2) for i in range(0, len(bits), 8))


def flip_bit(bits: str, zero_based_index: int) -> str:
    """Return a copy of bits with one bit inverted."""
    if zero_based_index < 0 or zero_based_index >= len(bits):
        raise ValueError(f"Bit index {zero_based_index} is outside 0..{len(bits) - 1}")
    replacement = "1" if bits[zero_based_index] == "0" else "0"
    return bits[:zero_based_index] + replacement + bits[zero_based_index + 1 :]


def make_crc32_packet(payload: bytes) -> bytes:
    """Append CRC-32 checksum to payload. Checksum is stored as 4 big-endian bytes."""
    crc = binascii.crc32(payload) & 0xFFFFFFFF
    return payload + crc.to_bytes(4, byteorder="big")


def verify_crc32_packet(packet: bytes) -> tuple[bool, bytes, int, int]:
    """Verify a payload+CRC packet.

    Returns: (is_ok, payload, expected_crc_from_packet, actual_crc_for_payload).
    """
    if len(packet) < 4:
        return False, b"", 0, 0
    payload = packet[:-4]
    expected_crc = int.from_bytes(packet[-4:], byteorder="big")
    actual_crc = binascii.crc32(payload) & 0xFFFFFFFF
    return expected_crc == actual_crc, payload, expected_crc, actual_crc


def _required_parity_bits(data_length: int) -> int:
    """Smallest r such that 2^r >= data_length + r + 1."""
    r = 0
    while (1 << r) < data_length + r + 1:
        r += 1
    return r


def _is_power_of_two(value: int) -> bool:
    return value > 0 and (value & (value - 1)) == 0


def hamming_encode(data_bits: str) -> str:
    """Encode arbitrary data bits with even-parity Hamming code.

    Parity bits are placed at 1-based positions 1, 2, 4, 8, ... .
    Each parity bit p checks positions whose binary index contains bit p.
    This is the same as: take p bits, skip p bits, take p bits, skip p bits, ... .
    """
    if any(ch not in "01" for ch in data_bits):
        raise ValueError("data_bits may contain only 0 and 1")

    r = _required_parity_bits(len(data_bits))
    n = len(data_bits) + r
    encoded = [0] * n

    data_index = 0
    for position in range(1, n + 1):
        if not _is_power_of_two(position):
            encoded[position - 1] = int(data_bits[data_index])
            data_index += 1

    for p in (1 << i for i in range(r)):
        parity = 0
        for position in range(1, n + 1):
            if position & p:
                parity ^= encoded[position - 1]
        encoded[p - 1] = parity

    return "".join(str(bit) for bit in encoded)


def hamming_decode(received_bits: str) -> HammingDecodeResult:
    """Decode Hamming bits and correct one bit if the syndrome points to it."""
    if any(ch not in "01" for ch in received_bits):
        raise ValueError("received_bits may contain only 0 and 1")

    corrected = [int(ch) for ch in received_bits]
    n = len(corrected)
    r = 0
    while (1 << r) <= n:
        r += 1

    syndrome = 0
    for p in (1 << i for i in range(r)):
        parity = 0
        for position in range(1, n + 1):
            if position & p:
                parity ^= corrected[position - 1]
        if parity:
            syndrome += p

    was_corrected = False
    if 1 <= syndrome <= n:
        corrected[syndrome - 1] ^= 1
        was_corrected = True

    data_bits = "".join(
        str(corrected[position - 1])
        for position in range(1, n + 1)
        if not _is_power_of_two(position)
    )

    return HammingDecodeResult(
        received_bits=received_bits,
        corrected_bits="".join(str(bit) for bit in corrected),
        data_bits=data_bits,
        syndrome=syndrome,
        corrected=was_corrected,
    )


def binary_preview(bits: str, limit: int = 96) -> str:
    """Short readable bit preview for console output."""
    if len(bits) <= limit:
        return bits
    return bits[:limit] + f"... ({len(bits)} bits total)"
