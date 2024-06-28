""" This is where HTTP parsing happens, as well as certain operations on parsed HTTP messages. """

import copy
import dataclasses
import gzip
import re
from typing import Self, Sequence, Final

from util import translate

# We are deliberately ignoring HEAD, OPTIONS, CONNECT, and TRACE
METHODS: Final[list[bytes]] = [
    b"ACL",
    b"ANNOUNCE",
    b"BASELINE-CONTROL",
    b"BIND",
    b"CHECKIN",
    b"CHECKOUT",
    b"COPY",
    b"DELETE",
    b"DESCRIBE",
    b"FLUSH",
    b"GET",
    b"GET_PARAMETER",
    b"LABEL",
    b"LINK",
    b"LOCK",
    b"M-SEARCH",
    b"MERGE",
    b"MKACTIVITY",
    b"MKCALENDAR",
    b"MKCOL",
    b"MKREDIRECTREF",
    b"MKWORKSPACE",
    b"MOVE",
    b"NOTIFY",
    b"ORDERPATCH",
    b"PATCH",
    b"PAUSE",
    b"PLAY",
    b"POST",
    b"PRI",
    b"PROPFIND",
    b"PROPPATCH",
    b"PURGE",
    b"PUT",
    b"QUERY",
    b"REBIND",
    b"RECORD",
    b"REDIRECT",
    b"REFRESH",
    b"REPORT",
    b"SEARCH",
    b"SETUP",
    b"SET_PARAMETER",
    b"SOURCE",
    b"SUBSCRIBE",
    b"TEARDOWN",
    b"UNBIND",
    b"UNCHECKOUT",
    b"UNKNOWN",
    b"UNLINK",
    b"UNLOCK",
    b"UNSET",
    b"UNSUBSCRIBE",
    b"UPDATE",
    b"UPDATEREDIRECTREF",
    b"VERSION-CONTROL",
    b"*",
]


@dataclasses.dataclass
class HTTPRequest:
    """Stores a parsed HTTP request"""

    # Method
    method: bytes
    # Path
    uri: bytes
    # The headers
    headers: list[tuple[bytes, bytes]]
    # The body
    body: bytes
    # The HTTP version
    version: bytes

    def has_header(self: Self, name: bytes, value: bytes | None = None) -> bool:
        return any(k.lower() == name.lower() and (value is None or value == v) for k, v in self.headers)

    def __eq__(self: Self, other: object) -> bool:
        if not isinstance(other, HTTPRequest):
            return False
        return (
            self.method == other.method
            and self.uri == other.uri
            and self.headers == other.headers
            and self.body == other.body
            and (self.version == other.version or other.version == b"" or self.version == b"")
        )


@dataclasses.dataclass
class HTTPResponse:
    """Stores a parsed HTTP response"""

    # The HTTP version (e.g. b"1.1")
    version: bytes
    # The status code (e.g. b"200")
    code: bytes
    # The status reason (e.g. b"OK")
    reason: bytes
    # The headers (e.g. [(b"Content-Length", b"2"), (b"Content-Type", b"application/json")])
    headers: list[tuple[bytes, bytes]]
    # The body (e.g. b"{}")
    body: bytes

    def __eq__(self: Self, other: object) -> bool:
        if not isinstance(other, HTTPResponse):
            return False
        return self.code == other.code


def parse_response(raw: bytes) -> tuple[HTTPResponse, bytes]:
    """
    Permissively parses an HTTP/1 response.
    If `raw` contains multiple HTTP responses, this will parse only what it believes to be the first one.
    Returns the parsed response, along with the unconsumed input
    """
    # Parse response line
    m: re.Match[bytes] | None = re.match(
        rb"\A(?P<version>[^\s]+)[\v\f\r \t]+(?P<code>\d+)[\v\f\r \t]+(?P<reason>.*?)\r?\n", raw
    )
    if m is None:
        raise ValueError("Invalid HTTP response line.")
    version: bytes = m["version"]
    if version.startswith(b"HTTP/"):
        version = version[len(b"HTTP/") :]
    code: bytes = m["code"]
    reason: bytes = m["reason"]
    rest: bytes = raw[m.end() :]

    headers, rest = parse_headers(rest)
    body, rest = parse_body(headers, rest, is_response=True)

    return (
        HTTPResponse(
            version=version,
            code=code,
            reason=reason,
            headers=headers,
            body=body,
        ),
        rest,
    )


def parse_request_stream(payload: bytes) -> tuple[list[HTTPRequest], bytes]:
    parse_trees: list[HTTPRequest] = []
    remaining = payload
    while remaining != b"":
        try:
            parsed_request, remaining = parse_request(remaining)
        except ValueError:
            break
        parse_trees.append(parsed_request)
    return parse_trees, remaining


def parse_request(raw: bytes) -> tuple[HTTPRequest, bytes]:
    """
    Permissively parses an HTTP/1 request.
    If `raw` contains multiple HTTP requests, this will parse only what it believes to be the first one.
    Returns the parsed request, along with the unconsumed input
    """
    # Parse request line
    m: re.Match[bytes] | None = re.match(
        rb"\A(?P<method>[^\s]+)\s+(?P<uri>[^\s]+)\s+(?:HTTP/(?P<version>[^\s]+))?\r?\n",
        raw,
    )
    if m is None:
        raise ValueError("Invalid HTTP response line.")
    rest: bytes = raw[m.end() :]

    headers, rest = parse_headers(rest)
    body, rest = parse_body(headers, rest, is_response=False)
    version: bytes = m["version"]
    if version is None:
        version = b"0.9"

    return (
        HTTPRequest(headers=headers, body=body, method=m["method"], uri=m["uri"], version=version),
        rest,
    )


def parse_headers(
    raw: bytes,
) -> tuple[list[tuple[bytes, bytes]], bytes]:
    """
    Permissively parses HTTP/1 headers.
    Returns the headers as a list of (name, value) pairs, along with the unconsumed input
    """

    # Parse null headers and body (as in "GET / HTTP/1.1\r\n\r\n")
    if raw.startswith(b"\r\n"):
        return [], raw[2:]

    # Parse headers
    header_terminator: re.Match[bytes] | None = re.search(rb"\r?\n\r?\n", raw)
    if header_terminator is None:
        raise ValueError("No header termination sequence found.")
    raw_headers: bytes = raw[: header_terminator.start()]
    header_lines: list[bytes] = re.split(rb"\r?\n", raw_headers)
    headers: list[tuple[bytes, bytes]] = []
    for line in header_lines:
        header_match: re.Match[bytes] | None = re.match(rb"\A(?P<name>.+):\s+(?P<value>.*?)\s*\Z", line)
        if header_match is None:
            raise ValueError("Invalid header line.")
        headers.append((header_match["name"], header_match["value"]))
    return headers, raw[header_terminator.end() :]


def parse_body(headers: Sequence[tuple[bytes, bytes]], rest: bytes, is_response: bool) -> tuple[bytes, bytes]:
    """
    Parses an HTTP message body.
    Raises ValueError on failure.
    """
    cl: int | None = None
    te_values: list[bytes] = []
    ce_values: list[bytes] = []
    for k, v in headers:
        if k.lower() == b"content-length":
            if not v.isascii() or not v.isdigit():
                raise ValueError("Invalid Content-Length")
            cl = int(v)
        if k.lower() == b"transfer-encoding":
            te_values.append(v.lower())
        if k.lower() == b"content-encoding":
            ce_values.append(v.lower())

    if is_response and cl is None and b"chunked" not in te_values:
        return rest, b""

    body: bytes = b""
    if b"chunked" in te_values:
        if b"gzip" in ce_values:
            raise ValueError("CE: gzip combined with TE: chunked not supported.")
        body = b""
        while True:
            chunk_header: re.Match[bytes] | None = re.match(rb"\A(?P<length>[0-9a-fA-F]+)\r\n", rest)
            if chunk_header is None:
                raise ValueError("Invalid chunk header.")
            rest = rest[chunk_header.end() :]
            chunk_length: int = int(chunk_header["length"], 16)
            chunk_data: re.Match[bytes] | None = re.match(
                rf"\A(?P<data>[\x00-\xff]{{{chunk_length}}})\r\n".encode("latin1"), rest
            )
            if chunk_data is None:
                raise ValueError("Invalid chunk data")
            body += chunk_data["data"]
            rest = rest[chunk_data.end() :]
            if chunk_length == 0:
                break
    elif cl is not None:
        body = rest[:cl]
        rest = rest[cl:]
        if b"gzip" in ce_values:
            body = gzip.decompress(body)
    return body, rest


def remove_request_header(req: HTTPRequest, key: bytes, value: bytes | None = None) -> HTTPRequest:
    result: HTTPRequest = copy.deepcopy(req)
    result.headers = [h for h in req.headers if h[0].lower() != key.lower() and h[1] != value]
    return result


def insert_request_header(req: HTTPRequest, key: bytes, value: bytes) -> HTTPRequest:
    result: HTTPRequest = copy.deepcopy(req)
    result.headers += [(key, value)]
    result.headers.sort()
    return result


def translate_request_header_names(req: HTTPRequest, tr: dict[bytes, bytes]) -> HTTPRequest:
    result: HTTPRequest = copy.deepcopy(req)
    result.headers = [(translate(h[0], tr), h[1]) for h in req.headers]
    result.headers.sort()
    return result
