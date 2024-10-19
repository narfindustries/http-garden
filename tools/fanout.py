""" This is where the code for actually talking to the servers lives. """

import base64
import binascii
import functools
import json
import re
import socket
import ssl
import sys

from typing import Sequence, Final

from http1 import parse_request_stream, parse_response, HTTPRequest, HTTPResponse, parse_response_json, strip_http_0_9_headers, parse_http_0_9_response
from targets import Service
from util import stream_t, eager_pmap, ssl_wrap, really_recv


def raw_transducer_roundtrip(data: stream_t, transducer: Service) -> stream_t:
    """Roundtrips a payload through a transducer pointing at an HTTP echo server."""
    result: stream_t = []
    try:
        with socket.create_connection((transducer.address, transducer.port)) as sock:
            if transducer.requires_tls:
                sock = ssl_wrap(sock, transducer.address)
            sock.settimeout(transducer.timeout)
            for datum in data:
                try:
                    sock.sendall(datum)
                except ssl.SSLEOFError as e:
                    raise ValueError(
                        f"{transducer.name} closed the TLS connection in response to {data!r}!"
                    ) from e
                except BrokenPipeError as e:
                    raise ValueError(f"{transducer.name} broke the pipe in response to {data!r}!") from e
                result.append(really_recv(sock))
            sock.shutdown(socket.SHUT_WR)
            result.append(really_recv(sock))
            sock.close()
    except OSError:  # Either no route to host, or failed to shut down the socket
        pass
    return result


def transducer_roundtrip(data: stream_t, transducer: Service) -> stream_t:
    """Roundtrips a payload through a transducer pointing at an HTTP echo server. Collects response bodies into a list."""
    remaining: bytes = b"".join(raw_transducer_roundtrip(data, transducer))
    pieces: stream_t = []
    while len(remaining) > 0:
        try:  # Parse it as H1
            response, remaining = parse_response(remaining)
        except ValueError as e:
            raise ValueError(
                f"Couldn't parse {transducer.name}'s response to {data!r}:\n    {remaining!r}"
            ) from e
        if response.code != b"200":  # It parsed, but the status is bad
            raise ValueError(f"{transducer.name} rejected the payload with status {response.code!r}")
        pieces.append(response.body)
    return pieces


def parsed_transducer_roundtrip(data: stream_t, transducer: Service) -> list[HTTPRequest | HTTPResponse]:
    remaining: bytes = b"".join(raw_transducer_roundtrip(data, transducer))
    responses: list[HTTPResponse] = []
    while len(remaining) > 0:
        try:  # Parse it as H1
            response, remaining = parse_response(remaining)
        except ValueError as e:
            raise ValueError(
                f"Couldn't parse {transducer.name}'s response to {data!r}:\n    {remaining!r}"
            ) from e
        responses.append(response)

    result: list[HTTPRequest | HTTPResponse] = []
    leftovers: bytes = b""
    for response in responses:
        if response.code == b"200":
            requests, rest = parse_request_stream(leftovers + response.body)
            result += requests
            leftovers += rest
        else:
            result.append(response)
    if len(leftovers) > 0:
        raise ValueError(f"Couldn't parse {transducer.name}'s transformation of {leftovers!r}")
    return result


def server_roundtrip(data: stream_t, server: Service) -> stream_t:
    """Sends data, then receives data over TCP (potentially with SSL) to host:port"""
    result: stream_t = []
    try:
        with socket.create_connection((server.address, server.port)) as sock:
            if server.requires_tls:
                sock = ssl_wrap(sock, server.address)
            sock.settimeout(server.timeout)
            for datum in data:
                sock.sendall(datum)
                result.append(really_recv(sock))
            sock.shutdown(socket.SHUT_WR)
            if b := really_recv(sock):
                result.append(b)
    except (ConnectionRefusedError, BrokenPipeError, OSError):
        pass
    return result


def extract_trace(server: Service) -> frozenset[int] | None:
    result: set[int] = set()
    with open(f"/tmp/{server.name}/dump_count", "rb") as f:
        dump_count = f.read(1)[0]
        if dump_count != server.dump_count % 256:
            dump_count = server.dump_count
            # The server has fallen behind on processing requests
            return None
    server.dump_count += 1
    with open(f"/tmp/{server.name}/trace", "rb") as f:
        for line in f.readlines():
            if len(line.strip()) == 0:
                continue
            try:
                result.add(int(line.split(b":")[0]))
            except ValueError:
                # This can happen when there's a race condition on writing the trace
                return None

    return frozenset(result)


_DUMP_SIGNAL: Final[str] = "SIGUSR1"
_CLEAR_SIGNAL: Final[str] = "SIGUSR2"


def traced_server_roundtrip(
    data: stream_t, server: Service, retries_left: int = 2
) -> tuple[stream_t, frozenset[int]]:
    """Calls server_roundtrip, and extracts the trace if the target is instrumented."""
    if server.is_traced:
        # Reset the tracing
        assert server.container is not None
        server.container.kill(signal=_CLEAR_SIGNAL)

    response: stream_t = server_roundtrip(data, server)

    if server.is_traced:
        # Dump the trace
        assert server.container is not None
        server.container.kill(signal=_DUMP_SIGNAL)
        # May want to sleep here?
        trace: frozenset[int] | None = extract_trace(server)
        if trace is None:  # The trace failed, so we should try again
            if retries_left > 0:
                return traced_server_roundtrip(data, server, retries_left - 1)
            assert False
    else:
        trace = frozenset()

    return (response, trace)


def parsed_server_roundtrip(
    data: stream_t, server: Service, traced: bool = True
) -> tuple[list[HTTPRequest | HTTPResponse], frozenset[int]]:
    if traced:
        pieces, trace = traced_server_roundtrip(data, server)
    else:
        pieces = server_roundtrip(data, server)
        trace = frozenset()
    remaining = b"".join(pieces)
    result: list[HTTPRequest | HTTPResponse] = []
    while len(remaining) > 0:
        extracted: HTTPRequest | HTTPResponse | None = None
        try:  # The bytes we got back might not be a valid HTTP/1 response
            parsed_response, new_remaining = parse_response(remaining)
            if parsed_response.code != b"200":
                extracted = parsed_response
            else:
                extracted = parse_response_json(parsed_response.body)
        except ValueError:
            pass

        if extracted is None and server.allows_http_0_9:
            try:
                extracted = parse_response_json(strip_http_0_9_headers(remaining))
                new_remaining = b""
                break
            except ValueError:
                pass
            try:
                extracted = parse_http_0_9_response(strip_http_0_9_headers(remaining))
                new_remaining = b""
            except ValueError:
                pass

        if extracted is None:
            print(
                f"Couldn't parse {server.name}'s response to {data!r}:\n    {remaining!r}",
                file=sys.stderr,
            )
            new_remaining = b""
        else:
            result.append(extracted)
        remaining = new_remaining
    return (result, trace)


def adjust_host_header(data: stream_t, service: Service) -> stream_t:
    return [
        re.sub(
            rb"[Hh][Oo][Ss][Tt]:[^\r\n]*\r?\n",
            b"Host: " + (service.address.encode("latin1")) + b"\r\n",
            datum,
        )
        for datum in data
    ]


def fanout(
    data: stream_t, servers: Sequence[Service], traced: bool = True
) -> list[tuple[list[HTTPRequest | HTTPResponse], frozenset[int]]]:
    return eager_pmap(functools.partial(parsed_server_roundtrip, data, traced=traced), servers)
