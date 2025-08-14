"""
Probes the Docker environment and config files to extract information about running services.
Also contains code for interacting with the running containers.
"""

import base64
import dataclasses
import re
import sys
import socket
from pathlib import PosixPath
from typing import Any

import docker
import yaml
from docker.models.containers import Container

from http1 import (
    HTTPRequest,
    HTTPResponse,
    parse_request_stream,
    parse_http_0_9_response,
    parse_response,
    parse_response_json,
    strip_http_0_9_headers,
)
from util import ssl_wrap, roundtrip_to_server, recvall

_DEFAULT_ORIGIN_TIMEOUT: float = 0.02
_DEFAULT_TRANSDUCER_TIMEOUT: float = 0.5
_NETWORK_NAME: str = "http-garden_default"
_COMPOSE_YML_PATH: PosixPath = PosixPath(f"{sys.path[0] or '.'}/../docker-compose.yml")
_EXTERNAL_YML_PATH: PosixPath = PosixPath(f"{sys.path[0] or '.'}/../external-services.yml")
_ANOMALIES_YML_PATH: PosixPath = PosixPath(f"{sys.path[0] or '.'}/../anomalies.yml")


@dataclasses.dataclass
class Server:
    """Server (server/proxy) configuration dataclass"""

    name: str  # The name of the Docker service
    container: (
        Container | None
    )  # The container for this service, or None for external services
    address: str  # An IP or hostname
    port: int  # A port
    requires_tls: bool  # Whether to use SSL
    timeout: float  # The fastest timeout that can be used in connections with this server

    allows_http_0_9: bool  # Whether HTTP/0.9 is accepted
    added_headers: list[
        bytes
    ]  # Header keys that are added to every request before passing it to the scripting backend
    requires_length_in_post: bool  # Whether a Content-Length or Transfer-Encoding header is required in all POST requests
    allows_missing_host_header: (
        bool  # Whether the server accepts requests that don't have a host header
    )
    header_name_translation: dict[
        bytes,
        bytes,
    ]  # Translation array to account for servers that replace characters before processing
    doesnt_support_version: (
        bool  # Whether this server doesn't include a version in its response object
    )
    method_character_blacklist: (
        bytes  # The tchars that this server doesn't allow in methods
    )
    method_whitelist: (
        list[bytes] | None
    )  # The list of methods that the server allows, or None if the server allows all methods.
    removed_headers: list[
        bytes
    ]  # The list of header keys that this server removes from incoming requests
    trashed_headers: list[
        bytes
    ]  # The list of header keys that this server overwrites from incoming requests
    doesnt_support_persistence: (
        bool  # Whether this server supports keep-alive and pipelining
    )
    requires_specific_host_header: (
        bool  # Whether this server requires that the host header have a particular value
    )
    joins_duplicate_headers: bool # Whether this server joins duplicate headers
    duplicate_header_joiner: bytes # The byte sequence inserted between header values that have been joined. Usually b", ".

    def parsed_roundtrip(self, _data: list[bytes]) -> list[HTTPRequest | HTTPResponse]:
        raise AssertionError

    def unparsed_roundtrip(self, _data: list[bytes]) -> list[bytes]:
        raise AssertionError

def _make_container_dict(network_name: str) -> dict[str, Container]:
    """Constructs a dict that maps Docker aliases to their local IPs. Required because containers in the docker network are reachable from the host by IP."""
    try:
        return {
            c.labels["com.docker.compose.service"]: c
            for c in docker.from_env().networks.get(network_name).containers
        }
    except docker.errors.NotFound:  # type: ignore
        return {}


def _get_container_ip(container: Container | None, network_name: str) -> str | None:
    if container is None:
        return None

    return container.attrs["NetworkSettings"]["Networks"][network_name]["IPAddress"]


def _extract_services() -> list[Server]:
    """Returns a list of the running services with the requested role as Server objects."""
    with open(_ANOMALIES_YML_PATH, encoding="latin1") as f:
        anomalies_dict: dict = yaml.safe_load(f) or {}
    with open(_COMPOSE_YML_PATH, encoding="latin1") as f:
        internal_services: dict = yaml.safe_load(f).get("services", {})
    with open(_EXTERNAL_YML_PATH, encoding="latin1") as f:
        external_services: dict = yaml.safe_load(f) or {}
    services: dict = internal_services | external_services

    containers_that_arent_running: list[str] = []
    result: list[Server] = []
    for svc_name, svc in services.items():
        x_props: dict[str, Any] = svc.get("x-props", {})
        cls = Server
        if x_props.get("role") == "origin":
            cls = Origin
        elif x_props.get("role") == "transducer":
            cls = Transducer

        container: Container | None = _CONTAINER_DICT.get(svc_name)
        if cls != Server and container is None and svc_name not in external_services:
            containers_that_arent_running.append(svc_name)
            continue

        untyped_address: Any = x_props.get("address", _get_container_ip(container, _NETWORK_NAME))
        if not isinstance(untyped_address, str):
            continue
        address: str = untyped_address

        anomalies: dict = anomalies_dict.get(svc_name, {}) or {}
        requires_tls: bool = x_props.get("requires-tls", False)
        result.append(
            cls(
                name=svc_name,
                container=container,
                address=address,
                port=x_props.get("port", 443 if requires_tls else 80),
                requires_tls=requires_tls,
                timeout=float(
                    x_props.get("timeout")
                    or (
                        _DEFAULT_ORIGIN_TIMEOUT
                        if x_props.get("role") == "origin"
                        else _DEFAULT_TRANSDUCER_TIMEOUT
                    ),
                ),
                allows_http_0_9=anomalies.get("allows-http-0-9", False),
                added_headers=[
                    k.encode("latin1") for k in (anomalies.get("added-headers", []))
                ],
                requires_length_in_post=anomalies.get("requires-length-in-post", False),
                allows_missing_host_header=anomalies.get(
                    "allows-missing-host-header", False
                ),
                header_name_translation={
                    k.encode("latin1"): v.encode("latin1")
                    for k, v in (anomalies.get("header-name-translation", {})).items()
                },
                doesnt_support_version=anomalies.get("doesnt-support-version", False),
                method_whitelist=[
                    s.encode("latin1") for s in anomalies.get("method-whitelist", [])
                ]
                or None,
                method_character_blacklist=anomalies.get(
                    "method-character-blacklist", ""
                ).encode("latin1"),
                removed_headers=[
                    k.encode("latin1") for k in (anomalies.get("removed-headers", []))
                ],
                trashed_headers=[
                    k.encode("latin1") for k in (anomalies.get("trashed-headers", []))
                ],
                doesnt_support_persistence=anomalies.get(
                    "doesnt-support-persistence", False
                ),
                requires_specific_host_header=anomalies.get(
                    "requires-specific-host-header", False
                ),
                joins_duplicate_headers=anomalies.get("joins-duplicate-headers", False),
                duplicate_header_joiner=anomalies.get("duplicate-header-joiner", "").encode("latin1"),
            ),
        )

    if len(containers_that_arent_running) > 0:
        print(
            f"Warning: {', '.join(containers_that_arent_running)} container(s) not running!",
            file=sys.stderr,
        )
    return result


class Origin(Server):
    def unparsed_roundtrip(self, data: list[bytes]) -> list[bytes]:
        """Sends data, then receives data over TCP (potentially with SSL) to host:port"""
        if self.requires_specific_host_header:
            data = adjust_host_header(data, self.address.encode("latin1"))

        with socket.create_connection((self.address, self.port)) as sock:
            if self.requires_tls:
                sock = ssl_wrap(sock, self.address)
            sock.settimeout(self.timeout)
            return roundtrip_to_server(sock, data)

    def parsed_roundtrip(self, data: list[bytes]) -> list[HTTPRequest | HTTPResponse]:
        pieces = self.unparsed_roundtrip(data)
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

            if extracted is None and self.allows_http_0_9:
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
                    f"Couldn't parse {self.name}'s response to {data!r}:\n    {remaining!r}",
                    file=sys.stderr,
                )
                new_remaining = b""
            else:
                result.append(extracted)
            remaining = new_remaining
        return result


def adjust_host_header(data: list[bytes], new_value: bytes) -> list[bytes]:
    return [
        re.sub(
            rb"[Hh][Oo][Ss][Tt]:[^\r\n]*\r?\n",
            b"Host: " + new_value + b"\r\n",
            datum,
        )
        for datum in data
    ]


class Transducer(Server):
    def unparsed_roundtrip(self, data: list[bytes]) -> list[bytes]:
        if self.requires_specific_host_header:
            data = adjust_host_header(data, self.address.encode("latin1"))
        sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.address, self.port))
        sock.settimeout(self.timeout)
        if self.requires_tls:
            sock = ssl_wrap(sock, self.address)
        pcap_sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        pcap_sock.connect((self.address, 0xda1e))
        pcap_sock.settimeout(0.01)
        pcap_sock.shutdown(socket.SHUT_WR) # We're not writing into this
        _dummy_response: list[bytes] = roundtrip_to_server(sock, data)
        sock.close()
        result: list[bytes] = []
        for line in recvall(pcap_sock).splitlines():
            _ip, _port, pcap_data = map(base64.b64decode, line.split(b":"))
            result.append(pcap_data)
        pcap_sock.close()
        return result

    def parsed_roundtrip(self, data: list[bytes]) -> list[HTTPRequest | HTTPResponse]:
        result, leftovers = parse_request_stream(b"".join(self.unparsed_roundtrip(data)))
        if leftovers:
            print("{self.name} left some extra data on the end of the request stream: {leftovers}", file=sys.stderr)
        return [*result] # This is just to satisfy mypy. Really dumb that it can't figure this out.

    def update_payload(self, data: list[bytes]) -> None:
        with socket.create_connection((self.address, 0xda1e)) as sock:
            sock.settimeout(0.01)
            sock.shutdown(socket.SHUT_RD)
            sock.sendall(b":".join(base64.b64encode(datum) for datum in data))


_CONTAINER_DICT: dict[str, Container] = _make_container_dict(_NETWORK_NAME)

SERVER_DICT: dict[str, Server] = {
    s.name: s
    for s in sorted(_extract_services(), key=lambda s: s.name)
    if isinstance(s, (Origin, Transducer))
}

TRANSDUCER_DICT: dict[str, Transducer] = {
    k: v for k, v in SERVER_DICT.items() if isinstance(v, Transducer)
}
