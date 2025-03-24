""" This is where the fuzzing code goes. """

import enum
import itertools
from typing import Final

from http1 import (
    HTTPRequest,
    HTTPResponse,
    remove_request_header,
    translate_request_header_names,
)
from targets import Server
from util import translate


def normalize_request(r1: HTTPRequest, s1: Server, s2: Server) -> HTTPRequest:
    """Normalizes r1 with respect to r2.
    You almost certainly want to call this function twice.
    """
    # If s1 added headers to r1, remove them
    for k in s1.added_headers:
        r1 = remove_request_header(r1, k)

    # If s2 added headers to r2, remove them from r1
    # This ends up being symmetric since this function runs twice.
    for k in (translate(k, s1.header_name_translation) for k in s2.added_headers):
        r1 = remove_request_header(r1, k)

    # If s2 removed or trashed headers from r2, remove them from r1
    # If s1 trashes or (sometimes) removes headers, just remove them
    for k in (
        [translate(k, s1.header_name_translation) for k in s2.removed_headers + s2.trashed_headers]
        + s1.trashed_headers
        + s1.removed_headers
    ):
        r1 = remove_request_header(r1, k)

    # If s2 translates header names, then translate r1's header names.
    if len(s2.header_name_translation) > 0:
        r1 = translate_request_header_names(r1, s2.header_name_translation)

    r1.headers.sort()
    return r1


class ErrorType(enum.Enum):
    OK = 0  # Equal
    TYPE_DISCREPANCY = 1 # One rejected, one accepted
    RESPONSE_DISCREPANCY = 2  # Both responses, but different statuses
    REQUEST_DISCREPANCY = 3  # Both requests, but not equal
    STREAM_DISCREPANCY = 4  # Differing stream length or invalid stream
    INVALID = 5 # Parsed request violates RFCs

def categorize_discrepancy(
    pts1: list[HTTPRequest | HTTPResponse],
    pts2: list[HTTPRequest | HTTPResponse],
    s1: Server,
    s2: Server,
) -> ErrorType:
    if s1.doesnt_support_persistence or s2.doesnt_support_persistence:
        pts1 = pts1[:1]
        pts2 = pts2[:1]
    for r1, r2 in itertools.zip_longest(pts1, pts2):
        if isinstance(r1, HTTPRequest) and not r1.is_valid() or isinstance(r2, HTTPRequest) and not r2.is_valid():
            return ErrorType.INVALID

        # If one server responded 400, and the other didn't respond at all, that's okay
        if (r1 is None and isinstance(r2, HTTPResponse) and r2.code == b"400") or (
            r2 is None and isinstance(r1, HTTPResponse) and r1.code == b"400"
        ):
            break

        # One server didn't respond
        if (r1 is None or r2 is None) and r1 is not r2:
            return ErrorType.STREAM_DISCREPANCY

        # One server rejected and the other accepted:
        if (isinstance(r1, HTTPRequest) and not isinstance(r2, HTTPRequest)) or (
            not isinstance(r1, HTTPRequest) and isinstance(r2, HTTPRequest)
        ):
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

            # If one server has a method character blacklist, and the method has a character in the blacklist, that's okay.
            if (
                isinstance(r1, HTTPResponse)
                and isinstance(r2, HTTPRequest)
                and any(b in s1.method_character_blacklist for b in r2.method)
            ) or (
                isinstance(r2, HTTPResponse)
                and isinstance(r1, HTTPRequest)
                and any(b in s2.method_character_blacklist for b in r1.method)
            ):
                break

            return ErrorType.TYPE_DISCREPANCY

        # Both servers rejected
        if isinstance(r1, HTTPResponse) and isinstance(r2, HTTPResponse):
            if r1 != r2:
                return ErrorType.RESPONSE_DISCREPANCY

        # Both servers accepted:
        if isinstance(r1, HTTPRequest) and isinstance(r2, HTTPRequest):
            new_r1: HTTPRequest = normalize_request(r1, s1, s2)
            new_r2: HTTPRequest = normalize_request(r2, s2, s1)

            if new_r1 != new_r2:
                return ErrorType.REQUEST_DISCREPANCY

    return ErrorType.OK
