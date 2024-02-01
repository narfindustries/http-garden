import itertools
from typing import Final, Iterable, TypeVar

import tqdm

from fanout import fanout
from http1 import (
    HTTPRequest,
    HTTPResponse,
    remove_request_header,
    insert_request_header,
    translate_chunked_to_cl,
    translate_request_header_names,
)
from mutations import mutate
from targets import Service

T = TypeVar("T")
U = TypeVar("U")
fingerprint_t = tuple[frozenset[int], ...]  # You might want to make this a hash.
stream_t = list[bytes]


_MIN_GENERATION_SIZE: Final[int] = 10
_SEEDS: Final[list[stream_t]] = [
    [b"GET / HTTP/1.1\r\n\r\n"],
    [b"POST / HTTP/1.1\r\nContent-Length: 10\r\nHost: b\r\n\r\n0123456789"],
    [
        b"POST / HTTP/1.1\r\nHost: c\r\nTransfer-Encoding: chunked\r\n\r\n5\r\n01234\r\n5\r\n56789\r\n0\r\n\r\n"
    ],
]


def unzip(collection: Iterable[tuple[T, U]]) -> tuple[list[T], list[U]]:
    return ([p[0] for p in collection], [p[1] for p in collection])


def stream_is_invalid(parse_trees: list[HTTPRequest | HTTPResponse]) -> bool:
    return any(isinstance(r, HTTPResponse) and r.code == b"400" for r in parse_trees[:-1])


def normalize_messages(
    r1: HTTPRequest | HTTPResponse | None, s1: Service, r2: HTTPRequest | HTTPResponse | None, s2: Service
):
    # If there are added headers and both parses succeeded, ensure that they're present in both structs.
    if isinstance(r1, HTTPRequest) and isinstance(r2, HTTPRequest):
        for h in s1.added_headers:
            if r1.has_header(*h) and not r2.has_header(*h):
                r2 = insert_request_header(r2, *h)
        for h in s2.added_headers:
            if r2.has_header(*h) and not r1.has_header(*h):
                r1 = insert_request_header(r1, *h)

    # If there are added headers and one parse failed, delete the added header from the request
    if isinstance(r1, HTTPRequest) and isinstance(r2, HTTPResponse):
        for h in s1.added_headers:
            r1 = remove_request_header(r1, *h)
    if isinstance(r2, HTTPRequest) and isinstance(r1, HTTPResponse):
        for h in s2.added_headers:
            r2 = remove_request_header(r2, *h)

    # If one server translates chunked bodies to use CL, do the translation for the other server too.
    if s1.translates_chunked_to_cl and not s2.translates_chunked_to_cl and isinstance(r2, HTTPRequest):
        r2 = translate_chunked_to_cl(r2)
    if s2.translates_chunked_to_cl and not s1.translates_chunked_to_cl and isinstance(r1, HTTPRequest):
        r1 = translate_chunked_to_cl(r1)

    # If there's header name translation, apply it uniformly.
    if len(s1.header_name_translation) > 0 and isinstance(r1, HTTPRequest) and isinstance(r2, HTTPRequest):
        r2 = translate_request_header_names(r2, s1.header_name_translation)
    if len(s2.header_name_translation) > 0 and isinstance(r2, HTTPRequest) and isinstance(r1, HTTPRequest):
        r1 = translate_request_header_names(r1, s2.header_name_translation)

    return r1, r2


def is_result(parse_trees: list[list[HTTPRequest | HTTPResponse]], servers: list[Service]) -> bool:
    for (pt1, s1), (pt2, s2) in itertools.combinations(zip(parse_trees, servers), 2):
        # If the stream is invalid, then we have an interesting result
        if stream_is_invalid(pt1) or stream_is_invalid(pt2):
            # print("Either {s1.name} or {s2.name} produced an invalid stream")
            return True
        for r1, r2 in itertools.zip_longest(pt1, pt2):
            # Normalize the messages
            r1, r2 = normalize_messages(r1, s1, r2, s2)
            # One server rejected and the other accepted:
            if (isinstance(r1, HTTPRequest) and not isinstance(r2, HTTPRequest)) or (
                not isinstance(r1, HTTPRequest) and isinstance(r2, HTTPRequest)
            ):
                # If one server responded 400, and the other didn't respond at all, that's okay.
                if (r1 is None and isinstance(r2, HTTPResponse) and r2.code == b"400") or (
                    r2 is None and isinstance(r1, HTTPResponse) and r1.code == b"400"
                ):
                    break
                # If one server parsed a request as HTTP/0.9, and the other doesn't allow 0.9, that's okay.
                if (
                    isinstance(r1, HTTPRequest)
                    and r1.version == b"0.9"
                    and isinstance(r2, HTTPResponse)
                    and not s2.allows_http_0_9
                ) or (
                    isinstance(r2, HTTPRequest)
                    and r2.version == b"0.9"
                    and isinstance(r1, HTTPResponse)
                    and not s2.allows_http_0_9
                ):
                    break
                # If one server requires length in POST requests, and the other doesn't, that's okay.
                if (
                    isinstance(r1, HTTPResponse)
                    and r1.code == b"411"
                    and s1.requires_length_in_post
                    and isinstance(r2, HTTPRequest)
                    and r2.method == b"POST"
                    and not s2.requires_length_in_post
                ) or (
                    isinstance(r2, HTTPResponse)
                    and r2.code == b"411"
                    and s2.requires_length_in_post
                    and isinstance(r1, HTTPRequest)
                    and r1.method == b"POST"
                    and not s1.requires_length_in_post
                ):
                    break
                # If one server requires the host header, and the other doesn't, that's okay.
                if (
                    isinstance(r1, HTTPResponse)
                    and r1.code == b"400"
                    and not s1.allows_missing_host_header
                    and isinstance(r2, HTTPRequest)
                    and s2.allows_missing_host_header
                    and not r2.has_header(b"host")
                ) or (
                    isinstance(r2, HTTPResponse)
                    and r2.code == b"400"
                    and not s2.allows_missing_host_header
                    and isinstance(r1, HTTPRequest)
                    and s1.allows_missing_host_header
                    and not r1.has_header(b"host")
                ):
                    break
                # print(f"{s1.name} rejects when {s2.name} accepts")
                return True
            # Both servers accepted:
            if isinstance(r1, HTTPRequest) and isinstance(r2, HTTPRequest):
                if r1 != r2:
                    # print(f"{s1.name} and {s2.name} accepted with different interpretations.")
                    return True
    return False


def run_one_generation(
    servers: list[Service], inputs: list[stream_t], seen: set[fingerprint_t]
) -> tuple[list[stream_t], list[stream_t]]:
    """
    Takes a list of servers, inputs, and seen fingerprints.
    Returns (result_inducing_inputs, interesting_inputs)
    """
    result_inducing_inputs: list[stream_t] = []
    interesting_inputs: list[stream_t] = []
    for current_input in tqdm.tqdm(inputs):
        parse_trees, fingerprint_l = unzip(fanout(current_input, servers))
        fingerprint = tuple(fingerprint_l)
        if is_result(parse_trees, servers):
            result_inducing_inputs.append(current_input)
        elif fingerprint not in seen:
            interesting_inputs.append(current_input)
        seen.add(fingerprint)
    return result_inducing_inputs, interesting_inputs


def report(results: stream_t) -> None:
    print(results)


def generate_inputs(interesting_inputs: list[stream_t], min_generation_size: int) -> list[stream_t]:
    result: list[stream_t] = []
    while len(result) < min_generation_size:
        result.extend(map(mutate, interesting_inputs))
    return result


def fuzz(servers: list[Service], seeds: list[stream_t], min_generation_size: int) -> None:
    inputs: list[stream_t] = list(seeds)
    seen: set[fingerprint_t] = set()
    while len(inputs) > 0:
        results, interesting = run_one_generation(servers, inputs, seen)
        print(results)
        print(f"{len(interesting)} interesting inputs encountered.")
        inputs = generate_inputs(interesting, min_generation_size)


if __name__ == "__main__":
    import argparse
    from targets import SERVER_DICT

    def main() -> None:
        arg_parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Narf HTTP fuzzer script.")
        arg_parser.add_argument(
            "--servers",
            required=True,
            help="Comma-separated list of server names from docker-compose.yml.",
        )
        args: argparse.Namespace = arg_parser.parse_args()
        servers: list[Service] = [SERVER_DICT[s] for s in args.servers.split(",")]
        fuzz(servers, _SEEDS, _MIN_GENERATION_SIZE)

    main()
