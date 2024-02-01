"""HTTP echo server. Receives TCP data, sends back an HTTP response containing that data in its message body."""

import socket
import threading
import sys

RECV_SIZE: int = 65536
SOCKET_TIMEOUT:float = 0.1


def really_recv(sock: socket.socket) -> bytes:
    """Receives bytes from a socket until a timeout expires."""
    result: bytes = b""
    try:
        while b := sock.recv(RECV_SIZE):
            result += b
    except TimeoutError:
        pass
    return result


def handle_connection(client_sock: socket.socket) -> None:
    client_sock.settimeout(SOCKET_TIMEOUT)
    while payload := really_recv(client_sock):
        try:
            client_sock.sendall(
                f"HTTP/1.1 200 OK\r\nContent-Length: {len(payload)}\r\n\r\n".encode("ascii") + payload
            )
        except ConnectionResetError:
            pass
    client_sock.close()


def main() -> None:
    """Serve"""
    server_sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(("0.0.0.0", 80))
    server_sock.listen()
    while True:
        client_sock, _ = server_sock.accept()
        t: threading.Thread = threading.Thread(target=handle_connection, args=(client_sock,))
        t.start()

if __name__ == "__main__":
    main()
