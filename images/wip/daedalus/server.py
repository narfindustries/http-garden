"""
A server to service the Daedalus parser
"""
import subprocess
import socket
import sys
import json
import base64
from typing import TypeGuard, Any

SOCKET_TIMEOUT: float = 0.1

json_t = int | bool | str | dict[str, "json_t"] | list["json_t"] | None

RECV_SIZE: int = 65536


def really_recv(sock: socket.socket) -> bytes:
    result: bytes = b""
    try:
        while b := sock.recv(RECV_SIZE):
            result += b
    except TimeoutError as e:
        pass
    return result


def extract_method(json_dict: dict[str, json_t]):
    """
    Extracts the method from Daedalus's JSON.
    """
    assert isinstance(json_dict["start"], dict)
    assert isinstance(json_dict["start"]["method"], dict)
    return next(iter(json_dict["start"]["method"]))[1:].encode("ascii")


def is_int_list(l: Any) -> TypeGuard[list[int]]:
    return isinstance(l, list) and all(isinstance(i, int) for i in l)


def extract_origin_uri(origin: dict[str, json_t]) -> bytes:
    result: bytes = b""
    assert isinstance(origin["path"], list)
    for segment in origin["path"]:
        assert isinstance(segment, list)
        assert is_int_list(segment)
        result += b"/" + bytes(segment)
    if origin["query"] is not None:
        assert isinstance(origin["query"], dict)
        assert is_int_list(origin["query"]["$$just"])
        result += b"?" + bytes(origin["query"]["$$just"])
    return result


def extract_absolute_uri(absolute_uri: dict[str, json_t]) -> bytes:
    assert is_int_list(absolute_uri["scheme"])
    result: bytes = bytes(absolute_uri["scheme"]) + b":"
    if absolute_uri["authority"] is not None:
        assert isinstance(absolute_uri["authority"], dict)
        assert isinstance(absolute_uri["authority"]["$$just"], dict)
        result += b"//"
        auth_dict: dict[str, json_t] = absolute_uri["authority"]["$$just"]
        if auth_dict["user_info"] is not None:
            assert isinstance(auth_dict["user_info"], dict)
            user_info: dict[str, json_t] = auth_dict["user_info"]
            assert is_int_list(user_info["$$just"])
            result += bytes(user_info["$$just"]) + b"@"
        assert isinstance(auth_dict["host"], dict)
        host: dict[str, json_t] = auth_dict["host"]
        if "$Named" in host:
            assert is_int_list(host["$Named"])
            result += bytes(host["$Named"])
        elif "$IPv4" in host:
            assert is_int_list(host["$IPv4"])
            result += ".".join(map(str, host["$IPv4"])).encode("ascii")
        elif "$IPLiteral" in host:
            result += b"["
            assert isinstance(host["$IPLiteral"], dict)
            ip_literal: dict[str, json_t] = host["$IPLiteral"]
            if "$IPv6" in ip_literal:
                assert is_int_list(ip_literal["$IPv6"])
                result += b":".join(hex(i)[2:].zfill(4).encode("ascii") for i in ip_literal["$IPv6"])
            elif "$IPvFuture" in ip_literal:
                assert isinstance(ip_literal["$IPvFuture"], dict)
                ipvfuture: dict[str, json_t] = ip_literal["$IPvFuture"]
                assert is_int_list(ipvfuture["version"])
                assert is_int_list(ipvfuture["data"])
                result += (
                    b"v"
                    + b"".join(hex(i)[2:].encode("ascii") for i in ipvfuture["version"])
                    + b"."
                    + bytes(ipvfuture["data"])
                )
            result += b"]"
        assert is_int_list(auth_dict["port"])
        port: bytes = "".join(map(str, auth_dict["port"])).encode("ascii")
        if len(port) != 0:
            result += b":" + port
    if not absolute_uri["rootless"]:
        result += b"/"
    segments: list[bytes] = []
    assert isinstance(absolute_uri["path"], list)
    for segment in absolute_uri["path"]:
        assert is_int_list(segment)
        segments.append(bytes(segment))
    result += b"/".join(segments)
    if absolute_uri["query"] is not None:
        assert isinstance(absolute_uri["query"], dict)
        assert is_int_list(absolute_uri["query"]["$$just"])
        result += b"?" + bytes(absolute_uri["query"]["$$just"])
    return result


def extract_uri(json_dict: dict[str, json_t]) -> bytes:
    """
    Extracts the URI from Daedalus's JSON.
    This currently doesn't support authority-form URIs because Daedalus has a bug.
    """
    assert isinstance(json_dict["start"], dict)
    start: dict[str, json_t] = json_dict["start"]
    assert isinstance(start["target"], dict)
    target: dict[str, json_t] = start["target"]
    assert len(target) == 1

    if "$Origin" in target:
        assert isinstance(target["$Origin"], dict)
        return extract_origin_uri(target["$Origin"])
    if "$AbsoluteURI" in target:
        assert isinstance(target["$AbsoluteURI"], dict)
        return extract_absolute_uri(target["$AbsoluteURI"])
    if "$Asterisk" in target:
        return b"*"
    assert False


def extract_body(json_dict: dict[str, json_t]) -> bytes:
    assert isinstance(json_dict["body"], dict)
    body: dict[str, json_t] = json_dict["body"]
    assert len(body) == 1
    if "$bytes" in body:
        assert "$chunked" not in body
        assert is_int_list(body["$bytes"])
        return bytes(body["$bytes"])
    if "$chunked" in body:
        assert isinstance(body["$chunked"], dict)
        assert isinstance(body["$chunked"]["chunks"], list)
        result: bytes = b""
        for chunk in body["$chunked"]["chunks"]:
            assert isinstance(chunk, dict)
            assert is_int_list(chunk["contents"])
            result += bytes(chunk["contents"])
        return result
    elif "$remaining" in body:
        assert is_int_list(body["$remaining"])
        # This field is only generated when an invalid Transfer-Encoding is specified.
        # Unhandled for now.
        print("Invalid transfer encoding!", file=sys.stderr)
        return b""
    assert False


def extract_header_field(field: dict[str, json_t]) -> tuple[bytes, bytes]:
    if "$Field" in field:
        assert isinstance(field["$Field"], dict)
        assert is_int_list(field["$Field"]["name"])
        assert is_int_list(field["$Field"]["value"])
        return (bytes(field["$Field"]["name"]), bytes(field["$Field"]["value"]))
    elif "$Content_Length" in field:
        assert isinstance(field["$Content_Length"], int)
        return (b"Content-Length", str(field["$Content_Length"]).encode("ascii"))
    elif "$Transfer_Encoding" in field:
        assert isinstance(field["$Transfer_Encoding"], dict)
        assert isinstance(field["$Transfer_Encoding"]["encodings"], list)
        values: list[bytes] = []
        for encoding in field["$Transfer_Encoding"]["encodings"]:
            assert isinstance(encoding, dict)
            assert is_int_list(encoding["type"])
            value: bytes = bytes(encoding["type"])
            assert isinstance(encoding["params"], list)
            for param in encoding["params"]:
                assert isinstance(param, dict)
                assert is_int_list(param["name"])
                value += b";" + bytes(param["name"])
                assert isinstance(param["value"], dict)
                if "$Token" in param["value"]:
                    assert is_int_list(param["value"]["$Token"])
                    value += b"=" + bytes(param["value"]["$Token"])
                elif "$QuotedString" in param["value"]:
                    assert is_int_list(param["value"]["$QuotedString"])
                    value += b'="' + bytes(param["value"]["$QuotedString"]) + b'"'
            values.append(value)
        if field["$Transfer_Encoding"]["is_chunked"]:
            values.append(b"chunked")
        return (b"Transfer-Encoding", b",".join(values))
    assert False


def extract_headers(json_dict: dict[str, json_t]) -> list[tuple[bytes, bytes]]:
    result: list[tuple[bytes, bytes]] = []
    assert isinstance(json_dict["field_info"], dict)
    assert isinstance(json_dict["field_info"]["fields"], list)
    for field in json_dict["field_info"]["fields"]:
        assert isinstance(field, dict)
        result.append(extract_header_field(field))

    assert isinstance(json_dict["body"], dict)
    if "$chunked" in json_dict["body"]:
        assert isinstance(json_dict["body"]["$chunked"], dict)
        assert isinstance(json_dict["body"]["$chunked"]["trailer_fields"], list)
        for field in json_dict["body"]["$chunked"]["trailer_fields"]:
            assert isinstance(field, dict)
            result.append(extract_header_field(field))

    return result


def extract_version(json_dict: dict[str, json_t]) -> bytes:
    """
    Extracts the version from Daedalus's JSON.
    """
    assert isinstance(json_dict["start"], dict)
    assert isinstance(json_dict["start"]["version"], dict)
    return (str(json_dict["start"]["version"]["major"]) + "." + str(json_dict["start"]["version"]["minor"])).encode("ascii")


DAEDALUS_COMMAND: list[
    str
] = "/bin/daedalus run HTTP-1.1.ddl --entry=HTTP_request --input=/dev/stdin --json".split(" ")


def main() -> None:
    """
    Receives requests over TCP port 80
    Responds with JSON parse trees.
    """
    server_sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(("0.0.0.0", 80))
    server_sock.listen()
    while True:
        client_sock, _ = server_sock.accept()
        client_sock.settimeout(SOCKET_TIMEOUT)
        with client_sock:
            proc: subprocess.CompletedProcess = subprocess.run(
                DAEDALUS_COMMAND, capture_output=True, input=really_recv(client_sock), check=False
            )
            try:
                daedalus_response_json: list[json_t] = json.loads(
                    proc.stdout,
                    parse_float=lambda s: s,
                    parse_constant=lambda s: s,
                )
            except json.decoder.JSONDecodeError:
                try:
                    reason: str = "You found a bug in Daedalus!"
                    client_sock.sendall(
                        f"HTTP/1.1 400 AWESOME\r\nContent-Length: {len(reason)}\r\n\r\n{reason}".encode(
                            "ascii"
                        )
                    )
                finally:
                    sys.exit(1)

            if isinstance(daedalus_response_json, list):
                assert len(daedalus_response_json) == 1
                assert isinstance(daedalus_response_json[0], dict)
                json_dict: dict[str, json_t] = daedalus_response_json[0]
                response_dict: dict[str, json_t] = {
                    "uri": base64.b64encode(extract_uri(json_dict)).decode("ascii"),
                    "body": base64.b64encode(extract_body(json_dict)).decode("ascii"),
                    "method": base64.b64encode(extract_method(json_dict)).decode("ascii"),
                    "headers": [
                        [base64.b64encode(name).decode("ascii"), base64.b64encode(value).decode("ascii")]
                        for name, value in extract_headers(json_dict)
                    ],
                    "version": base64.b64encode(extract_version(json_dict)).decode("ascii")
                }
                response_json: str = json.dumps(response_dict)
                response = (
                    f"HTTP/1.1 200 OK\r\nContent-Length: {len(response_json)}\r\n\r\n{response_json}".encode(
                        "ascii"
                    )
                )
            elif isinstance(daedalus_response_json, dict):
                assert "error" in daedalus_response_json
                response = b"HTTP/1.1 400 Bad Request\r\n\r\n"
            else:
                assert False

            try:
                client_sock.sendall(response)
            except ConnectionResetError:
                pass


if __name__ == "__main__":
    main()
