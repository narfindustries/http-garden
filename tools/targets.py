""" Probes the Docker environment and config files to extract information about running services. """

import dataclasses
import sys
from pathlib import PosixPath

import docker  # type: ignore
import yaml


_DEFAULT_SERVER_TIMEOUT: float = 0.01
_DEFAULT_TRANSDUCER_TIMEOUT: float = 0.5
_NETWORK_NAME: str = "http-garden_default"
_COMPOSE_YML_PATH: PosixPath = PosixPath(f"{sys.path[0] or '.'}/../docker-compose.yml")
_EXTERNAL_YML_PATH: PosixPath = PosixPath(f"{sys.path[0] or '.'}/../external-services.yml")
_ANOMALIES_YML_PATH: PosixPath = PosixPath(f"{sys.path[0] or '.'}/../anomalies.yml")


@dataclasses.dataclass
class Service:
    """Service (server/proxy) configuration dataclass"""

    name: str  # The name of the Docker service
    container: (
        docker.models.containers.Container | None
    )  # The container for this service, or None for external services
    address: str  # An IP or hostname
    port: int  # A port
    requires_tls: bool  # Whether to use SSL
    timeout: float  # The fastest timeout that can be used in connections with this server
    is_traced: bool  # Whether this is traced.
    dump_count: int  # How many times we've cleared the coverage for this server. Used to ensure that trace collection doesn't get out of sync.

    allows_http_0_9: bool  # Whether HTTP/0.9 is accepted
    added_headers: list[
        tuple[bytes, bytes]
    ]  # Headers that are added to every request before passing it to the scripting backend
    translates_chunked_to_cl: bool  # Whether messages with chunked bodies have the Transfer-Encoding header replaced with a Content-Length header.
    translates_only_empty_chunked_to_cl: bool # Whether messages with empty chunked bodies have the Transfer-Encoding header replaced with a Content-Length header.
    adds_cl_to_chunked: bool  # Whether messages with chunked bodies get a Content-Length header tacked on.
    requires_length_in_post: (
        bool  # Whether a Content-Length or Transfer-Encoding header is required in all POST requests
    )
    allows_missing_host_header: bool  # Whether the server accepts requests that don't have a host header
    header_name_translation: dict[
        bytes, bytes
    ]  # Translation array to account for servers that replace characters before processing
    doesnt_support_version: bool  # Whether this server doesn't include a version in its response object
    method_whitelist: (
        list[bytes] | None
    )  # The list of methods that the server allows, or None if the server allows all methods.
    removed_headers: list[tuple[bytes, bytes]]


def _make_container_dict(network_name: str) -> dict[str, str]:
    """Constructs a dict that maps Docker aliases to their local IPs. Required because containers in the docker network are reachable from the host by IP."""
    try:
        network = docker.from_env().networks.get(network_name)
    except docker.errors.NotFound:
        return {}
    return {c.labels["com.docker.compose.service"]: c for c in network.containers}


def _get_container_ip(container: docker.models.containers.Container, network_name: str) -> str | None:
    if container is None:
        return None

    return container.attrs["NetworkSettings"]["Networks"][network_name]["IPAddress"]


def _extract_services(role: str) -> list[Service]:
    """Returns a list of the running services with the requested role as Service objects."""
    with open(_ANOMALIES_YML_PATH, encoding="latin1") as f:
        anomalies_dict: dict = yaml.safe_load(f)
    with open(_COMPOSE_YML_PATH, encoding="latin1") as f:
        services: dict = yaml.safe_load(f).get("services") or {}
    with open(_EXTERNAL_YML_PATH, encoding="latin1") as f:
        services |= yaml.safe_load(f) or {}

    result: list[Service] = []
    for svc_name in services:
        x_props: dict = services[svc_name].get("x-props") or {}
        if x_props.get("role") != role:
            continue

        container: docker.models.containers.Container | None = _CONTAINER_DICT.get(svc_name)
        address: str | None = x_props.get("address") or _get_container_ip(container, _NETWORK_NAME)
        if address is None:  # This is a local service that isn't running
            continue

        anomalies: dict = anomalies_dict.get(svc_name) or {}
        requires_tls: bool = x_props.get("requires-tls") or False
        is_traced = x_props.get("is-traced") or False
        dump_count: int = 0
        if is_traced:
            try:
                with open(f"/tmp/{svc_name}/dump_count", "rb") as f:
                    dump_count = f.read(1)[0] + 1
            except FileNotFoundError:
                pass

        result.append(
            Service(
                name=svc_name,
                container=container,
                address=address,
                port=x_props.get("port") or (443 if requires_tls else 80),
                requires_tls=requires_tls,
                timeout=float(
                    x_props.get("timeout")
                    or (_DEFAULT_SERVER_TIMEOUT if role == "server" else _DEFAULT_TRANSDUCER_TIMEOUT)
                ),
                is_traced=x_props.get("is-traced") or False,
                dump_count=dump_count,
                allows_http_0_9=anomalies.get("allows-http-0-9") or False,
                added_headers=[
                    (k.encode("latin1"), v.encode("latin1"))
                    for k, v in (anomalies.get("added-headers") or [])
                ],
                translates_chunked_to_cl=anomalies.get("translates-chunked-to-cl") or False,
                translates_only_empty_chunked_to_cl=anomalies.get("translates-only-empty-chunked-to-cl") or False,
                adds_cl_to_chunked=anomalies.get("adds-cl-to-chunked") or False,
                requires_length_in_post=anomalies.get("requires-length-in-post") or False,
                allows_missing_host_header=anomalies.get("allows-missing-host-header") or False,
                header_name_translation={
                    k.encode("latin1"): v.encode("latin1")
                    for k, v in (anomalies.get("header-name-translation") or {}).items()
                },
                doesnt_support_version=anomalies.get("doesnt-support-version") or False,
                method_whitelist=[s.encode("latin1") for s in anomalies.get("method-whitelist") or []]
                or None,
                removed_headers=[
                    (k.encode("latin1"), v.encode("latin1"))
                    for k, v in (anomalies.get("removed-headers") or [])
                ],
            )
        )
    return result


_CONTAINER_DICT: dict[str, str] = _make_container_dict(_NETWORK_NAME)

SERVER_DICT: dict[str, Service] = {server.name: server for server in _extract_services("server")}

TRANSDUCER_DICT: dict[str, Service] = {t.name: t for t in _extract_services("transducer")}
