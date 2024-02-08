""" This is where we keep the functions for mutating stream_ts """

import copy
import itertools
import random
from typing import Callable, Final

from http1 import HTTPRequest, parse_request_stream, METHODS
from util import stream_t


_SEED_HEADERS: Final[list[tuple[bytes, bytes]]] = [
    (b"Content-Length", b"0"),
    (b"Transfer-Encoding", b"chunked"),
    (b"Transfer-Encoding", b"identity"),
    (b"", b""),
    (b"Test", b""),
    (b"Connection", b"close"),
    (b"Connection", b"keep-alive"),
]


_SEED_REQUESTS: Final[list[bytes]] = [
    b"GET / HTTP/1.1\r\n\r\n",
    b"POST / HTTP/1.1\r\nContent-Length: 10\r\nHost: b\r\n\r\n0123456789",
    b"POST / HTTP/1.1\r\nHost: c\r\nTransfer-Encoding: chunked\r\n\r\n5\r\n01234\r\n5\r\n56789\r\n0\r\n\r\n",
]


def mutate(s: stream_t) -> stream_t:
    mutations: list[Callable[[stream_t], stream_t]] = [
        _insert_random_request,
        _delete_random_byte,
        _replace_random_byte,
        _insert_random_byte,
        _insert_random_meaningful_byte,
        _delete_random_request,
        _replace_random_request,
        _concat_random_requests,
        _shift_random_request_boundaries,
        _delete_random_header,
        _insert_random_header,
        _replace_random_header,
        _replace_method,
    ]

    while True:
        idx, mutation = random.choice(list(enumerate(mutations)))
        try:
            return mutation(s)
        except AssertionError:
            mutations.pop(idx)
    assert False


def _delete_random_byte(s: stream_t) -> stream_t:
    assert len(s) >= 1
    total_len: int = sum(len(r) for r in s)
    assert total_len >= 1
    idx: int = random.randint(0, total_len - 1)
    result: stream_t = s.copy()
    for req_idx, req in enumerate(s):
        if len(req) > idx:
            result[req_idx] = req[:idx] + req[idx + 1 :]
            return result
        idx -= len(req)
    assert False


def _replace_random_byte(s: stream_t) -> stream_t:
    assert len(s) >= 1
    total_len: int = sum(len(r) for r in s)
    assert total_len >= 1
    idx: int = random.randint(0, total_len - 1)
    result: stream_t = s.copy()
    for req_idx, req in enumerate(s):
        if len(req) > idx:
            result[req_idx] = req[:idx] + bytes([random.randint(0, 255)]) + req[idx + 1 :]
            return result
        idx -= len(req)
    assert False


_MEANINGFUL_BYTES: Final[list[bytes]] = [b"\r\n", b"\r", b"\n", b"\x00", b":", b"\t", b" "]


def _insert_random_meaningful_byte(s: stream_t) -> stream_t:
    assert len(s) >= 1
    total_len: int = sum(len(r) for r in s)
    idx: int = random.randint(0, total_len)
    result: stream_t = s.copy()
    for req_idx, req in enumerate(s):
        if len(req) > idx:
            result[req_idx] = req[:idx] + random.choice(_MEANINGFUL_BYTES) + req[idx:]
            return result
        idx -= len(req)
    assert False


def _insert_random_byte(s: stream_t) -> stream_t:
    assert len(s) >= 1
    total_len: int = sum(len(r) for r in s)
    idx: int = random.randint(0, total_len)
    result: stream_t = s.copy()
    for req_idx, req in enumerate(s):
        if len(req) > idx:
            result[req_idx] = req[:idx] + bytes([random.randint(0, 255)]) + req[idx:]
            return result
        idx -= len(req)
    assert False


def _randomly_chunk(data: bytes) -> bytes:
    if len(data) == 0:
        return b"0\r\n\r\n"
    num_cuts: int = random.randint(0, len(data) - 1)  # This will need to be tweaked
    cuts: list[int] = [
        0,
        *sorted(random.sample(range(1, len(data)), num_cuts)),
        len(data),
    ]
    chunks: stream_t = [data[start:end] for start, end in itertools.pairwise(cuts)]
    return (
        b"".join(hex(len(chunk))[2:].encode("latin1") + b"\r\n" + chunk + b"\r\n" for chunk in chunks)
        + b"0\r\n\r\n"
    )


def _unparse_request(request: HTTPRequest) -> bytes:
    is_chunked: bool = b"transfer-encoding" in map(lambda p: p[0].lower(), request.headers)
    return (
        request.method
        + b" "
        + request.uri
        + b" "
        + b"HTTP/"
        + request.version
        + b"\r\n"
        + b"".join(k + b": " + v + b"\r\n" for k, v in request.headers)
        + b"\r\n"
        + (_randomly_chunk(request.body) if is_chunked else request.body)
    )


def _delete_random_header(s: stream_t) -> stream_t:
    assert len(s) >= 1
    substream_idx, substream = random.choice(list(enumerate(s)))
    parsed_substream, rest = parse_request_stream(substream)
    assert len(parsed_substream) >= 1
    request_idx, request = random.choice(list(enumerate(parsed_substream)))
    assert len(request.headers) >= 1
    idx: int = random.randint(0, len(request.headers) - 1)  # You can delete in n places
    new_request: HTTPRequest = copy.deepcopy(request)
    new_request.headers = new_request.headers[:idx] + new_request.headers[idx + 1 :]
    parsed_substream.pop(request_idx)
    parsed_substream.insert(request_idx, new_request)
    new_substream: bytes = b"".join(map(_unparse_request, parsed_substream)) + rest

    return s[:substream_idx] + [new_substream] + s[substream_idx + 1 :]


def _insert_random_header(s: stream_t) -> stream_t:
    assert len(s) >= 1
    substream_idx, substream = random.choice(list(enumerate(s)))
    parsed_substream, rest = parse_request_stream(substream)
    assert len(parsed_substream) >= 1
    request_idx, request = random.choice(list(enumerate(parsed_substream)))
    idx: int = random.randint(0, len(request.headers))  # You can insert in n + 1 places
    header: tuple[bytes, bytes] = random.choice(_SEED_HEADERS)
    new_request: HTTPRequest = copy.deepcopy(request)
    new_request.headers = new_request.headers[:idx] + [header] + new_request.headers[idx + 1 :]
    parsed_substream.pop(request_idx)
    parsed_substream.insert(request_idx, new_request)
    new_substream: bytes = b"".join(map(_unparse_request, parsed_substream)) + rest
    return s[:substream_idx] + [new_substream] + s[substream_idx + 1 :]


def _replace_random_header(s: stream_t) -> stream_t:
    assert len(s) >= 1
    substream_idx, substream = random.choice(list(enumerate(s)))
    parsed_substream, rest = parse_request_stream(substream)
    assert len(parsed_substream) >= 1
    request_idx, request = random.choice(list(enumerate(parsed_substream)))
    assert len(request.headers) >= 1
    idx: int = random.randint(0, len(request.headers) - 1)  # You can replace in n places
    new_request: HTTPRequest = copy.deepcopy(request)
    new_request.headers = (
        new_request.headers[:idx] + [random.choice(_SEED_HEADERS)] + new_request.headers[idx + 1 :]
    )
    parsed_substream.pop(request_idx)
    parsed_substream.insert(request_idx, new_request)
    new_substream: bytes = b"".join(map(_unparse_request, parsed_substream)) + rest
    return s[:substream_idx] + [new_substream] + s[substream_idx + 1 :]


def _replace_method(s: stream_t) -> stream_t:
    assert len(s) >= 1
    substream_idx, substream = random.choice(list(enumerate(s)))
    parsed_substream, rest = parse_request_stream(substream)
    assert len(parsed_substream) >= 1
    request_idx, request = random.choice(list(enumerate(parsed_substream)))
    new_request: HTTPRequest = copy.deepcopy(request)
    new_request.method = random.choice(METHODS)
    parsed_substream.pop(request_idx)
    parsed_substream.insert(request_idx, new_request)
    new_substream: bytes = b"".join(map(_unparse_request, parsed_substream)) + rest
    return s[:substream_idx] + [new_substream] + s[substream_idx + 1 :]


def _insert_random_request(s: stream_t) -> stream_t:
    result: stream_t = s.copy()
    result.insert(random.randint(0, len(s)), random.choice(_SEED_REQUESTS))
    return result


def _replace_random_request(s: stream_t) -> stream_t:
    assert len(s) >= 2
    result: stream_t = s.copy()
    idx: int = random.randint(0, len(s) - 1)
    result.pop(idx)
    result.insert(idx, random.choice(_SEED_REQUESTS))
    return result


def _delete_random_request(s: stream_t) -> stream_t:
    assert len(s) >= 2
    result: stream_t = s.copy()
    idx: int = random.randint(0, len(s) - 1)
    result.pop(idx)
    result.insert(idx, random.choice(_SEED_REQUESTS))
    return result


def _concat_random_requests(s: stream_t) -> stream_t:
    assert len(s) >= 2
    result: stream_t = s.copy()
    idx: int = random.randint(0, len(s) - 2)
    first_req: bytes = result.pop(idx)
    result[idx] = first_req + result[idx]
    return result


def _shift_random_request_boundaries(s: stream_t) -> stream_t:
    assert len(s) >= 2
    result: stream_t = s.copy()
    idx: int = random.randint(0, len(s) - 2)
    combined: bytes = result.pop(idx) + result.pop(idx)
    boundary: int = random.randint(0, len(combined))
    first = combined[:boundary]
    second = combined[boundary:]
    result.insert(idx, first)
    result.insert(idx, second)
    return result
