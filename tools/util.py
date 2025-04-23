"""This is where the extra random junk lives."""

import multiprocessing
import multiprocessing.pool
import socket
import ssl
from collections.abc import Sequence
from typing import Callable


def ssl_wrap(sock: socket.socket, host: str) -> socket.socket:
    """Turns a plain socket into a TLS-capable socket."""
    ctx = ssl.create_default_context()
    return ctx.wrap_socket(sock, server_hostname=host)


_RECV_SIZE: int = 65536


def really_recv(sock: socket.socket) -> bytes:
    """Receives bytes from a socket until a timeout expires."""
    result: bytes = b""
    while True:
        try:
            b: bytes = sock.recv(_RECV_SIZE)
        except (BlockingIOError, ConnectionResetError, TimeoutError):
            break
        if len(b) == 0:
            break
        result += b
    return result


def eager_pmap[U, T](f: Callable[[U], T], s: Sequence[U]) -> list[T]:
    with multiprocessing.pool.ThreadPool(multiprocessing.cpu_count()) as pool:
        return list(pool.map(f, s))


def translate(b: bytes, tr: dict[bytes, bytes]) -> bytes:
    result: bytes = b
    for old, new in tr.items():
        result = result.replace(old, new)
    return result
