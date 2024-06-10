"""
This script automatically detects certain simple parsing quirks in servers, so that they can later be ignored.
You can redirect its output to `anomalies.yml` to have these quirks taken into account in the REPL and while fuzzing.
"""

import argparse
from typing import Any

from targets import SERVER_DICT, Service
from fanout import server_roundtrip, parsed_server_roundtrip
from http1 import remove_request_header, HTTPRequest, HTTPResponse, METHODS
from util import stream_t, translate


def get_method_whitelist(server: Service) -> list[bytes] | None:
    pts, _ = parsed_server_roundtrip([b"SLUDGE / HTTP/1.1\r\nHost: a\r\n\r\n"], server, traced=False)
    assert len(pts) == 1
    if isinstance(pts[0], HTTPRequest):
        return None
    result: list[bytes] = []
    for method in METHODS:
        pts, _ = parsed_server_roundtrip([method + b" / HTTP/1.1\r\nHost: a\r\n\r\n"], server, traced=False)
        assert len(pts) == 1
        if isinstance(pts[0], HTTPRequest):
            result.append(method)
    return result


def requires_alphabetical_method(server: Service) -> bool:
    pts, _ = parsed_server_roundtrip([b"0 / HTTP/1.1\r\nHost: a\r\n\r\n"], server, traced=False)
    assert len(pts) == 1
    return isinstance(pts[0], HTTPResponse)


def allows_http_0_9(server: Service) -> bool:
    response_stream: stream_t = server_roundtrip([b"GET /\r\n\r\n"], server)
    assert len(response_stream) == 1
    response: bytes = b"".join(response_stream)
    eol: int = response.find(b"\n")
    if eol == -1:
        eol = len(response)
    return len(response) > 0 and b"400" not in response[:eol]


def get_removed_headers(
    server: Service, header_name_translation: dict[bytes, bytes]
) -> list[tuple[bytes, bytes]]:
    HEADERS: list[tuple[bytes, bytes]] = [
        (b"connection", b"keep-alive"),
        (b"connection", b"close"),
        (b"content-length", b"0"),
    ]
    result: list[tuple[bytes, bytes]] = []
    for key, val in HEADERS:
        pts, _ = parsed_server_roundtrip(
            [b"GET / HTTP/1.1\r\nHost: a\r\n" + key + b": " + val + b"\r\n\r\n"], server, traced=False
        )
        assert len(pts) == 1 and isinstance(pts[0], HTTPRequest)
        if not pts[0].has_header(translate(key, header_name_translation), val):
            result.append((key, val))
    return result


def get_added_headers(
    server: Service, method_whitelist: list[bytes] | None, allows_missing_host_header: bool
) -> list[tuple[bytes, bytes]]:
    streams_with_host: list[stream_t] = [[b"GET / HTTP/1.1\r\nHost: a\r\n\r\n"]]
    if method_whitelist is None or b"DELETE" in method_whitelist:
        streams_with_host.append([b"DELETE / HTTP/1.1\r\nHost: a\r\n\r\n"])

    result: list[tuple[bytes, bytes]] = []
    for stream in streams_with_host:
        pts, _ = parsed_server_roundtrip(stream, server, traced=False)

        assert len(pts) == 1 and isinstance(pts[0], HTTPRequest)
        pt: HTTPRequest = remove_request_header(pts[0], b"host")

        result += pt.headers

    if allows_missing_host_header:
        pts, _ = parsed_server_roundtrip([b"GET / HTTP/1.1\r\n\r\n"], server, traced=False)

        if len(pts) > 0 and isinstance(pts[0], HTTPRequest):
            result += pts[0].headers

    return list(set(result))


def translates_chunked_to_cl(server: Service, header_name_translation: dict[bytes, bytes]) -> bool:
    pts, _ = parsed_server_roundtrip(
        [b"POST / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n1\r\nZ\r\n0\r\n\r\n"],
        server,
        traced=False,
    )
    assert len(pts) == 1 and isinstance(pts[0], HTTPRequest)
    return pts[0].has_header(translate(b"content-length", header_name_translation)) and not pts[0].has_header(
        translate(b"transfer-encoding", header_name_translation)
    )


def adds_cl_to_chunked(server: Service, header_name_translation: dict[bytes, bytes]) -> bool:
    pts, _ = parsed_server_roundtrip(
        [b"POST / HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n1\r\nZ\r\n0\r\n\r\n"],
        server,
        traced=False,
    )
    assert len(pts) == 1 and isinstance(pts[0], HTTPRequest)
    return pts[0].has_header(translate(b"content-length", header_name_translation)) and pts[0].has_header(
        translate(b"transfer-encoding", header_name_translation)
    )


def requires_length_in_post(server: Service) -> bool:
    pts, _ = parsed_server_roundtrip([b"POST / HTTP/1.1\r\nHost: a\r\n\r\n"], server, traced=False)
    assert len(pts) == 1
    return isinstance(pts[0], HTTPResponse)


def allows_missing_host_header(server: Service) -> bool:
    pts, _ = parsed_server_roundtrip([b"GET / HTTP/1.1\r\n\r\n"], server, traced=False)
    assert len(pts) == 1
    return isinstance(pts[0], HTTPRequest)


def get_header_name_translation(server: Service) -> dict[bytes, bytes]:
    pts, _ = parsed_server_roundtrip([b"GET / HTTP/1.1\r\nHost: a\r\na-b: a-b\r\n\r\n"], server, traced=False)
    assert len(pts) == 1
    assert isinstance(pts[0], HTTPRequest)
    return {b"-": b"_"} if pts[0].has_header(b"a_b") else {}


def doesnt_support_version(server: Service) -> bool:
    pts1, _ = parsed_server_roundtrip([b"GET / HTTP/1.1\r\nHost: a\r\n\r\n"], server, traced=False)
    assert len(pts1) == 1
    pt1 = pts1[0]
    assert isinstance(pt1, HTTPRequest)

    pts2, _ = parsed_server_roundtrip([b"GET / HTTP/1.0\r\nHost: a\r\n\r\n"], server, traced=False)
    assert len(pts2) == 1
    pt2 = pts2[0]
    assert isinstance(pt2, HTTPRequest)

    return pt1.version == pt2.version


def joins_duplicate_headers(server: Service) -> bool:
    pts, _ = parsed_server_roundtrip(
        [b"GET / HTTP/1.1\r\nHost: a\r\na: A\r\na: B\r\n\r\n"], server, traced=False
    )
    assert len(pts) == 1
    assert isinstance(pts[0], HTTPRequest)

    return pts[0].has_header(b"a", b"A, B") or pts[0].has_header(b"a", b"A,B")


def main() -> None:
    arg_parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="This script tests the specified servers for a number of common HTTP parsing quirks that are usually considered benign. Its output can be used in `anomalies.yml` so that these benign discrepancies can be ignored."
    )
    arg_parser.add_argument(
        "--servers",
        default=None,
        help="Comma-separated list of server names from docker-compose.yml. If omitted, uses all.",
    )

    args: argparse.Namespace = arg_parser.parse_args()

    servers: list[Service] = (
        list(SERVER_DICT.values())
        if args.servers is None
        else (
            [SERVER_DICT[s] for s in args.servers.split(",") if len(s) > 0]
            if args.servers is not None
            else []
        )
    )
    print("# This file generated by diagnose_anomalies.py")
    print("# This yaml file tracks the acceptable parsing anomalies in the servers.")

    for server in servers:
        anomalies: dict[str, Any] = {}

        if allows_http_0_9(server):
            anomalies["allows-http-0-9"] = "true"

        allows_missing_host_header_rc: bool = allows_missing_host_header(server)
        if allows_missing_host_header_rc:
            anomalies["allows-missing-host-header"] = "true"

        method_whitelist = get_method_whitelist(server)
        if method_whitelist is not None:
            anomalies["method-whitelist"] = [m.decode("latin1") for m in method_whitelist]

        added_headers = get_added_headers(server, method_whitelist, allows_missing_host_header_rc)
        if len(added_headers) > 0:
            anomalies["added-headers"] = [[k.decode("latin1"), v.decode("latin1")] for k, v in added_headers]

        header_name_translation = get_header_name_translation(server)
        if len(header_name_translation) > 0:
            anomalies["header-name-translation"] = {
                k.decode("latin1"): v.decode("latin1") for k, v in header_name_translation.items()
            }

        if translates_chunked_to_cl(server, header_name_translation):
            anomalies["translates-chunked-to-cl"] = "true"

        if adds_cl_to_chunked(server, header_name_translation):
            anomalies["adds-cl-to-chunked"] = "true"

        if requires_length_in_post(server):
            anomalies["requires-length-in-post"] = "true"

        if doesnt_support_version(server):
            anomalies["doesnt-support-version"] = "true"

        if method_whitelist is None and requires_alphabetical_method(server):
            anomalies["requires-alphabetical-method"] = "true"

        removed_headers = get_removed_headers(server, header_name_translation)
        if len(removed_headers) > 0:
            anomalies["removed-headers"] = [
                [k.decode("latin1"), v.decode("latin1")] for k, v in removed_headers
            ]

        if len(anomalies) > 0:
            print(f"{server.name}:")
        for k, v in anomalies.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
