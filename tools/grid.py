from diff import ErrorType, categorize_discrepancy
from targets import Server
from fanout import fanout
from http1 import HTTPRequest, HTTPResponse

Grid = tuple[tuple[ErrorType | None, ...], ...]


def grid(payload: list[bytes], servers: list[Server]) -> Grid:
    pts: list[list[HTTPRequest | HTTPResponse]] = fanout(payload, servers)
    result = []
    for i, (s1, pt1) in enumerate(zip(servers, pts)):
        row: list[ErrorType | None] = []
        for j, (s2, pt2) in enumerate(zip(servers, pts)):
            if j < i:
                row.append(None)
            else:
                row.append(categorize_discrepancy(pt1, pt2, s1, s2))
        result.append(tuple(row))
    return tuple(result)
