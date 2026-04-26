"""One-command demo for task 1: CRC-32 and Hamming in a client-server app.

Run:
    python coding_demo.py --message "Hello, KS!"
"""

from __future__ import annotations

import argparse
import threading
import time

from coding_app.client import demo_crc32, demo_hamming
from coding_app.server import start_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Automatic client-server demo for CRC-32 and Hamming")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9009)
    parser.add_argument("--message", default="Hello, KS!")
    parser.add_argument("--crc-error-bit", type=int, default=5)
    parser.add_argument("--hamming-error-bit", type=int, default=7)
    args = parser.parse_args()

    server_thread = threading.Thread(
        target=start_server,
        kwargs={"host": args.host, "port": args.port, "max_messages": 3},
        daemon=True,
    )
    server_thread.start()
    time.sleep(0.25)

    demo_crc32(args.host, args.port, args.message, args.crc_error_bit)
    demo_hamming(args.host, args.port, args.message, args.hamming_error_bit)

    server_thread.join(timeout=3)
    print("\n[DEMO] Coding demo finished")


if __name__ == "__main__":
    main()
