"""This is where the extra random junk lives."""

import multiprocessing
import multiprocessing.pool
import socket
import ssl
from collections.abc import Sequence
from typing import Callable, Iterable


def to_bits(byte: int) -> list[bool]:
    """ MSB first. """
    assert 0 <= byte < 0x100
    return [bool(((byte >> (7 - i)) & 1)) for i in range(8)]


def ssl_wrap(sock: socket.socket, host: str, alpn_protocols: list[str] | None = None) -> socket.socket:
    """Turns a plain socket into a TLS-capable socket."""
    ctx: ssl.SSLContext = ssl._create_unverified_context()
    if alpn_protocols is not None:
        ctx.set_alpn_protocols(alpn_protocols)
    return ctx.wrap_socket(sock, server_hostname=host)


_RECV_SIZE: int = 0x10000


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
