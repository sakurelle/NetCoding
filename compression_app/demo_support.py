"""Helpers for detailed single-algorithm compression demos."""

from __future__ import annotations

from pathlib import Path

from compression_app.algorithms import (
    compress_bytes,
    decompress_bytes,
    describe_symbol,
    encode_bits,
    frequencies,
)
from demo_ui import configure_console_utf8, preview_bits, preview_text, print_banner, print_kv, print_step


DEFAULT_SAMPLE = """Computer networks and coding systems demo.\n""" \
    """This file intentionally contains repeated words: demo demo demo, code code code, network network.\n""" \
    """Алгоритмы Шеннона-Фано и Хаффмана хорошо сжимают повторяющиеся символы.\n""" \
    """0000000000111111111122222222223333333333\n"""

ALGORITHM_TITLES = {
    "shannon_fano": "ШЕННОН-ФАНО",
    "huffman": "ХАФФМАН",
}


def ensure_sample_file() -> Path:
    path = Path("data/sample.txt")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(DEFAULT_SAMPLE, encoding="utf-8")
    return path


def _table_preview(data: bytes, codebook: dict[int, str], limit: int = 12) -> list[tuple[str, int, str]]:
    freq = frequencies(data)
    items = sorted(codebook.items(), key=lambda item: (-freq[item[0]], item[0]))[:limit]
    return [(describe_symbol(symbol), freq[symbol], code) for symbol, code in items]


def _ratio(part: int, whole: int) -> float:
    return (part / whole) if whole else 0.0


def run_single_algorithm_demo(source_path: Path, algorithm: str) -> None:
    configure_console_utf8()
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    data = source_path.read_bytes()
    result = compress_bytes(data, algorithm)  # type: ignore[arg-type]
    bit_string = encode_bits(data, result.codebook) if data else ""

    suffix = ".sfano.ksc" if algorithm == "shannon_fano" else ".huff.ksc"
    compressed_path = source_path.with_name(source_path.name + suffix)
    restored_path = source_path.with_name(source_path.name + suffix + ".restored")
    compressed_path.write_bytes(result.compressed)
    restored = decompress_bytes(result.compressed)
    restored_path.write_bytes(restored)

    try:
        text_preview = preview_text(data.decode("utf-8"))
    except UnicodeDecodeError:
        text_preview = data[:48].hex(" ")

    print_banner(f"ЧАСТЬ 2. {ALGORITHM_TITLES.get(algorithm, algorithm.upper())}: СЖАТИЕ ФАЙЛА")

    print_step(1, "Исходный файл")
    print_kv("Файл:", source_path)
    print_kv("Размер:", f"{len(data)} байт")
    print_kv("Превью:", text_preview)

    print_step(2, "Частоты символов")
    for symbol, count, _ in _table_preview(data, result.codebook):
        print_kv(f"Символ {symbol!r}:", f"частота {count}")

    print_step(3, "Построенная кодовая таблица")
    for symbol, count, code in _table_preview(data, result.codebook):
        print_kv(f"Символ {symbol!r}:", f"частота {count}, код {code}")

    print_step(4, "Кодирование")
    print_kv("Длина битового потока:", f"{len(bit_string)} бит")
    print_kv("Первые биты:", preview_bits(bit_string))

    print_step(5, "Результат сжатия")
    print_kv("Сжатая полезная нагрузка:", f"{result.encoded_payload_size} байт")
    print_kv("Итоговый .ksc файл:", f"{result.container_size} байт")
    print_kv("Коэффициент по payload:", f"{_ratio(result.encoded_payload_size, result.original_size):.3f}")
    print_kv("Коэффициент по .ksc:", f"{_ratio(result.container_size, result.original_size):.3f}")
    print_kv("Сжатый файл:", compressed_path)

    print_step(6, "Восстановление")
    print_kv("Восстановленный файл:", restored_path)
    print_kv("Совпадает с исходным:", restored == data)
    print("[DEMO] На маленьких файлах итоговый .ksc может быть больше исходника из-за заголовка с таблицей кодов.")
