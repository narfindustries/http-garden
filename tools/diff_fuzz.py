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


def normalize_request_wrt_response(r: HTTPRequest, s: Service) -> HTTPRequest:
    # If s added headers to r, then remove them.
    for k, v in s.added_headers:
        if r.has_header(k, v):
            r = remove_request_header(r, k, v)
    return r


def normalize_request_wrt_request(r1: HTTPRequest, s1: Service, r2: HTTPRequest, s2: Service) -> HTTPRequest:
    """
    Normalizes r1 with respect to r2.
    You almost certainly want to call this function twice.
    """
    # If s2 added headers to r2, then add them to r1 as well.
    for h in s2.added_headers:
        h_translated: tuple[bytes, bytes] = (translate(h[0], s1.header_name_translation), h[1])
        if r2.has_header(*h) and not r1.has_header(*h_translated):
            r1 = insert_request_header(r1, *h_translated)

    # If s1 removed headers from r1, then add them back to r1.
    for k, v in s1.removed_headers:
        if not r1.has_header(translate(k, s1.header_name_translation), v) and r2.has_header(translate(k, s2.header_name_translation), v):
            r1 = insert_request_header(r1, translate(k, s1.header_name_translation), v)

    te_header_name_1: bytes = translate(b"transfer-encoding", s1.header_name_translation)
    cl_header_name_1: bytes = translate(b"content-length", s1.header_name_translation)
    te_header_name_2: bytes = translate(b"transfer-encoding", s2.header_name_translation)
    cl_header_name_2: bytes = translate(b"content-length", s2.header_name_translation)

    # If s1 added a CL (in addition to TE) in r1, and s2 didn't do that to r2, then remove the CL header from r1.
    if (
        s1.adds_cl_to_chunked
        and not s2.adds_cl_to_chunked
        and r1.has_header(cl_header_name_1)
        and r1.has_header(te_header_name_1)
    ):
        r1 = remove_request_header(r1, cl_header_name_1)

    # If s2 replaced TE with CL in r2, then replace TE with CL in r1.
    if (
        s2.translates_chunked_to_cl
        and not s1.translates_chunked_to_cl
        and r1.has_header(te_header_name_1)
        and not r1.has_header(cl_header_name_1)
        and r2.has_header(cl_header_name_2)
        and not r2.has_header(te_header_name_2)
    ):
        r1 = remove_request_header(r1, te_header_name_1)
        r1.headers.append((cl_header_name_1, str(len(r1.body)).encode("latin1")))

    # If s2 translates header names, then translate r1's header names.
    if len(s2.header_name_translation) > 0:
        r1 = translate_request_header_names(r1, s2.header_name_translation)

    r1.headers.sort()
    return r1


class DiscrepancyType(enum.Enum):
    NO_DISCREPANCY = 0  # Equal
    STATUS_DISCREPANCY_GT = 11  # Both responses, but different statuses
    STATUS_DISCREPANCY_LT = 12  # Both responses, but different statuses
    SUBTLE_DISCREPANCY_GT = 21  # Both requests, but not equal
    SUBTLE_DISCREPANCY_LT = 22  # Both requests, but not equal
    STREAM_DISCREPANCY_GT = 31  # Differing stream length or invalid stream
    STREAM_DISCREPANCY_LT = 32  # Differing stream length or invalid stream


def categorize_discrepancy(
    parse_trees: list[list[HTTPRequest | HTTPResponse]], servers: list[Service]
) -> DiscrepancyType:
    for (pt1, s1), (pt2, s2) in itertools.combinations(zip(parse_trees, servers), 2):
        # If the stream is invalid, then we have an interesting result
        if stream_is_invalid(pt1):
            return DiscrepancyType.STREAM_DISCREPANCY_GT
        if stream_is_invalid(pt2):
            # print("Either {s1.name} or {s2.name} produced an invalid stream")
            return DiscrepancyType.STREAM_DISCREPANCY_LT
        for r1, r2 in itertools.zip_longest(pt1, pt2):
            # If one server responded 400, and the other didn't respond at all, that's okay.
            if (r1 is None and isinstance(r2, HTTPResponse) and r2.code == b"400") or (
                r2 is None and isinstance(r1, HTTPResponse) and r1.code == b"400"
            ):
                break

            # One server didn't respond
            if r1 is None and r2 is not None:
                return DiscrepancyType.STREAM_DISCREPANCY_GT
            if r2 is None and r1 is not None:
                return DiscrepancyType.STREAM_DISCREPANCY_LT
            # One server rejected and the other accepted:
            if (isinstance(r1, HTTPRequest) and not isinstance(r2, HTTPRequest)) or (
                not isinstance(r1, HTTPRequest) and isinstance(r2, HTTPRequest)
            ):
                if isinstance(r1, HTTPRequest):
                    r1 = normalize_request_wrt_response(r1, s1)
                elif isinstance(r2, HTTPRequest):
                    r2 = normalize_request_wrt_response(r2, s2)
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
                    (r1 is None or (isinstance(r1, HTTPResponse) and r1.code == b"400"))
                    and not s1.allows_missing_host_header
                    and isinstance(r2, HTTPRequest)
                    and s2.allows_missing_host_header
                    and not r2.has_header(b"host")
                ) or (
                    (r2 is None or (isinstance(r2, HTTPResponse) and r2.code == b"400"))
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

                print(f"{s1.name} rejects when {s2.name} accepts")
                print(r1)
                print(r2)
                return (
                    DiscrepancyType.STATUS_DISCREPANCY_GT
                    if r1 > r2
                    else DiscrepancyType.STATUS_DISCREPANCY_LT
                )
            # Both servers accepted:
            elif isinstance(r1, HTTPRequest) and isinstance(r2, HTTPRequest):
                new_r1: HTTPRequest = normalize_request_wrt_request(r1, s1, r2, s2)
                new_r2: HTTPRequest = normalize_request_wrt_request(r2, s2, r1, s1)
                r1 = new_r1
                r2 = new_r2

                if r1 > r2:
                    print(f"{s1.name} and {s2.name} accepted with different interpretations.")
                    print(r1)
                    print(r2)
                    return DiscrepancyType.SUBTLE_DISCREPANCY_GT
                if r1 < r2:
                    print(f"{s1.name} and {s2.name} accepted with different interpretations.")
                    print(r1)
                    print(r2)
                    return DiscrepancyType.SUBTLE_DISCREPANCY_LT
    return DiscrepancyType.NO_DISCREPANCY


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
        if categorize_discrepancy(parse_trees, servers) != DiscrepancyType.NO_DISCREPANCY:
            result_inducing_inputs.append(current_input)
        elif fingerprint not in seen:
            interesting_inputs.append(current_input)
        seen.add(fingerprint)
    return result_inducing_inputs, interesting_inputs
