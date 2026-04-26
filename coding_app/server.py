"""TCP server for CRC-32 and Hamming coding demo."""

from __future__ import annotations

import argparse
import json
import socket
import sys
from typing import Any

from coding_app.algorithms import (
    binary_preview,
    bits_to_bytes,
    hamming_decode,
    verify_crc32_packet,
)


def _decode_text(payload: bytes) -> str:
    return payload.decode("utf-8", errors="replace")


def _configure_console_utf8() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _error_response(note: str) -> dict[str, Any]:
    return {"status": "error", "note": note}


def _require_string(message: dict[str, Any], field: str) -> str:
    value = message.get(field)
    if not isinstance(value, str):
        raise ValueError(f"Field {field!r} must be a string")
    return value


def _require_int(message: dict[str, Any], field: str) -> int:
    value = message.get(field)
    if not isinstance(value, int):
        raise ValueError(f"Field {field!r} must be an integer")
    return value


def handle_message(message: dict[str, Any]) -> dict[str, Any]:
    try:
        algorithm = message.get("algorithm")

        if algorithm == "crc32":
            packet_bits = _require_string(message, "packet_bits")
            packet = bits_to_bytes(packet_bits)
            ok, payload, expected_crc, actual_crc = verify_crc32_packet(packet)

            print("\n[SERVER] CRC-32 packet received")
            print(f"[SERVER] bits: {binary_preview(packet_bits)}")
            print(f"[SERVER] checksum from packet: 0x{expected_crc:08X}")
            print(f"[SERVER] checksum calculated: 0x{actual_crc:08X}")

            if ok:
                text = _decode_text(payload)
                print("[SERVER] CRC result: OK, no error detected")
                print(f"[SERVER] restored message: {text!r}")
                return {
                    "status": "ok",
                    "algorithm": "crc32",
                    "message": text,
                    "note": "CRC detected no error. Payload is accepted.",
                }

            print("[SERVER] CRC result: ERROR DETECTED")
            print("[SERVER] CRC can detect corruption, but it cannot identify and fix the wrong bit.")
            return {
                "status": "error_detected",
                "algorithm": "crc32",
                "expected_crc": f"0x{expected_crc:08X}",
                "actual_crc": f"0x{actual_crc:08X}",
                "note": "CRC-32 does not restore data by itself. Ask client to retransmit.",
            }

        if algorithm == "hamming":
            encoded_bits = _require_string(message, "encoded_bits")
            original_data_bit_length = _require_int(message, "original_data_bit_length")
            result = hamming_decode(encoded_bits)
            if original_data_bit_length < 0 or original_data_bit_length > len(result.data_bits):
                raise ValueError("original_data_bit_length is outside the decoded data range")
            if original_data_bit_length % 8 != 0:
                raise ValueError("original_data_bit_length must be divisible by 8")

            data_bits = result.data_bits[:original_data_bit_length]
            payload = bits_to_bytes(data_bits)
            text = _decode_text(payload)

            print("\n[SERVER] Hamming codeword received")
            print(f"[SERVER] bits: {binary_preview(encoded_bits)}")
            print(f"[SERVER] syndrome: {result.syndrome}")
            if result.corrected:
                print(f"[SERVER] error position: {result.syndrome} (1-based), bit corrected")
            else:
                print("[SERVER] no single-bit error detected")
            print(f"[SERVER] restored message: {text!r}")

            return {
                "status": "corrected" if result.corrected else "ok",
                "algorithm": "hamming",
                "syndrome": result.syndrome,
                "corrected": result.corrected,
                "message": text,
                "corrected_bits_preview": binary_preview(result.corrected_bits),
            }

        return _error_response(f"Unknown algorithm: {algorithm!r}")
    except (TypeError, ValueError, KeyError) as exc:
        return _error_response(str(exc))


def _recv_json_line(conn: socket.socket) -> dict[str, Any] | None:
    chunks: list[bytes] = []
    while True:
        chunk = conn.recv(4096)
        if not chunk:
            break
        chunks.append(chunk)
        if b"\n" in chunk:
            break
    if not chunks:
        return None
    raw = b"".join(chunks).split(b"\n", 1)[0]
    return json.loads(raw.decode("utf-8"))


def start_server(host: str = "127.0.0.1", port: int = 9009, max_messages: int | None = None) -> None:
    """Run server. If max_messages is given, stop after that many requests."""
    _configure_console_utf8()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen()
        print(f"[SERVER] listening on {host}:{port}")

        processed = 0
        while max_messages is None or processed < max_messages:
            conn, addr = server_socket.accept()
            with conn:
                print(f"\n[SERVER] connection from {addr[0]}:{addr[1]}")
                try:
                    request = _recv_json_line(conn)
                    if request is None:
                        response = _error_response("Empty request")
                    else:
                        response = handle_message(request)
                except (json.JSONDecodeError, TypeError, ValueError) as exc:
                    print(f"[SERVER] bad request: {exc}")
                    response = _error_response(str(exc))
                except Exception as exc:
                    print(f"[SERVER] unexpected error: {exc}")
                    response = _error_response("Internal server error")
                conn.sendall((json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8"))
                processed += 1

        print("\n[SERVER] demo request limit reached; server stopped")


def main() -> None:
    parser = argparse.ArgumentParser(description="Server for CRC-32 and Hamming demo")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9009)
    parser.add_argument(
        "--max-messages",
        type=int,
        default=None,
        help="Stop after N messages. Omit for a long-running server.",
    )
    args = parser.parse_args()
    start_server(args.host, args.port, args.max_messages)


if __name__ == "__main__":
    main()
