""" This is where the fuzzing code goes. """

import enum
import itertools
from typing import Final

import tqdm

from fanout import fanout
from http1 import (
    HTTPRequest,
    HTTPResponse,
    remove_request_header,
    insert_request_header,
    translate_request_header_names,
)
from targets import Service
from util import stream_t, unzip, fingerprint_t, translate

_MIN_GENERATION_SIZE: Final[int] = 10
SEEDS: Final[list[stream_t]] = [
    [b"GET / HTTP/1.1\r\n\r\n"],
    [b"POST / HTTP/1.1\r\nContent-Length: 10\r\nHost: b\r\n\r\n0123456789"],
    [
        b"POST / HTTP/1.1\r\nHost: c\r\nTransfer-Encoding: chunked\r\n\r\n5\r\n01234\r\n5\r\n56789\r\n0\r\n\r\n"
    ],
]


def stream_is_invalid(parse_trees: list[HTTPRequest | HTTPResponse]) -> bool:
    return any(isinstance(r, HTTPResponse) and r.code == b"400" for r in parse_trees[:-1])


def normalize_messages(
    r1: HTTPRequest | HTTPResponse | None, s1: Service, r2: HTTPRequest | HTTPResponse | None, s2: Service
):
    # If both parses succeeded,
    if isinstance(r1, HTTPRequest) and isinstance(r2, HTTPRequest):
        h_translated: tuple[bytes, bytes]

        # ... and there are added headers, ensure that they're present in both requests.
        for h in s1.added_headers:
            h_translated = (translate(h[0], s2.header_name_translation), h[1])
            if r1.has_header(*h) and not r2.has_header(*h_translated):
                r2 = insert_request_header(r2, *h_translated)
        for h in s2.added_headers:
            h_translated = (translate(h[0], s1.header_name_translation), h[1])
            if r2.has_header(*h) and not r1.has_header(*h_translated):
                r1 = insert_request_header(r1, *h_translated)

        # ... and there are removed headers, ensure that they're added back if needed:
        for h in s1.removed_headers:
            h_translated = (translate(h[0], s2.header_name_translation), h[1])
            if not r1.has_header(*h) and r2.has_header(*h_translated):
                r1 = insert_request_header(r1, *h)
        for h in s2.removed_headers:
            h_translated = (translate(h[0], s1.header_name_translation), h[1])
            if not r2.has_header(*h) and r1.has_header(*h_translated):
                r2 = insert_request_header(r2, *h)

    # If there are added headers and one parse failed, delete the added header from the request
    if isinstance(r1, HTTPRequest) and isinstance(r2, HTTPResponse):
        for h in s1.added_headers:
            r1 = remove_request_header(r1, *h)
    if isinstance(r2, HTTPRequest) and isinstance(r1, HTTPResponse):
        for h in s2.added_headers:
            r2 = remove_request_header(r2, *h)

    # If one server translates chunked bodies to use CL, do the translation for the other server too.
    if s1.translates_chunked_to_cl and not s2.translates_chunked_to_cl and isinstance(r2, HTTPRequest):
        te_header_name = translate(b"transfer-encoding", s2.header_name_translation)
        if r2.has_header(te_header_name):
            r2 = remove_request_header(r2, te_header_name)
            cl_header_name = translate(b"content-length", s2.header_name_translation)
            r2.headers += [(cl_header_name, str(len(r2.body)).encode("latin1"))]
            r2.headers.sort()
    if s2.translates_chunked_to_cl and not s1.translates_chunked_to_cl and isinstance(r1, HTTPRequest):
        te_header_name = translate(b"transfer-encoding", s1.header_name_translation)
        if r1.has_header(te_header_name):
            r1 = remove_request_header(r1, te_header_name)
            cl_header_name = translate(b"content-length", s1.header_name_translation)
            r1.headers += [(cl_header_name, str(len(r1.body)).encode("latin1"))]
            r1.headers.sort()

    # If there's header name translation, apply it uniformly.
    if len(s1.header_name_translation) > 0 and isinstance(r1, HTTPRequest) and isinstance(r2, HTTPRequest):
        r2 = translate_request_header_names(r2, s1.header_name_translation)
    if len(s2.header_name_translation) > 0 and isinstance(r2, HTTPRequest) and isinstance(r1, HTTPRequest):
        r1 = translate_request_header_names(r1, s2.header_name_translation)

    return r1, r2


class DiscrepancyType(enum.Enum):
    NoDiscrepancy = 0
    StatusDiscrepancy = 1
    SubtleDiscrepancy = 2
    StreamDiscrepancy = 3


def categorize_discrepancy(
    parse_trees: list[list[HTTPRequest | HTTPResponse]], servers: list[Service]
) -> DiscrepancyType:
    for (pt1, s1), (pt2, s2) in itertools.combinations(zip(parse_trees, servers), 2):
        # If the stream is invalid, then we have an interesting result
        if stream_is_invalid(pt1) or stream_is_invalid(pt2):
            # print("Either {s1.name} or {s2.name} produced an invalid stream")
            return DiscrepancyType.StreamDiscrepancy
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
                    and not s1.allows_missing_host_header
                    and isinstance(r2, HTTPRequest)
                    and s2.allows_missing_host_header
                    and not r2.has_header(b"host")
                ) or (
                    isinstance(r2, HTTPResponse)
                    and not s2.allows_missing_host_header
                    and isinstance(r1, HTTPRequest)
                    and s1.allows_missing_host_header
                    and not r1.has_header(b"host")
                ):
                    break
                # If one server has a method whitelist, and the request wasn't on it, that's okay.
                if (
                    s1.method_whitelist is not None
                    and isinstance(r1, HTTPResponse)
                    and isinstance(r2, HTTPRequest)
                    and r2.method not in s1.method_whitelist
                ) or (
                    s2.method_whitelist is not None
                    and isinstance(r2, HTTPResponse)
                    and isinstance(r1, HTTPRequest)
                    and r1.method not in s2.method_whitelist
                ):
                    break

                # print(f"{s1.name} rejects when {s2.name} accepts")
                return DiscrepancyType.StatusDiscrepancy  # True
            # Both servers accepted:
            if isinstance(r1, HTTPRequest) and isinstance(r2, HTTPRequest):
                if r1 != r2:
                    # print(f"{s1.name} and {s2.name} accepted with different interpretations.")
                    return DiscrepancyType.SubtleDiscrepancy
    return DiscrepancyType.NoDiscrepancy


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
        if categorize_discrepancy(parse_trees, servers) != DiscrepancyType.NoDiscrepancy:
            result_inducing_inputs.append(current_input)
        elif fingerprint not in seen:
            interesting_inputs.append(current_input)
        seen.add(fingerprint)
    return result_inducing_inputs, interesting_inputs
