"""This is where the code for actually talking to the servers lives."""

from http1 import (
    HTTPRequest,
    HTTPResponse,
)
from targets import Server
from util import eager_pmap


def fanout(
    data: list[bytes], servers: list[Server]
) -> list[list[HTTPRequest | HTTPResponse]]:
    return eager_pmap(
        lambda server: server.parsed_roundtrip(data),
        servers,
    )


def unparsed_fanout(data: list[bytes], servers: list[Server]) -> list[list[bytes]]:
    return eager_pmap(
        lambda t: t[0].unparsed_roundtrip(t[1]),
        list(zip(servers, [data for _ in range(len(servers))])),
    )
