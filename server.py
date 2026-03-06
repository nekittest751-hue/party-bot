#!/usr/bin/env python3
"""Simple TCP messenger server with broadcast chat."""

from __future__ import annotations

import argparse
import socket
import threading
from dataclasses import dataclass

BUFFER_SIZE = 4096


@dataclass
class Client:
    conn: socket.socket
    addr: tuple[str, int]
    username: str


class MessengerServer:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients: list[Client] = []
        self.lock = threading.Lock()

    def start(self) -> None:
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"[server] Listening on {self.host}:{self.port}")

        try:
            while True:
                conn, addr = self.server_socket.accept()
                thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
                thread.start()
        except KeyboardInterrupt:
            print("\n[server] Shutting down")
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        with self.lock:
            for client in self.clients:
                client.conn.close()
            self.clients.clear()
        self.server_socket.close()

    def handle_client(self, conn: socket.socket, addr: tuple[str, int]) -> None:
        conn.sendall(b"Enter username: ")
        username = self._recv_line(conn)
        if not username:
            conn.close()
            return

        client = Client(conn=conn, addr=addr, username=username)
        with self.lock:
            self.clients.append(client)

        self.broadcast(f"*** {username} joined the chat ***", sender=conn)
        conn.sendall(b"Welcome to messenger! Type /quit to leave.\n")
        print(f"[server] {username} connected from {addr[0]}:{addr[1]}")

        try:
            while True:
                message = self._recv_line(conn)
                if message is None or message.lower() == "/quit":
                    break
                if not message.strip():
                    continue
                self.broadcast(f"{username}: {message}", sender=conn)
        finally:
            with self.lock:
                self.clients = [c for c in self.clients if c.conn != conn]
            conn.close()
            self.broadcast(f"*** {username} left the chat ***", sender=None)
            print(f"[server] {username} disconnected")

    def broadcast(self, message: str, sender: socket.socket | None) -> None:
        payload = (message + "\n").encode("utf-8")
        with self.lock:
            disconnected: list[Client] = []
            for client in self.clients:
                if sender is not None and client.conn == sender:
                    continue
                try:
                    client.conn.sendall(payload)
                except OSError:
                    disconnected.append(client)

            if disconnected:
                self.clients = [c for c in self.clients if c not in disconnected]

    @staticmethod
    def _recv_line(conn: socket.socket) -> str | None:
        data = bytearray()
        while True:
            try:
                chunk = conn.recv(BUFFER_SIZE)
            except OSError:
                return None
            if not chunk:
                return None
            data.extend(chunk)
            if b"\n" in chunk:
                break
        return data.decode("utf-8", errors="ignore").strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run messenger server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind (default: 5000)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    MessengerServer(args.host, args.port).start()
