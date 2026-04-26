"""Quick correctness checks for the demo project."""

from coding_app.algorithms import (
    bits_to_bytes,
    bytes_to_bits,
    flip_bit,
    hamming_decode,
    hamming_encode,
    make_crc32_packet,
    verify_crc32_packet,
)
from compression_app.algorithms import compress_bytes, decompress_bytes


def test_crc() -> None:
    data = "Hello, KS!".encode("utf-8")
    packet = make_crc32_packet(data)
    ok, restored, _, _ = verify_crc32_packet(packet)
    assert ok and restored == data

    corrupted_bits = flip_bit(bytes_to_bits(packet), 3)
    corrupted_packet = bits_to_bytes(corrupted_bits)
    ok, _, _, _ = verify_crc32_packet(corrupted_packet)
    assert not ok


def test_hamming() -> None:
    data = "Hello, KS!".encode("utf-8")
    data_bits = bytes_to_bits(data)
    encoded = hamming_encode(data_bits)
    corrupted = flip_bit(encoded, 7)
    result = hamming_decode(corrupted)
    restored = bits_to_bytes(result.data_bits[: len(data_bits)])
    assert result.corrected
    assert restored == data


def test_compression() -> None:
    data = ("demo demo demo code code network network " * 10).encode("utf-8")
    for algorithm in ("shannon_fano", "huffman"):
        result = compress_bytes(data, algorithm)  # type: ignore[arg-type]
        restored = decompress_bytes(result.compressed)
        assert restored == data


def main() -> None:
    test_crc()
    test_hamming()
    test_compression()
    print("All tests passed")


if __name__ == "__main__":
    main()
