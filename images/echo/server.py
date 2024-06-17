"""HTTP echo server. Receives TCP data, sends back an HTTP response containing that data in its message body."""

import socket
import threading

RECV_SIZE = 65536
SOCKET_TIMEOUT = 0.1


def really_recv(sock: socket.socket) -> bytes:
    """Receives bytes from a socket until a timeout expires."""
    result: bytes = b""
    while True:
        try:
            b: bytes = sock.recv(RECV_SIZE)
            if len(b) == 0:
                break
            result += b
        except (BlockingIOError, ConnectionResetError, TimeoutError):
            break
    return result


def handle_connection(client_sock: socket.socket, _client_address: tuple[str, int]) -> None:
    client_sock.settimeout(SOCKET_TIMEOUT)
    while payload := really_recv(client_sock):
        try:
            client_sock.sendall(
                    f"HTTP/1.1 200 OK\r\nCache-Control: public, max-age=2592000\r\nServer: echo-python\r\nContent-Length: {len(payload)}\r\n\r\n".encode("ascii") + payload
            )
        except ConnectionResetError:
            break
    client_sock.close()


def main() -> None:
    """Serve"""
    server_sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(("0.0.0.0", 80))
    server_sock.listen()
    while True:
        t: threading.Thread = threading.Thread(target=handle_connection, args=(*server_sock.accept(),))
        t.start()

if __name__ == "__main__":
    main()
