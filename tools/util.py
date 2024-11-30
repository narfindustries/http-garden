""" This is where the extra random junk lives. """

import multiprocessing.pool
import socket
import ssl
from collections.abc import Iterable, Sequence
from typing import Callable, TypeVar

fingerprint_t = tuple[frozenset[int], ...]  # You might want to make this a hash.


def ssl_wrap(sock: socket.socket, host: str) -> socket.socket:
    """Turns a plain socket into a TLS-capable socket."""
    ctx = ssl.create_default_context()
    ctx.maximum_version = ssl.TLSVersion.TLSv1_3
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
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


_T = TypeVar("_T")
_U = TypeVar("_U")


def unzip(collection: Iterable[tuple[_T, _U]]) -> tuple[list[_T], list[_U]]:
    return ([p[0] for p in collection], [p[1] for p in collection])


def eager_pmap(f: Callable[[_U], _T], s: Sequence[_U]) -> list[_T]:
    with multiprocessing.pool.ThreadPool(32) as pool:
        return list(pool.map(f, s))


def translate(b: bytes, tr: dict[bytes, bytes]) -> bytes:
    result: bytes = b
    for old, new in tr.items():
        result = result.replace(old, new)
    return result
