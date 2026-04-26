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


@dataclass(frozen=True)
class HammingParityDetail:
    parity_position: int
    covered_positions: tuple[int, ...]
    covered_values: tuple[int, ...]
    ones_count: int
    parity_value: int


@dataclass(frozen=True)
class HammingEncodeDetails:
    data_bits: str
    arranged_bits: str
    encoded_bits: str
    parity_details: tuple[HammingParityDetail, ...]


@dataclass(frozen=True)
class HammingParityCheck:
    parity_position: int
    covered_positions: tuple[int, ...]
    covered_values: tuple[int, ...]
    xor_result: int


@dataclass(frozen=True)
class HammingDecodeDetails:
    result: HammingDecodeResult
    parity_checks: tuple[HammingParityCheck, ...]


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


def parity_positions_for_length(data_length: int) -> list[int]:
    """Return parity bit positions for a Hamming word containing data_length bits."""
    return [1 << i for i in range(_required_parity_bits(data_length))]


def arrange_hamming_bits(data_bits: str) -> str:
    """Place data bits into non-parity positions and fill parity positions with 0."""
    if any(ch not in "01" for ch in data_bits):
        raise ValueError("data_bits may contain only 0 and 1")

    r = _required_parity_bits(len(data_bits))
    n = len(data_bits) + r
    arranged = [0] * n

    data_index = 0
    for position in range(1, n + 1):
        if not _is_power_of_two(position):
            arranged[position - 1] = int(data_bits[data_index])
            data_index += 1

    return "".join(str(bit) for bit in arranged)


def parity_coverage(length: int, parity_position: int) -> list[int]:
    """Return 1-based positions controlled by a parity bit."""
    if parity_position <= 0 or not _is_power_of_two(parity_position):
        raise ValueError("parity_position must be a positive power of two")
    return [position for position in range(1, length + 1) if position & parity_position]


def hamming_encode_detailed(data_bits: str) -> HammingEncodeDetails:
    """Return encoded Hamming bits together with parity calculation details."""
    arranged_bits = arrange_hamming_bits(data_bits)
    encoded = [int(ch) for ch in arranged_bits]
    parity_details: list[HammingParityDetail] = []

    for parity_position in parity_positions_for_length(len(data_bits)):
        covered = parity_coverage(len(encoded), parity_position)
        values = [encoded[position - 1] for position in covered]
        ones_count = sum(values)
        parity_value = ones_count % 2
        encoded[parity_position - 1] = parity_value
        parity_details.append(
            HammingParityDetail(
                parity_position=parity_position,
                covered_positions=tuple(covered),
                covered_values=tuple(values),
                ones_count=ones_count,
                parity_value=parity_value,
            )
        )

    return HammingEncodeDetails(
        data_bits=data_bits,
        arranged_bits=arranged_bits,
        encoded_bits="".join(str(bit) for bit in encoded),
        parity_details=tuple(parity_details),
    )


def hamming_encode(data_bits: str) -> str:
    """Encode arbitrary data bits with even-parity Hamming code.

    Parity bits are placed at 1-based positions 1, 2, 4, 8, ... .
    Each parity bit p checks positions whose binary index contains bit p.
    This is the same as: take p bits, skip p bits, take p bits, skip p bits, ... .
    """
    return hamming_encode_detailed(data_bits).encoded_bits


def hamming_decode_detailed(received_bits: str) -> HammingDecodeDetails:
    """Decode a Hamming word and return parity-check details used for the syndrome."""
    if any(ch not in "01" for ch in received_bits):
        raise ValueError("received_bits may contain only 0 and 1")

    received = [int(ch) for ch in received_bits]
    parity_checks: list[HammingParityCheck] = []
    syndrome = 0
    parity_position = 1

    while parity_position <= len(received):
        covered = parity_coverage(len(received), parity_position)
        values = [received[position - 1] for position in covered]
        xor_result = 0
        for value in values:
            xor_result ^= value
        if xor_result:
            syndrome += parity_position
        parity_checks.append(
            HammingParityCheck(
                parity_position=parity_position,
                covered_positions=tuple(covered),
                covered_values=tuple(values),
                xor_result=xor_result,
            )
        )
        parity_position <<= 1

    corrected = received[:]
    was_corrected = False
    if 1 <= syndrome <= len(corrected):
        corrected[syndrome - 1] ^= 1
        was_corrected = True

    data_bits = "".join(
        str(corrected[position - 1])
        for position in range(1, len(corrected) + 1)
        if not _is_power_of_two(position)
    )

    result = HammingDecodeResult(
        received_bits=received_bits,
        corrected_bits="".join(str(bit) for bit in corrected),
        data_bits=data_bits,
        syndrome=syndrome,
        corrected=was_corrected,
    )
    return HammingDecodeDetails(result=result, parity_checks=tuple(parity_checks))


def hamming_decode(received_bits: str) -> HammingDecodeResult:
    """Decode Hamming bits and correct one bit if the syndrome points to it."""
    return hamming_decode_detailed(received_bits).result


def binary_preview(bits: str, limit: int = 96) -> str:
    """Short readable bit preview for console output."""
    if len(bits) <= limit:
        return bits
    return bits[:limit] + f"... ({len(bits)} bits total)"
