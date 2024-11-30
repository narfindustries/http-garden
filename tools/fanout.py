""" This is where the code for actually talking to the servers lives. """

from typing import Callable, ParamSpec, TypeVar

from http1 import (
    HTTPRequest,
    HTTPResponse,
)
from targets import Server
from util import eager_pmap

A = ParamSpec("A")
R = TypeVar("R")


def trace(server: Server, f: Callable[A, R]) -> Callable[A, tuple[R, frozenset[int]]]:
    def result(*args, **kwargs):
        server.clear_trace()
        return (f(*args, **kwargs), server.collect_trace())

    return result


def fanout(data: list[bytes], servers: list[Server]) -> list[list[HTTPRequest | HTTPResponse]]:
    return eager_pmap(
        lambda t: t[0].parsed_roundtrip(t[1]),
        list(zip(servers, [data for _ in range(len(servers))])),
    )


def unparsed_fanout(data: list[bytes], servers: list[Server]) -> list[list[bytes]]:
    return eager_pmap(
        lambda t: t[0].unparsed_roundtrip(t[1]),
        list(zip(servers, [data for _ in range(len(servers))])),
    )
