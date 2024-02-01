"""Invisible TCP proxy that logs all input and output."""

import socket
import sys

RECV_SIZE = 65536
SOCKET_TIMEOUT = 0.1


def really_recv(sock: socket.socket) -> bytes:
    """Receives bytes from a socket until a timeout expires."""
    result: bytes = b""
    try:
        while b := sock.recv(RECV_SIZE):
            result += b
    except TimeoutError:
        pass
    return result


def main(backend: str, backend_port: int, frontend_port: int) -> None:
    """Serve"""
    frontend_sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    frontend_sock.bind(("0.0.0.0", frontend_port))
    frontend_sock.listen()
    while True:
        client_sock, _ = frontend_sock.accept()
        client_sock.settimeout(SOCKET_TIMEOUT)
        backend_sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        backend_sock.connect((backend, backend_port))
        backend_sock.settimeout(SOCKET_TIMEOUT)
        while payload := really_recv(client_sock):
            print(f"Client: {payload!r}", file=sys.stderr, flush=True)
            backend_sock.sendall(payload)
            response: bytes = really_recv(backend_sock)
            print(f"Backend: {response!r}", file=sys.stderr, flush=True)
            client_sock.sendall(response)
        client_sock.close()
        backend_sock.close()


if __name__ == "__main__":
    import argparse

    arg_parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Narf HTTP fanout script. Takes input on stdin, and forwards it to all servers specified in `targets.py`."
    )
    arg_parser.add_argument(
        "--backend",
        required=True,
        type=str,
        help="The host to which we'll forward the traffic",
    )
    arg_parser.add_argument(
        "--backend-port",
        required=True,
        type=int,
        help="The port to which we'll forward the traffic",
    )
    arg_parser.add_argument(
        "--frontend-port",
        required=True,
        type=int,
        help="The port from which we'll forward the traffic",
    )

    args: argparse.Namespace = arg_parser.parse_args()
    main(args.backend, args.backend_port, args.frontend_port)
