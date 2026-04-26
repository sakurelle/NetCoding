"""Detailed terminal demo for the Hamming-code client-server part of the assignment."""

from __future__ import annotations

import argparse
import threading
import time

from coding_app.algorithms import (
    bytes_to_bits,
    flip_bit,
    hamming_encode_detailed,
    parity_positions_for_length,
)
from coding_app.client import send_json
from coding_app.server import start_server
from demo_ui import (
    configure_console_utf8,
    group_bits,
    highlight_bit,
    preview_bits,
    print_banner,
    print_kv,
    print_step,
    render_positions,
    render_values,
)


def _build_role_row(length: int, parity_positions: set[int]) -> list[str]:
    roles: list[str] = []
    data_index = 1
    for position in range(1, length + 1):
        if position in parity_positions:
            roles.append(f"P{position}")
        else:
            roles.append(f"D{data_index}")
            data_index += 1
    return roles


def _build_arranged_value_row(arranged_bits: str, parity_positions: set[int]) -> list[str]:
    values: list[str] = []
    for position, bit in enumerate(arranged_bits, start=1):
        values.append("_" if position in parity_positions else bit)
    return values


def main() -> None:
    configure_console_utf8()

    parser = argparse.ArgumentParser(description="Detailed Hamming-code client-server demo")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9011)
    parser.add_argument("--message", default="KS")
    parser.add_argument("--error-bit", type=int, default=7, help="0-based bit index to flip in the encoded word")
    args = parser.parse_args()

    server_thread = threading.Thread(
        target=start_server,
        kwargs={"host": args.host, "port": args.port, "max_messages": 1},
        daemon=True,
    )
    server_thread.start()
    time.sleep(0.25)

    payload = args.message.encode("utf-8")
    data_bits = bytes_to_bits(payload)
    details = hamming_encode_detailed(data_bits)
    parity_positions = set(parity_positions_for_length(len(data_bits)))
    corrupted_bits = flip_bit(details.encoded_bits, args.error_bit)

    print_banner("ЧАСТЬ 1B. КОД ХЭММИНГА: ОБНАРУЖЕНИЕ И ИСПРАВЛЕНИЕ ОШИБКИ")

    print_step(1, "Исходное сообщение")
    print_kv("Текст:", repr(args.message))
    print_kv("UTF-8 байты:", payload.hex(" "))
    print_kv("Биты сообщения:", group_bits(data_bits))

    print_step(2, "Расстановка служебных битов")
    print_kv("Служебные позиции:", sorted(parity_positions))
    if len(details.arranged_bits) <= 32:
        print("Позиции: ", render_positions(list(range(1, len(details.arranged_bits) + 1))))
        print("Роли:    ", render_values(_build_role_row(len(details.arranged_bits), parity_positions)))
        print("Значения:", render_values(_build_arranged_value_row(details.arranged_bits, parity_positions)))
    else:
        print_kv("Разложенное слово:", preview_bits(details.arranged_bits))

    print_step(3, "Вычисление контрольных битов")
    for detail in details.parity_details:
        positions = ",".join(str(position) for position in detail.covered_positions)
        values = "".join(str(value) for value in detail.covered_values)
        print_kv(
            f"P{detail.parity_position}:",
            f"позиции [{positions}] -> биты {values} -> единиц {detail.ones_count} -> P = {detail.parity_value}",
        )
    print_kv("Готовое кодовое слово:", group_bits(details.encoded_bits))

    print_step(4, "Внесение искусственной ошибки")
    print_kv("Выбранный бит ошибки:", f"{args.error_bit} (0-based index)")
    print_kv("До ошибки:", highlight_bit(details.encoded_bits, args.error_bit))
    print_kv("После ошибки:", highlight_bit(corrupted_bits, args.error_bit))

    print_step(5, "Передача кодового слова на сервер")
    response = send_json(
        args.host,
        args.port,
        {
            "algorithm": "hamming",
            "encoded_bits": corrupted_bits,
            "original_data_bit_length": len(data_bits),
        },
    )
    print_kv("Ответ сервера:", response)

    server_thread.join(timeout=3)
    print_banner("HAMMING DEMO FINISHED", char="-")


if __name__ == "__main__":
    main()
