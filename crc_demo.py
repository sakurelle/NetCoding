"""Detailed terminal demo for the CRC-32 client-server part of the assignment."""

from __future__ import annotations

import argparse
import threading
import time

from coding_app.algorithms import bytes_to_bits, flip_bit, make_crc32_packet
from coding_app.client import send_json
from coding_app.server import start_server
from demo_ui import configure_console_utf8, group_bits, highlight_bit, print_banner, print_kv, print_step


def main() -> None:
    configure_console_utf8()

    parser = argparse.ArgumentParser(description="Detailed CRC-32 client-server demo")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9010)
    parser.add_argument("--message", default="Привет, КС!")
    parser.add_argument("--error-bit", type=int, default=5, help="0-based bit index to flip in the transmitted packet")
    args = parser.parse_args()

    server_thread = threading.Thread(
        target=start_server,
        kwargs={"host": args.host, "port": args.port, "max_messages": 2},
        daemon=True,
    )
    server_thread.start()
    time.sleep(0.25)

    payload = args.message.encode("utf-8")
    payload_bits = bytes_to_bits(payload)
    packet = make_crc32_packet(payload)
    packet_bits = bytes_to_bits(packet)
    crc_bytes = packet[-4:]
    crc_bits = bytes_to_bits(crc_bytes)
    corrupted_bits = flip_bit(packet_bits, args.error_bit)

    print_banner("ЧАСТЬ 1A. CRC-32: КЛИЕНТ-СЕРВЕРНОЕ ОБНАРУЖЕНИЕ ОШИБКИ")

    print_step(1, "Исходное сообщение")
    print_kv("Текст:", repr(args.message))
    print_kv("UTF-8 байты:", payload.hex(" "))
    print_kv("Биты сообщения:", group_bits(payload_bits))

    print_step(2, "Формирование CRC-пакета")
    print_kv("CRC-32 (hex):", "0x" + crc_bytes.hex().upper())
    print_kv("CRC-32 (bits):", group_bits(crc_bits))
    print_kv("Пакет целиком:", group_bits(packet_bits))

    print_step(3, "Внесение искусственной ошибки")
    print_kv("Выбранный бит ошибки:", f"{args.error_bit} (0-based index)")
    print_kv("До ошибки:", highlight_bit(packet_bits, args.error_bit))
    print_kv("После ошибки:", highlight_bit(corrupted_bits, args.error_bit))

    print_step(4, "Передача повреждённого пакета на сервер")
    response = send_json(
        args.host,
        args.port,
        {
            "algorithm": "crc32",
            "packet_bits": corrupted_bits,
        },
    )
    print_kv("Ответ сервера:", response)

    print_step(5, "Восстановление сообщения")
    if response.get("status") == "error_detected":
        print("[CLIENT] CRC-32 только обнаруживает ошибку, поэтому отправляем пакет повторно без искажения.")
        response = send_json(
            args.host,
            args.port,
            {
                "algorithm": "crc32",
                "packet_bits": packet_bits,
            },
        )
        print_kv("Ответ после повтора:", response)
    else:
        print("[CLIENT] Сервер не обнаружил ошибку, повторная передача не понадобилась.")

    server_thread.join(timeout=3)
    print_banner("CRC-32 DEMO FINISHED", char="-")


if __name__ == "__main__":
    main()
