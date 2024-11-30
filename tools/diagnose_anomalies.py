"""This script automatically detects certain simple parsing quirks in servers, so that they can later be ignored.
You can redirect its output to `anomalies.yml` to have these quirks taken into account in the REPL and while fuzzing.
"""

import argparse
from typing import Any

import tqdm

from http1 import METHODS, HTTPRequest, HTTPResponse, remove_request_header
from targets import SERVICE_DICT, Server
from util import translate

# TODO: Support servers that drop header names containing certain characters (e.g., '_')


def requires_specific_host_header(server: Server) -> bool:
    pts: list[HTTPRequest | HTTPResponse] = server.parsed_roundtrip([b"GET / HTTP/1.1\r\nHost: a\r\n\r\n"])
    return len(pts) != 1 or not isinstance(pts[0], HTTPRequest)


def doesnt_support_persistence(server: Server) -> bool:
    pts: list[HTTPRequest | HTTPResponse] = server.parsed_roundtrip(
        [b"GET / HTTP/1.1\r\nHost: a\r\n\r\n", b"GET / HTTP/1.1\r\nHost: a\r\n\r\n"],
    )
    return len(pts) != 2 or any(not isinstance(pt, HTTPRequest) for pt in pts)


def get_method_character_blacklist(server: Server) -> bytes:
    result: bytes = b""
    for b in (
        b"!",
        b"#",
        b"$",
        b"%",
        b"&",
        b"'",
        b"*",
        b"+",
        b"-",
        b".",
        b"^",
        b"_",
        b"`",
        b"|",
        b"~",
    ):
        pts = server.parsed_roundtrip(
            [b"".join((b"GET", b, b" / HTTP/1.1\r\nHost: a\r\n\r\n"))],
        )
        if len(pts) == 0:
            continue
        if len(pts) != 1:
            raise ValueError(f"Unexpected number of responses from {server.name}: {len(pts)}")
        if isinstance(pts[0], HTTPResponse):
            result += b
    return result


def get_method_whitelist(server: Server) -> list[bytes] | None:
    pts = server.parsed_roundtrip([b"SLUDGE / HTTP/1.1\r\nHost: a\r\n\r\n"])
    if len(pts) == 1 and isinstance(pts[0], HTTPRequest):
        return None

    result: list[bytes] = []
    for method in METHODS:
        pts = server.parsed_roundtrip([method + b" / HTTP/1.1\r\nHost: a\r\n\r\n"])
        if len(pts) == 1 and isinstance(pts[0], HTTPRequest):
            result.append(method)
    return result


def requires_alphabetical_method(server: Server) -> bool:
    pts = server.parsed_roundtrip([b"0 / HTTP/1.1\r\nHost: a\r\n\r\n"])
    if len(pts) != 1:
        raise ValueError(f"Unexpected number of responses from {server.name}: {len(pts)}")
    return isinstance(pts[0], HTTPResponse)


def allows_http_0_9(server: Server) -> bool:
    response: bytes = b"".join(server.unparsed_roundtrip([b"GET /\r\n\r\n"]))
    eol: int = response.find(b"\n")
    if eol == -1:
        eol = len(response)
    return len(response) > 0 and b"400" not in response[:eol]


# TODO: Add transfer-encoding: chunked to this
_REMOVED_HEADERS: list[tuple[bytes, bytes]] = [
    (b"connection", b"keep-alive"),
    (b"connection", b"close"),
    (b"content-length", b"0"),
]


def get_removed_headers(server: Server, header_name_translation: dict[bytes, bytes]) -> list[bytes]:
    result: list[bytes] = []
    for key, val in _REMOVED_HEADERS:
        pts = server.parsed_roundtrip(
            [b"GET / HTTP/1.1\r\nHost: a\r\n" + key + b": " + val + b"\r\n\r\n"],
        )
        if len(pts) != 1:
            raise ValueError(f"Unexpected number of responses from {server.name}: {len(pts)}")
        assert isinstance(pts[0], HTTPRequest)
        if not pts[0].has_header(translate(key, header_name_translation), val):
            result.append(key)
    return result


_TRASHED_HEADERS: list[tuple[bytes, bytes]] = [
    (b"Host", b"a"),
]


def get_trashed_headers(server: Server, header_name_translation: dict[bytes, bytes]) -> list[bytes]:
    result: list[bytes] = []
    for key, val in _TRASHED_HEADERS:
        pts = server.parsed_roundtrip(
            [b"GET / HTTP/1.1\r\n" + key + b": " + val + b"\r\n\r\n"],
        )
        if len(pts) != 1:
            raise ValueError(f"Unexpected number of responses from {server.name}: {len(pts)}")
        assert isinstance(pts[0], HTTPRequest)
        if not pts[0].has_header(translate(key, header_name_translation), val):
            result.append(key)
    return result


def get_added_headers(
    server: Server,
    method_whitelist: list[bytes] | None,
    does_allow_missing_host_header: bool,
) -> list[bytes]:
    streams_with_host: list[list[bytes]] = [[b"GET / HTTP/1.1\r\nHost: a\r\n\r\n"]]
    if method_whitelist is None or b"DELETE" in method_whitelist:
        streams_with_host.append([b"DELETE / HTTP/1.1\r\nHost: a\r\n\r\n"])

    result: list[bytes] = []
    for stream in streams_with_host:
        pts = server.parsed_roundtrip(stream)

        if len(pts) != 1:
            raise ValueError(f"Unexpected number of responses from {server.name}: {len(pts)}")
        assert isinstance(pts[0], HTTPRequest)
        pt: HTTPRequest = remove_request_header(pts[0], b"host")

        result += [h[0] for h in pt.headers]

    if does_allow_missing_host_header:
        pts = server.parsed_roundtrip([b"GET / HTTP/1.1\r\n\r\n"])

        if len(pts) > 0 and isinstance(pts[0], HTTPRequest):
            result += [h[0] for h in pts[0].headers]

    return list(set(result))


def requires_length_in_post(server: Server) -> bool:
    pts = server.parsed_roundtrip([b"POST / HTTP/1.1\r\nHost: a\r\n\r\n"])
    if len(pts) > 1:
        raise ValueError(f"Unexpected number of responses from {server.name}: {len(pts)}")
    return len(pts) == 0 or isinstance(pts[0], HTTPResponse)


def allows_missing_host_header(server: Server) -> bool:
    pts = server.parsed_roundtrip([b"GET / HTTP/1.1\r\n\r\n"])
    if len(pts) > 1:
        raise ValueError(f"Unexpected number of responses from {server.name}: {len(pts)}")

    return len(pts) != 0 and not isinstance(pts[0], HTTPResponse)


def get_header_name_translation(server: Server) -> dict[bytes, bytes]:
    pts = server.parsed_roundtrip([b"GET / HTTP/1.1\r\nHost: a\r\na-b: test\r\n\r\n"])
    if len(pts) != 1:
        raise ValueError(f"Unexpected number of responses from {server.name}: {len(pts)}")
    assert isinstance(pts[0], HTTPRequest)
    return {b"-": b"_"} if pts[0].has_header(b"a_b") else {}


def doesnt_support_version(server: Server) -> bool:
    pts1 = server.parsed_roundtrip([b"GET / HTTP/1.1\r\nHost: a\r\n\r\n"])
    if len(pts1) != 1:
        raise ValueError(f"Unexpected number of responses from {server.name}: {len(pts1)}")
    pt1 = pts1[0]
    assert isinstance(pt1, HTTPRequest)

    pts2 = server.parsed_roundtrip([b"GET / HTTP/1.0\r\nHost: a\r\n\r\n"])
    if len(pts2) != 1:
        pts2 = server.parsed_roundtrip([b"GET / HTTP/1.0\r\n\r\n"])
        if len(pts2) != 1:
            raise ValueError("Unexpected number of responses from {server.name}: {len(pts2)}")
    pt2 = pts2[0]
    assert isinstance(pt2, HTTPRequest)

    return pt1.version == pt2.version


def joins_duplicate_headers(server: Server) -> bool:
    pts = server.parsed_roundtrip([b"GET / HTTP/1.1\r\nHost: a\r\na: A\r\na: B\r\n\r\n"])
    if len(pts) != 1:
        raise ValueError(f"Unexpected number of responses from {server.name}: {len(pts)}")
    assert isinstance(pts[0], HTTPRequest)

    return pts[0].has_header(b"a", b"A, B") or pts[0].has_header(b"a", b"A,B")


def fails_sanity_check(server: Server) -> bool:
    pts = server.parsed_roundtrip([b"GET / HTTP/1.1\r\nHost: whatever\r\n\r\n"])
    return len(pts) != 1 or not isinstance(pts[0], HTTPRequest)


def main() -> None:
    arg_parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="This script tests the specified servers for a number of common HTTP parsing quirks that are usually considered benign. Its output can be used in `anomalies.yml` so that these benign discrepancies can be ignored.",
    )
    arg_parser.add_argument(
        "--servers",
        default=None,
        help="Comma-separated list of server names from docker-compose.yml. If omitted, uses all.",
    )

    args: argparse.Namespace = arg_parser.parse_args()

    servers: list[Server] = (
        list(SERVICE_DICT.values())
        if args.servers is None
        else (
            [SERVICE_DICT[s] for s in args.servers.split(",") if len(s) > 0]
            if args.servers is not None
            else []
        )
    )
    print("# This file generated by diagnose_anomalies.py")
    print("# This yaml file tracks the acceptable parsing anomalies in the servers.")

    list(map(fails_sanity_check, tqdm.tqdm(servers, desc="Sending warmup requests")))

    for server in tqdm.tqdm(servers, desc="Testing for host header requirements"):
        # This needs to be special-cased because roundtripping depends on
        # whether the server requires a specific host header value.
        server.requires_specific_host_header = False
        if requires_specific_host_header(server):
            server.requires_specific_host_header = True

    for i, val in enumerate(
        tqdm.tqdm((fails_sanity_check(server) for server in servers), desc="Sanity checking"),
    ):
        if val:
            raise ValueError(f"{servers[i].name} failed the sanity check!")

    for server in tqdm.tqdm(servers, desc="Anomaly testing"):
        print(f"{server.name}:")
        anomalies: dict[str, Any] = {}

        if server.requires_specific_host_header:
            anomalies["requires-specific-host-header"] = "true"

        if allows_http_0_9(server):
            anomalies["allows-http-0-9"] = "true"

        if doesnt_support_version(server):
            anomalies["doesnt-support-version"] = "true"

        allows_missing_host_header_rc: bool = allows_missing_host_header(server)
        if allows_missing_host_header_rc:
            anomalies["allows-missing-host-header"] = "true"

        method_whitelist = get_method_whitelist(server)
        if method_whitelist is not None:
            anomalies["method-whitelist"] = [m.decode("latin1") for m in method_whitelist]
        else:
            method_character_blacklist: bytes = get_method_character_blacklist(server)
            if len(method_character_blacklist) > 0:
                anomalies["method-character-blacklist"] = (
                    '"' + method_character_blacklist.decode("latin1") + '"'
                )
            if requires_alphabetical_method(server):
                anomalies["requires-alphabetical-method"] = "true"

        header_name_translation = get_header_name_translation(server)
        if len(header_name_translation) > 0:
            anomalies["header-name-translation"] = {
                k.decode("latin1"): v.decode("latin1") for k, v in header_name_translation.items()
            }

        added_headers = get_added_headers(server, method_whitelist, allows_missing_host_header_rc)
        if len(added_headers) > 0:
            anomalies["added-headers"] = [k.decode("latin1") for k in added_headers]

        removed_headers = get_removed_headers(server, header_name_translation)
        if len(removed_headers) > 0:
            anomalies["removed-headers"] = [k.decode("latin1") for k in removed_headers]

        trashed_headers = get_trashed_headers(server, header_name_translation)
        if len(trashed_headers) > 0:
            anomalies["trashed-headers"] = [k.decode("latin1") for k in trashed_headers]

        if requires_length_in_post(server):
            anomalies["requires-length-in-post"] = "true"

        if doesnt_support_persistence(server):
            anomalies["doesnt-support-persistence"] = "true"

        for k, v in anomalies.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
