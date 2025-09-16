"""This is where the extra random junk lives."""

import multiprocessing
import multiprocessing.pool
import socket
import ssl
from collections.abc import Sequence
from typing import Callable, Iterator


def safe_next[T](it: Iterator[T]) -> T | None:
    try:
        return next(it)
    except StopIteration:
        return None


def to_bits(byte: int) -> list[bool]:
    """MSB first."""
    assert 0 <= byte < 0x100
    return [bool(((byte >> (7 - i)) & 1)) for i in range(8)]


def ssl_wrap(sock: socket.socket, host: str, alpn_protocols: list[str] | None = None) -> socket.socket:
    """Turns a plain socket into a TLS-capable socket."""
    ctx: ssl.SSLContext = ssl._create_unverified_context()
    if alpn_protocols is not None:
        ctx.set_alpn_protocols(alpn_protocols)
    return ctx.wrap_socket(sock, server_hostname=host)


_RECV_SIZE: int = 0x10000


def sendall(sock: socket.socket, data: bytes) -> None:
    # print(f"=> {data!r} {sock.getpeername()}", file=sys.stderr)
    sock.sendall(data)


def recvall(sock: socket.socket, flags: socket.MsgFlag | None = None) -> bytes:
    """Receives bytes from a socket until a timeout expires."""
    result: bytes = b""
    while True:
        try:
            b: bytes
            if flags is None:
                b = sock.recv(_RECV_SIZE)
            else:
                b = sock.recv(_RECV_SIZE, flags)
            result += b
        except TimeoutError:
            break
        if len(b) == 0:
            break
    # print(f"<= {result!r} {sock.getpeername()}", file=sys.stderr)
    return result


def roundtrip(sock: socket.socket, data: list[bytes], recv_callback=recvall) -> list[bytes]:
    """Run by a client to connect to a server. Sends each piece of data, receiving between each send, and returns the received bytes."""
    result: list[bytes] = []
    try:
        for datum in data:
            sendall(sock, datum)
            result.append(recv_callback(sock))
        postamble: bytes = recv_callback(sock)
        if postamble:
            result.append(postamble)
    except (ssl.SSLEOFError, ConnectionRefusedError, BrokenPipeError, OSError, BlockingIOError, ConnectionResetError):
        pass
    return result


def eager_pmap[U, T](f: Callable[[U], T], s: Sequence[U]) -> list[T]:
    with multiprocessing.pool.ThreadPool(multiprocessing.cpu_count()) as pool:
        return list(pool.map(f, s))


def list_split[T](l: list[T], t: T) -> list[list[T]]:
    result: list[list[T]] = []
    while t in l:
        result.append(l[: l.index(t)])
        l = l[l.index(t) + 1 :]
    result.append(l)
    return result


def translate(b: bytes, tr: dict[bytes, bytes]) -> bytes:
    result: bytes = b
    for old, new in tr.items():
        result = result.replace(old, new)
    return result
