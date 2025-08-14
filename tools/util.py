"""This is where the extra random junk lives."""

import multiprocessing
import multiprocessing.pool
import socket
import ssl
from collections.abc import Sequence
from typing import Callable


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


def sendall(sock: socket.socket, data: bytes) -> None:
    sock.sendall(data)


def is_closed_for_writing(sock: socket.socket) -> bool:
    try:
        sock.sendall(b"")
    except OSError:
        return True
    return False


def is_closed_for_reading(sock: socket.socket) -> bool:
    try:
        return sock.recv(1, socket.MSG_PEEK | socket.MSG_DONTWAIT) == b""
    except TimeoutError:
        return False
    except ConnectionResetError:
        return True


def recvall(sock: socket.socket) -> bytes:
    """Receives bytes from a socket until a timeout expires."""
    result: bytes = b""
    while True:
        try:
            b: bytes = sock.recv(_RECV_SIZE)
            result += b
        except TimeoutError:
            break
        if len(b) == 0:
            break
    return result


def roundtrip_to_server(sock: socket.socket, data: list[bytes]) -> list[bytes]:
    """Run by a client to connect to a server. Sends each piece of data, receiving between each send, and returns the received bytes."""
    result: list[bytes] = []
    try:
        for datum in data:
            sendall(sock, datum)
            result.append(recvall(sock))
        sock.shutdown(socket.SHUT_WR)
        if not is_closed_for_reading(sock):
            result.append(recvall(sock))
    except (ssl.SSLEOFError, ConnectionRefusedError, BrokenPipeError, OSError, BlockingIOError, ConnectionResetError):
        pass
    return result


def roundtrip_to_client(sock: socket.socket, data: bytes, recv_callback=recvall) -> list[bytes]:
    """Run by a server in response to a connection established by a client. Sends each piece of data, receiving between each send, and returns the received bytes."""
    result: list[bytes] = []
    try:
        while True:
            result.append(recv_callback(sock))
            if result[-1]:
                sendall(sock, data)
            else:
                break
            if is_closed_for_reading(sock) or is_closed_for_writing(sock):
                break
    except (ssl.SSLEOFError, ConnectionRefusedError, BrokenPipeError, OSError, BlockingIOError, ConnectionResetError):
        pass
    return result


def eager_pmap[U, T](f: Callable[[U], T], s: Sequence[U]) -> list[T]:
    with multiprocessing.pool.ThreadPool(multiprocessing.cpu_count()) as pool:
        return list(pool.map(f, s))


def translate(b: bytes, tr: dict[bytes, bytes]) -> bytes:
    result: bytes = b
    for old, new in tr.items():
        result = result.replace(old, new)
    return result
