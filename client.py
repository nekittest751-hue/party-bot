#!/usr/bin/env python3
"""Simple TCP messenger client."""

from __future__ import annotations

import argparse
import socket
import sys
import threading

BUFFER_SIZE = 4096


def recv_messages(sock: socket.socket) -> None:
    while True:
        try:
            data = sock.recv(BUFFER_SIZE)
        except OSError:
            break
        if not data:
            print("\n[client] Connection closed by server")
            break
        print(data.decode("utf-8", errors="ignore"), end="")


def run_client(host: str, port: int, username: str) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    prompt = sock.recv(BUFFER_SIZE).decode("utf-8", errors="ignore")
    print(prompt, end="")
    sock.sendall((username + "\n").encode("utf-8"))

    recv_thread = threading.Thread(target=recv_messages, args=(sock,), daemon=True)
    recv_thread.start()

    try:
        for line in sys.stdin:
            sock.sendall(line.encode("utf-8"))
            if line.strip().lower() == "/quit":
                break
    except KeyboardInterrupt:
        sock.sendall(b"/quit\n")
    finally:
        sock.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run messenger client")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="Server port (default: 5000)")
    parser.add_argument("--username", required=True, help="Your username")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_client(args.host, args.port, args.username)
