"""Client helpers for the CRC-32 and Hamming coding demo."""

from __future__ import annotations

import argparse
import json
import socket
import sys

from coding_app.algorithms import (
    binary_preview,
    bytes_to_bits,
    flip_bit,
    hamming_encode,
    make_crc32_packet,
)


def _configure_console_utf8() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def send_json(host: str, port: int, message: dict) -> dict:
    raw = (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")
    with socket.create_connection((host, port), timeout=5) as sock:
        sock.sendall(raw)
        chunks: list[bytes] = []
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            if b"\n" in chunk:
                break
    response_raw = b"".join(chunks).split(b"\n", 1)[0]
    return json.loads(response_raw.decode("utf-8"))


def demo_crc32(host: str, port: int, text: str, error_bit: int) -> None:
    _configure_console_utf8()
    payload = text.encode("utf-8")
    packet = make_crc32_packet(payload)
    packet_bits = bytes_to_bits(packet)
    corrupted_bits = flip_bit(packet_bits, error_bit)

    print("\n[CLIENT] CRC-32 demo")
    print(f"[CLIENT] original message: {text!r}")
    print(f"[CLIENT] packet bits: {binary_preview(packet_bits)}")
    print(f"[CLIENT] sending packet with artificial error at bit index {error_bit} (0-based)")

    response = send_json(
        host,
        port,
        {
            "algorithm": "crc32",
            "packet_bits": corrupted_bits,
            "comment": "This packet was intentionally corrupted for the demo.",
        },
    )
    print(f"[CLIENT] server response: {response}")

    if response.get("status") == "error_detected":
        print("[CLIENT] CRC detected the error. Now retransmitting the correct packet.")
        response = send_json(
            host,
            port,
            {
                "algorithm": "crc32",
                "packet_bits": packet_bits,
                "comment": "Retransmission after CRC error detection.",
            },
        )
        print(f"[CLIENT] server response after retransmission: {response}")


def demo_hamming(host: str, port: int, text: str, error_bit: int) -> None:
    _configure_console_utf8()
    payload = text.encode("utf-8")
    data_bits = bytes_to_bits(payload)
    encoded_bits = hamming_encode(data_bits)
    corrupted_bits = flip_bit(encoded_bits, error_bit)

    print("\n[CLIENT] Hamming demo")
    print(f"[CLIENT] original message: {text!r}")
    print(f"[CLIENT] data bits: {binary_preview(data_bits)}")
    print(f"[CLIENT] encoded bits: {binary_preview(encoded_bits)}")
    print(f"[CLIENT] sending codeword with artificial error at bit index {error_bit} (0-based)")

    response = send_json(
        host,
        port,
        {
            "algorithm": "hamming",
            "encoded_bits": corrupted_bits,
            "original_data_bit_length": len(data_bits),
            "comment": "This Hamming codeword was intentionally corrupted for the demo.",
        },
    )
    print(f"[CLIENT] server response: {response}")


def main() -> None:
    _configure_console_utf8()
    parser = argparse.ArgumentParser(description="Client for CRC-32 and Hamming demo")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9009)
    parser.add_argument("--message", default="Hello, KS!")
    parser.add_argument("--algorithm", choices=["crc32", "hamming"], required=True)
    parser.add_argument("--error-bit", type=int, default=5)
    args = parser.parse_args()

    if args.algorithm == "crc32":
        demo_crc32(args.host, args.port, args.message, args.error_bit)
    else:
        demo_hamming(args.host, args.port, args.message, args.error_bit)


if __name__ == "__main__":
    main()
